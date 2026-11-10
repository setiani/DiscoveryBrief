"""Stable event grouping and transparent deterministic ranking."""

import re
from datetime import date, timedelta

STOPWORDS = {
    "a",
    "an",
    "and",
    "at",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "dan",
    "di",
    "dengan",
    "ke",
    "pada",
    "untuk",
    "yang",
}
TOPICS = {
    "portal": ("portal",),
    "integration": ("integration", "integrasi"),
    "identity": ("identity", "identitas", "sso"),
    "search": ("search", "pencarian"),
    "devops": ("devops", "ci/cd"),
}


def derive_relevance(
    statement: str,
    selected_topics: list[str],
    meeting_type: str,
    category: str,
    requirements: list[dict],
) -> dict:
    def present(text: str) -> set[str]:
        lower = text.casefold()
        return {
            topic
            for topic, words in TOPICS.items()
            if any(
                re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", lower)
                for word in words
            )
        }

    claim_topics = present(statement)
    requirements_topics = (
        set().union(*(present(req.get("summary", "")) for req in requirements))
        if requirements
        else set()
    )
    types = {
        "rfp_clarification": {"launch", "operations"},
        "partnership": {"partnership"},
        "discovery": {"launch", "partnership", "leadership", "operations", "other"},
    }
    return {
        "topic_match": bool(claim_topics.intersection(selected_topics)),
        "meeting_type_match": category in types.get(meeting_type, set()),
        "rfp_link": bool(claim_topics.intersection(requirements_topics)),
    }


def tokens(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[^\W_]+", text.casefold())
        if word not in STOPWORDS
    }


def same_event(first: dict, second: dict) -> bool:
    if first.get("category") != second.get("category"):
        return False
    a_date, b_date = first.get("event_on"), second.get("event_on")
    if a_date and b_date and a_date == b_date:
        a, b = tokens(first.get("statement", "")), tokens(second.get("statement", ""))
        return bool(a or b) and len(a & b) / len(a | b) >= 0.8
    if not a_date or not b_date:
        return bool(tokens(first.get("statement", ""))) and tokens(
            first.get("statement", "")
        ) == tokens(second.get("statement", ""))
    return False


def cluster_events(claims: list[dict]) -> list[dict]:
    representatives = []
    result = []
    for claim in sorted(claims, key=lambda c: c["claim_id"]):
        group = next(
            (
                item["event_cluster_id"]
                for item in representatives
                if same_event(claim, item)
            ),
            None,
        )
        if group is None:
            group = f"event{len(representatives) + 1:04d}"
            representatives.append({**claim, "event_cluster_id": group})
        result.append({**claim, "event_cluster_id": group})
    return result


def score_claim(claim: dict, cutoff: date) -> int:
    score = {"official": 3, "reputable_news": 2}.get(claim.get("source_kind"), 0)
    score += (
        2 if claim.get("temporal_basis") in ("explicit_event", "publication") else 0
    )
    relevance = claim.get("relevance", {})
    score += 2 if relevance.get("topic_match") else 0
    score += 1 if relevance.get("meeting_type_match") else 0
    score += 1 if relevance.get("rfp_link") else 0
    try:
        event = date.fromisoformat(claim.get("event_on") or "")
        score += 1 if cutoff - timedelta(days=7) <= event <= cutoff else 0
    except ValueError:
        pass
    return score
