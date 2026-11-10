"""Aggregate provider usage conservatively: unknown is never silently zero."""

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class UsageLedger:
    input_tokens: list[int | None] = field(default_factory=list)
    output_tokens: list[int | None] = field(default_factory=list)
    tavily_credits: list[float | None] = field(default_factory=list)
    model_coverage_known: bool = True
    on_call: Callable[[dict], None] | None = field(default=None, repr=False)
    calls: list[dict] = field(default_factory=list)

    def _record(self, kind: str, usage, metadata: dict | None = None):
        call = {
            "call_id": f"call{len(self.calls) + 1:04d}",
            "kind": kind,
            "usage": usage,
            **(metadata or {}),
        }
        self.calls.append(call)
        if self.on_call:
            self.on_call(call)

    def record_model(self, usage: dict | None, metadata: dict | None = None) -> None:
        def count(key):
            value = usage.get(key) if isinstance(usage, dict) else None
            return (
                value
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0
                else None
            )

        self.input_tokens.append(count("prompt_tokens"))
        self.output_tokens.append(count("completion_tokens"))
        self._record(
            "model",
            {
                "input_tokens": self.input_tokens[-1],
                "output_tokens": self.output_tokens[-1],
            },
            metadata,
        )

    def record_tavily(self, value: float | None, metadata: dict | None = None) -> None:
        self.tavily_credits.append(
            value
            if isinstance(value, (int, float))
            and not isinstance(value, bool)
            and value >= 0
            else None
        )
        self._record("tavily", {"credits": self.tavily_credits[-1]}, metadata)

    def summary(self) -> dict:
        def total(values):
            return (
                sum(values)
                if values and all(item is not None for item in values)
                else None
            )

        model_complete = self.model_coverage_known and all(
            item is not None for item in self.input_tokens + self.output_tokens
        )
        tavily_complete = all(item is not None for item in self.tavily_credits)
        return {
            "llm_input_tokens": total(self.input_tokens),
            "llm_output_tokens": total(self.output_tokens),
            "tavily_credits_reported": total(self.tavily_credits),
            "usage_complete": model_complete and tavily_complete,
            "model_usage_complete": model_complete,
            "tavily_usage_complete": tavily_complete,
            "estimated_model_cost_microusd": None,
        }
