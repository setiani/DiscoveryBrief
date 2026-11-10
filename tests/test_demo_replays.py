import time
from datetime import UTC, datetime

import pytest
from discoverybrief.api.main import create_app
from discoverybrief.clock import FrozenClock
from discoverybrief.contracts import BriefBundle
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "sample_id,quality",
    [
        ("ready", "ready"),
        ("context-only", "context_only"),
        ("partial-source", "limited"),
    ],
)
def test_three_curated_samples_replay_without_new_paid_calls(
    tmp_path, sample_id, quality
):
    app = create_app(
        data_dir=tmp_path,
        mode="public_demo",
        clock=FrozenClock(datetime(2028, 1, 1, tzinfo=UTC)),
    )
    with TestClient(app) as client:
        response = client.post(f"/api/samples/{sample_id}/replay")
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        for _ in range(1000):
            state = client.get(f"/api/runs/{run_id}").json()
            if state["status"] in {"completed", "failed"}:
                break
            time.sleep(0.01)
        assert state["status"] == "completed"
        output = client.get(f"/api/runs/{run_id}/brief").json()
        BriefBundle.model_validate(output)
        assert output["brief"]["quality"] == quality
        assert output["brief"]["research_mode"] == "replay"
        assert output["original_research_mode"] == "frozen_research"
        assert (
            output["metrics"]["llm_requests"] == 0
            and output["metrics"]["search_requests"] == 0
        )
        assert output["original_metrics"]["llm_requests"] > 0
