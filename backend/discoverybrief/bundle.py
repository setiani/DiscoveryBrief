"""Resolve selected report references into a safe, minimal output bundle."""

from datetime import timedelta
from hashlib import sha256
from urllib.parse import urlsplit

from discoverybrief.contracts import BriefBundle, SourceRecord
from discoverybrief.research import normalize_url
from discoverybrief.schemas import RunRequest


def build_bundle(request: RunRequest, result: dict) -> dict:
    if result.get("status") != "completed":
        raise ValueError("run has no completed brief")
    selected = result.get("brief_selection")
    if not isinstance(selected, dict):
        raise ValueError("brief selection is missing")  # noqa: TRY004
    claims = {claim["claim_id"]: claim for claim in result.get("claims", [])}
    requirements = {
        item["requirement_id"]: item for item in result.get("requirements", [])
    }
    sources = {source["source_id"]: source for source in result.get("sources", [])}
    approved_claims, approved_requirements, approved_sources = [], [], {}
    for claim_id in selected.get("finding_ids", []):
        claim = claims.get(claim_id)
        if not claim or not claim.get("evidence"):
            raise ValueError("unresolved claim")
        safe_evidence = []
        for evidence in claim["evidence"]:
            source_id = evidence.get("source_id")
            source = sources.get(source_id)
            if (
                not source
                or source.get("extraction_status") != "ok"
                or source.get("text_origin") != "extract"
            ):
                raise ValueError("unresolved or unextracted source")
            source_text = source.get("text", "")
            if sha256(source_text.encode("utf-8")).hexdigest() != source.get(
                "content_sha256"
            ):
                raise ValueError("source hash mismatch")
            start, end = evidence.get("start"), evidence.get("end")
            if (
                not isinstance(start, int)
                or not isinstance(end, int)
                or start < 0
                or end <= start
                or end > len(source_text)
                or source_text[start:end] != evidence.get("quote")
            ):
                raise ValueError("invalid evidence span")
            if sha256(evidence["quote"].encode("utf-8")).hexdigest() != evidence.get(
                "quote_sha256"
            ):
                raise ValueError("evidence hash mismatch")
            url = normalize_url(source.get("canonical_url", ""))
            approved_sources[source_id] = {
                "source_id": source_id,
                "url": url,
                "title": source.get("title", ""),
                "retrieved_at": source.get("retrieved_at"),
                "published_on": source.get("published_on"),
            }
            safe_evidence.append(
                {
                    key: evidence[key]
                    for key in ("evidence_id", "source_id", "quote", "start", "end")
                }
            )
        approved_claims.append(
            {
                "claim_id": claim_id,
                "statement": claim["statement"],
                "evidence": safe_evidence,
            }
        )
    for requirement_id in selected.get("requirement_ids", []):
        item = requirements.get(requirement_id)
        if not item or request.rfp_text[item["start"] : item["end"]] != item["quote"]:
            raise ValueError("invalid requirement reference")
        approved_requirements.append(
            {
                key: item[key]
                for key in ("requirement_id", "summary", "quote", "start", "end")
            }
        )
    context = []
    if request.meeting_goal:
        context.append(
            {
                "field": "meeting_goal",
                "text": request.meeting_goal,
                "provenance": "user_provided",
            }
        )
    for participant in request.participants:
        if len(context) == 3:
            break
        text = participant.name + (f" — {participant.role}" if participant.role else "")
        context.append(
            {"field": "participant", "text": text, "provenance": "user_provided"}
        )
    return {
        "schema_version": "1.0",
        "company_name": request.company_name,
        "meeting_at": request.meeting_at.isoformat(),
        "language": request.language,
        "research_mode": result["research_mode"],
        "quality": result["quality"],
        "knowledge_cutoff": result["knowledge_cutoff"],
        "window_start": result.get(
            "window_start", (request.meeting_at - timedelta(days=30)).isoformat()
        ),
        "window_end": result["knowledge_cutoff"],
        "meeting_timezone": request.meeting_timezone,
        "coverage_notes": coverage_notes(request, result),
        "overflow_note": result.get("overflow_note"),
        "context_summary": context,
        "claims": approved_claims,
        "requirements": approved_requirements,
        "questions": selected.get("questions", []),
        "hypotheses": selected.get("hypotheses", []),
        "unknowns": selected.get("unknowns", []),
        "sources": list(approved_sources.values()),
        "warnings": result.get("warnings", []),
        "metrics": result.get("metrics", {}),
        "original_research_mode": result.get("original_research_mode"),
        "original_metrics": result.get("original_metrics"),
        "synthetic": bool(
            result.get("synthetic", result.get("research_mode") == "fixture")
        ),
    }


