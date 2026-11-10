"""Build the sanitized synthetic replay artifact offline; no external calls."""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from discoverybrief.clients import CallBudget
from discoverybrief.fixture import FIXTURES
from discoverybrief.fixtures import FixtureModel, FixtureResearch
from discoverybrief.pipeline import run_live
from discoverybrief.schemas import RunRequest


async def main():
    request = RunRequest.model_validate_json(
        (FIXTURES / "request.json").read_text(encoding="utf-8")
    )
    result = await run_live(
        request,
        datetime(2026, 11, 8, 3, tzinfo=UTC),
        FixtureResearch(),
        FixtureModel(),
        CallBudget(),
        research_mode="fixture",
    )
    if result.get("status") != "completed":
        raise RuntimeError("fixture did not complete")
    selection = result["brief_selection"]
    selected_claims = set(selection["finding_ids"])
    selected_requirements = set(selection["requirement_ids"])
    result["claims"] = [
        claim for claim in result["claims"] if claim["claim_id"] in selected_claims
    ]
    result["requirements"] = [
        item
        for item in result["requirements"]
        if item["requirement_id"] in selected_requirements
    ]
    source_ids = {
        e["source_id"] for claim in result["claims"] for e in claim["evidence"]
    }
    result["sources"] = [
        source for source in result["sources"] if source["source_id"] in source_ids
    ]
    result["composition"] = {
        "question": selection["questions"],
        "hypothesis": selection["hypotheses"],
        "unknown": selection["unknowns"],
    }
    result["synthetic"] = True
    output = Path("demo_runs/sagara.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Synthetic replay artifact created:", output.as_posix())


if __name__ == "__main__":
    asyncio.run(main())
