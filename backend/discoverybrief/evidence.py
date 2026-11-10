"""Structural approval gates. Semantic decisions must be supplied by the verifier."""

import re
from datetime import date, datetime
from hashlib import sha256
from zoneinfo import ZoneInfo

from discoverybrief.research import exact_quote, recent_date
from discoverybrief.temporal import eligibility, parse_date, parse_instant


def parse_literal_date(value: str) -> date | None:
    """Parse only explicit, unambiguous date strings; unknown formats abstain."""
    return parse_date(value)


def approve_claim(
    candidate: dict,
    review: dict,
    sources: dict[str, dict],
    window_start: datetime,
    cutoff: datetime,
    meeting_timezone: str = "UTC",
) -> tuple[dict | None, str]:
    if review.get("candidate_id") != candidate.get("candidate_id"):
        return None, "review_id_mismatch"
    if review.get("support") != "supported" or review.get("entity_match") != "matched":
        return None, "unsupported_or_wrong_entity"
    if review.get("temporal_kind") != "recent_development" or review.get(
        "conflict_group"
    ):
        return None, "not_recent_or_conflicted"
    proposed_date = candidate.get("proposed_event_on")
    reviewed_date = review.get("event_on")
    if proposed_date and reviewed_date and proposed_date != reviewed_date:
        return None, "missing_or_conflicting_date"
    if reviewed_date and not parse_date(reviewed_date):
        return None, "invalid_date"
    proposals = candidate.get("evidence_proposals", [])
    if not proposals or len(proposals) > 2:
        return None, "invalid_evidence_count"
    records = []
    temporal_basis = "explicit_event"
    precision_limited = False
    precision = "day"
    for proposal in proposals:
        source = sources.get(proposal.get("source_id"))
        if (
            not source
            or source.get("text_origin") != "extract"
            or source.get("extraction_status") != "ok"
        ):
            return None, "source_not_extracted"
        published = source.get("published_on")
        if published:
            try:
                if (
                    date.fromisoformat(published)
                    > cutoff.astimezone(ZoneInfo(meeting_timezone)).date()
                ):
                    return None, "published_after_cutoff"
            except (TypeError, ValueError):
                return None, "invalid_publication_date"
        text = source.get("text", "")
        if sha256(text.encode("utf-8")).hexdigest() != source.get("content_sha256"):
            return None, "source_hash_mismatch"
        evidence = exact_quote(text, proposal.get("quote", ""))
        if not evidence:
            return None, "quote_not_found"
        date_quote = review.get("date_quote")
        if proposed_date and not recent_date(
            parse_date(proposed_date), window_start, cutoff, meeting_timezone
        ):
            return None, "outside_window"
        if date_quote:
            if date_quote not in text:
                return None, "date_quote_not_found"
            literal_day = parse_date(date_quote)
            if not literal_day or (
                reviewed_date and literal_day != parse_date(reviewed_date)
            ):
                return None, "date_quote_mismatch"
            date_position = text.find(date_quote)
            prefix = text[max(0, date_position - 30) : date_position]
            if re.search(
                r"\b(?:updated|last updated|diperbarui|diubah)\s*[:\-]?\s*$",
                prefix,
                re.IGNORECASE,
            ):
                return None, "update_date_not_event_date"
            value = date_quote
            if source.get("date_basis") == "publication" and date_quote == source.get(
                "date_quote"
            ):
                temporal_basis = "publication"
        else:
            if proposed_date:
                return None, "date_quote_not_found"
            if (
                source.get("date_basis") not in {"publication", "provider_estimate"}
                or not published
            ):
                return None, "date_quote_not_found"
            if reviewed_date and parse_date(reviewed_date) != parse_date(published):
                return None, "date_quote_mismatch"
            value = source.get("published_at") or published
            temporal_basis = source["date_basis"]
            if temporal_basis == "provider_estimate":
                precision_limited = True
        # An explicit old event cannot be replaced by a publication/update date.
        candidate_quote = candidate.get("event_date_quote")
        if (
            candidate_quote
            and candidate_quote in text
            and parse_date(candidate_quote)
            and parse_date(candidate_quote) != parse_date(value)
        ):
            return None, "date_quote_mismatch"
        eligible, partial = eligibility(value, window_start, cutoff, meeting_timezone)
        if not eligible:
            return None, "outside_window"
        # Publication instants after cutoff are never known, even on the same date.
        published_at = parse_instant(source.get("published_at"))
        if published_at and published_at > cutoff:
            return None, "published_after_cutoff"
        precision_limited |= partial
        precision = "instant" if parse_instant(value) else "day"
        reviewed_date = parse_date(value).isoformat()
        records.append({"source_id": proposal["source_id"], **evidence})
    return {
        "candidate_id": candidate["candidate_id"],
        "statement": candidate["statement"],
        "event_on": reviewed_date,
        "evidence": records,
        "temporal_basis": temporal_basis,
        "date_precision": precision,
        "precision_limited": precision_limited,
        "published_on": sources[proposals[0]["source_id"]].get("published_on"),
    }, "supported"


def approve_requirement(
    requirement: dict, review: dict, rfp: str
) -> tuple[dict | None, str]:
    if review.get("requirement_id") != requirement.get("requirement_id"):
        return None, "review_id_mismatch"
    if review.get("support") != "supported":
        return None, "unsupported_or_unreviewed"
    start, end = requirement.get("start"), requirement.get("end")
    if (
        not isinstance(start, int)
        or not isinstance(end, int)
        or start < 0
        or end <= start
    ):
        return None, "invalid_offsets"
    if end > len(rfp) or rfp[start:end] != requirement.get("quote"):
        return None, "quote_not_found"
    return requirement, "supported"


def align_requirement_quote(requirement: dict, rfp: str) -> dict:
    """Derive offsets from one exact occurrence; never guess an ambiguous span."""
    quote = requirement.get("quote")
    if not isinstance(quote, str) or not quote:
        return requirement
    start, end = requirement.get("start"), requirement.get("end")
    if (
        type(start) is int
        and type(end) is int
        and 0 <= start < end <= len(rfp)
        and rfp[start:end] == quote
    ):
        return requirement
    first = rfp.find(quote)
    if first < 0 or rfp.find(quote, first + 1) >= 0:
        return requirement
    return {
        **requirement,
        "start": first,
        "end": first + len(quote),
        "offset_relocated": True,
    }
