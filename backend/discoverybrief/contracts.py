"""Canonical public output contracts; rendering views are derived from this ledger."""

from datetime import date, datetime
from hashlib import sha256
from typing import Literal
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from discoverybrief.roles import Grounding
from discoverybrief.schemas import StrictModel

Mode = Literal["live", "fixture", "replay", "frozen_research"]
Quality = Literal["ready", "limited", "context_only"]


class Warning(StrictModel):
    code: str
    message: str
    affected_ids: list[str] = Field(default_factory=list)


class RunError(StrictModel):
    code: str
    message: str
    retryable: bool = False
    stage: str | None = None


class EntityResolution(StrictModel):
    status: Literal["matched", "user_scoped", "needs_input"]
    company_name: str | None = None
    domain: str | None = None
    candidate_companies: list[dict] = Field(default_factory=list, max_length=3)
    basis_source_ids: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RunEvent(StrictModel):
    seq: int = Field(ge=1)
    event_id: UUID
    run_id: UUID
    at: datetime
    type: Literal[
        "stage_started",
        "stage_completed",
        "model_call",
        "tool_call",
        "candidate_rejected",
        "warning",
        "artifact_created",
        "run_finished",
    ]
    stage: str | None = None
    summary: str = Field(max_length=300)
    metadata: dict = Field(default_factory=dict)


class RunMetrics(StrictModel):
    duration_ms: int | None = None
    search_requests: int = 0
    extract_requests: int = 0
    extract_url_attempts: int = 0
    llm_requests: int = 0
    llm_input_tokens: int | None = None
    llm_output_tokens: int | None = None
    estimated_model_cost_microusd: int | None = None
    tavily_credits_reported: float | None = None
    tavily_credits_reserved: int = 0
    usage_complete: bool = False
    model_usage_complete: bool = False
    tavily_usage_complete: bool = False
    fallbacks_observed: int | None = None


