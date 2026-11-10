# DiscoveryBrief implementation gap analysis

Audit date: 9 November 2026, Asia/Jakarta. This describes the local snapshot at that time,
not release certification. This English translation preserves the historical findings;
see [repair status](remediation-status.md) and [progress](progress.md) for subsequent fixes.

## Conclusion

DiscoveryBrief had a working offline application foundation and an experimental live integration
path. It **did not yet meet the implementation specification**, particularly output contracts,
evidence-ledger completeness, temporal rules, result quality, independent evaluation, and
submission-package reproduction. Continuing the existing code was preferable to rebuilding.

File/test counts did not support a defensible completion percentage. No milestone had been
accepted by the progress record. M0/M4/M5 contained substantial implementation; M2/M3 still
had core gaps, while M6-M8 lacked complete acceptance evidence.

## Scope and evidence limits

- Read workspace instructions/context, the numbered specifications and examples, progress,
  spike/evaluation notes, and relevant backend, frontend, tests, runners, and result artifacts.
- Inventoried the workspace and compared the original and application-local specification
  copies: they were byte-identical during this audit. Behavioral differences came from code.
- Installed dependencies, caches, bytecode, gateway databases, and credentials were not design
  documents requiring exhaustive reading. The audit did not inspect `.env` contents or private
  gateway logs. Prior projects referenced in memory were unavailable and were not dependencies.
- Did not change application code, enable live mode, or make paid Tavily/Bifrost calls. Stored
  live/frozen-research artifacts were historical observations, not new calls or fresh web checks.
- Compared implementation with the local specification. Competition rules, deadlines, external
  pricing, and provider behavior were not revalidated or asserted current by this audit.

## Checks rerun during the audit

Working directory: the application repository root.

| Check | Actual result |
|---|---|
| `.\.venv\Scripts\python.exe -m pytest -q` | **63 passed**, one FastAPI/Starlette TestClient deprecation warning; 22.27 seconds. Available browser/PDF checks ran, with no skipped tests. |
| `npm --prefix web run build` | **Passed** TypeScript checking and Vite build. |
| `.\.venv\Scripts\ruff.exe check .` | **Passed**. |
| `.\.venv\Scripts\ruff.exe format --check .` | **Failed** one Python block in integration-specification documentation; 100 other files formatted. Housekeeping issue, not a runtime defect. |
| `npm --prefix web run test` | **Failed** because Vitest found no test files. Python browser tests still passed; this did not mean all frontend behavior was untested. |
| Fixture API with clock `2026-11-15T03:00:00Z` | **422 VALIDATION_ERROR**, meeting outside the accepted horizon. |
| Evidence route registration | `/api/runs/{run_id}/evidence` was **absent**. |
| Missing Tavily usage, model usage present | `tavily_credits_reported=null` but `usage_complete=true`; coverage only considered model usage. |
| Planner selected partnership and leadership with domain supplied | Neither query had an official-domain filter; no official-news query was added. |

Initial `uv run` was blocked by global-cache access outside the sandbox. Checks used the
existing `.venv` tools directly; this did not prove that fresh installation or ordinary-user
`uv sync` was broken. No workspace-root Git metadata was present; external public-repository
existence was not checked.

## Existing implementation worth preserving

- Pydantic input limits, aware datetimes, offset/IANA checks, Unicode/newline normalization,
  and public-context allowlisting.
- Tavily Search/Extract adapters with bounded calls/retries, URL normalization, and URL-based
  matching of extraction results.
- Gateway-only Bifrost client, structured submissions, and one schema repair; no hidden direct
  provider fallback.
- Five role contexts, literal quote/hash checks, requirement entailment through the Verifier,
  premise filtering through the Auditor, and neutral-question fallback.
- Deterministic ranking, event clustering, and bounded selection.
- FastAPI, SQLite WAL, backend idempotency, bounded queue, cancellation, and interruption
  recovery without automatic paid resume.
- Artifact manifests, path/hash checks, escaped HTML, Markdown/JSON/PDF exports, page-count
  checks, and pruning.
- Input/progress/evidence/download UI, fixture/replay paths, and a 390-pixel browser smoke.
- Ten synthetic cases, twenty stored baseline/candidate outputs, and a human-review worksheet.
- An eight-slide PPTX draft and demo script; file existence did not establish final acceptance.

## Prioritized findings

### GAP-01 - High: fixture API depended on the execution date

**Expected:** deterministic fixtures without keys; replay retains original dates. R13/G4,
TC40-TC41, M8.

