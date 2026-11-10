"""Bounded adapters; the application never talks directly to a model provider."""

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from threading import Lock
from time import monotonic
from urllib.parse import urlsplit

import httpx

from discoverybrief.gateway_config import gateway_model
from discoverybrief.metrics import UsageLedger
from discoverybrief.research import normalize_url


@dataclass
class CallBudget:
    search: int = 0
    extract: int = 0
    extract_urls: int = 0
    models: int = 0
    tavily_credits_reserved: int = 0
    deadline: float = 0
    _lock: Lock = field(default_factory=Lock, repr=False, compare=False)
    ledger: UsageLedger = field(default_factory=UsageLedger, repr=False, compare=False)

    def reserve(self, kind: str, urls: int = 0) -> None:
        with self._lock:
            if self.deadline and monotonic() >= self.deadline:
                raise RuntimeError("RUN_TIMEOUT")
            limit = {"search": 8, "extract": 4, "models": 8}[kind]
            credits = (
                2 if kind == "search" else ((urls + 4) // 5 if kind == "extract" else 0)
            )
            if (
                getattr(self, kind) >= limit
                or self.extract_urls + urls > 10
                or self.tavily_credits_reserved + credits > 24
            ):
                raise RuntimeError("BUDGET_LIMIT")
            setattr(self, kind, getattr(self, kind) + 1)
            self.extract_urls += urls
            self.tavily_credits_reserved += credits


class TavilyClient:
    def __init__(
        self,
        key: str,
        budget: CallBudget,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        if not key:
            raise ValueError("Tavily key missing")
        self.key, self.budget, self.transport = key, budget, transport

    async def _post(self, path: str, payload: dict, kind: str, urls: int = 0) -> dict:
        async with httpx.AsyncClient(transport=self.transport, timeout=20) as client:
            for attempt in range(2):
                self.budget.reserve(kind, urls)
                started = monotonic()
                metadata = {
                    "operation": kind,
                    "request_sha256": hashlib.sha256(
                        json.dumps(payload, sort_keys=True).encode()
                    ).hexdigest(),
                }

                def record_usage(credits, metadata=metadata, started=started):
                    self.budget.ledger.record_tavily(
                        credits,
                        {
                            **metadata,
                            "duration_ms": round((monotonic() - started) * 1000),
                        },
                    )

                try:
                    response = await client.post(
                        "https://api.tavily.com/" + path,
                        headers={"Authorization": "Bearer " + self.key},
                        json=payload,
                    )
                except asyncio.CancelledError:
                    record_usage(None)
                    raise
                except (httpx.TimeoutException, httpx.NetworkError):
                    record_usage(None)
                    if attempt:
                        raise
                    await asyncio.sleep(0.2)
                    continue
                if attempt == 0 and (
                    response.status_code == 429 or response.status_code >= 500
                ):
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait = float(retry_after) if retry_after is not None else 0.2
                    except ValueError:
                        wait = 4
                    if 0 <= wait <= 3:
                        record_usage(None)
                        await asyncio.sleep(wait)
                        continue
                if response.is_error:
                    record_usage(None)
                    response.raise_for_status()
                try:
                    data = response.json()
                    if not isinstance(data, dict):
                        raise ValueError("invalid Tavily response")  # noqa: TRY004
                except ValueError:
                    record_usage(None)
                    raise
                usage = data.get("usage")
                record_usage(usage.get("credits") if isinstance(usage, dict) else None)
                return data
        raise AssertionError("unreachable")

    async def search(self, query: dict, start_date: str, end_date: str) -> dict:
        payload = {
            "query": query["query"],
            "search_depth": "advanced",
            "topic": "general",
            "max_results": 5,
            "start_date": start_date,
            "end_date": end_date,
            "include_published_date": True,
            "include_usage": True,
        }
        if "include_domains" in query:
            payload["include_domains"] = query["include_domains"]
        return await self._post("search", payload, "search")

    async def extract(self, urls: list[str]) -> dict:
        if not 1 <= len(urls) <= 5:
            raise ValueError("extract expects 1 to 5 URLs")
        normalized = [normalize_url(url) for url in urls]
        if any((urlsplit(u).hostname or "").endswith(".example") for u in normalized):
            raise ValueError("synthetic domains cannot be sent to live Tavily")
        result = await self._post(
            "extract",
            {
                "urls": normalized,
                "extract_depth": "basic",
                "format": "text",
                "timeout": 15,
                "include_usage": True,
            },
            "extract",
            len(normalized),
        )
        failed_urls = []
        requested = set(normalized)
        for failed in result.get("failed_results", []):
            try:
                url = normalize_url(failed.get("url", ""))
            except (ValueError, AttributeError):
                continue
            if url in requested and url not in failed_urls:
                failed_urls.append(url)
        if failed_urls:
            try:
                retry = await self._post(
                    "extract",
                    {
                        "urls": failed_urls,
                        "extract_depth": "basic",
                        "format": "text",
                        "timeout": 15,
                        "include_usage": True,
                    },
                    "extract",
                    len(failed_urls),
                )
            except (httpx.HTTPError, ValueError, RuntimeError):
                return result
            result["results"] = [*result.get("results", []), *retry.get("results", [])]
            retried = set()
            for item in retry.get("results", []):
                try:
                    retried.add(normalize_url(item.get("url", "")))
                except (ValueError, AttributeError):
                    continue
            remaining = []
            for item in result.get("failed_results", []):
                try:
                    if normalize_url(item.get("url", "")) not in retried:
                        remaining.append(item)
                except (ValueError, AttributeError):
                    remaining.append(item)
            result["failed_results"] = remaining
        return result


class BifrostClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        budget: CallBudget,
        virtual_key: str = "",
        transport: httpx.AsyncBaseTransport | None = None,
        fallback_model: str = "",
        min_interval_seconds: float = 0,
    ):
        if not model or not base_url.startswith(("http://", "https://")):
            raise ValueError("Bifrost URL and model are required")
        parsed = urlsplit(base_url)
        if (
            parsed.hostname not in {"127.0.0.1", "::1", "localhost", "bifrost"}
            or parsed.username
            or parsed.password
        ):
            raise ValueError("Bifrost must point to the configured local gateway")
        self.base_url, self.model, self.budget = (
            base_url.rstrip("/"),
            gateway_model(model),
            budget,
        )
        self.virtual_key, self.transport = virtual_key, transport
        self.fallback_model = gateway_model(fallback_model) if fallback_model else None
        if not 0 <= min_interval_seconds <= 60:
            raise ValueError("model call interval must be between 0 and 60 seconds")
        self.min_interval_seconds = min_interval_seconds
        self._last_model_start = 0.0
        self._model_lock = asyncio.Lock()
        if self.fallback_model:
            # Gateway fallback attempts may incur usage not included in the final response.
            self.budget.ledger.model_coverage_known = False

    async def submit(self, messages: list[dict], schema: dict, max_tokens: int) -> dict:
        async with self._model_lock:
            return await self._submit(messages, schema, max_tokens)

    async def complete(self, messages: list[dict], max_tokens: int) -> dict:
        """Make a single ordinary completion, used for the evaluation baseline."""
        async with self._model_lock:
            return await self._submit(messages, None, max_tokens)

    async def _submit(
        self, messages: list[dict], schema: dict | None, max_tokens: int
    ) -> dict:
        if len(json.dumps(messages, ensure_ascii=False)) > 48000:
            raise ValueError("model input exceeds limit")
        headers = {"x-bf-vk": self.virtual_key} if self.virtual_key else {}
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if schema is not None:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": "submit_payload",
                        "description": "Submit structured role result",
                        "parameters": schema,
                    },
                }
            ]
            payload["tool_choice"] = "auto"
        if self.fallback_model:
            payload["fallbacks"] = [self.fallback_model]
        async with httpx.AsyncClient(transport=self.transport, timeout=100) as client:
            delay = max(
                0.0, self._last_model_start + self.min_interval_seconds - monotonic()
            )
            if self.budget.deadline and monotonic() + delay >= self.budget.deadline:
                raise RuntimeError("RUN_TIMEOUT")
            if delay:
                await asyncio.sleep(delay)
            self.budget.reserve("models")
            self._last_model_start = monotonic()
            started = monotonic()
            call_metadata = {
                "requested_model": self.model,
                "resolved_model": None,
                "role": schema.get("title") if schema else "baseline",
                "schema_version": "1.0",
                "prompt_sha256": hashlib.sha256(
                    json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()
                ).hexdigest(),
                "schema_sha256": hashlib.sha256(
                    json.dumps(schema, sort_keys=True).encode()
                ).hexdigest(),
            }
            try:
                response = await client.post(
                    self.base_url + "/chat/completions", headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    raise ValueError("invalid Bifrost response")  # noqa: TRY004
            except (httpx.HTTPError, ValueError, asyncio.CancelledError):
                self.budget.ledger.record_model(
                    None,
                    {
                        **call_metadata,
                        "duration_ms": round((monotonic() - started) * 1000),
                        "status": "failed",
                    },
                )
                raise
            extra = data.get("extra_fields")
            extra = extra if isinstance(extra, dict) else {}
            resolved = extra.get("resolved_model_used") or data.get("model")
            self.budget.ledger.record_model(
                data.get("usage"),
                {
                    **call_metadata,
                    "resolved_model": resolved if isinstance(resolved, str) else None,
                    "duration_ms": round((monotonic() - started) * 1000),
                    "status": "received",
                    "provider_request_id": response.headers.get("x-request-id"),
                },
            )
            return data
