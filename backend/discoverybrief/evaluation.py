"""Small, explicit metric calculations over independently labeled evaluation records."""

from statistics import median


def ratio(numerator: int, denominator: int) -> float | None:
    if numerator < 0 or denominator < 0 or numerator > denominator:
        raise ValueError("invalid metric counts")
    return numerator / denominator if denominator else None


def summarize(cases: list[dict]) -> dict:
    claims = [claim for case in cases for claim in case.get("claims", [])]
    requirements = [item for case in cases for item in case.get("requirements", [])]
    questions = [question for case in cases for question in case.get("questions", [])]
    references = [ref for case in cases for ref in case.get("references", [])]
    required_atoms = [atom for case in cases for atom in case.get("required_atoms", [])]
    if any(type(item.get("human_supported")) is not bool for item in claims):
        raise ValueError(
            "all displayed claims require independent human support labels"
        )
    if any(
        type(item.get("entity_correct")) is not bool
        or type(item.get("temporal_eligible")) is not bool
        for item in claims
    ):
        raise ValueError("all displayed claims require entity and temporal labels")
    ratings = [item.get("rating") for item in questions]
    if any(type(rating) is not int or not 0 <= rating <= 4 for rating in ratings):
        raise ValueError("question rating must be an integer 0..4")
    if any(type(item.get("grounded")) is not bool for item in requirements):
        raise ValueError("each displayed requirement needs a grounding label")
    if any(type(item.get("valid")) is not bool for item in references):
        raise ValueError("each reference needs an independent validity label")
    if any(type(item.get("surfaced")) is not bool for item in required_atoms):
        raise ValueError(
            "each eligible required atom needs an independent recall label"
        )
    labeled_outcomes = [
        case["outcome_correct"] for case in cases if "outcome_correct" in case
    ]
    if labeled_outcomes and (
        len(labeled_outcomes) != len(cases)
        or any(type(value) is not bool for value in labeled_outcomes)
    ):
        raise ValueError("outcome labels must cover every case and be boolean")
    return {
        "case_count": len(cases),
        "claim_count": len(claims),
        "public_support_precision": ratio(
            sum(item["human_supported"] for item in claims), len(claims)
        ),
        "entity_correctness": ratio(
            sum(item["entity_correct"] for item in claims), len(claims)
        ),
        "temporal_eligibility": ratio(
            sum(item["temporal_eligible"] for item in claims), len(claims)
        ),
        "requirement_count": len(requirements),
        "rfp_grounding": ratio(
            sum(item["grounded"] for item in requirements), len(requirements)
        ),
        "question_count": len(questions),
        "question_usefulness_median": median(ratings) if ratings else None,
        "reference_count": len(references),
        "reference_validity": ratio(
            sum(item["valid"] for item in references), len(references)
        ),
        "required_atom_count": len(required_atoms),
        "required_fact_recall": ratio(
            sum(item["surfaced"] for item in required_atoms), len(required_atoms)
        ),
        "outcome_correctness": ratio(sum(labeled_outcomes), len(labeled_outcomes)),
    }
