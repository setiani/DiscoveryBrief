"""Synthetic auditor diagnostic with live model, independent of web search."""

import asyncio
import json
import os
from pathlib import Path

import httpx
from discoverybrief.clients import BifrostClient, CallBudget
from discoverybrief.config import Settings
from discoverybrief.pipeline import messages
from discoverybrief.roles import PremiseAudit
from discoverybrief.structured import submit_role


async def main():
    settings = Settings.load()
    if os.getenv("ENABLE_LIVE_TESTS") != "1":
        raise SystemExit("Set ENABLE_LIVE_TESTS=1")
    base = Path(__file__).resolve().parents[1] / "tests/fixtures"
    roles = json.loads((base / "role-outputs.json").read_text(encoding="utf-8"))
    budget = CallBudget()
    client = BifrostClient(
        settings.bifrost_base_url,
        settings.model_primary,
        budget,
        settings.bifrost_virtual_key,
        min_interval_seconds=settings.model_min_interval_seconds,
    )

    class SyntheticRecorder:
        async def submit(self, messages, schema, max_tokens):
            response = await client.submit(messages, schema, max_tokens)
            # This spike uses synthetic input only. Runtime data/ is git-ignored.
            out = Path("data/spikes")
            out.mkdir(parents=True, exist_ok=True)
            (out / f"auditor-{budget.models}.json").write_text(
                json.dumps(response, ensure_ascii=False), encoding="utf-8"
            )
            return response

    context = {
        "proposals": roles["composer"],
        "claims": [{"claim_id": "c0001", **roles["analyst"]["claims"][0]}],
        "requirements": [
            {"requirement_id": "r0001", **roles["analyst"]["requirements"][0]}
        ],
        "context": {"company_name": "Sagara Insurance", "participants": []},
    }
    prompt = messages(
        "Premise Auditor",
        "Reject any question or hypothesis that assumes unsupported facts. Review each supplied item. "
        "Submit exactly one JSON object using the tool, with each reason under 200 characters.",
        context,
    )
    try:
        output = await submit_role(SyntheticRecorder(), PremiseAudit, prompt, 1024)
        print("auditor: valid schema; decisions:", len(output.items))
    except httpx.HTTPStatusError as exc:
        print("auditor: HTTP", exc.response.status_code)
    except (httpx.HTTPError, ValueError, RuntimeError) as exc:
        print(
            "auditor: invalid output category:",
            str(exc) if isinstance(exc, ValueError) else type(exc).__name__,
        )
    print("Bifrost requests:", budget.models)


if __name__ == "__main__":
    asyncio.run(main())
