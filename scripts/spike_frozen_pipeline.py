"""Synthetic fixed evidence with live model: not a Tavily live integration."""

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx
from discoverybrief.clients import BifrostClient, CallBudget
from discoverybrief.config import Settings
from discoverybrief.pipeline import run_live
from discoverybrief.schemas import RunRequest


async def main():
    settings = Settings.load()
    if os.getenv("ENABLE_LIVE_TESTS") != "1":
        raise SystemExit("Set ENABLE_LIVE_TESTS=1")
    base = Path(__file__).resolve().parents[1] / "tests/fixtures"
    request = RunRequest.model_validate_json(
        (base / "request.json").read_text(encoding="utf-8")
    )
    sources = json.loads((base / "research-fixture.json").read_text(encoding="utf-8"))[
        "sources"
    ]

    class FixedResearch:
        async def search(self, query, start, end):
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

    budget = CallBudget()
    gateway = BifrostClient(
        settings.bifrost_base_url,
        settings.model_primary,
        budget,
        settings.bifrost_virtual_key,
        min_interval_seconds=settings.model_min_interval_seconds,
    )
    print("Mode: synthetic fixed evidence + live model; no Tavily calls")
    try:
        result = await run_live(
            request,
            datetime(2026, 11, 8, 3, tzinfo=UTC),
            FixedResearch(),
            gateway,
            budget,
            research_mode="frozen_research",
        )
        print("status:", result["status"], "quality:", result.get("quality"))
        print(
            "claims:",
            len(result.get("claims", [])),
            "requirements:",
            len(result.get("requirements", [])),
        )
        print("warnings:", ", ".join(result.get("warnings", [])))
        print("diagnostics:", result.get("diagnostics", {}))
        print("identity_reason:", (result.get("entity") or {}).get("reason"))
    except httpx.HTTPStatusError as exc:
        print("pipeline failed HTTP:", exc.response.status_code)
    except (httpx.HTTPError, ValueError, RuntimeError) as exc:
        print("pipeline failed:", type(exc).__name__)
    print("Bifrost requests:", budget.models)


if __name__ == "__main__":
    asyncio.run(main())
