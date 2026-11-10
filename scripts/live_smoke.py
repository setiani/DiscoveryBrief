"""Small, explicitly enabled paid smoke test; prints only non-secret metadata."""

import asyncio
import os

import httpx
from discoverybrief.clients import BifrostClient, CallBudget, TavilyClient
from discoverybrief.config import Settings
from discoverybrief.gateway_config import gateway_model


async def main() -> None:
    settings = Settings.load()
    if os.getenv("ENABLE_LIVE_TESTS") != "1":
        raise SystemExit("Set ENABLE_LIVE_TESTS=1 explicitly for paid tests")
    budget = CallBudget()
    model = gateway_model(settings.model_primary)
    tavily = TavilyClient(settings.tavily_api_key, budget)
    bifrost = BifrostClient(
        settings.bifrost_base_url, model, budget, settings.bifrost_virtual_key
    )
    for name, call in [
        (
            "tavily_search",
            lambda: tavily.search(
                {
                    "query": '"OpenAI" news announcements',
                    "include_domains": ["openai.com"],
                },
                "2026-10-10",
                "2026-11-09",
            ),
        ),
        (
            "bifrost_model",
            lambda: bifrost.submit(
                [
                    {
                        "role": "user",
                        "content": "Return the word hello using the submit_payload tool.",
                    }
                ],
                {
                    "type": "object",
                    "properties": {"greeting": {"type": "string"}},
                    "required": ["greeting"],
                    "additionalProperties": False,
                },
                1024,
            ),
        ),
        (
            "tavily_extract",
            lambda: tavily.extract(
                [
                    "https://openai.com/news/",
                    "https://openai.com/this-page-is-a-discoverybrief-test-404",
                ]
            ),
        ),
    ]:
        if os.getenv("SMOKE_ONLY") and os.getenv("SMOKE_ONLY") != name:
            continue
        try:
            result = await call()
            if name == "tavily_search":
                print(
                    f"{name}: HTTP success, result_count={len(result.get('results', []))}, usage_reported={result.get('usage') is not None}"
                )
            elif name == "tavily_extract":
                print(
                    f"{name}: HTTP success, succeeded={len(result.get('results', []))}, failed={len(result.get('failed_results', []))}, usage_reported={result.get('usage') is not None}"
                )
            else:
                choice = (result.get("choices") or [{}])[0]
                calls = choice.get("message", {}).get("tool_calls") or []
                print(
                    f"{name}: HTTP success, tool_call_count={len(calls)}, usage_reported={result.get('usage') is not None}"
                )
                print(
                    f"  response_fields={sorted(result)}, choices={len(result.get('choices') or [])}, finish_reason={choice.get('finish_reason')}, content_present={bool(choice.get('message', {}).get('content'))}"
                )
                if not calls:
                    print(
                        "  INVALID_MODEL_OUTPUT: no structured tool call; do not treat HTTP 200 as a passing model spike"
                    )
        except httpx.HTTPStatusError as exc:
            print(f"{name}: HTTP {exc.response.status_code}")
            if name == "bifrost_model":
                try:
                    error = exc.response.json().get("error", {})
                    print(
                        f"  error type={error.get('type', 'unknown')}; code={error.get('code', 'unknown')}"
                    )
                    message = str(error.get("message", ""))[:500]
                    for key in (
                        "MODEL_PROVIDER_API_KEY",
                        "BIFROST_VIRTUAL_KEY",
                        "TAVILY_API_KEY",
                    ):
                        secret = os.getenv(key, "")
                        if secret:
                            message = message.replace(secret, "[redacted]")
                    print(f"  message={message}")
                except (ValueError, AttributeError):
                    print("  provider did not return a structured error")
        except (httpx.HTTPError, ValueError) as exc:
            print(f"{name}: {type(exc).__name__}")
    print(f"calls: search={budget.search}, model={budget.models}")


if __name__ == "__main__":
    asyncio.run(main())
