"""Read the synthetic planning example; never substitutes for an actual research run."""

import json
from datetime import datetime
from pathlib import Path

from discoverybrief.evidence import approve_claim, approve_requirement

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def sample() -> dict:
    def read(name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    request, research, roles = (
        read("request.json"),
        read("research-fixture.json"),
        read("role-outputs.json"),
    )
    sources = {source["source_id"]: source for source in research["sources"]}
    start = datetime.fromisoformat("2026-10-13T03:00:00+00:00")
    cutoff = datetime.fromisoformat(research["clock_at"])
    findings = []
    for index, candidate in enumerate(roles["analyst"]["claims"], 1):
        candidate = {"candidate_id": f"a{index:04d}", **candidate}
        review = roles["verifier"]["reviews"][index - 1]
        claim, _ = approve_claim(candidate, review, sources, start, cutoff)
        if claim and not any(
            f["statement"] == claim["statement"] and f["event_on"] == claim["event_on"]
            for f in findings
        ):
            findings.append(claim)
    requirements = []
    for index, req in enumerate(roles["analyst"]["requirements"], 1):
        req = {"requirement_id": f"r{index:04d}", **req}
        approved, _ = approve_requirement(
            req,
            roles["verifier"]["requirement_reviews"][index - 1],
            request["rfp_text"],
        )
        if approved:
            requirements.append(approved)
    audited = {
        (i["kind"], i["index"])
        for i in roles["auditor"]["items"]
        if i["decision"] == "accept"
    }
    return {
        "synthetic": True,
        "research_mode": "fixture",
        "quality": "limited",
        "company_name": request["company_name"],
        "meeting_at": request["meeting_at"],
        "knowledge_cutoff": cutoff.isoformat(),
        "findings": findings,
        "requirements": requirements,
        "questions": [
            x
            for i, x in enumerate(roles["composer"]["question_proposals"])
            if ("question", i) in audited
        ],
        "hypotheses": [
            x
            for i, x in enumerate(roles["composer"]["hypothesis_proposals"])
            if ("hypothesis", i) in audited
        ],
        "unknowns": [
            x
            for i, x in enumerate(roles["composer"]["unknown_proposals"])
            if ("unknown", i) in audited
        ],
        "sources": [
            {"source_id": s["source_id"], "title": s["title"], "url": s["original_url"]}
            for s in research["sources"]
            if s["source_id"] == "s0001"
        ],
    }
