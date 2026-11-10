"""Paid, bounded gateway fallback checks using public synthetic input only."""

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
from discoverybrief.clients import BifrostClient, CallBudget
from discoverybrief.config import Settings
from discoverybrief.structured import parse_submission
from pydantic import BaseModel, ConfigDict


class Greeting(BaseModel):
    model_config = ConfigDict(extra="forbid")
    greeting: str


async def main(use_primary_as_fallback=False):
    settings = Settings.load()
    if not settings.enable_live_tests:
        raise SystemExit("Set ENABLE_LIVE_TESTS=1")
    fallback = (
        settings.model_primary if use_primary_as_fallback else settings.model_fallback
    )
    if not fallback:
        raise SystemExit("Set MODEL_FALLBACK or pass --use-primary-as-fallback")
    invalid = "invalid-model-discoverybrief-spike"
    cases = [
        ("primary_unavailable", invalid, ""),
        ("fallback_structured", invalid, fallback),
        ("both_unavailable", invalid, invalid + "-fallback"),
    ]
    records = []
    for name, primary, secondary in cases:
        budget = CallBudget()
        client = BifrostClient(
            settings.bifrost_base_url,
            primary,
            budget,
            settings.bifrost_virtual_key,
            fallback_model=secondary,
        )
        record = {
            "case": name,
            "requested_model": client.model,
            "fallback_model": client.fallback_model,
        }
        try:
            result = await client.submit(
                [
                    {
                        "role": "user",
                        "content": "Call submit_payload with greeting set to hello.",
                    }
                ],
                Greeting.model_json_schema(),
                128,
            )
            parsed = parse_submission(result, Greeting)
            record.update(
                status="received",
                structured_output_valid=bool(parsed.greeting),
                response_model=result.get("model"),
                routing={
                    k: v
                    for k, v in (result.get("extra_fields") or {}).items()
                    if k
                    in {"provider", "original_model_requested", "resolved_model_used"}
                },
            )
        except httpx.HTTPStatusError as exc:
            record.update(status="failed", http_status=exc.response.status_code)
        except (httpx.HTTPError, ValueError, RuntimeError) as exc:
            record.update(status="failed", error_type=type(exc).__name__)
        record["calls"] = budget.ledger.calls
        record["metrics"] = budget.ledger.summary()
        records.append(record)
    passed = (
        records[0]["status"] == "failed"
        and records[1].get("structured_output_valid") is True
        and records[2]["status"] == "failed"
    )
    result = {
        "checked_at": datetime.now(UTC).isoformat(),
        "passed": passed,
        "scope": "Unavailable model recovery on the same provider; not provider outage failover",
        "cases": records,
    }
    output = Path("data/spikes") / (
        "fallback-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + ".json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print("artifact:", output)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--use-primary-as-fallback", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.use_primary_as_fallback))
