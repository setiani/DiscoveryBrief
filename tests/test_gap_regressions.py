"""Release regressions derived from the gap analysis, not mock quality measurements."""

import asyncio
import json
import sqlite3
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from discoverybrief.api.main import create_app
from discoverybrief.clients import BifrostClient, CallBudget, TavilyClient
from discoverybrief.clock import FrozenClock
from discoverybrief.contracts import BriefBundle
from discoverybrief.fixtures import FixtureModel, FixtureResearch
from discoverybrief.frozen_research import FrozenResearch
from discoverybrief.metrics import UsageLedger
from discoverybrief.pipeline import run_live
from discoverybrief.research import evidence_passages, make_queries
from discoverybrief.schemas import RunRequest
from discoverybrief.store import RunStore
from discoverybrief.temporal import eligibility, publication_metadata
from fastapi.testclient import TestClient
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]


def request():
    return RunRequest.model_validate_json(
        (ROOT / "tests/fixtures/request.json").read_text(encoding="utf-8")
    )


def wait(client, run_id):
    for _ in range(1000):
        record = client.get(f"/api/runs/{run_id}").json()
        if record["status"] in {"completed", "failed", "needs_input"}:
            return record
        time.sleep(0.01)
    raise AssertionError("run did not terminate")


def test_TC40_fixture_is_reproducible_after_meeting_and_TC31_bundle_integrity(tmp_path):
    app = create_app(
        data_dir=tmp_path,
        mode="local",
        research_mode="fixture",
        clock=FrozenClock(datetime(2027, 11, 15, tzinfo=UTC)),
    )
    with TestClient(app) as client:
        response = client.post("/api/runs", json=request().model_dump(mode="json"))
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        state = wait(client, run_id)
        assert (
            state["status"] == "completed"
            and state["started_at"]
            and state["finished_at"]
        )
        bundle = client.get(f"/api/runs/{run_id}/brief").json()
        BriefBundle.model_validate(bundle)
        assert bundle["brief"]["knowledge_cutoff"].startswith("2026-11-08")
        assert str(bundle["brief"]["run_id"]) == run_id
        evidence = client.get(f"/api/runs/{run_id}/evidence").json()
        assert evidence["candidates"] and evidence["reviews"] and evidence["rejections"]
        export = client.get(f"/api/runs/{run_id}/artifacts/evidence.json").json()
        assert len(export["candidates"]) > len(bundle["brief"]["finding_ids"])
        assert export["sources"][0]["text"]
        broken = deepcopy(bundle)
        broken["brief"]["finding_ids"] = ["another-run-c9999"]
        with pytest.raises(ValidationError):
            BriefBundle.model_validate(broken)


def test_TC05_ready_requires_distinct_evidence_and_TC52_audit_failure_caps_quality():
    research = json.loads(
        (ROOT / "eval/fixtures/E01/research.json").read_text(encoding="utf-8")
    )

    class Model(FixtureModel):
        def __init__(self, fail_audit=False):
            super().__init__()
            self.fail_audit = fail_audit
            self.responses["analyst"]["entity_candidates"] = [
                {
                    "name": "Sagara Insurance",
                    "domain": "sagara.example",
                    "source_ids": ["s0001"],
                }
            ]
            self.responses["verifier"]["entity"] = {
                "status": "user_scoped",
                "company_name": "Sagara Insurance",
                "domain": "sagara.example",
                "basis_source_ids": ["s0001"],
                "candidate_companies": [],
                "notes": [],
            }
            self.responses["analyst"]["claims"] = []
            self.responses["verifier"]["reviews"] = []
            for i, source in enumerate(research["sources"], 1):
                self.responses["analyst"]["claims"].append(
                    {
                        "statement": source["text"],
                        "category": ["launch", "partnership", "leadership"][i - 1],
                        "evidence_proposals": [
                            {"source_id": f"s{i:04d}", "quote": source["text"]}
                        ],
                        "proposed_event_on": source["event_on"],
                        "event_date_quote": source["date_quote"],
                        "relevance_reason": "ANALYST_REASONING_MUST_NOT_REACH_VERIFIER",
                    }
                )
                self.responses["verifier"]["reviews"].append(
                    {
                        "candidate_id": f"a{i:04d}",
                        "support": "supported",
                        "entity_match": "matched",
                        "temporal_kind": "recent_development",
                        "event_on": source["event_on"],
                        "date_quote": source["date_quote"],
                        "conflict_group": None,
                        "reasoning": "The whole statement is in the source.",
                    }
                )

        async def submit(self, messages, schema, max_tokens):
            if schema["title"] == "VerifierOutput":
                assert "ANALYST_REASONING_MUST_NOT_REACH_VERIFIER" not in json.dumps(
                    messages
                )
            if schema["title"] == "PremiseAudit" and self.fail_audit:
                raise RuntimeError("provider unavailable")
            return await super().submit(messages, schema, max_tokens)

    def run(fail=False):
        return asyncio.run(
            run_live(
                request(),
                datetime(2026, 11, 8, 3, tzinfo=UTC),
                FrozenResearch(research),
                Model(fail),
                CallBudget(),
                research_mode="fixture",
            )
        )

    ready = run()
    assert (
        ready["quality"] == "ready"
        and len(ready["brief_selection"]["finding_ids"]) == 3
    )
    assert run(True)["quality"] == "limited"


