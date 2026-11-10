"""Public-only basic inference smoke through local Bifrost; no raw contents or secrets printed."""

import asyncio
import os

import httpx
from discoverybrief.config import Settings
from discoverybrief.gateway_config import gateway_model


async def main():
    settings = Settings.load()
    if os.getenv("ENABLE_LIVE_TESTS") != "1":
        raise SystemExit("Set ENABLE_LIVE_TESTS=1")
    model = gateway_model(os.getenv("SMOKE_MODEL", settings.model_primary))
    async with httpx.AsyncClient(timeout=100) as client:
        try:
            response = await client.post(
                settings.bifrost_base_url + "/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Reply with hello."}],
                    "max_tokens": 128,
                },
            )
            print("status:", response.status_code)
            data = response.json()
            choices = data.get("choices") or []
            print(
                "choices:",
                len(choices),
                "usage_reported:",
                data.get("usage") is not None,
            )
            if choices:
                print(
                    "content_present:",
                    bool(choices[0].get("message", {}).get("content")),
                )
            elif response.status_code >= 400:
                print("error_type:", data.get("error", {}).get("type", "unknown"))
        except httpx.HTTPError as exc:
            print("request_error:", type(exc).__name__)


if __name__ == "__main__":
    asyncio.run(main())
