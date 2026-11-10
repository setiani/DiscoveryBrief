"""Explicitly enabled experimental live run using public data and a synthetic RFP."""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from discoverybrief.clients import BifrostClient, CallBudget, TavilyClient
from discoverybrief.config import Settings
from discoverybrief.pipeline import run_live
from discoverybrief.schemas import RunRequest


async def main():
    settings = Settings.load()
    if os.getenv("ENABLE_LIVE_TESTS") != "1":
        raise SystemExit("Set ENABLE_LIVE_TESTS=1")
    now = datetime.now(UTC)
    meeting = (now + timedelta(days=1)).astimezone(ZoneInfo("Asia/Jakarta"))
    request = RunRequest(
        company_name="OpenAI",
        company_domain="openai.com",
        meeting_at=meeting,
        meeting_timezone="Asia/Jakarta",
        language="en",
        rfp_text="The portal must support SSO and integration with existing systems.",
    )
    budget = CallBudget()
    research = TavilyClient(settings.tavily_api_key, budget)
    gateway = BifrostClient(
        settings.bifrost_base_url,
        settings.model_primary,
        budget,
        settings.bifrost_virtual_key,
        min_interval_seconds=settings.model_min_interval_seconds,
    )
    try:
        result = await run_live(request, now, research, gateway, budget)
        print("status:", result["status"], "quality:", result.get("quality"))
        print(
            "claims:",
            len(result.get("claims", [])),
            "requirements:",
            len(result.get("requirements", [])),
        )
        print("warnings:", ", ".join(result.get("warnings", [])))
    except httpx.HTTPStatusError as exc:
        print("pipeline failed HTTP:", exc.response.status_code)
    except (httpx.HTTPError, ValueError, RuntimeError) as exc:
        print("pipeline failed:", type(exc).__name__)
    print(
        "attempts:",
        "search",
        budget.search,
        "extract",
        budget.extract,
        "model",
        budget.models,
    )


if __name__ == "__main__":
    asyncio.run(main())
