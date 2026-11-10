import json
import time
from datetime import UTC, datetime
from uuid import uuid4

from discoverybrief.api.main import create_app
from discoverybrief.clock import FrozenClock
from discoverybrief.fixture import FIXTURES
from fastapi.testclient import TestClient


def test_fixture_run_is_persisted_and_safe(tmp_path, monkeypatch):
    import httpx

    async def no_external(*args, **kwargs):
        raise AssertionError("fixture must not call the network")

    monkeypatch.setattr(httpx.AsyncClient, "post", no_external)
    clock = FrozenClock(datetime(2026, 11, 8, 3, tzinfo=UTC))
    application = create_app(data_dir=tmp_path, clock=clock, research_mode="fixture")
    payload = json.loads((FIXTURES / "request.json").read_text(encoding="utf-8"))
    payload["client_request_id"] = str(uuid4())
    with TestClient(application) as client:
        response = client.post("/api/runs", json=payload)
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        assert client.post("/api/runs", json=payload).status_code == 200
        changed = {**payload, "company_name": "Different Company"}
        assert client.post("/api/runs", json=changed).status_code == 409
        for _ in range(1000):
            status = client.get("/api/runs/" + run_id).json()
            if status["status"] in ("completed", "failed", "needs_input"):
                break
            time.sleep(0.01)
        assert status["status"] == "completed"
        assert status["research_mode"] == "fixture" and status["quality"] == "limited"
        listing = client.get("/api/runs").json()["items"]
        assert len(listing) == 1 and listing[0]["run_id"] == run_id
        assert "rfp_text" not in listing[0] and "notes" not in listing[0]
        assert "rfp_text" not in status and "notes" not in status
        assert {
            "brief.json",
            "brief.md",
            "brief.html",
            "evidence.json",
            "trace.json",
        } <= set(status["artifacts"])
        response = client.get("/api/runs/" + run_id + "/brief")
        assert response.status_code == 200
        brief = response.json()
        assert (
            len(brief["brief"]["finding_ids"]) == 1
            and len(brief["brief"]["questions"]) == 3
        )
        assert brief["evidence"][0]["source_id"] in brief["brief"]["source_ids"]
        artifact = client.get("/api/runs/" + run_id + "/artifacts/brief.json")
        assert (
            artifact.status_code == 200
            and artifact.json()["brief"]["research_mode"] == "fixture"
        )
        trace = client.get("/api/runs/" + run_id + "/artifacts/trace.json").json()
        assert trace["note"] and "notes" not in str(trace)
        assert (
            client.get("/api/runs/" + run_id + "/artifacts/unknown.txt").status_code
            == 404
        )
        if "brief.pdf" in status["artifacts"]:
            assert client.get(
                "/api/runs/" + run_id + "/artifacts/brief.pdf"
            ).content.startswith(b"%PDF-")
        events = client.get("/api/runs/" + run_id + "/events").json()
        assert events["terminal"] is True
        types = [x["type"] for x in events["events"]]
        assert (
            types[:2] == ["stage_started", "stage_started"]
            and types[-1] == "run_finished"
        )
        assert "stage_started" in types


def test_demo_is_read_only_and_live_is_not_enabled(tmp_path):
    with TestClient(
        create_app(data_dir=tmp_path / "demo", mode="public_demo")
    ) as client:
        assert client.post("/api/runs", json={}).status_code == 403
        assert client.get("/api/runs").status_code == 403
        assert client.get("/api/runs/" + str(uuid4())).status_code == 404
    with TestClient(
        create_app(data_dir=tmp_path / "live", research_mode="live")
    ) as client:
        assert client.post("/api/runs", json={}).status_code == 503
        assert client.get("/api/health").json()["live_enabled"] is False


