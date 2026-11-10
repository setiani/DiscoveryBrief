import json
from datetime import UTC, datetime
from pathlib import Path

from discoverybrief.evidence import approve_claim, approve_requirement

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_claim_gate_rejects_bad_quotes_and_future_dates():
    outputs = load("role-outputs.json")
    sources = {s["source_id"]: s for s in load("research-fixture.json")["sources"]}
    candidate = {"candidate_id": "a0001", **outputs["analyst"]["claims"][0]}
    review = outputs["verifier"]["reviews"][0]
    start = datetime(2026, 10, 13, tzinfo=UTC)
    cutoff = datetime(2026, 11, 8, tzinfo=UTC)
    assert approve_claim(candidate, review, sources, start, cutoff)[0] is not None
    future_publication = {
        **sources,
        "s0001": {**sources["s0001"], "published_on": "2026-11-09"},
    }
    assert (
        approve_claim(candidate, review, future_publication, start, cutoff)[1]
        == "published_after_cutoff"
    )
    assert (
        approve_claim(
            candidate, {**review, "date_quote": "200 agents"}, sources, start, cutoff
        )[1]
        == "date_quote_mismatch"
    )
    altered = {
        **candidate,
        "evidence_proposals": [{"source_id": "s0001", "quote": "fabricated"}],
    }
    assert (
        approve_claim(altered, review, sources, start, cutoff)[1] == "quote_not_found"
    )
    future = {"candidate_id": "a0005", **outputs["analyst"]["claims"][4]}
    assert approve_claim(
        future, outputs["verifier"]["reviews"][4], sources, start, cutoff
    )[1] in {"outside_window", "published_after_cutoff"}
    old = {"candidate_id": "a0003", **outputs["analyst"]["claims"][2]}
    old["proposed_event_on"] = "2026-11-06"
    bad_review = {
        **outputs["verifier"]["reviews"][2],
        "temporal_kind": "recent_development",
        "event_on": "2026-11-06",
        "date_quote": "6 November 2026",
    }
    assert (
        approve_claim(old, bad_review, sources, start, cutoff)[1]
        == "update_date_not_event_date"
    )
    assert (
        approve_claim(
            candidate, {**review, "support": "uncertain"}, sources, start, cutoff
        )[0]
        is None
    )


def test_requirement_needs_independent_support_and_exact_span():
    outputs = load("role-outputs.json")
    req = {"requirement_id": "r0001", **outputs["analyst"]["requirements"][0]}
    review = outputs["verifier"]["requirement_reviews"][0]
    rfp = load("request.json")["rfp_text"]
    assert approve_requirement(req, review, rfp)[0] is not None
    assert approve_requirement(req, {**review, "support": "uncertain"}, rfp)[0] is None
    assert approve_requirement({**req, "start": 1}, review, rfp)[0] is None