def canonical_bundle(request: RunRequest, result: dict, run_id: str) -> dict:
    """Canonical API/export envelope, retaining approved items beyond page selection."""
    selected = build_bundle(request, result)
    full_selection = {
        **result["brief_selection"],
        "finding_ids": [c["claim_id"] for c in result.get("claims", [])],
        "requirement_ids": [
            r["requirement_id"] for r in result.get("requirements", [])
        ],
    }
    # Validate hashes and quote spans for all approved material, including overflow items.
    build_bundle(request, {**result, "brief_selection": full_selection})
    evidence = []
    claims = []
    source_map = {s["source_id"]: s for s in result.get("sources", [])}
    for c in result.get("claims", []):
        evidence.extend(c["evidence"])
        sources = list(dict.fromkeys(e["source_id"] for e in c["evidence"]))
        claims.append(
            {
                "claim_id": c["claim_id"],
                "candidate_id": c["candidate_id"],
                "statement": c["statement"],
                "evidence_ids": [e["evidence_id"] for e in c["evidence"]],
                "source_ids": sources,
                "category": c.get("category", "other"),
                "event_on": c.get("event_on"),
                "published_on": c.get("published_on"),
                "temporal_basis": c.get("temporal_basis", "explicit_event"),
                "eligibility": c.get("eligibility", "recent"),
                "event_cluster_id": c["event_cluster_id"],
                "relevance": c.get("relevance", {}),
                "rank_score": c.get("rank_score", 0),
                "date_precision": c.get("date_precision", "day"),
            }
        )
    source_ids = list(dict.fromkeys(sid for c in claims for sid in c["source_ids"]))
    sources = []
    for sid in source_ids:
        raw = source_map[sid]
        sources.append(
            {
                k: v
                for k, v in {
                    **raw,
                    "host": urlsplit(raw["canonical_url"]).hostname or "",
                }.items()
                if k in SourceRecord.model_fields
            }
        )

    def items(kind, prefix, field):
        return [
            {**item, field: item.get(field, f"{prefix}{i:04d}")}
            for i, item in enumerate(selected[kind], 1)
        ]

    cutoff = result["knowledge_cutoff"]
    brief = {
        "schema_version": "1.0",
        "run_id": run_id,
        "language": request.language,
        "company_name": request.company_name,
        "company_domain": request.company_domain,
        "meeting_at": request.meeting_at,
        "meeting_timezone": request.meeting_timezone,
        "knowledge_cutoff": cutoff,
        "window_start": result.get(
            "window_start", (request.meeting_at - timedelta(days=30)).isoformat()
        ),
        "window_end": cutoff,
        "quality": result["quality"],
        "research_mode": result["research_mode"],
        "finding_ids": result["brief_selection"]["finding_ids"],
        "requirement_ids": result["brief_selection"]["requirement_ids"],
        "questions": items("questions", "q", "question_id"),
        "hypotheses": items("hypotheses", "h", "hypothesis_id"),
        "unknowns": items("unknowns", "u", "unknown_id"),
        "context_summary": selected["context_summary"],
        "coverage_notes": coverage_notes(request, result),
        "overflow_note": selected.get("overflow_note"),
        "source_ids": source_ids,
        "evidence_ids": [e["evidence_id"] for e in evidence],
    }
    warnings = [
        w
        if isinstance(w, dict)
        else {
            "code": w,
            "message": warning_message(w, request.language),
            "affected_ids": [],
        }
        for w in result.get("warnings", [])
    ]
    bundle = {
        "brief": brief,
        "claims": claims,
        "requirements": result.get("requirements", []),
        "sources": sources,
        "evidence": evidence,
        "metrics": result.get("metrics", {}),
        "warnings": warnings,
        "synthetic": selected["synthetic"],
        "original_research_mode": selected.get("original_research_mode"),
        "original_metrics": selected.get("original_metrics"),
    }
    return BriefBundle.model_validate(bundle).model_dump(mode="json")


def coverage_notes(request, result):
    notes = []
    english = request.language == "en"
    if request.meeting_at.isoformat() != result["knowledge_cutoff"]:
        notes.append(
            "Research covers only information available up to the knowledge cutoff."
            if english
            else "Riset hanya mencakup informasi yang tersedia hingga batas pengetahuan."
        )
    if not result.get("claims"):
        notes.append(
            "No recent developments could be verified from the available evidence."
            if english
            else "Belum ditemukan perkembangan terbaru yang dapat diverifikasi dari bukti tersedia."
        )
    if result.get("quality") != "ready":
        notes.append(
            "Coverage is limited; inspect the evidence before using this brief."
            if english
            else "Cakupan terbatas; periksa bukti sebelum menggunakan brief."
        )
    return notes[:3]


def warning_message(code, language):
    messages = {
        "date_precision_limit": (
            "Bukti tanggal memiliki keterbatasan presisi.",
            "Date evidence has limited precision.",
        ),
        "estimated_date_basis": (
            "Tanggal merupakan estimasi penyedia.",
            "The date is estimated by the provider.",
        ),
        "unresolved_conflict": (
            "Informasi sumber bertentangan dan belum terselesaikan.",
            "Source information conflicts and remains unresolved.",
        ),
        "EXPORT_FAILED": (
            "PDF tidak tersedia; gunakan HTML atau Markdown.",
            "PDF is unavailable; use HTML or Markdown.",
        ),
        "verification_unavailable": (
            "Verifikasi tidak tersedia; klaim publik dan ringkasan kebutuhan ditahan.",
            "Verification is unavailable; public claims and requirement summaries are withheld.",
        ),
    }
    return messages.get(
        code,
        (
            "Sebagian proses atau cakupan memiliki keterbatasan.",
            "Part of the workflow or coverage has limitations.",
        ),
    )[language == "en"]
