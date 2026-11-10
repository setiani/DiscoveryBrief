"""Literal date evidence and explicit instant/day eligibility."""

import re
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

MONTHS = dict(
    zip(
        (
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ),
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        strict=True,
    )
)


def parse_instant(value: str | None) -> datetime | None:
    if not value or "T" not in value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.utcoffset() is not None else None
    except ValueError:
        return None


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    instant = parse_instant(value)
    if instant:
        return instant.date()
    for indonesian, english in MONTHS.items():
        value = re.sub(r"\b" + indonesian + r"\b", english, value, flags=re.IGNORECASE)
    for fmt in (
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%B %d %Y",
        "%b %d %Y",
    ):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            pass
    return None


def eligibility(
    value: str, start: datetime, cutoff: datetime, timezone: str
) -> tuple[bool, bool]:
    """Day-only boundaries are inclusive but carry uncertainty on partial days."""
    instant = parse_instant(value)
    if instant:
        return start <= instant <= cutoff, False
    day = parse_date(value)
    zone = ZoneInfo(timezone)
    lower, upper = start.astimezone(zone), cutoff.astimezone(zone)
    if not day or not lower.date() <= day <= upper.date():
        return False, False
    partial = (day == lower.date() and lower.time() != time.min) or (
        day == upper.date() and upper.time() != time.max
    )
    return True, partial


def publication_metadata(text: str) -> dict:
    """Only an explicit original publication label establishes publication basis."""
    match = re.search(
        r"(?:^|\n)\s*(?:Published|Originally published|Diterbitkan)\s*[:\-]?\s*"
        r"(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))?|\d{1,2} [A-Za-z]+ \d{4}|[A-Za-z]+ \d{1,2},? \d{4})",
        text,
        re.IGNORECASE,
    )
    if not match or not parse_date(match[1]):
        return {}
    literal = match[1]
    instant = parse_instant(literal)
    return {
        "published_on": parse_date(literal).isoformat(),
        "published_at": instant.isoformat() if instant else None,
        "date_quote": literal,
        "date_basis": "publication",
        "date_precision": "instant" if instant else "day",
    }
