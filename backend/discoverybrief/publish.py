"""Create manifest-backed report artifacts before publishing a completed run."""

import asyncio
import json
import logging
from time import monotonic

from discoverybrief.artifacts import ArtifactStore
from discoverybrief.bundle import build_bundle, canonical_bundle
from discoverybrief.exports import markdown_report
from discoverybrief.reporting import render_bundle_html
from discoverybrief.schemas import RunRequest

logger = logging.getLogger("discoverybrief.publish")


async def publish_artifacts(
    request: RunRequest, result: dict, artifacts: ArtifactStore, run_id: str
) -> None:
    if result.get("status") != "completed":
        return
    started = monotonic()
    bundle = build_bundle(request, result)
    pdf = None
    try:
        from discoverybrief.pdf import bundle_pdf

        bundle, pdf = await asyncio.to_thread(bundle_pdf, bundle)
        result["brief_selection"] = {
            "finding_ids": [claim["claim_id"] for claim in bundle["claims"]],
            "requirement_ids": [
                item["requirement_id"] for item in bundle["requirements"]
            ],
            "questions": bundle["questions"],
            "hypotheses": bundle["hypotheses"],
            "unknowns": bundle["unknowns"],
        }
        result["overflow_note"] = bundle.get("overflow_note")
        if result["quality"] == "ready" and len(bundle["claims"]) < 3:
            result["quality"] = "limited"
            result.setdefault("warnings", []).append("layout_coverage_limit")
        bundle = build_bundle(request, result)
    except Exception as exc:  # noqa: BLE001 -- PDF is optional when its platform dependency fails
        logger.warning("PDF generation unavailable: %s", type(exc).__name__)
        result.setdefault("warnings", []).append("EXPORT_FAILED")
        bundle = build_bundle(request, result)
    if pdf is not None:
        try:
            artifacts.write(run_id, "brief.pdf", pdf)
        except OSError as exc:
            logger.warning("PDF artifact unavailable: %s", type(exc).__name__)
            result.setdefault("warnings", []).append("EXPORT_FAILED")
            bundle = build_bundle(request, result)
    result.setdefault("metrics", {})["duration_ms"] = (
        result.get("metrics", {}).get("duration_ms") or 0
    ) + round((monotonic() - started) * 1000)
    bundle = build_bundle(request, result)
    selection = result["brief_selection"]
    markdown = markdown_report(
        request.company_name,
        selection,
        bundle["claims"],
        bundle["requirements"],
        bundle["sources"],
        mode=bundle["research_mode"],
        quality=bundle["quality"],
        cutoff=bundle["knowledge_cutoff"],
        language=bundle["language"],
        meeting_at=bundle["meeting_at"],
        context_summary=bundle["context_summary"],
        overflow_note=bundle.get("overflow_note"),
    )
    html = render_bundle_html(bundle)
    artifacts.write(
        run_id,
        "brief.json",
        json.dumps(
            canonical_bundle(request, result, run_id), ensure_ascii=False, indent=2
        ).encode("utf-8"),
    )
    artifacts.write(run_id, "brief.md", markdown.encode("utf-8"))
    artifacts.write(run_id, "brief.html", html.encode("utf-8"))
    evidence = {
        key: result.get(key, [])
        for key in (
            "sources",
            "candidates",
            "reviews",
            "requirement_candidates",
            "requirement_reviews",
            "claims",
            "requirements",
            "rejections",
            "composer_proposals",
            "premise_reviews",
        )
    }
    evidence["diagnostics"] = result.get("diagnostics", {})
    trace = {
        "research_mode": bundle["research_mode"],
        "original_research_mode": bundle.get("original_research_mode"),
        "original_metrics": bundle.get("original_metrics"),
        "events": artifacts.store.events(run_id),
        "metrics": bundle["metrics"],
        "calls": artifacts.store.ledger(run_id, "calls"),
        "snapshot_stage": artifacts.store.get(run_id)["stage"],
        "note": "Events are captured before terminal status is committed.",
    }
    artifacts.write(
        run_id,
        "evidence.json",
        json.dumps(evidence, ensure_ascii=False, indent=2).encode("utf-8"),
    )
    artifacts.write(
        run_id,
        "trace.json",
        json.dumps(trace, ensure_ascii=False, indent=2).encode("utf-8"),
    )
