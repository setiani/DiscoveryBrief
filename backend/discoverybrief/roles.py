"""Model role payload contracts. Code assigns identifiers after validation."""

from typing import Annotated, Literal

from pydantic import Field

from discoverybrief.schemas import StrictModel


class ResearchPlan(StrictModel):
    query_kinds: list[
        Literal[
            "official_news",
            "product_launch",
            "partnership",
            "leadership",
            "digital_platform",
            "business_updates",
        ]
    ] = Field(min_length=2, max_length=6)
    reason: str = Field(max_length=300)


class EntityCandidate(StrictModel):
    name: str = Field(max_length=160)
    domain: str
    source_ids: list[str]


class EvidenceProposal(StrictModel):
    source_id: str
    quote: str = Field(min_length=1, max_length=600)


class ClaimCandidate(StrictModel):
    statement: str = Field(min_length=1, max_length=180)
    evidence_proposals: list[EvidenceProposal] = Field(min_length=1, max_length=2)
    category: Literal["launch", "partnership", "leadership", "operations", "other"]
    proposed_event_on: str | None = None
    event_date_quote: str | None = None
    relevance_reason: str = Field(max_length=200)


class RequirementCandidate(StrictModel):
    summary: str = Field(min_length=1, max_length=140)
    quote: str = Field(min_length=1, max_length=600)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    category: Literal[
        "integration",
        "identity",
        "access",
        "workflow",
        "performance",
        "acceptance",
        "other",
    ]
    unspecified: list[Annotated[str, Field(max_length=100)]] = Field(
        default_factory=list, max_length=3
    )


class AnalystOutput(StrictModel):
    entity_candidates: list[EntityCandidate] = Field(default_factory=list, max_length=3)
    claims: list[ClaimCandidate] = Field(default_factory=list, max_length=12)
    requirements: list[RequirementCandidate] = Field(default_factory=list, max_length=8)
    warnings: list[str] = Field(default_factory=list, max_length=5)


class EntityDecision(StrictModel):
    status: Literal["matched", "user_scoped", "needs_input"]
    company_name: str | None
    domain: str | None
    candidate_companies: list[EntityCandidate] = Field(
        default_factory=list, max_length=3
    )
    basis_source_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ClaimReview(StrictModel):
    candidate_id: str
    support: Literal["supported", "unsupported", "uncertain"]
    entity_match: Literal["matched", "ambiguous", "mismatched"]
    temporal_kind: Literal["recent_development", "historical", "uncertain"]
    event_on: str | None
    date_quote: str | None
    conflict_group: str | None
    reasoning: str = Field(max_length=300)


class RequirementReview(StrictModel):
    requirement_id: str
    support: Literal["supported", "unsupported", "uncertain"]
    reason: str = Field(max_length=300)


class VerifierOutput(StrictModel):
    entity: EntityDecision
    reviews: list[ClaimReview] = Field(max_length=12)
    requirement_reviews: list[RequirementReview] = Field(max_length=8)


class Grounding(StrictModel):
    claim_ids: list[str] = Field(default_factory=list)
    requirement_ids: list[str] = Field(default_factory=list)
    context_fields: list[
        Literal["meeting_goal", "notes", "participants", "company_name", "meeting_type"]
    ] = Field(default_factory=list)


class QuestionProposal(StrictModel):
    text: str = Field(min_length=1, max_length=180)
    grounding: Grounding
    priority: Literal["high", "medium"]


class HypothesisProposal(StrictModel):
    text: str = Field(min_length=1, max_length=140)
    grounding: Grounding


class UnknownProposal(StrictModel):
    text: str = Field(min_length=1, max_length=120)
    related_claim_ids: list[str] = Field(default_factory=list)
    related_requirement_ids: list[str] = Field(default_factory=list)


class ComposerOutput(StrictModel):
    question_proposals: list[QuestionProposal] = Field(max_length=4)
    hypothesis_proposals: list[HypothesisProposal] = Field(max_length=2)
    unknown_proposals: list[UnknownProposal] = Field(max_length=3)


class AuditItem(StrictModel):
    kind: Literal["question", "hypothesis", "unknown"]
    index: int = Field(ge=0)
    decision: Literal["accept", "reject"]
    reason: str = Field(max_length=200)


class PremiseAudit(StrictModel):
    items: list[AuditItem] = Field(max_length=9)
