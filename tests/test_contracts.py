import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from discoverybrief.schemas import RunRequest
from pydantic import ValidationError


def fixture() -> dict:
    return json.loads(
        (Path(__file__).parent / "fixtures" / "request.json").read_text(
            encoding="utf-8"
        )
    )


def test_sample_request_and_public_boundary():
    request = RunRequest.model_validate(fixture())
    request.validate_horizon(datetime(2026, 11, 8, 3, tzinfo=UTC))
    public = request.public_context(datetime(2026, 11, 8, 3, tzinfo=UTC))
    assert set(public).isdisjoint({"rfp_text", "notes", "participants", "meeting_goal"})
    assert "Rina" not in str(public)
    assert public["window_start"].startswith("2026-10-13")


def test_english_default_preserves_explicit_indonesian_requests():
    data = fixture()
    assert data["language"] == "id"
    assert RunRequest.model_validate(data).language == "id"
    data.pop("language")
    assert RunRequest.model_validate(data).language == "en"


@pytest.mark.parametrize(
    "field,value",
    [
        ("meeting_at", "2026-11-12T10:00:00"),
        ("meeting_at", "2026-11-12T10:00:00+00:00"),
        ("rfp_text", "x" * 12001),
        ("company_domain", "https://example.com/path"),
        ("company_domain", "127.0.0.1"),
    ],
)
def test_invalid_input_rejected(field, value):
    data = fixture()
    data[field] = value
    with pytest.raises(ValidationError):
        RunRequest.model_validate(data)


def test_horizon_rejected():
    request = RunRequest.model_validate(fixture())
    with pytest.raises(ValueError, match="within"):
        request.validate_horizon(datetime(2026, 1, 1, tzinfo=UTC))
