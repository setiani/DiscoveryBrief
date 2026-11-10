import asyncio
import json

import httpx
import pytest
from discoverybrief.clients import BifrostClient, CallBudget, TavilyClient


def test_tavily_payload_and_budget():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"results": [], "failed_results": []})

    budget = CallBudget()
    client = TavilyClient("test-key", budget, httpx.MockTransport(handler))
    asyncio.run(client.search({"query": '"Company" news'}, "2026-10-01", "2026-11-01"))
    assert seen[0].url.host == "api.tavily.com"
    assert json.loads(seen[0].content)["query"] == '"Company" news'
    assert budget.search == 1
    assert budget.tavily_credits_reserved == 2
    assert budget.ledger.summary()["tavily_credits_reported"] is None
    with pytest.raises(ValueError):
        asyncio.run(client.extract(["https://sagara.example/fake"]))
    assert budget.extract == 0


def test_bifrost_only_and_budget():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"choices": []})

    budget = CallBudget(models=7)
    client = BifrostClient(
        "http://127.0.0.1:8080/v1",
        "provider/model",
        budget,
        transport=httpx.MockTransport(handler),
        fallback_model="nvidia/test:free",
    )
    with pytest.raises(ValueError, match="local gateway"):
        BifrostClient("https://router.bynara.id/v1", "model", CallBudget())
    asyncio.run(client.submit([], {"type": "object"}, 512))
    assert str(seen[0].url) == "http://127.0.0.1:8080/v1/chat/completions"
    assert json.loads(seen[0].content)["model"] == "custom/provider/model"
    assert json.loads(seen[0].content)["fallbacks"] == ["custom/nvidia/test:free"]
    with pytest.raises(RuntimeError, match="BUDGET_LIMIT"):
        asyncio.run(client.submit([], {"type": "object"}, 512))
    assert len(seen) == 1


def test_baseline_completion_is_one_gateway_call_without_tools():
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    budget = CallBudget()
    client = BifrostClient(
        "http://127.0.0.1:8080/v1",
        "model",
        budget,
        transport=httpx.MockTransport(handler),
    )
    asyncio.run(client.complete([{"role": "user", "content": "hello"}], 20))
    assert len(requests) == budget.models == 1
    assert "tools" not in requests[0] and "tool_choice" not in requests[0]


def test_tavily_retries_are_counted_and_401_is_not_retried():
    attempts = []

    def handler(request):
        attempts.append(request)
        return httpx.Response(503 if len(attempts) == 1 else 200, json={"results": []})

    budget = CallBudget()
    client = TavilyClient("test-key", budget, httpx.MockTransport(handler))
    asyncio.run(client.search({"query": "public"}, "2026-10-01", "2026-11-01"))
    assert len(attempts) == budget.search == 2
    assert len(budget.ledger.tavily_credits) == 2
    attempts.clear()

    def unauthorized(request):
        attempts.append(request)
        return httpx.Response(401)

    client = TavilyClient("test-key", CallBudget(), httpx.MockTransport(unauthorized))
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(client.search({"query": "public"}, "2026-10-01", "2026-11-01"))
    assert len(attempts) == 1


def test_partial_extract_retries_only_original_failed_urls():
    attempts = []

    def handler(request):
        payload = json.loads(request.content)
        attempts.append(payload["urls"])
        if len(attempts) == 1:
            return httpx.Response(
                200,
                json={
                    "results": [{"url": "https://one.test/page", "raw_content": "ok"}],
                    "failed_results": [
                        {"url": "https://two.test/page"},
                        {"url": "https://unrequested.test/"},
                    ],
                },
            )
        return httpx.Response(
            200,
            json={
                "results": [{"url": "https://two.test/page", "raw_content": "now ok"}],
                "failed_results": [],
            },
        )

    budget = CallBudget()
    client = TavilyClient("test", budget, httpx.MockTransport(handler))
    result = asyncio.run(
        client.extract(["https://one.test/page", "https://two.test/page"])
    )
    assert attempts == [
        ["https://one.test/page", "https://two.test/page"],
        ["https://two.test/page"],
    ]
    assert len(result["results"]) == 2
    assert budget.extract == 2 and budget.extract_urls == 3


def test_model_requests_obey_configured_interval(monkeypatch):
    from discoverybrief import clients

    clock = [1000.0]

    async def advance(delay):
        clock[0] += delay

    monkeypatch.setattr(clients, "monotonic", lambda: clock[0])
    monkeypatch.setattr(clients.asyncio, "sleep", advance)
    starts = []

    def handler(request):
        starts.append(clock[0])
        return httpx.Response(200, json={"choices": []})

    client = BifrostClient(
        "http://127.0.0.1:8080/v1",
        "model",
        CallBudget(),
        transport=httpx.MockTransport(handler),
        min_interval_seconds=0.03,
    )

    async def run():
        await asyncio.gather(client.submit([], {}, 20), client.submit([], {}, 20))

    asyncio.run(run())
    assert starts[1] - starts[0] >= 0.029


def test_resolved_gateway_model_preserves_unknown_fallback_usage():
    def handler(request):
        return httpx.Response(
            200,
            json={
                "model": "provider/backup",
                "extra_fields": {"resolved_model_used": "backup"},
                "usage": {"prompt_tokens": 10, "completion_tokens": 2},
                "choices": [],
            },
        )

    budget = CallBudget()
    client = BifrostClient(
        "http://127.0.0.1:8080/v1",
        "missing-primary",
        budget,
        fallback_model="backup",
        transport=httpx.MockTransport(handler),
    )
    asyncio.run(client.complete([], 16))
    assert budget.ledger.calls[0]["requested_model"] == "custom/missing-primary"
    assert budget.ledger.calls[0]["resolved_model"] == "backup"
    assert budget.ledger.summary()["llm_input_tokens"] == 10
    assert budget.ledger.summary()["model_usage_complete"] is False
