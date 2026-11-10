"""Deterministic public-query and evidence checks used by the research pipeline."""

from datetime import date, datetime
from hashlib import sha256
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from discoverybrief.schemas import RunRequest

QUERY_PHRASES = {
    "official_news": "news announcements",
    "product_launch": "product launch service launch",
    "partnership": "partnership distribution agreement",
    "leadership": "executive appointment leadership",
    "digital_platform": "digital platform customer portal",
    "business_updates": "company business update",
}


def make_queries(request: RunRequest, kinds: list[str]) -> list[dict]:
    """Only explicit public fields enter Tavily queries."""
    if (
        not 2 <= len(kinds) <= 6
        or len(set(kinds)) != len(kinds)
        or any(k not in QUERY_PHRASES for k in kinds)
    ):
        raise ValueError("invalid research plan")
    if request.company_domain and "official_news" not in kinds:
        kinds = ["official_news", *kinds[:5]]
    result = []
    for kind in kinds:
        # The company name is quoted after rejecting control characters and quotes.
        name = (
            request.company_name.replace('"', " ").replace("\n", " ").replace("\r", " ")
        )
        pieces = [
            f'"{name}"',
            request.company_country or "",
            request.company_industry or "",
            QUERY_PHRASES[kind],
            *request.public_topics,
        ]
        item = {"kind": kind, "query": " ".join(p for p in pieces if p)}
        if kind == "official_news" and request.company_domain:
            item["include_domains"] = [request.company_domain]
        result.append(item)
    return result


def evidence_passages(sources: list[dict], limit: int = 24000) -> list[dict]:
    """Distribute the prompt budget across distinct extracts, preserving literal prefixes."""
    usable = [
        s
        for s in sources
        if s.get("extraction_status") == "ok" and not s.get("duplicate_of_source_id")
    ]
    selected = usable or [s for s in sources if not s.get("duplicate_of_source_id")]
    selected = selected[:10]
    if not selected:
        return []
    allowance = limit // len(selected)
    return [
        {
            "source_id": s["source_id"],
            "url": s["canonical_url"],
            "text": s["text"][:allowance],
            "text_origin": s["text_origin"],
            "extraction_status": s["extraction_status"],
            "date": s.get("raw_provider_date"),
            "published_on": s.get("published_on"),
            "published_at": s.get("published_at"),
            "date_basis": s.get("date_basis", "unknown"),
            "date_quote": s.get("date_quote"),
            "prompt_truncated": len(s["text"]) > allowance,
        }
        for s in selected
    ]


def normalize_url(url: str) -> str:
    import re
    from ipaddress import ip_address

    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not host
        or parsed.username
        or parsed.password
    ):
        raise ValueError("invalid public URL")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("private hostname")
    try:
        addr = ip_address(host)
        if not addr.is_global:
            raise ValueError("private IP")
    except ValueError as exc:
        if str(exc) == "private IP":
            raise
    if not re.fullmatch(r"[a-z0-9.-]+", host) or "." not in host:
        raise ValueError("invalid public hostname")
    labels = host.split(".")
    if any(
        not label or len(label) > 63 or label.startswith("-") or label.endswith("-")
        for label in labels
    ):
        raise ValueError("invalid public hostname")
    if all(re.fullmatch(r"(?:0x[0-9a-f]+|[0-9]+)", label) for label in labels):
        raise ValueError("numeric hostname is not permitted")
    port = parsed.port
    authority = host + (
        f":{port}"
        if port and (parsed.scheme.lower(), port) not in {("http", 80), ("https", 443)}
        else ""
    )
    query = sorted(
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"}
    )
    return urlunsplit(
        (parsed.scheme.lower(), authority, parsed.path, urlencode(query), "")
    )


def exact_quote(text: str, quote: str) -> dict | None:
    if not quote or len(quote) > 600:
        return None
    start = text.find(quote)
    if start < 0:
        return None
    return {
        "quote": quote,
        "start": start,
        "end": start + len(quote),
        "quote_sha256": sha256(quote.encode("utf-8")).hexdigest(),
    }


def recent_date(
    event_on: date | None,
    window_start: datetime,
    cutoff: datetime,
    meeting_timezone: str = "UTC",
) -> bool:
    """A date-only filter; caller must flag partial boundary-day ambiguity."""
    from zoneinfo import ZoneInfo

    zone = ZoneInfo(meeting_timezone)
    return bool(
        event_on
        and window_start.astimezone(zone).date()
        <= event_on
        <= cutoff.astimezone(zone).date()
    )
