# Acceptance traceability — repair session

The commands are `python -m pytest -q`, `npm --prefix web run test`, `npm --prefix web run build`,
`ruff check .`, and `ruff format --check .` in the application directory. Python tests are
offline by default: HTTP network transports are blocked; Windows asyncio loopback self-pipes
are allowed. Browser subprocesses use intercepted requests or blocked remote report loads.

“Offline” below means deterministic assertions exist, not that a real model always makes the
correct semantic decision. “Review” means human/live acceptance remains separate. The detailed
test names and fixtures can be found in the named test files. No claim of 54 independently
passed live/semantic scenarios is made.

| Scenario | Executable evidence | Scope / remaining acceptance |
|---|---|---|
| TC01 | test_api.py, test_gap_regressions.py | Offline real API/SQLite/export |
| TC02 | test_contracts.py | Offline timezone/offset rejection |
| TC03 | test_release_boundaries.py, test_contracts.py | Offline body/field caps; no queued job |
| TC04 | test_contracts.py | Offline horizon rejection; fixture intentionally uses fixed clock |
| TC05 | test_gap_regressions.py | Three distinct events → ready; E01 live-model outcome also observed |
| TC06 | test_gap_regressions.py | Exact instant ±1 second and partial-day flag |
| TC07 | test_evidence.py, test_pipeline.py | Future-date exclusion; semantic review separate |
| TC08 | test_evidence.py, test_evaluation.py | Old/update conflict and literal date parsing |
| TC09 | test_evidence.py, test_pipeline.py | Missing date cannot create recent claim; semantic abstention review separate |
| TC10 | test_research.py, test_evidence.py | Exact Unicode spans/hashes |
| TC11 | test_evidence.py, test_pipeline.py | Missing source/quote rejected |
| TC12 | test_evidence.py | Supplied unsupported review blocks promotion; actual entailment needs human evaluation |
| TC13 | eval/fixtures and new 20 outputs | Human whole-statement support review pending |
| TC14 | test_ranking.py, test_pipeline.py | Clustering/dedup; lexical similarity remains approximate |
| TC15 | test_normalize.py, test_clients.py | Snippet-only/failed extract cannot masquerade as extracted evidence |
| TC16 | test_identity.py, E02 | Source-backed ambiguity and needs_input; UI candidates implemented |
| TC17 | test_identity.py | Mismatched/uncertain verifier identity withheld; model identity recall review pending |
| TC18 | test_pipeline.py, test_api.py | User-role provenance retained, not public verification |
| TC19 | E07 and conflict code path | Context-only observed; semantic conflict/unknown review pending |
| TC20 | E03 | Context-only with RFP observed; replay/export regression |
| TC21 | neutral fallback and evidence gates | Empty-evidence product behavior implemented; broader human usability review pending |
| TC22 | test_evidence.py, test_pipeline.py | Independent support + literal RFP slice |
| TC23 | test_evidence.py and evaluation labels | Supported summary gate; semantic overstatement review pending |
| TC24 | test_contracts.py, test_research.py | NFC/newlines/Unicode offsets; browser displays text |
| TC25 | test_pipeline.py, fixture auditor | Rejected unsupported premise withheld; human usefulness review pending |
| TC26 | test_structured.py, E08 | Only submit_payload accepted, untrusted text rendered as data; no universal injection immunity claim |
| TC27 | test_pdf.py | Maximum lengths, both languages, zero news, long names/URLs, one page |
| TC28 | test_browser.py, test_pdf.py | ID/EN labels and input preservation; interface toggle makes no inference call |
| TC29 | test_pdf.py | Deterministic pruning; minimum font retained |
| TC30 | test_release_boundaries.py | Controlled PDF failure preserves HTML/MD/JSON |
| TC31 | test_gap_regressions.py, test_artifacts.py | Unresolved IDs/hashes rejected; manifest path bounded |
| TC32 | test_research.py, test_pipeline.py | Private fields excluded from queries; HTTP payload contracts |
| TC33 | test_artifacts.py, test_fixture.py, test_exports.py | Traversal, URL policy, HTML/Markdown escaping |
| TC34 | test_structured.py, test_research.py | Enum query plans and exact tool/schema boundaries |
| TC35 | test_clients.py, test_structured.py | Global caps and repair bounds; worker deadline implemented |
| TC36 | recorded provider spike | Fallback unavailable and disabled; direct bypass absent; success not claimed |
| TC37 | test_structured.py, test_pipeline.py | One repair and documented role fallback |
| TC38 | test_metrics.py, test_gap_regressions.py | Missing null, genuine zero, separate Tavily/model coverage |
| TC39 | test_runner.py, CallBudget lock | Cancellation/state and reservation boundaries; research is currently serialized |
| TC40 | test_api.py, test_gap_regressions.py, conftest.py | Fixture never calls paid transports even with keys configured; future clock passes |
| TC41 | test_api.py, test_demo_replays.py | Fresh replay run; zero new calls; original metrics retained |
| TC42 | test_api.py | Public demo creation/listing/cancel boundaries; separate data directory |
| TC43 | test_api.py, test_store.py, web/src/api.test.ts | Backend dedup and frontend retry ID reuse |
| TC44 | test_api.py, test_store.py | Changed input + same ID rejected |
| TC45 | test_store.py | Unfinished jobs interrupted without paid auto-resume |
| TC46 | test_store.py, test_runner.py | Cancellation cannot overwrite terminal result |
| TC47 | test_clients.py | 401 not retried; bounded 429/503 handling |
| TC48 | test_clients.py, test_normalize.py | Mixed/unordered Extract matched by URL; failed-URL retries only |
| TC49 | test_release_boundaries.py, test_store.py | One active + three queued; additional job rejected |
| TC50 | test_release_boundaries.py | Acceptance timestamp retained across midnight |
| TC51 | test_pipeline.py | Verifier failure withholds claims and unchecked requirement summaries |
| TC52 | test_gap_regressions.py, fixture auditor | Audit failure caps quality and uses neutral questions; omitted items default reject |
| TC53 | review_index and structured parser | Duplicate/unknown IDs fail closed; missing reviews withheld |
| TC54 | evaluation records, replay metadata | Frozen research explicitly separate from live Tavily; zero Tavily calls recorded |

Release limitations still requiring external evidence: independent human support/recall/question
judgments, native presentation review, and authorized public repository/submission verification.
Container build/runtime and configured model fallback passed on 10 November via Podman;
see [scope and evidence](container-fallback-verification-2026-11-10.md). No provider-outage
failover or fallback semantic-quality claim.
