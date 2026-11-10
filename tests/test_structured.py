import asyncio

import pytest
from discoverybrief.structured import parse_submission, submit_role
from pydantic import BaseModel, ConfigDict


class Result(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: str


def response(name, arguments):
    return {
        "choices": [
            {
                "message": {
                    "tool_calls": [{"function": {"name": name, "arguments": arguments}}]
                }
            }
        ]
    }


def test_only_exact_tool_and_schema_are_accepted():
    assert (
        parse_submission(response("submit_payload", '{"value":"ok"}'), Result).value
        == "ok"
    )
    with pytest.raises(ValueError):
        parse_submission(response("execute_shell", '{"value":"ok"}'), Result)
    with pytest.raises(ValueError):
        parse_submission(response("submit_payload", '{"value":"ok","extra":1}'), Result)
    with pytest.raises(ValueError) as error:
        parse_submission(
            response("submit_payload", '{"value":"ok","PRIVATE-CANARY":1}'), Result
        )
    assert "PRIVATE-CANARY" not in str(error.value)
    with pytest.raises(ValueError):
        parse_submission({"choices": ["malformed"]}, Result)


def test_repair_is_bounded():
    class FakeClient:
        def __init__(self):
            self.calls = 0

        async def submit(self, *_):
            self.calls += 1
            return response("submit_payload", '{"bad":1}')

    client = FakeClient()
    with pytest.raises(ValueError):
        asyncio.run(submit_role(client, Result, [], 512))
    assert client.calls == 2


def test_repair_receives_safe_schema_diagnostic():
    class FakeClient:
        def __init__(self):
            self.calls = []

        async def submit(self, messages, *_):
            self.calls.append(messages)
            return response(
                "submit_payload",
                '{"value": 1}' if len(self.calls) == 1 else '{"value":"ok"}',
            )

    client = FakeClient()
    assert asyncio.run(submit_role(client, Result, [], 100)).value == "ok"
    assert "string_type@value" in client.calls[1][-1]["content"]
