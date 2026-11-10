from datetime import UTC, datetime

import pytest
from discoverybrief.artifacts import ArtifactStore
from discoverybrief.schemas import RunRequest
from discoverybrief.store import RunStore
from test_contracts import fixture


def test_manifest_artifacts_are_atomic_bounded_and_verified(tmp_path):
    store = RunStore(tmp_path / "runs.db")
    artifacts = ArtifactStore(tmp_path, store)
    now = datetime(2026, 11, 8, 3, tzinfo=UTC)
    run_id, _ = store.create(RunRequest.model_validate(fixture()), now)
    store.claim_next(now)
    artifacts.write(run_id, "brief.md", b"synthetic brief")
    assert artifacts.resolve(run_id, "brief.md") is None
    with pytest.raises(ValueError):
        artifacts.write(run_id, "../outside", b"bad")
    with pytest.raises(ValueError):
        artifacts.write(run_id, "brief.md", b"overwrite")
    store.finish(run_id, "completed", now, result={"status": "completed"})
    path, entry = artifacts.resolve(run_id, "brief.md")
    assert path.read_bytes() == b"synthetic brief" and entry["size_bytes"] == 15
    path.write_bytes(b"tampered")
    assert artifacts.resolve(run_id, "brief.md") is None
    store.close()