**Observed:** the API injected the fixed 8 November clock only after job start, while
`RunStore.create()` still called `request.validate_horizon(now)` for fixtures. The canonical
meeting was 12 November; a simulated 15 November request failed before the workflow began.
CLI fixture, sample display, and replay were separate paths and did not necessarily fail alike.

**Impact:** offline-example execution could fail after the sample meeting horizon even though
8 November FrozenClock tests passed.

**Recommended repair:** separate live horizon validation from the repository-controlled fixture
clock, preserve original-date labels, and add a fixture API regression far beyond that date.

### GAP-02 - High: the pipeline could not produce ready quality

**Expected:** at least three eligible distinct event clusters, without material conflict or
fallback limits, can be `ready`; TC05 and E01.

**Observed:** pipeline line 494 returned `context_only` for zero clusters and otherwise always
`limited`. Comments acknowledged incomplete date/conflict/release gates. Stored E01 contained
one claim and `limited`, rather than the expected `ready` outcome.

**Impact:** both quality derivation and three-event coverage were incomplete. Merely permitting
the string `ready` would not fix recall or correctness.

**Recommended repair:** finish eligibility/uncertainty/conflict/fallback gates before deriving
quality. Test three valid events and boundary/conflict/auditor variants. Inspect the full ledger
to explain E01's missing atoms.

### GAP-03 - High: temporal policy implemented only part of the contract

**Expected:** explicit event, original publication, provider-estimated basis, instant precision,
partial boundary days, old-event/update precedence, unknown/conflict; specifications 03/04,
TC06-TC09.

**Observed:** `approve_claim()` required an exact parseable event-date quotation, and
`recent_date()` compared local dates only. Original-publication/provider-estimate paths were
missing; publication instants/precision and boundary warnings were not retained. Approved
claims were marked `explicit_event`. Conflicting claims were rejected without becoming
inspectable unknowns.

**Impact:** eligible evidence could be over-rejected and partial-day limits hidden. Date-only
logic did not prove instant filtering; conservative quality did not replace the required policy.

**Recommended repair:** typed date evidence/basis/precision, deterministic instant/day
predicates, boundary warnings, gated publication/estimate fallbacks, and durable conflict/
coverage reasons. Keep exact-quote gates intact rather than relaxing them for more findings.

### GAP-04 - High: evidence ledger and rejection explanations were incomplete

**Expected:** immutable sources; candidates, reviews, approvals, rejections; evidence endpoint;
excluded findings; and preservation after later-stage failure. R10, M2/M3/M4.

**Observed:** no evidence route. The pipeline returned approved claims and aggregate rejection
counts, rather than full item-level records. `publish.py` exported evidence from the bundle
already selected for one page. Sources held selected metadata/quotes; full text existed only
inside a successful local result. Analyst/provider failure lost in-memory research/evidence
without stage checkpoints.

**Impact:** users could not explain missing findings; PDF-pruned accepted material was absent
from detail exports despite overflow guidance. Paid calls could precede an incomplete failure
record.

**Recommended repair:** persist stage ledgers independently of page selection, expose evidence
and excluded findings, sanitize downloads, and retain checkpoints on failed/cancelled runs.

### GAP-05 - High: output contracts diverged from the normative specification

**Expected:** canonical records for runs, sources, claims, briefs/bundles, events, warnings,
errors, and metrics; specifications 03/07.

**Observed:** `schemas.py` mainly defined inputs; many outputs were dictionaries.
`build_bundle()` produced a flat structure, missing canonical brief/ledger separation and run,
domain, timezone, window, and claim temporal fields. Questions/hypotheses/unknowns lacked IDs.
Requirements lost category/unspecified fields. RunView, errors, warnings, and events omitted
contracted structures and metadata.

**Impact:** internal UI/API agreement did not establish specification compliance. Consumers
lost attribution, temporal, and grounding information; tests accepted the implementation shape.

**Recommended repair:** implement and validate canonical output models across API/pipeline/
exports. Any intentional simplification needs an explicit decision and synchronized contracts.
Folder-layout differences alone are not defects; missing fields/invariants are the issue.

### GAP-06 - High: the Verifier still received Analyst reasoning

**Expected:** fresh-context Verifier without Analyst reasoning; specifications 03/05, M3.

**Observed:** the pipeline passed full candidates, including `relevance_reason`. That field
was Analyst justification rather than source evidence. Message-context separation existed,
but reasoning-input separation did not.

**Impact:** possible bias and reduced independence; a boundary violation, not proof that any
specific claim was false.

**Recommended repair:** explicit Verifier input allowlist for statement/ID/evidence/necessary
date metadata, excluding reasoning or desired answers; assert this boundary in payload tests.

### GAP-07 - Medium-high: research coverage did not follow the strategy

