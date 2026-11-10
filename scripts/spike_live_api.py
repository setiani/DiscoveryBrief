"""Explicit public/synthetic live API smoke; stores only the resulting safe bundle."""

import json
import os
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4
from zoneinfo import ZoneInfo

from discoverybrief.api.main import create_app
from fastapi.testclient import TestClient


def main():
    if os.getenv("ENABLE_LIVE_TESTS") != "1":
        raise SystemExit("Set ENABLE_LIVE_TESTS=1 explicitly")
    now = datetime.now(UTC)
    meeting = (now + timedelta(days=1)).astimezone(ZoneInfo("Asia/Jakarta"))
    payload = {
        "client_request_id": str(uuid4()),
        "company_name": "OpenAI",
        "company_domain": "openai.com",
        "meeting_at": meeting.isoformat(),
        "meeting_timezone": "Asia/Jakarta",
        "language": "en",
        "rfp_text": "The portal must support SSO and integration with existing systems.",
    }
    with tempfile.TemporaryDirectory(prefix="discoverybrief-spike-") as directory:
        application = create_app(
            data_dir=Path(directory), research_mode="live", allow_live=True
        )
        with TestClient(application) as client:
            response = client.post("/api/runs", json=payload)
            print("create HTTP:", response.status_code, flush=True)
            if response.status_code != 202:
                return
            run_id = response.json()["run_id"]
            last_stage = ""
            deadline = time.monotonic() + 320
            while time.monotonic() < deadline:
                status = client.get("/api/runs/" + run_id).json()
                if status["stage"] != last_stage:
                    last_stage = status["stage"]
                    print("stage:", last_stage, flush=True)
                if status["status"] in (
                    "completed",
                    "failed",
                    "needs_input",
                    "cancelled",
                ):
                    print(
                        "status:",
                        status["status"],
                        "quality:",
                        status.get("quality"),
                        flush=True,
                    )
                    if status.get("error_code"):
                        print("error_code:", status["error_code"], flush=True)
                    if status["status"] == "completed":
                        response = client.get("/api/runs/" + run_id + "/brief")
                        print("brief HTTP:", response.status_code, flush=True)
                        if response.status_code == 200:
                            bundle = response.json()
                            print(
                                "claims:",
                                len(bundle["claims"]),
                                "requirements:",
                                len(bundle["requirements"]),
                                "questions:",
                                len(bundle["brief"]["questions"]),
                                flush=True,
                            )
                            print(
                                "warnings:",
                                ", ".join(w["code"] for w in bundle["warnings"]),
                                flush=True,
                            )
                            target = Path("data/spikes") / f"live-brief-{run_id}.json"
                            target.parent.mkdir(parents=True, exist_ok=True)
                            target.write_text(
                                json.dumps(bundle, ensure_ascii=False, indent=2),
                                encoding="utf-8",
                            )
                            print(
                                "sanitized bundle saved:", target.as_posix(), flush=True
                            )
                    break
                time.sleep(1)
            else:
                print("poll timeout; no automatic resume", flush=True)


if __name__ == "__main__":
    main()
