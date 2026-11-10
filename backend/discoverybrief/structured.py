"""Strict parsing of Bifrost tool submissions, with one bounded repair."""

import json
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from discoverybrief.clients import BifrostClient

T = TypeVar("T", bound=BaseModel)


def parse_submission(response: dict, model: type[T], *, allow_json: bool = False) -> T:
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("expected exactly one model choice")
    if not isinstance(choices[0], dict):
        raise ValueError("invalid model choice")  # noqa: TRY004
    message = choices[0].get("message", {})
    if not isinstance(message, dict):
        raise ValueError("invalid model message")  # noqa: TRY004
    calls = message.get("tool_calls") or []
    if not isinstance(calls, list):
        raise ValueError("invalid tool call collection")  # noqa: TRY004
    if calls:
        if len(calls) != 1 or not isinstance(calls[0], dict):
            raise ValueError("unexpected tool submission")
        function = calls[0].get("function")
        if not isinstance(function, dict) or function.get("name") != "submit_payload":
            raise ValueError("unexpected tool submission")
        raw = function.get("arguments")
    elif allow_json:
        raw = message.get("content")
    else:
        raise ValueError("missing structured submission")
    if not isinstance(raw, str) or len(raw) > 48000:
        raise ValueError("invalid payload size")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid_json") from exc
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        allowed = set()

        def collect(node):
            if isinstance(node, dict):
                allowed.update(node.get("properties", {}).keys())
                for value in node.values():
                    collect(value)
            elif isinstance(node, list):
                for value in node:
                    collect(value)

        collect(model.model_json_schema())
        errors = exc.errors(
            include_input=False, include_context=False, include_url=False
        )
        details = []
        for item in errors[:10]:
            location = ".".join(
                str(part)
                for part in item["loc"]
                if isinstance(part, int) or part in allowed
            )
            details.append(item["type"] + ("@" + location if location else ""))
        # Field names are taken only from the schema; never copy model input into diagnostics.
        raise ValueError("schema_invalid:" + ",".join(details)) from exc


async def submit_role(
    client: BifrostClient,
    model: type[T],
    messages: list[dict],
    max_tokens: int,
    *,
    allow_json: bool = False,
) -> T:
    if len(json.dumps(messages, ensure_ascii=False)) > 48000:
        raise ValueError("model input exceeds limit")
    for attempt in range(2):
        if len(json.dumps(messages, ensure_ascii=False)) > 48000:
            raise ValueError("model input exceeds limit")
        response = await client.submit(messages, model.model_json_schema(), max_tokens)
        try:
            return parse_submission(response, model, allow_json=allow_json)
        except ValueError as exc:
            if attempt:
                raise
            reason = str(exc)
            if not reason.startswith(("schema_invalid:", "invalid_json")):
                reason = "invalid structured submission"
            messages = [
                *messages,
                {
                    "role": "user",
                    "content": f"The submission was invalid ({reason}). Submit a valid payload matching the schema exactly.",
                },
            ]
    raise AssertionError("unreachable")
