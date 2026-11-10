"""Deterministic selection for a bounded one-page brief."""


def select_findings(claims: list[dict]) -> list[dict]:
    selected, seen = [], set()
    for claim in sorted(claims, key=lambda x: (-x.get("rank_score", 0), x["claim_id"])):
        group = claim["event_cluster_id"]
        if group in seen:
            continue
        selected.append(claim)
        seen.add(group)
        if len(selected) == 4:
            break
    return selected


def select_questions(questions: list[dict]) -> list[dict]:
    order = {"high": 0, "medium": 1}
    indexed = enumerate(questions)
    return [
        q
        for _, q in sorted(
            indexed, key=lambda item: (order.get(item[1].get("priority"), 2), item[0])
        )[:4]
    ]


def select_requirements(requirements: list[dict], questions: list[dict]) -> list[dict]:
    priority = {}
    for index, question in enumerate(questions):
        for requirement_id in question.get("grounding", {}).get("requirement_ids", []):
            priority.setdefault(requirement_id, index)
    return sorted(
        requirements,
        key=lambda r: (
            priority.get(r["requirement_id"], len(questions)),
            r["requirement_id"],
        ),
    )[:4]