**Expected:** official-domain query when a domain exists; supplemental queries if fewer than
three usable extracted sources remain after deduplication; URL/content deduplication before
selection. Specification 04, M2.

**Observed:** Planner could omit `official_news`; code did not add it. No supplemental pass.
Content duplicates were marked after extraction but retained in prompts. Extraction selected
the first ten URLs without an explained usable-source strategy. Early 12,000-character sources
could consume the entire 24,000-character evidence prompt after only two pages.

**Impact:** narrow coverage and wasted budget/context on duplicates or early pages. Consistent
with low-recall risk, but not proven as E01's sole cause.

**Recommended repair:** enforce official search, deduplicated extraction selection, a bounded
supplemental pass, distributed source passages, and retained selection/truncation reasons.
Respect existing hard caps.

### GAP-08 - High: quality evaluation was incomplete

**Expected:** human-supported precision, entity/time/reference validity, RFP grounding, recall,
question ratings, and baseline overhead; R14/G2/M7.

**Observed:** twenty `data/eval-v2/evaluation/` records shared one implementation fingerprint.
Ten baselines parsed; candidate status/quality matched labels in 9/10 cases. The worksheet
was blank. **9/10 was not semantic accuracy.** Neither independent judgments nor aggregate
quality comparison existed. Raw outputs were ignored local data, not a sanitized public set.

**Impact:** no evidence that the pipeline was more useful/accurate than one summarization call;
more roles could add cost/latency. Four live claims from one source were not four independent
sources or a quality validation.

**Recommended repair:** judge both systems against prepared labels, record denominators/N/A,
and calculate usefulness/recall/precision/overhead. Check temporal fairness: candidate received
an explicit historical cutoff/window, while baseline lacked an equivalent explicit clock.
Correct and version the experiment if material. Do not relabel E01 to manufacture a pass.

### GAP-09 - Medium-high: observability, usage, and failure taxonomy were incomplete

**Expected:** durable per-call usage/correlation, prompt/schema/model versions, durations,
stable errors, and unknown-coverage semantics; specifications 03/05/06/07/12.

**Observed:** mostly in-memory aggregates; no durable role request IDs, prompt hashes, resolved
models, latency, or usage. Failure results lost the ledger. `usage_complete` considered model
tokens only, so missing Tavily usage could coexist with true. Normal responses lacked duration/
fallback observations. Budget/timeouts and other exceptions became generic `PIPELINE_FAILED`.
Correlation headers and queue Retry-After were absent.

**Impact:** difficult diagnosis and operational comparisons; misleading completeness flags.
Unknown model cost being null was already correct, not a gap to fill with a guess.

**Recommended repair:** durable per-call/failure records, separate model/Tavily coverage,
measured duration, typed stable errors, and nulls for genuinely unknown values.

### GAP-10 - Medium: lifecycle/storage and deadlines did not meet the whole contract

**Observed:** WAL, foreign keys, locking, state/event transactions, cancellation, restart, and
idempotency existed. Schema versioning/newer-schema rejection, start/finish timestamps, and
ledger/checkpoint equivalents were absent. Files were manifested before a terminal transaction,
rather than published as one complete unit. The 300-second timeout covered `run_live()`, while
rendering/PDF publication happened afterwards.

**Impact:** contract-level recovery/schema compatibility and end-to-end timing were unproven.
This did not establish exposure of partial artifacts: downloads still required completion.

**Recommended repair:** schema versions, lifecycle timestamps, checkpoints/publication
semantics, and a worker deadline including rendering while preserving safe alternate exports.

### GAP-11 - Medium-high: core UX was incomplete

**Observed:** report language selection existed, but interface text and timezone were hardcoded
to Indonesian and Asia/Jakarta/+07:00. Identity ambiguity showed a generic error rather than
API candidates. Evidence lacked event/basis/entity/conflict/exclusion detail. No elapsed time.
Public demo retained a disabled creation form. Every submission generated a new UUID without
same-ID network retry. Complete state/keyboard/error-association browser evidence was missing.

**Impact:** R12/G3 incomplete; backend idempotency alone did not protect frontend retries.
Demo playback needed explicit explanation.

**Recommended repair:** static ID/EN dictionary/switch, timezone input or agreed scope,
actionable identity choices, richer evidence details, retained submission ID, and keyboard/
error-state checks.

### GAP-12 - Medium: exports/layout needed wider acceptance evidence

**Observed:** JSON/Markdown/HTML/PDF existed and three synthetic PDF tests passed. The matrix
did not cover maximum-length ID/EN text, long names/roles, no news, long URLs/titles, and
Chromium failure. Pruning could remove all claims without a retained accepted-detail ledger
(GAP-04). Window/date-precision/coverage metadata was incomplete. Browser/report renderers
differed despite shared selected bundles.

