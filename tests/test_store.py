from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from discoverybrief.schemas import RunRequest
from discoverybrief.store import Conflict, QueueFull, RunStore
from test_contracts import fixture


def test_idempotency_and_restart(tmp_path):
    store = RunStore(tmp_path / "runs.db")
    data = fixture()
    data["client_request_id"] = str(uuid4())
    now = datetime(2026, 11, 8, 3, tzinfo=UTC)
    request = RunRequest.model_validate(data)
    run_id, created = store.create(request, now)
    assert created and store.create(request, now) == (run_id, False)
    assert store.create(request, now + timedelta(days=365)) == (run_id, False)
    data["company_name"] = "Other Company"
    with pytest.raises(Conflict):
        store.create(RunRequest.model_validate(data), now)
    assert "rfp_text" not in store.get(run_id)
    assert store.interrupt_unfinished(now) == 1
    assert store.get(run_id)["error_code"] == "INTERRUPTED"
    assert [e["type"] for e in store.events(run_id)] == [
        "stage_started",
        "run_finished",
    ]
    store.close()


def test_queue_and_cancel(tmp_path):
    store = RunStore(tmp_path / "runs.db")
    data = fixture()
    data["client_request_id"] = None
    request = RunRequest.model_validate(data)
    now = datetime(2026, 11, 8, 3, tzinfo=UTC)
    ids = [store.create(request, now)[0] for _ in range(3)]
    with pytest.raises(QueueFull):
        store.create(request, now)
    assert store.cancel(ids[0], now) == "cancelled"
    assert store.cancel(ids[0], now) == "cancelled"
    assert store.create(request, now)[1]
    store.close()


def test_single_worker_and_terminal_state_cannot_be_overwritten(tmp_path):
    store = RunStore(tmp_path / "runs.db")
    data = fixture()
    data["client_request_id"] = None
    request = RunRequest.model_validate(data)
    now = datetime(2026, 11, 8, 3, tzinfo=UTC)
    run_id, _ = store.create(request, now)
    store.create(request, now)
    claimed = store.claim_next(now)
    assert claimed[0] == run_id and claimed[2] == now
    assert store.claim_next(now) is None
    store.update_stage(run_id, "researching", now)
    with pytest.raises(Conflict):
        store.update_stage(run_id, "planning", now)
    with pytest.raises(ValueError):
        store.finish(run_id, "completed", now, result={"status": "failed"})
    assert store.get(run_id)["status"] == "running"
    store.finish(
        run_id, "completed", now, result={"status": "completed", "quality": "limited"}
    )
    assert store.result(run_id)["quality"] == "limited"
    events = store.events(run_id)
    assert [e["seq"] for e in events] == list(range(1, len(events) + 1))
    assert "stage_completed" in {e["type"] for e in events}
    assert [e["type"] for e in store.events(run_id, after=1)] == [
        "stage_started",
        "stage_completed",
        "stage_started",
        "run_finished",
    ]
    with pytest.raises(Conflict):
        store.finish(run_id, "failed", now, "INTERRUPTED")
    assert store.claim_next(now) is not None
    store.close()
