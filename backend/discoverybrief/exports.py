"""Deterministic Markdown export of approved, selected items with resolved sources."""

from discoverybrief.research import normalize_url


def markdown_report(
    company_name: str,
    selected: dict,
    claims: list[dict],
    requirements: list[dict],
    sources: list[dict],
    *,
    mode: str,
    quality: str,
    cutoff: str,
    language: str = "en",
    meeting_at: str = "",
    context_summary: list[dict] | None = None,
    overflow_note: str | None = None,
) -> str:
    by_claim = {c["claim_id"]: c for c in claims}
    by_requirement = {r["requirement_id"]: r for r in requirements}
    by_source = {s["source_id"]: s for s in sources}
    refs, findings = {}, []
    for claim_id in selected.get("finding_ids", []):
        claim = by_claim.get(claim_id)
        if not claim or not claim.get("evidence"):
            raise ValueError("unresolved claim or evidence")
        numbers = []
        for evidence in claim["evidence"]:
            sid = evidence.get("source_id")
            if sid not in by_source:
                raise ValueError("unresolved source")
            if sid not in refs:
                refs[sid] = len(refs) + 1
            numbers.append(refs[sid])
        findings.append((claim["statement"], numbers))

    def plain(text):
        # Avoid generating active Markdown links/images from untrusted prose.
        return (
            str(text)
            .replace("\\", "\\\\")
            .replace("[", "\\[")
            .replace("]", "\\]")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", " ")
        )

    labels = {
        "en": {
            "quality": "Quality",
            "cutoff": "Knowledge cutoff",
            "meeting": "Meeting",
            "context": "User-provided context",
            "findings": "Recent developments",
            "requirements": "Explicit requirements",
            "questions": "Priority questions",
            "hypotheses": "Hypotheses to confirm",
            "unknowns": "Unknowns",
            "sources": "Sources",
            "user": "user-provided",
            "synthetic": "SYNTHETIC EXAMPLE",
        },
        "id": {
            "quality": "Kualitas",
            "cutoff": "Batas pengetahuan",
            "meeting": "Meeting",
            "context": "Konteks dari pengguna",
            "findings": "Perkembangan terbaru",
            "requirements": "Kebutuhan eksplisit",
            "questions": "Pertanyaan prioritas",
            "hypotheses": "Hipotesis untuk dikonfirmasi",
            "unknowns": "Hal yang belum diketahui",
            "sources": "Sumber",
            "user": "dari pengguna",
            "synthetic": "CONTOH SINTETIS",
        },
    }[language]
    lines = [
        f"# {plain(company_name)} — DiscoveryBrief",
        "",
        f"Mode: {plain(mode)} · {labels['quality']}: {plain(quality)} · {labels['cutoff']}: {plain(cutoff)}",
    ]
    if meeting_at:
        lines.append(f"{labels['meeting']}: {plain(meeting_at)}")
    if mode in ("fixture", "replay"):
        lines.append("**" + labels["synthetic"] + "**")
    if context_summary:
        lines.extend(["", "## " + labels["context"]])
        lines.extend("- " + plain(item["text"]) for item in context_summary)
    lines.extend(["", "## " + labels["findings"]])
    lines.extend(
        f"- {plain(text)} " + " ".join(f"[{n}]" for n in nums)
        for text, nums in findings
    )
    lines.extend(["", "## " + labels["requirements"]])
    for rid in selected.get("requirement_ids", []):
        req = by_requirement.get(rid)
        if not req:
            raise ValueError("unresolved requirement")
        lines.append("- " + plain(req["summary"]) + " (" + labels["user"] + ")")
    for heading, field in [
        (labels["questions"], "questions"),
        (labels["hypotheses"], "hypotheses"),
        (labels["unknowns"], "unknowns"),
    ]:
        lines.extend(["", "## " + heading])
        lines.extend("- " + plain(item["text"]) for item in selected.get(field, []))
    if overflow_note:
        lines.extend(["", plain(overflow_note)])
    lines.extend(["", "## " + labels["sources"]])
    for sid, number in refs.items():
        source = by_source[sid]
        url = normalize_url(
            source.get("canonical_url")
            or source.get("url")
            or source.get("original_url", "")
        )
        lines.append(f"[{number}]: {url}")
    return "\n".join(lines) + "\n"
