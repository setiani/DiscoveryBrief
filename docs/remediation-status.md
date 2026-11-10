# Repair status — 9 November 2026

Reference: [original gap analysis](gap-analysis-2026-11-09.md). This document records actual
repairs and remaining acceptance work; it does not retroactively change the original audit.

| Gap | Implemented repair | Verification / remaining limit |
|---|---|---|
| 01 Fixture date | Live-only horizon at job acceptance; fixture historical clock retained | Future-clock API regression passes; no paid calls |
| 02 Ready quality | Distinct event count plus date/conflict/composition/audit gates; layout can downgrade coverage | Three-event scripted regression and live-model E01 ready; real API ready observed |
| 03 Time policy | Aware instant/day filtering, partial-day warning, literal date support, publication/provider-estimate fallbacks, RFC timestamp preservation | Boundary ±1 second, original publication/update and estimate tests; semantic date interpretation still model-dependent |
| 04 Evidence ledger | Durable sources/candidates/reviews/rejections, local evidence endpoint, full approved/detail exports and failed-stage checkpoints | Failed Analyst retains collected evidence; overflow does not remove accepted ledger |
| 05 Output contracts | Canonical typed Brief/BriefBundle, sources/evidence, requirements, composition IDs, warnings/metrics/errors and RunView | Pydantic response and reference/hash validation; old flat API is replaced |
| 06 Verifier independence | Explicit claim-input allowlist excludes Analyst relevance reasoning | Regression inspects actual Verifier input |
| 07 Research coverage | Enforced official query, bounded supplemental kinds, duplicate exclusion from prompt passages, distributed source context | Deterministic query/passage checks; source truncation remains a disclosed approximation |
| 08 Evaluation | New fair-window 20-output run; sanitized records, overhead summary and human worksheet/form | 10/10 expected candidate outcomes; semantic quality and baseline superiority remain unjudged |
| 09 Observability | Durable per-call prompt/schema hashes, usage/latency, model/tool events, separate model/Tavily coverage and stable failures | Usage/failure regressions; resolved routing, monetary cost and hidden downstream usage remain unknown |
| 10 Lifecycle | DB schema version, timestamps, canonical event IDs/types, worker timeout including publication | Queue/cancel/restart/state tests; single worker remains intentional |
| 11 UX | ID/EN interface strings, IANA input, request-ID reuse on retry, candidates for clarification, excluded findings, elapsed time and public sample-only form | Browser serialization, mobile width, language/input preservation and keyboard smoke; no exhaustive accessibility certification |
| 12 Exports | Canonical ledger export, shared selected content and expanded max-field/ID/EN/no-news PDF matrix | Seven PDF tests; exported report artifact metrics are a pre-terminal snapshot |
| 13 CLI/setup | API-backed CLI run, doctor --live, evaluate, synthetic build-demo, dev.ps1, app Dockerfile/Compose | New-source/new-venv/npm-ci run passes without .env; Podman build/Compose/replay/PDF/restart verified 10 Nov (see container report) |
| 14 Acceptance coverage | Boundary/contract/browser/PDF regressions, offline HTTP/socket guards and scenario traceability | [Acceptance matrix](acceptance.md); count of pytest cases is not a claim that human semantic scenarios passed |
| 15 Review package | Three synthetic replay cases, real report exports/screenshots, review PPTX, MIT license, notices, architecture and corrected README | Human quality review, PowerPoint visual review, public GitHub and submission receipt remain outstanding |

## Recorded checks

- Clean-source verification: `data/reproduction-20261109T155314Z/verification.json`.
  New copied source tree, new venv, `uv sync --extra dev --extra pdf --frozen`, `npm ci`,
  build, doctor, fixture CLI, **83 passing Python tests** and **4 passing Vitest tests**.
  No `.env` or runtime data was copied. Host Chromium cache was reused.
- The original environment also passed **83 Python tests**, **four Vitest tests**, TypeScript
  build and Ruff checks after the RFC-date regression was added. One TestClient deprecation
  warning remains; it does not fail the tests.
- `npm --prefix web run build`: passed. Ruff is explicitly configured to exclude runtime
  data, reproduction directories and dependency caches.
- The first clean attempt caught a missing root import path for `scripts`; fixed with
  pytest pythonpath configuration. Other intermediate attempts caught changed event-contract
  assertions and short polling limits under concurrent browser load; these failed logs remain.
- A broad lint command briefly touched the task-created reproduction cache. That cache is
  not reused. A new pristine cache was used for the successful clean verification. All 1,327
  hashed Python source files in the original venv matched installed distribution hashes.
- [Live verification and source inspection](live-verification-2026-11-09.md) distinguish actual
  paid integration observations from synthetic/model quality evidence.

## Required external/human work

1. Complete the [independent review form](../eval/review-gapfix.html), then calculate and
   publish support/recall/grounding/question metrics with actual denominators. No human ratings
   have been fabricated and no accuracy target is claimed.
2. Review `submission/DiscoveryBrief-review.pptx` in PowerPoint or an equivalent renderer.
   Package structure and slide content are checked locally; native slide visual review remains.
3. Container build/runtime is now verified on Podman; Docker Desktop itself is not tested.
   See [10 November report](container-fallback-verification-2026-11-10.md) for scope.
4. Publish the sanitized source under the owner's applicable authorization, verify its URL,
   recheck organizer requirements, and submit. No external publication/submission was performed.

Configured beam-1.0 fallback now passes host/container structured-routing checks.
Same-provider outage resilience and semantic fallback quality remain unverified. CRM, calendar, uploaded-PDF parsing and public paid inference are outside the MVP.