**Recommended repair:** TC27-TC30 regressions, independent accepted ledgers, consistent selected
content across exports, and preserved evidence details. Safe renderers need not be replaced
merely to unify file organization.

### GAP-13 - Medium: CLI and clean setup did not match the planned deliverable

**Observed:** CLI only had offline doctor and fixture `sample()` printing, without API-shared
persisted workflow. Live run, evaluate, sanitized build-demo, and live doctor were absent.
Separate evaluation scripts did not satisfy the whole CLI contract. Compose only ran Bifrost;
app Dockerfile/service and `scripts/dev.ps1` were missing. Fresh setup was untested. Quickstart
used dev extras while Playwright/pypdf were in PDF extras, with incomplete Chromium guidance.
Npm wrapper and transport version numbers differed legitimately and needed explanation.

**Recommended repair:** shared API/CLI workflow, documented equivalent commands/deviations,
no-key fixture setup with complete optional PDF installation, app+Bifrost packaging, and fresh
setup smoke. Public deployment is not a substitute for reproducible local behavior.

### GAP-14 - Medium: 63 tests did not establish acceptance traceability

**Observed:** no executed TC01-TC54 mapping. Several helpers/happy paths were well tested, but
ready quality, instant boundaries, wrong entity/domain, Auditor omissions, outage paths, maximum
input, cross-boundary queue, keyboard/i18n, and offline socket enforcement lacked full evidence.
Vitest had no tests; one code-block format check failed. Intercepted browser HTTP was not a
real live API-to-browser acceptance run.

**Recommended repair:** actual pass/partial/missing matrix and meaningful behavior/boundary
regressions, followed by core release checks. Do not equate 63 cases with 54 accepted scenarios
or write tests that merely preserve hardcoded limited quality.

### GAP-15 - High for submission: final package was not ready for release review

**Observed:** readable eight-slide draft, without final/native visual review. One saved sample
rather than ready/context-only/failure examples. Missing final license/attribution. README lacked
complete architecture/setup/mode/retention/removal/limits. Root index still said no application
existed; historical specification/progress snapshots were easy to misread. No workspace evidence
of Git metadata, verified public repo, clean checkout, final deck/screenshots, or submission receipt.

**Recommended repair:** complete correctness/evaluation first; curate sanitized samples/results,
license/README/final deck and fresh setup evidence. Publication/submission requires applicable
authorization. Deployment/video were optional in the local plan; absence alone did not invalidate
an otherwise functioning MVP.

## Milestone assessment at the audit date

| Milestone | Evidence-based assessment |
|---|---|
| M0 Bootstrap/contracts | Scaffold/input existed; canonical output contracts incomplete. |
| M1 Spikes | Limited live checks stored; fallback honestly disabled; logging/usage/environment limits remained. |
| M2 Research/evidence | Partial official/supplemental/temporal/full-ledger behavior. |
| M3 Role pipeline | Five roles connected; Verifier boundary, schemas, quality/coverage incomplete. |
| M4 API/storage/CLI | Many basic paths passed; evidence/checkpoints/schema/CLI gaps remained. |
| M5 UI/exports | Form/brief/download/PDF worked; language/identity/evidence/layout acceptance incomplete. |
| M6 Live/freeze | Stored live completed/limited result; semantic inspection/release evidence incomplete. |
| M7 Evaluation/presentation | Twenty outputs and draft deck; human judging/comparison/final presentation pending. |
| M8 Reproduction/submission | Not accepted; fixture-date regression blocked real reproduction. |

## Recommended completion order

1. **Offline reproduction/contracts:** fixture clock, canonical models/invariants, actual-evidence
   acceptance traceability.
2. **Evidence/correctness:** durable detail ledgers, temporal policy, Verifier allowlist, identity/
   failure paths; finish uncertainty/conflict behavior before allowing ready.
3. **Coverage/quality:** official/supplemental queries, deduplication/passage allocation, E01 recall
   analysis, and quality derivation with regressions.
4. **Product workflow:** language/timezone/identity/evidence UX, usage/errors, whole-run deadline,
   export consistency, and full layout matrix.
5. **Evaluation:** review existing outputs; after material behavior changes use separately versioned
   datasets/fingerprints/runs, preserve previous artifacts, and disclose failures/denominators.
6. **Release package:** clean setup, sanitized samples/results, license/README, final presentation,
   and authorized publication/submission.

Unverified fallback could remain disabled with an explicit limitation. CRM, calendar, PDF upload
parsing, another benchmark platform, and public live hosting were not needed to close MVP gaps.