class SourceRecord(StrictModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    source_id: str
    original_url: str
    canonical_url: str
    host: str
    title: str
    text: str = ""
    text_origin: Literal["extract", "search_snippet"]
    retrieved_at: datetime
    published_on: date | None = None
    event_on: date | None = None
    date_basis: Literal[
        "publication", "last_updated", "provider_estimate", "unknown"
    ] = "unknown"
    date_precision: Literal["day", "instant", "unknown"] = "unknown"
    published_at: datetime | None = None
    date_quote: str | None = None
    raw_provider_date: str | None = None
    source_kind: Literal["official", "reputable_news", "other"] = "other"
    entity_match: Literal["matched", "ambiguous", "mismatched", "unreviewed"] = (
        "unreviewed"
    )
    extraction_status: Literal["ok", "failed", "snippet_only"]
    extraction_error: str | None = None
    truncated: bool = False
    content_sha256: str
    duplicate_of_source_id: str | None = None
    suspected_instructions: bool = False


class EvidenceRecord(StrictModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    evidence_id: str
    source_id: str
    quote: str = Field(min_length=1, max_length=600)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    quote_sha256: str


class Relevance(StrictModel):
    topic_match: bool = False
    meeting_type_match: bool = False
    rfp_link: bool = False


class ApprovedClaim(StrictModel):
    claim_id: str
    candidate_id: str
    statement: str = Field(min_length=1, max_length=180)
    evidence_ids: list[str] = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    category: Literal["launch", "partnership", "leadership", "operations", "other"]
    event_on: date | None = None
    published_on: date | None = None
    temporal_basis: Literal[
        "explicit_event", "publication", "provider_estimate", "unknown"
    ]
    eligibility: Literal["recent", "background"] = "recent"
    event_cluster_id: str
    relevance: Relevance
    rank_score: int
    date_precision: Literal["day", "instant", "unknown"] = "day"


class Requirement(StrictModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)
    requirement_id: str
    summary: str = Field(min_length=1, max_length=140)
    quote: str = Field(min_length=1, max_length=600)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    category: str
    unspecified: list[str] = Field(default_factory=list, max_length=3)
    offset_relocated: bool = False


class Question(StrictModel):
    question_id: str
    text: str = Field(min_length=1, max_length=180)
    grounding: Grounding = Field(default_factory=Grounding)
    priority: Literal["high", "medium"] = "medium"
    origin: Literal["model", "template"] = "model"

    @model_validator(mode="after")
    def grounded(self):
        if self.origin != "template" and not any(self.grounding.model_dump().values()):
            raise ValueError("model question requires grounding")
        return self


class Hypothesis(StrictModel):
    hypothesis_id: str
    text: str = Field(min_length=1, max_length=140)
    grounding: Grounding


class Unknown(StrictModel):
    unknown_id: str
    text: str = Field(min_length=1, max_length=120)
    related_claim_ids: list[str] = Field(default_factory=list)
    related_requirement_ids: list[str] = Field(default_factory=list)


class ContextItem(StrictModel):
    field: str
    text: str
    provenance: Literal["user_provided"] = "user_provided"


class Brief(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: UUID
    language: Literal["id", "en"]
    company_name: str
    company_domain: str | None
    meeting_at: datetime
    meeting_timezone: str
    knowledge_cutoff: datetime
    window_start: datetime
    window_end: datetime
    quality: Quality
    research_mode: Mode
    finding_ids: list[str] = Field(max_length=4)
    requirement_ids: list[str] = Field(max_length=4)
    questions: list[Question] = Field(max_length=4)
    hypotheses: list[Hypothesis] = Field(max_length=2)
    unknowns: list[Unknown] = Field(max_length=3)
    context_summary: list[ContextItem] = Field(max_length=3)
    coverage_notes: list[str] = Field(default_factory=list, max_length=3)
    overflow_note: str | None = None
    source_ids: list[str]
    evidence_ids: list[str]


class BriefBundle(StrictModel):
    brief: Brief
    claims: list[ApprovedClaim]
    requirements: list[Requirement]
    sources: list[SourceRecord]
    evidence: list[EvidenceRecord]
    metrics: RunMetrics
    warnings: list[Warning]
    synthetic: bool = False
    original_research_mode: Mode | None = None
    original_metrics: dict | None = None

    @model_validator(mode="after")
    def references(self):
        def index(items, key):
            indexed = {getattr(item, key): item for item in items}
            if len(indexed) != len(items):
                raise ValueError("duplicate ledger ID")
            return indexed

        claims = index(self.claims, "claim_id")
        requirements = index(self.requirements, "requirement_id")
        sources = index(self.sources, "source_id")
        evidence = index(self.evidence, "evidence_id")
        for ids, known in (
            (self.brief.finding_ids, claims),
            (self.brief.requirement_ids, requirements),
            (self.brief.source_ids, sources),
            (self.brief.evidence_ids, evidence),
        ):
            if not set(ids) <= known.keys():
                raise ValueError("unresolved brief reference")
        for claim in self.claims:
            if (
                not set(claim.evidence_ids) <= evidence.keys()
                or not set(claim.source_ids) <= sources.keys()
            ):
                raise ValueError("unresolved claim reference")
            if {evidence[e].source_id for e in claim.evidence_ids} != set(
                claim.source_ids
            ):
                raise ValueError("claim source/evidence mismatch")
        for item in self.evidence:
            if item.source_id not in sources:
                raise ValueError("unresolved evidence source")
            source = sources[item.source_id]
            if (
                source.text[item.start : item.end] != item.quote
                or sha256(item.quote.encode()).hexdigest() != item.quote_sha256
                or sha256(source.text.encode()).hexdigest() != source.content_sha256
            ):
                raise ValueError("invalid literal evidence or content hash")
        selected = [claims[c] for c in self.brief.finding_ids]
        if (
            self.brief.quality == "ready"
            and len({c.event_cluster_id for c in selected}) < 3
        ):
            raise ValueError("ready requires three distinct developments")
        if self.brief.quality == "context_only" and selected:
            raise ValueError("context_only cannot display public findings")
        for item in [*self.brief.questions, *self.brief.hypotheses]:
            if (
                not set(item.grounding.claim_ids) <= claims.keys()
                or not set(item.grounding.requirement_ids) <= requirements.keys()
            ):
                raise ValueError("unresolved grounding reference")
        return self


class RunView(StrictModel):
    schema_version: Literal["1.0"] = "1.0"
    run_id: UUID
    company_name: str
    meeting_at: datetime
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    status: Literal[
        "queued", "running", "completed", "needs_input", "failed", "cancelled"
    ]
    stage: str
    research_mode: Mode
    quality: Quality | None
    window_start: datetime
    window_end: datetime
    knowledge_cutoff: datetime
    entity: EntityResolution | None = None
    warnings: list[Warning]
    metrics: RunMetrics
    error: RunError | None
    error_code: str | None = None
    artifacts: list[str]
    brief: Brief | None = None
