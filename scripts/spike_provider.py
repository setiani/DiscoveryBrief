"""One public, non-sensitive gateway connectivity check; requires explicit opt-in."""

import asyncio

import httpx
from discoverybrief.clients import BifrostClient, CallBudget
from discoverybrief.config import Settings


async def main():
    settings = Settings.load()
    if not settings.enable_live_tests:
        raise SystemExit("Set ENABLE_LIVE_TESTS=1 for this paid check.")
    client = BifrostClient(
        settings.bifrost_base_url,
        settings.model_primary,
        CallBudget(),
        settings.bifrost_virtual_key,
    )
    try:
        response = await client.complete(
            [{"role": "user", "content": "Reply with the word OK."}], 32
        )
        choices = response.get("choices") or []
        content = choices[0].get("message", {}).get("content") if choices else None
        print(
            f"Gateway response: HTTP success; nonempty content: {bool(content)}; model: {settings.model_primary}"
        )
    except httpx.HTTPStatusError as exc:
        print(
            f"Gateway response: HTTP {exc.response.status_code}; model: {settings.model_primary}"
        )
    except httpx.HTTPError as exc:
        print(f"Gateway transport failure: {type(exc).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
