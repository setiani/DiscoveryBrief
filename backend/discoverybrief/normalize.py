"""Normalize Tavily responses without treating search snippets as extracted evidence."""

import hashlib
import re
import unicodedata
from datetime import date
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit

from discoverybrief.research import normalize_url
from discoverybrief.temporal import parse_instant, publication_metadata


def clean_text(value: str, limit: int = 12000) -> tuple[str, bool]:
    text = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    text = "".join(c for c in text if unicodedata.category(c) != "Cf")
    return text[:limit], len(text) > limit


def normalize_sources(
    search_results: list[dict], extraction: dict, retrieved_at: str
) -> list[dict]:
    success = {}
    failure = {}
    for item in extraction.get("results", []):
        try:
            success[normalize_url(item.get("url", ""))] = item
        except ValueError:
            continue
    for item in extraction.get("failed_results", []):
        try:
            failure[normalize_url(item.get("url", ""))] = item
        except ValueError:
            continue
    seen_urls, seen_hashes, sources = set(), {}, []
    for item in search_results:
        try:
            url = normalize_url(item.get("url", ""))
        except ValueError:
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)
        fetched = success.get(url)
        source_text = (
            fetched.get("raw_content", "") if fetched else item.get("content", "")
        )
        if not isinstance(source_text, str):
            source_text = ""
        text, truncated = clean_text(source_text)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        source_id = f"s{len(sources) + 1:04d}"
        raw_date = item.get("published_date")
        if not isinstance(raw_date, str):
            raw_date = None
        published_on = None
        published_at = parse_instant(raw_date)
        if isinstance(raw_date, str):
            try:
                published_on = date.fromisoformat(raw_date[:10]).isoformat()
            except ValueError:
                try:
                    parsed = parsedate_to_datetime(raw_date)
                    if parsed.utcoffset() is not None:
                        published_at = parsed
                        published_on = parsed.date().isoformat()
                except (TypeError, ValueError):
                    pass
        sources.append(
            {
                "source_id": source_id,
                "original_url": item["url"],
                "canonical_url": url,
                "title": str(item.get("title", ""))[:300],
                "host": urlsplit(url).hostname or "",
                "text": text,
                "text_origin": "extract" if fetched else "search_snippet",
                "extraction_status": "ok"
                if fetched and text
                else ("failed" if url in failure else "snippet_only"),
                "retrieved_at": retrieved_at,
                "published_on": published_on,
                "event_on": None,
                "date_basis": "provider_estimate" if published_on else "unknown",
                "raw_provider_date": raw_date,
                "date_precision": "instant"
                if published_at
                else ("day" if published_on else "unknown"),
                "published_at": published_at.isoformat() if published_at else None,
                "date_quote": None,
                "source_kind": "other",
                "entity_match": "unreviewed",
                "extraction_error": "extract_failed" if url in failure else None,
                "content_sha256": digest,
                "truncated": truncated,
                "duplicate_of_source_id": seen_hashes.get(digest) if text else None,
                "suspected_instructions": bool(
                    re.search(
                        r"ignore (?:all |previous )?instructions|reveal.{0,30}(?:key|secret)|system prompt",
                        text,
                        re.IGNORECASE,
                    )
                ),
            }
        )
        sources[-1].update(publication_metadata(text) if fetched else {})
        if text:
            seen_hashes.setdefault(digest, source_id)
        if len(sources) >= 10:
            break
    return sources