def test_TC06_instant_and_partial_day_boundaries():
    start = datetime(2026, 10, 13, 3, tzinfo=UTC)
    end = datetime(2026, 11, 8, 3, tzinfo=UTC)
    assert eligibility("2026-10-13T03:00:00Z", start, end, "Asia/Jakarta") == (
        True,
        False,
    )
    assert eligibility("2026-10-13T02:59:59Z", start, end, "Asia/Jakarta") == (
        False,
        False,
    )
    assert eligibility("2026-11-08T03:00:01Z", start, end, "Asia/Jakarta") == (
        False,
        False,
    )
    assert eligibility("2026-11-08", start, end, "Asia/Jakarta") == (True, True)
    assert (
        publication_metadata("Published: 2026-11-01T10:00:00Z\nAn announcement")[
            "date_precision"
        ]
        == "instant"
    )
    assert not publication_metadata("Updated: 2026-11-01\nAn old event")


def test_research_keeps_official_query_and_shares_passage_budget():
    queries = make_queries(request(), ["leadership", "partnership"])
    assert queries[0]["include_domains"] == ["sagara.example"]
    sources = [
        {
            "source_id": f"s{i}",
            "text": "x" * 12000,
            "canonical_url": f"https://a.example/{i}",
            "text_origin": "extract",
            "extraction_status": "ok",
            "duplicate_of_source_id": None,
        }
        for i in range(6)
    ]
    passages = evidence_passages(sources)
    assert len(passages) == 6 and sum(len(p["text"]) for p in passages) == 24000
    sources[1]["duplicate_of_source_id"] = "s0"
    assert len(evidence_passages(sources)) == 5


def test_TC38_tavily_unknown_does_not_report_complete_usage():
    ledger = UsageLedger()
    ledger.record_model({"prompt_tokens": 0, "completion_tokens": 0})
    ledger.record_tavily(None)
    summary = ledger.summary()
    assert (
        summary["model_usage_complete"]
        and not summary["usage_complete"]
        and not summary["tavily_usage_complete"]
    )


def test_newer_database_is_rejected_without_mutation(tmp_path):
    path = tmp_path / "newer.db"
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA user_version=99")
    with pytest.raises(ValueError, match="newer"):
        RunStore(path)
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA user_version").fetchone()[0] == 99


def test_failed_analyst_preserves_collected_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "offline-test-key")
    monkeypatch.setenv("MODEL_PROVIDER_API_KEY", "offline-test-key")
    monkeypatch.setenv("MODEL_PRIMARY", "offline-test-model")
    research = FixtureResearch()

    async def search(self, *args):
        return await research.search(*args)

    async def extract(self, *args):
        return await research.extract(*args)

    model = FixtureModel()

    async def submit(self, messages, schema, max_tokens):
        if schema["title"] == "AnalystOutput":
            raise httpx.ConnectError("controlled offline outage")
        return await model.submit(messages, schema, max_tokens)

    monkeypatch.setattr(TavilyClient, "search", search)
    monkeypatch.setattr(TavilyClient, "extract", extract)
    monkeypatch.setattr(BifrostClient, "submit", submit)
    app = create_app(
        data_dir=tmp_path,
        mode="local",
        research_mode="live",
        allow_live=True,
        clock=FrozenClock(datetime(2026, 11, 8, 3, tzinfo=UTC)),
    )
    payload = request().model_dump(mode="json")
    payload["company_domain"] = "sagara.com"
    with TestClient(app) as client:
        response = client.post("/api/runs", json=payload)
        assert response.status_code == 202
        run_id = response.json()["run_id"]
        assert wait(client, run_id)["error_code"] == "PROVIDER_UNAVAILABLE"
        evidence = client.get(f"/api/runs/{run_id}/evidence").json()
        assert evidence["sources"] and evidence["sources"][0]["text"]
        assert client.get(f"/api/runs/{run_id}/brief").status_code == 409
