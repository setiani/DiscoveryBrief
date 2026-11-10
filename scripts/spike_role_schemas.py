"""Explicitly enabled paid, synthetic-only Bifrost role-schema smoke test."""

import asyncio
import json
import os
from pathlib import Path

import httpx
from discoverybrief.clients import BifrostClient, CallBudget
from discoverybrief.config import Settings
from discoverybrief.pipeline import messages
from discoverybrief.roles import (
    AnalystOutput,
    ComposerOutput,
    PremiseAudit,
    ResearchPlan,
    VerifierOutput,
)
from discoverybrief.structured import submit_role


async def main():
    settings = Settings.load()
    if os.getenv("ENABLE_LIVE_TESTS") != "1":
        raise SystemExit("Set ENABLE_LIVE_TESTS=1 explicitly")
    fixtures = Path(__file__).resolve().parents[1] / "tests/fixtures/role-outputs.json"
    sample = json.loads(fixtures.read_text(encoding="utf-8"))
    budget = CallBudget()
    gateway = BifrostClient(
        settings.bifrost_base_url,
        settings.model_primary,
        budget,
        settings.bifrost_virtual_key,
        min_interval_seconds=settings.model_min_interval_seconds,
    )
    for key, schema, limit in [
        ("planner", ResearchPlan, 512),
        ("analyst", AnalystOutput, 4096),
        ("verifier", VerifierOutput, 2048),
        ("composer", ComposerOutput, 2048),
        ("auditor", PremiseAudit, 1024),
    ]:
        if os.getenv("SPIKE_ROLE") and os.getenv("SPIKE_ROLE") != key:
            continue
        try:
            await submit_role(
                gateway,
                schema,
                messages(
                    key,
                    "Return the supplied synthetic example through submit_payload, preserving field values.",
                    {"example": sample[key]},
                ),
                limit,
            )
            print(f"{key}: schema valid")
        except httpx.HTTPStatusError as exc:
            print(f"{key}: HTTP {exc.response.status_code}")
        except (httpx.HTTPError, ValueError, RuntimeError) as exc:
            print(f"{key}: failed ({type(exc).__name__})")
        if budget.models >= 8:
            break
    print(f"bifrost_requests={budget.models}; maximum=8")


if __name__ == "__main__":
    asyncio.run(main())
