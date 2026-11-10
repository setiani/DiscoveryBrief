import asyncio
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from discoverybrief.bundle import build_bundle
from discoverybrief.clients import CallBudget
from discoverybrief.pipeline import run_live
from discoverybrief.reporting import render_bundle_html
from discoverybrief.schemas import RunRequest

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_experimental_pipeline_uses_scripted_roles_and_synthetic_research():
    outputs = load("role-outputs.json")
    sources = load("research-fixture.json")["sources"]

    class FakeTavily:
        async def search(self, query, start, end):
            assert "Rina" not in str(query)
            return {
                "results": [
                    {
                        "url": s["original_url"],
                        "title": s["title"],
                        "content": s["text"],
                    }
                    for s in sources
                ]
            }

        async def extract(self, urls):
            return {
                "results": [
                    {"url": s["original_url"], "raw_content": s["text"]}
                    for s in sources
                    if s["original_url"] in urls
                ],
                "failed_results": [],
            }

    class FakeBifrost:
        async def submit(self, messages, schema, max_tokens):
            name = {
                "ResearchPlan": "planner",
                "AnalystOutput": "analyst",
                "VerifierOutput": "verifier",
                "ComposerOutput": "composer",
                "PremiseAudit": "auditor",
            }[schema["title"]]
            return {
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "submit_payload",
                                        "arguments": json.dumps(
                                            outputs[name], ensure_ascii=False
                                        ),
                                    }
                                }
                            ]
                        }
                    }
                ]
            }

    result = asyncio.run(
        run_live(
            RunRequest.model_validate(load("request.json")),
            datetime(2026, 11, 8, 3, tzinfo=UTC),
            FakeTavily(),
            FakeBifrost(),
            CallBudget(),
            research_mode="fixture",
        )
    )
    assert result["status"] == "completed"
    assert result["research_mode"] == "fixture"
    assert result["quality"] == "limited"
    assert len({c["event_cluster_id"] for c in result["claims"]}) == 1
    assert len(result["requirements"]) == 1
    assert len(result["composition"]["question"]) == 3
    assert len(result["brief_selection"]["finding_ids"]) == 1
    assert result["claims"][0]["evidence"][0]["evidence_id"] == "e0001"
    bundle = build_bundle(RunRequest.model_validate(load("request.json")), result)
    assert len(bundle["claims"]) == 1 and len(bundle["sources"]) == 1
    assert "rfp_text" not in bundle and "notes" not in bundle
    assert bundle["context_summary"][0]["provenance"] == "user_provided"
    assert "text" not in bundle["sources"][0]
    html = render_bundle_html(bundle)
    assert "CONTOH SINTETIS" in html and "[1]" in html
    assert "Konteks dari pengguna" in html
    altered = deepcopy(result)
    altered["claims"][0]["evidence"][0]["quote"] = "fabricated quote"
    with pytest.raises(ValueError):
        build_bundle(RunRequest.model_validate(load("request.json")), altered)

    class FailingVerifier(FakeBifrost):
        async def submit(self, messages, schema, max_tokens):
            if schema["title"] == "VerifierOutput":
                raise ValueError("verification unavailable")
            return await super().submit(messages, schema, max_tokens)

    fallback = asyncio.run(
        run_live(
            RunRequest.model_validate(load("request.json")),
            datetime(2026, 11, 8, 3, tzinfo=UTC),
            FakeTavily(),
            FailingVerifier(),
            CallBudget(),
            research_mode="fixture",
        )
    )
    assert fallback["quality"] == "context_only"
    assert not fallback["claims"] and not fallback["requirements"]
    assert all(q["origin"] == "template" for q in fallback["composition"]["question"])
    safe_fallback = build_bundle(
        RunRequest.model_validate(load("request.json")), fallback
    )
    assert not safe_fallback["claims"] and len(safe_fallback["questions"]) == 2
