import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from discoverybrief.api.main import create_app
from discoverybrief.clock import FrozenClock
from discoverybrief.schemas import RunRequest
from discoverybrief.store import QueueFull, RunStore
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def test_TC03_request_size_is_rejected_before_persistence(tmp_path):
    app = create_app(data_dir=tmp_path, mode="local", research_mode="fixture")
    with TestClient(app) as client:
        response = client.post(
            "/api/runs",
            content=b"x" * 65537,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413 and response.headers["X-Correlation-ID"]
        assert client.get("/api/runs").json()["items"] == []


def test_TC49_queue_and_TC50_frozen_acceptance_time(tmp_path):
    request = RunRequest.model_validate_json(
        (ROOT / "tests/fixtures/request.json").read_text(encoding="utf-8")
    )
    request = request.model_copy(update={"client_request_id": None})
    store = RunStore(tmp_path / "queue.db")
    first = datetime(2026, 11, 8, 23, 59, tzinfo=UTC)
    try:
        run_id, _ = store.create(request, first, "live")
        claimed = store.claim_next(datetime(2026, 11, 9, 0, 1, tzinfo=UTC))
        assert (
            claimed[2] == first and store.get(run_id)["created_at"] == first.isoformat()
        )
        for _ in range(3):
            store.create(request, first, "live")
        with pytest.raises(QueueFull):
            store.create(request, first, "live")
    finally:
        store.close()


def test_TC30_pdf_failure_preserves_other_exports(tmp_path, monkeypatch):
    import discoverybrief.pdf

    def fail(*args):
        raise RuntimeError("controlled browser failure")

    monkeypatch.setattr(discoverybrief.pdf, "bundle_pdf", fail)
    clock = FrozenClock(datetime(2026, 11, 8, 3, tzinfo=UTC))
    payload = json.loads(
        (ROOT / "tests/fixtures/request.json").read_text(encoding="utf-8")
    )
    import time

    with TestClient(
        create_app(
            data_dir=tmp_path, mode="local", research_mode="fixture", clock=clock
        )
    ) as client:
        run_id = client.post("/api/runs", json=payload).json()["run_id"]
        for _ in range(1000):
            record = client.get(f"/api/runs/{run_id}").json()
            if record["status"] in {"completed", "failed"}:
                break
            time.sleep(0.01)
        assert (
            record["status"] == "completed" and "brief.pdf" not in record["artifacts"]
        )
        assert {"brief.json", "brief.html", "brief.md"} <= set(record["artifacts"])
        assert "EXPORT_FAILED" in {w["code"] for w in record["warnings"]}
