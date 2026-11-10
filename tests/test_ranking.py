from datetime import date

from discoverybrief.ranking import cluster_events, derive_relevance, score_claim


def test_duplicate_event_is_grouped_and_distinct_event_preserved():
    base = {
        "category": "launch",
        "event_on": "2026-11-05",
        "statement": "Sagara announced agent portal pilot",
    }
    claims = [
        {"claim_id": "c0001", **base},
        {"claim_id": "c0002", **base},
        {
            "claim_id": "c0003",
            **base,
            "statement": "Sagara announced cloud data center",
        },
    ]
    grouped = cluster_events(claims)
    assert grouped[0]["event_cluster_id"] == grouped[1]["event_cluster_id"]
    assert grouped[0]["event_cluster_id"] != grouped[2]["event_cluster_id"]


def test_ranking_is_deterministic():
    claim = {
        "source_kind": "official",
        "temporal_basis": "explicit_event",
        "event_on": "2026-11-05",
        "relevance": {
            "topic_match": True,
            "meeting_type_match": True,
            "rfp_link": False,
        },
    }
    assert score_claim(claim, date(2026, 11, 8)) == 9


def test_relevance_uses_only_literal_bilingual_topics():
    relevance = derive_relevance(
        "Peluncuran portal dengan integrasi",
        ["integration"],
        "rfp_clarification",
        "launch",
        [{"summary": "Integrasi dan SSO"}],
    )
    assert relevance == {
        "topic_match": True,
        "meeting_type_match": True,
        "rfp_link": True,
    }
    assert derive_relevance(
        "Corporate news", ["portal"], "partnership", "launch", []
    ) == {"topic_match": False, "meeting_type_match": False, "rfp_link": False}
