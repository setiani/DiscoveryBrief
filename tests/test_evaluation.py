import asyncio
import hashlib
import json
from datetime import datetime
from pathlib import Path

import pytest
from discoverybrief.evaluation import summarize
from discoverybrief.evidence import (
    align_requirement_quote,
    approve_requirement,
    parse_literal_date,
)
from discoverybrief.frozen_research import FrozenResearch
from discoverybrief.schemas import RunRequest

from scripts.evaluate_frozen import baseline

EVAL = Path(__file__).resolve().parents[1] / "eval"


def test_empty_results_are_na_not_perfect_scores():
    result = summarize([{"claims": [], "requirements": [], "questions": []}])
    assert result["public_support_precision"] is None
    assert result["rfp_grounding"] is None
    assert result["question_usefulness_median"] is None


def test_metrics_use_supplied_labels_and_correct_denominators():
    result = summarize(
        [
            {
                "claims": [
                    {
                        "human_supported": True,
                        "entity_correct": True,
                        "temporal_eligible": True,
                    },
                    {
                        "human_supported": False,
                        "entity_correct": True,
                        "temporal_eligible": False,
                    },
                ],
                "requirements": [{"grounded": True}],
                "questions": [{"rating": 3}, {"rating": 4}],
            }
        ]
    )
    assert result["public_support_precision"] == 0.5
    assert result["entity_correctness"] == 1
    assert result["temporal_eligibility"] == 0.5
    assert result["question_usefulness_median"] == 3.5
    with pytest.raises(ValueError):
        summarize([{"claims": [{"human_supported": None}]}])


def test_recall_and_reference_metrics_require_explicit_independent_labels():
    result = summarize(
        [
            {
                "references": [{"valid": True}, {"valid": False}],
                "required_atoms": [{"surfaced": True}, {"surfaced": False}],
                "outcome_correct": True,
            }
        ]
    )
    assert result["reference_validity"] == 0.5
    assert result["required_fact_recall"] == 0.5
    assert result["outcome_correctness"] == 1.0
    with pytest.raises(ValueError, match="outcome labels"):
        summarize([{"outcome_correct": True}, {}])
    with pytest.raises(ValueError, match="recall label"):
        summarize([{"required_atoms": [{}]}])


def test_fixed_cases_are_self_consistent_and_do_not_research():
    dataset = json.loads((EVAL / "dataset.json").read_text(encoding="utf-8"))
    assert dataset["status"] in {"not_run", "in_progress"}
    assert len(dataset["cases"]) == 10
    for case in dataset["cases"]:
        request = RunRequest.model_validate_json(
            (EVAL / case["request_path"]).read_text(encoding="utf-8")
        )
        request.validate_horizon(datetime.fromisoformat(case["clock_at"]))
        fixture = json.loads(
            (EVAL / case["research_fixture_path"]).read_text(encoding="utf-8")
        )
        labels = json.loads((EVAL / case["label_path"]).read_text(encoding="utf-8"))
        assert labels["required_fact_keys"] == case["required_fact_keys"]
        assert labels["forbidden_fact_keys"] == case["forbidden_fact_keys"]
        assert [atom["key"] for atom in labels["required_atoms"]] == case[
            "required_fact_keys"
        ]
        source_map = {source["source_id"]: source for source in fixture["sources"]}
        for atom in labels["required_atoms"]:
            assert atom["supporting_quote"] in source_map[atom["source_id"]]["text"]
        adapter = FrozenResearch(fixture)
        hits = asyncio.run(adapter.search({}, "2026-01-01", "2026-12-31"))["results"]
        result = asyncio.run(adapter.extract([hit["url"] for hit in hits]))
        assert len(result["results"]) + len(result["failed_results"]) == len(hits)
        for source, label in zip(
            fixture["sources"], labels["source_evidence"], strict=True
        ):
            assert label["quote"] in source["text"]
            assert (
                hashlib.sha256(source["text"].encode()).hexdigest()
                == source["content_sha256"]
            )


def test_fixed_evidence_rejects_tampering():
    fixture = json.loads(
        (EVAL / "fixtures/E01/research.json").read_text(encoding="utf-8")
    )
    fixture["sources"][0]["text"] += " altered"
    with pytest.raises(ValueError, match="hash mismatch"):
        FrozenResearch(fixture)


def test_baseline_records_invalid_output_without_retrying_or_approving_it():
    class InvalidModel:
        calls = 0

        async def complete(self, messages, max_tokens):
            self.calls += 1
            return {"choices": [{"message": {"content": "not JSON"}}]}

    request = RunRequest.model_validate_json(
        (EVAL / "fixtures/E01/request.json").read_text(encoding="utf-8")
    )
    model = InvalidModel()
    output = asyncio.run(baseline(model, request, []))
    assert model.calls == 1
    assert output == {"status": "parse_failed", "raw_output": "not JSON"}


def test_exact_requirement_offsets_can_be_recovered_only_from_unique_quote():
    rfp = "Kebutuhan: sistem mendukung SSO."
    item = {
        "requirement_id": "r0001",
        "quote": "sistem mendukung SSO",
        "start": 0,
        "end": 1,
    }
    aligned = align_requirement_quote(item, rfp)
    assert rfp[aligned["start"] : aligned["end"]] == item["quote"]
    assert approve_requirement(
        aligned, {"requirement_id": "r0001", "support": "supported"}, rfp
    )[0]
    duplicate = "SSO dan SSO"
    ambiguous = {"quote": "SSO", "start": 1, "end": 2}
    assert align_requirement_quote(ambiguous, duplicate) == ambiguous


def test_event_date_formats_stay_unambiguous():
    assert str(parse_literal_date("November 5, 2026")) == "2026-11-05"
    assert str(parse_literal_date("5 Nov 2026")) == "2026-11-05"
    assert parse_literal_date("05/11/2026") is None
