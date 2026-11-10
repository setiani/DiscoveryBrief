"""Conservative validation of verifier identity decisions against retrieved sources."""

from urllib.parse import urlsplit


def domain_matches(host: str, domain: str) -> bool:
    host, domain = host.lower().rstrip("."), domain.lower().rstrip(".")
    return host == domain or host.endswith("." + domain)


def resolve_identity(
    company_domain: str | None,
    decision: dict,
    sources: dict[str, dict],
    analyst_candidates: list[dict] | None = None,
) -> dict:
    """Returns needs_input if supporting hosts or verifier conclusion are inconsistent."""
    candidates = []
    for candidate in [
        *decision.get("candidate_companies", []),
        *(analyst_candidates or []),
    ]:
        host = (candidate.get("domain") or "").lower().rstrip(".")
        ids = candidate.get("source_ids", [])
        if not host or not ids:
            continue
        if any(sid not in sources for sid in ids):
            continue
        if not any(
            domain_matches(
                urlsplit(sources[sid].get("original_url", "")).hostname or "", host
            )
            for sid in ids
        ):
            continue
        if host not in {item["domain"] for item in candidates} and len(candidates) < 3:
            candidates.append(
                {"name": candidate.get("name", ""), "domain": host, "source_ids": ids}
            )
    basis = decision.get("basis_source_ids", [])
    if any(sid not in sources for sid in basis):
        return {
            "status": "needs_input",
            "candidate_companies": candidates,
            "reason": "unknown_basis",
        }
    status = decision.get("status")
    if status == "needs_input":
        return {
            "status": "needs_input",
            "candidate_companies": candidates,
            "reason": "verifier_uncertain",
        }
    if not company_domain and len({c["domain"] for c in candidates}) > 1:
        return {
            "status": "needs_input",
            "candidate_companies": candidates,
            "reason": "multiple_candidates",
        }
    domain = (decision.get("domain") or "").lower().rstrip(".")
    if company_domain:
        if domain and not (
            domain_matches(domain, company_domain)
            or domain_matches(company_domain, domain)
        ):
            return {
                "status": "needs_input",
                "candidate_companies": candidates,
                "reason": "decision_domain_conflict",
            }
        if status not in ("matched", "user_scoped"):
            return {
                "status": "needs_input",
                "candidate_companies": candidates,
                "reason": "invalid_identity_status",
            }
        return {
            "status": "user_scoped",
            "domain": company_domain,
            "candidate_companies": candidates,
        }
    if status != "matched" or not domain or not basis:
        return {
            "status": "needs_input",
            "candidate_companies": candidates,
            "reason": "missing_identity_basis",
        }
    if not any(
        domain_matches(
            urlsplit(sources[sid].get("original_url", "")).hostname or "", domain
        )
        for sid in basis
    ):
        return {
            "status": "needs_input",
            "candidate_companies": candidates,
            "reason": "unmatched_basis",
        }
    return {"status": "matched", "domain": domain, "candidate_companies": candidates}
