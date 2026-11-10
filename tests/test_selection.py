from discoverybrief.selection import (
    select_findings,
    select_questions,
    select_requirements,
)


def test_findings_are_ranked_deduplicated_and_bounded():
    claims = [
        {"claim_id": "c1", "rank_score": 1, "event_cluster_id": "e1"},
        {"claim_id": "c2", "rank_score": 5, "event_cluster_id": "e1"},
        *[
            {"claim_id": f"c{i}", "rank_score": i, "event_cluster_id": f"e{i}"}
            for i in range(3, 8)
        ],
    ]
    selected = select_findings(claims)
    assert len(selected) == 4
    assert len({c["event_cluster_id"] for c in selected}) == 4
    assert [c["rank_score"] for c in selected] == sorted(
        [c["rank_score"] for c in selected], reverse=True
    )


def test_requirements_follow_ranked_question_references():
    questions = [
        {"priority": "medium", "grounding": {"requirement_ids": ["r1"]}},
        {"priority": "high", "grounding": {"requirement_ids": ["r2"]}},
    ]
    selected = select_questions(questions)
    requirements = [{"requirement_id": "r1"}, {"requirement_id": "r2"}]
    assert [
        r["requirement_id"] for r in select_requirements(requirements, selected)
    ] == ["r2", "r1"]
