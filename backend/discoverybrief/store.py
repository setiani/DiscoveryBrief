"""Single-process SQLite persistence for private local runs."""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from uuid import NAMESPACE_URL, uuid4, uuid5

from discoverybrief.schemas import RunRequest


class Conflict(Exception):
    pass


class QueueFull(Exception):
    pass


STAGES = (
    "queued",
    "planning",
    "researching",
    "analyzing",
    "verifying",
    "composing",
    "auditing",
    "rendering",
    "finished",
)


def encoded_request(request: RunRequest) -> tuple[str, str]:
    payload = request.model_dump(mode="json", exclude={"client_request_id"})
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return encoded, hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class RunStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = RLock()
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            self.db.close()
            raise ValueError("unsupported newer database schema")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY, client_request_id TEXT UNIQUE,
                request_hash TEXT NOT NULL, request_json TEXT NOT NULL,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                status TEXT NOT NULL, stage TEXT NOT NULL, error_code TEXT,
                research_mode TEXT NOT NULL DEFAULT 'fixture'
            );
            CREATE TABLE IF NOT EXISTS events (
                run_id TEXT NOT NULL REFERENCES runs(run_id), seq INTEGER NOT NULL,
                at TEXT NOT NULL, event_type TEXT NOT NULL, summary TEXT NOT NULL,
                PRIMARY KEY(run_id, seq)
            );
            CREATE TABLE IF NOT EXISTS results (
                run_id TEXT PRIMARY KEY REFERENCES runs(run_id), payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                run_id TEXT NOT NULL REFERENCES runs(run_id), name TEXT NOT NULL,
                relative_path TEXT NOT NULL, sha256 TEXT NOT NULL, size_bytes INTEGER NOT NULL,
                media_type TEXT NOT NULL, PRIMARY KEY(run_id,name)
            );
            CREATE TABLE IF NOT EXISTS ledgers (
                run_id TEXT NOT NULL REFERENCES runs(run_id), kind TEXT NOT NULL,
                item_id TEXT NOT NULL, payload_json TEXT NOT NULL,
                PRIMARY KEY(run_id,kind,item_id)
            );
        """)
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(runs)")}
        if "research_mode" not in columns:
            self.db.execute(
                "ALTER TABLE runs ADD COLUMN research_mode TEXT NOT NULL DEFAULT 'fixture'"
            )
        for column in ("started_at", "finished_at"):
            if column not in columns:
                self.db.execute(f"ALTER TABLE runs ADD COLUMN {column} TEXT")
        event_columns = {row[1] for row in self.db.execute("PRAGMA table_info(events)")}
        if "metadata_json" not in event_columns:
            self.db.execute(
                "ALTER TABLE events ADD COLUMN metadata_json TEXT NOT NULL DEFAULT '{}'"
            )
        self.db.execute("PRAGMA user_version=1")
        self.db.commit()

    def close(self):
        self.db.close()

    def _event(
        self,
        run_id: str,
        at: str,
        kind: str,
        summary: str,
        metadata: dict | None = None,
    ) -> None:
        seq = self.db.execute(
            "SELECT COALESCE(MAX(seq),0)+1 FROM events WHERE run_id=?", (run_id,)
        ).fetchone()[0]
        self.db.execute(
            "INSERT INTO events (run_id,seq,at,event_type,summary,metadata_json) VALUES (?,?,?,?,?,?)",
            (run_id, seq, at, kind, summary, json.dumps(metadata or {})),
        )

    def events(self, run_id: str, after: int = 0) -> list[dict]:
        with self.lock:
            rows = self.db.execute(
                "SELECT seq,at,event_type,summary,metadata_json FROM events WHERE run_id=? AND seq>? ORDER BY seq LIMIT 200",
                (run_id, after),
            ).fetchall()
        return [
            {
                "seq": row[0],
                "event_id": str(uuid5(NAMESPACE_URL, f"{run_id}/{row[0]}")),
                "run_id": run_id,
                "at": row[1],
                "type": {
                    "queued": "stage_started",
                    "started": "stage_started",
                    "finished": "run_finished",
                    "cancelled": "run_finished",
                    "interrupted": "run_finished",
                }.get(row[2], row[2]),
                "summary": row[3],
                "stage": row[3].split(": ")[-1] if row[2] == "stage_started" else None,
                "metadata": json.loads(row[4]),
            }
            for row in rows
        ]

    def find_duplicate(self, request: RunRequest) -> str | None:
        if not request.client_request_id:
            return None
        _, digest = encoded_request(request)
        with self.lock:
            row = self.db.execute(
                "SELECT run_id,request_hash FROM runs WHERE client_request_id=?",
                (str(request.client_request_id),),
            ).fetchone()
        if row and row[1] != digest:
            raise Conflict("IDEMPOTENCY_CONFLICT")
        return row[0] if row else None

    def create(
        self, request: RunRequest, now: datetime, research_mode: str = "fixture"
    ) -> tuple[str, bool]:
        if research_mode not in {"fixture", "live", "replay"}:
            raise ValueError("unsupported run mode")
        encoded, digest = encoded_request(request)
        client_id = (
            str(request.client_request_id) if request.client_request_id else None
        )
        with self.lock, self.db:
            duplicate = self.find_duplicate(request)
            if duplicate:
                return duplicate, False
            if research_mode == "live":
                request.validate_horizon(now)
            pending = self.db.execute(
                "SELECT count(*) FROM runs WHERE status='queued'"
            ).fetchone()[0]
            if pending >= 3:
                raise QueueFull("QUEUE_FULL")
            run_id = str(uuid4())
            at = now.astimezone(UTC).isoformat()
            self.db.execute(
                "INSERT INTO runs (run_id,client_request_id,request_hash,request_json,created_at,updated_at,status,stage,error_code,research_mode) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    client_id,
                    digest,
                    encoded,
                    at,
                    at,
                    "queued",
                    "queued",
                    None,
                    research_mode,
                ),
            )
            self._event(run_id, at, "queued", "Run queued", {"stage": "queued"})
            return run_id, True

    def get(self, run_id: str) -> dict | None:
        with self.lock:
            row = self.db.execute(
                "SELECT run_id, created_at, updated_at, status, stage, error_code, request_json, research_mode, started_at, finished_at FROM runs WHERE run_id=?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        request = json.loads(row[6])
        return {
            "run_id": row[0],
            "created_at": row[1],
            "updated_at": row[2],
            "status": row[3],
            "stage": row[4],
            "error_code": row[5],
            "company_name": request["company_name"],
            "meeting_at": request["meeting_at"],
            "research_mode": row[7],
            "started_at": row[8],
            "finished_at": row[9],
        }

    def request(self, run_id: str) -> RunRequest | None:
        """Internal access only; API summaries must not return raw private input."""
        with self.lock:
            row = self.db.execute(
                "SELECT request_json FROM runs WHERE run_id=?", (run_id,)
            ).fetchone()
        return RunRequest.model_validate_json(row[0]) if row else None

    def list_runs(self, limit: int = 20) -> list[dict]:
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        with self.lock:
            ids = [
                row[0]
                for row in self.db.execute(
                    "SELECT run_id FROM runs ORDER BY created_at DESC, rowid DESC LIMIT ?",
                    (limit,),
                )
            ]
        return [item for run_id in ids if (item := self.get(run_id)) is not None]

    def claim_next(self, now: datetime) -> tuple[str, RunRequest, datetime] | None:
        """Claim one queued run; one process/worker only, never a distributed queue."""
        with self.lock, self.db:
            active = self.db.execute(
                "SELECT count(*) FROM runs WHERE status='running'"
            ).fetchone()[0]
            if active:
                return None
            row = self.db.execute(
                "SELECT run_id,request_json,created_at FROM runs WHERE status='queued' ORDER BY created_at, rowid LIMIT 1"
            ).fetchone()
            if row is None:
                return None
            self.db.execute(
                "UPDATE runs SET status='running',stage='planning',updated_at=?,started_at=? WHERE run_id=? AND status='queued'",
                (
                    now.astimezone(UTC).isoformat(),
                    now.astimezone(UTC).isoformat(),
                    row[0],
                ),
            )
            self._event(
                row[0], now.astimezone(UTC).isoformat(), "started", "Run started"
            )
            return (
                row[0],
                RunRequest.model_validate_json(row[1]),
                datetime.fromisoformat(row[2]),
            )

    def finish(
        self,
        run_id: str,
        status: str,
        now: datetime,
        error_code: str | None = None,
        result: dict | None = None,
    ) -> None:
        if status not in ("completed", "failed", "needs_input"):
            raise ValueError("invalid terminal state")
        with self.lock, self.db:
            cursor = self.db.execute(
                "UPDATE runs SET status=?,stage='finished',error_code=?,updated_at=?,finished_at=? WHERE run_id=? AND status='running'",
                (
                    status,
                    error_code,
                    now.astimezone(UTC).isoformat(),
                    now.astimezone(UTC).isoformat(),
                    run_id,
                ),
            )
            if cursor.rowcount != 1:
                raise Conflict("STATE_CONFLICT")
            if result is not None:
                if (
                    status not in ("completed", "needs_input")
                    or result.get("status") != status
                ):
                    raise ValueError("result status must match terminal status")
                self.db.execute(
                    "INSERT INTO results VALUES (?,?)",
                    (run_id, json.dumps(result, ensure_ascii=False)),
                )
            self._event(
                run_id,
                now.astimezone(UTC).isoformat(),
                "finished",
                "Run finished: " + status,
            )

    def update_stage(self, run_id: str, stage: str, now: datetime) -> None:
        if stage not in STAGES[1:-1]:
            raise ValueError("invalid stage")
        with self.lock, self.db:
            row = self.db.execute(
                "SELECT status,stage FROM runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if not row or row[0] != "running":
                raise Conflict("STATE_CONFLICT")
            if STAGES.index(stage) < STAGES.index(row[1]):
                raise Conflict("STAGE_REGRESSION")
            if row[1] == stage:
                return
            at = now.astimezone(UTC).isoformat()
            self._event(
                run_id,
                at,
                "stage_completed",
                "Stage completed: " + row[1],
                {"stage": row[1]},
            )
            self.db.execute(
                "UPDATE runs SET stage=?,updated_at=? WHERE run_id=?",
                (stage, at, run_id),
            )
            self._event(run_id, at, "stage_started", "Stage started: " + stage)

    def result(self, run_id: str) -> dict | None:
        with self.lock:
            row = self.db.execute(
                "SELECT payload_json FROM results WHERE run_id=?", (run_id,)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def checkpoint(self, run_id: str, kind: str, item_id: str, payload: dict) -> None:
        """Persist bounded stage evidence independently of terminal outcome."""
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO ledgers VALUES (?,?,?,?) ON CONFLICT(run_id,kind,item_id) DO UPDATE SET payload_json=excluded.payload_json",
                (
                    run_id,
                    kind,
                    item_id,
                    json.dumps(payload, ensure_ascii=False, default=str),
                ),
            )

    def ledger(self, run_id: str, kind: str) -> list[dict]:
        with self.lock:
            rows = self.db.execute(
                "SELECT payload_json FROM ledgers WHERE run_id=? AND kind=? ORDER BY item_id",
                (run_id, kind),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def record_call_event(self, run_id: str, call: dict) -> None:
        with self.lock, self.db:
            record = self.get(run_id)
            self._event(
                run_id,
                record["updated_at"],
                "model_call" if call["kind"] == "model" else "tool_call",
                "Completed bounded request",
                {
                    key: call.get(key)
                    for key in ("call_id", "role", "operation", "duration_ms", "status")
                },
            )

    def save_artifact(
        self,
        run_id: str,
        name: str,
        relative_path: str,
        digest: str,
        size: int,
        media_type: str,
    ) -> None:
        with self.lock, self.db:
            status = self.db.execute(
                "SELECT status FROM runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if not status or status[0] != "running":
                raise Conflict("STATE_CONFLICT")
            self.db.execute(
                "INSERT INTO artifacts VALUES (?,?,?,?,?,?)",
                (run_id, name, relative_path, digest, size, media_type),
            )

    def artifact(self, run_id: str, name: str) -> dict | None:
        with self.lock:
            row = self.db.execute(
                "SELECT relative_path,sha256,size_bytes,media_type FROM artifacts WHERE run_id=? AND name=?",
                (run_id, name),
            ).fetchone()
        return (
            {
                "relative_path": row[0],
                "sha256": row[1],
                "size_bytes": row[2],
                "media_type": row[3],
            }
            if row
            else None
        )

    def artifact_names(self, run_id: str) -> list[str]:
        with self.lock:
            return [
                row[0]
                for row in self.db.execute(
                    "SELECT name FROM artifacts WHERE run_id=? ORDER BY name", (run_id,)
                )
            ]

    def interrupt_unfinished(self, now: datetime) -> int:
        with self.lock, self.db:
            ids = [
                row[0]
                for row in self.db.execute(
                    "SELECT run_id FROM runs WHERE status IN ('queued','running')"
                )
            ]
            cursor = self.db.execute(
                "UPDATE runs SET status='failed',stage='finished',error_code='INTERRUPTED',updated_at=?,finished_at=? WHERE status IN ('queued','running')",
                (now.astimezone(UTC).isoformat(), now.astimezone(UTC).isoformat()),
            )
            for run_id in ids:
                self._event(
                    run_id,
                    now.astimezone(UTC).isoformat(),
                    "interrupted",
                    "Run interrupted by restart",
                )
            return cursor.rowcount

    def cancel(self, run_id: str, now: datetime) -> str:
        with self.lock, self.db:
            row = self.db.execute(
                "SELECT status FROM runs WHERE run_id=?", (run_id,)
            ).fetchone()
            if row is None:
                raise KeyError(run_id)
            if row[0] == "cancelled":
                return "cancelled"
            if row[0] not in ("queued", "running"):
                raise Conflict("STATE_CONFLICT")
            self.db.execute(
                "UPDATE runs SET status='cancelled',stage='finished',error_code='CANCELLED',updated_at=?,finished_at=? WHERE run_id=?",
                (
                    now.astimezone(UTC).isoformat(),
                    now.astimezone(UTC).isoformat(),
                    run_id,
                ),
            )
            self._event(
                run_id, now.astimezone(UTC).isoformat(), "cancelled", "Run cancelled"
            )
            return "cancelled"