def test_public_demo_replays_only_synthetic_sample_without_external_calls(
    tmp_path, monkeypatch
):
    import httpx

    async def no_external(*args, **kwargs):
        raise AssertionError("replay must not call the network")

    monkeypatch.setattr(httpx.AsyncClient, "post", no_external)
    from discoverybrief.fixtures import FixtureModel, FixtureResearch

    monkeypatch.setattr(FixtureModel, "submit", no_external)
    monkeypatch.setattr(FixtureResearch, "search", no_external)
    monkeypatch.setattr(FixtureResearch, "extract", no_external)
    clock = FrozenClock(datetime(2027, 11, 8, 3, tzinfo=UTC))
    application = create_app(data_dir=tmp_path, clock=clock, mode="public_demo")
    with TestClient(application) as client:
        assert client.post("/api/runs", json={}).status_code == 403
        response = client.post("/api/samples/sagara/replay")
        assert (
            response.status_code == 202 and response.json()["research_mode"] == "replay"
        )
        run_id = response.json()["run_id"]
        for _ in range(1000):
            status = client.get("/api/runs/" + run_id).json()
            if status["status"] in ("completed", "failed", "needs_input"):
                break
            time.sleep(0.01)
        assert status["status"] == "completed" and status["research_mode"] == "replay"
        brief = client.get("/api/runs/" + run_id + "/brief").json()
        assert brief["brief"]["research_mode"] == "replay" and brief["brief"][
            "knowledge_cutoff"
        ].startswith("2026-11-08")
        assert (
            brief["original_research_mode"] == "fixture" and brief["synthetic"] is True
        )
        assert isinstance(brief["original_metrics"], dict)
        assert (
            brief["metrics"]["llm_requests"] == 0
            and brief["metrics"]["search_requests"] == 0
        )


def test_opt_in_live_path_with_injected_offline_handler(tmp_path):
    async def fake_live(request, created_at, on_stage):
        return {
            "status": "completed",
            "research_mode": "live",
            "quality": "context_only",
            "knowledge_cutoff": created_at.isoformat(),
            "claims": [],
            "requirements": [],
            "sources": [],
            "brief_selection": {
                "finding_ids": [],
                "requirement_ids": [],
                "questions": [
                    {"text": "What should we clarify?", "origin": "template"}
                ],
                "hypotheses": [],
                "unknowns": [],
            },
            "warnings": ["synthetic_test"],
        }

    clock = FrozenClock(datetime(2026, 11, 8, 3, tzinfo=UTC))
    application = create_app(
        data_dir=tmp_path,
        clock=clock,
        research_mode="live",
        allow_live=True,
        live_handler=fake_live,
    )
    payload = json.loads((FIXTURES / "request.json").read_text(encoding="utf-8"))
    payload["client_request_id"] = str(uuid4())
    payload["company_name"] = "Another Company"
    payload["company_domain"] = "example.com"
    with TestClient(application) as client:
        assert client.get("/api/health").json()["live_enabled"] is True
        response = client.post("/api/runs", json=payload)
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        for _ in range(1000):
            record = client.get("/api/runs/" + run_id).json()
            if record["status"] == "completed":
                break
            time.sleep(0.01)
        assert record["status"] == "completed" and record["research_mode"] == "live"
        assert (
            client.get("/api/runs/" + run_id + "/brief").json()["brief"][
                "research_mode"
            ]
            == "live"
        )


def test_live_api_passes_configured_fallback(tmp_path, monkeypatch):
    import discoverybrief.api.main as api
    from discoverybrief.fixtures import FixtureModel, FixtureResearch

    monkeypatch.setenv("MODEL_FALLBACK", "tested-backup")
    monkeypatch.setenv("MODEL_PRIMARY", "test-primary")
    monkeypatch.setenv("MODEL_PROVIDER_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "synthetic-test-key")
    captured = {}

    def model(*args, **kwargs):
        captured.update(kwargs)
        return FixtureModel()

    monkeypatch.setattr(api, "BifrostClient", model)
    monkeypatch.setattr(api, "TavilyClient", lambda *args: FixtureResearch())
    application = api.create_app(
        data_dir=tmp_path,
        mode="local",
        research_mode="live",
        allow_live=True,
        clock=FrozenClock(datetime(2026, 11, 8, 3, tzinfo=UTC)),
    )
    payload = json.loads((FIXTURES / "request.json").read_text(encoding="utf-8"))
    payload["client_request_id"] = str(uuid4())
    payload["company_domain"] = None
    with TestClient(application) as client:
        created = client.post("/api/runs", json=payload)
        assert created.status_code == 202
        for _ in range(1000):
            record = client.get("/api/runs/" + created.json()["run_id"]).json()
            if record["status"] in {"completed", "failed", "needs_input"}:
                break
            time.sleep(0.01)
        assert captured["fallback_model"] == "tested-backup"
        assert record["status"] == "completed"
