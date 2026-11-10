from datetime import UTC, datetime

import pytest
from discoverybrief.research import (
    exact_quote,
    make_queries,
    normalize_url,
    recent_date,
)
from discoverybrief.schemas import RunRequest
from test_contracts import fixture


def test_query_construction_excludes_private_data():
    data = fixture()
    data["notes"] = "PRIVATE-RFP-CANARY-8721"
    data["rfp_text"] = "PRIVATE-RFP-CANARY-8721"
    queries = make_queries(
        RunRequest.model_validate(data), ["official_news", "partnership"]
    )
    assert "PRIVATE-RFP-CANARY-8721" not in str(queries)
    assert "Rina" not in str(queries)
    assert queries[0]["include_domains"] == ["sagara.example"]


def test_exact_unicode_quote_and_missing_quote():
    text = "😀 Portal harus mendukung SSO."
    assert exact_quote(text, "Portal harus mendukung SSO.")["start"] == 2
    assert exact_quote(text, "Portal harus mendukung OAuth.") is None


def test_urls_and_dates():
    assert (
        normalize_url("https://EXAMPLE.com/x?utm_source=a&b=2#fragment")
        == "https://example.com/x?b=2"
    )
    for url in [
        "http://127.0.0.1/a",
        "http://127.1/a",
        "http://0x7f.0.0.1/a",
        "http://localhost/a",
        "javascript:alert(1)",
    ]:
        with pytest.raises(ValueError):
            normalize_url(url)
    start = datetime(2026, 10, 13, tzinfo=UTC)
    cutoff = datetime(2026, 11, 8, tzinfo=UTC)
    assert not recent_date(datetime(2026, 9, 20).date(), start, cutoff)
    assert not recent_date(datetime(2026, 11, 10).date(), start, cutoff)


def test_date_only_window_uses_meeting_timezone():
    start = datetime(2026, 10, 12, 18, tzinfo=UTC)
    cutoff = datetime(2026, 11, 7, 18, tzinfo=UTC)
    assert not recent_date(datetime(2026, 10, 12).date(), start, cutoff, "Asia/Jakarta")
    assert recent_date(datetime(2026, 11, 8).date(), start, cutoff, "Asia/Jakarta")
