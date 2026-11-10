# DiscoveryBrief progress

Updated: 2026-11-10, Asia/Jakarta.

Status: core local workflow implemented and repaired. Independent human quality evaluation
and final publication/submission acceptance remain open. Container verification passed on Podman;
see the 10 November record below. Earlier entries
below preserve development history; use the latest repair record for current behavior.

## Default language - 10 November 2026

User requested English on first access. Interface and new-report selector now default to
English, HTML lang/description match, and static form labels/placeholders use English.
Indonesian remains selectable. Existing saved reports/replays retain their original language.
Four frontend tests and TypeScript/Vite build pass.

## Container and fallback verification - 10 November 2026

- Podman 6.1.4 / Docker Compose v5.7.0 built the Dockerfile and started app+Bifrost v1.5.0.
- Three HTTP replays, all six exports each, one-page PDFs, browser JavaScript, read-only
  boundary, healthcheck and persistence after restart passed.
- Fixed missing MODEL_FALLBACK forwarding in API/doctor/evaluation and Compose settings.
  Recorded resolved model metadata while preserving incomplete usage coverage.
- Unavailable-primary -> beam-1.0 structured fallback passed on host and container;
  unavailable primary alone and unavailable primary+fallback fail finitely. No cross-provider
  outage or fallback quality claim. Current `.env` was preserved.
- 85 Python regression tests passed (one upstream deprecation warning); Ruff passed.
- See [verification report](container-fallback-verification-2026-11-10.md) and
  [local Windows instructions](running-locally-windows.md) for commands and evidence.

## Latest repair record — 9 November 2026

The user authorized repairing the gap analysis and paid API verification. See
[repair status](remediation-status.md), [acceptance](acceptance.md), and
[live verification](live-verification-2026-11-09.md).

- Repaired fixture clock, canonical output envelopes, date/identity/quality gates,
  source coverage, Verifier input boundary, durable evidence/call checkpoints, API detail,
  lifecycle/versioning, CLI, report exports and frontend language/timezone/retry states.
- The successful clean-source run at `data/reproduction-20261109T155314Z/verification.json`
  used a new venv, no copied `.env`, `uv sync --frozen`, `npm ci`, build, doctor and fixture CLI;
  **83 Python tests and four Vitest tests passed**. Host Chromium cache was reused.
- Root Python/browser/PDF tests, TypeScript build and frontend unit tests were rerun; exact
  final counts are recorded in the repair status. Ruff excludes task runtime data/caches.
- A new 20-output fixed-evidence run matched **10/10 candidate outcome/quality labels**.
  Baseline used ten model calls versus 48 candidate calls; median elapsed times were 8.69 s
  and 36.91 s. Semantic support/recall/usefulness and superiority remain unmeasured. The
  [review form](../eval/review-gapfix.html) and [raw safe outputs](../eval/results/2026-11-09-gapfix/summary.json)
  contain no fabricated human ratings.
- Two real API smokes completed: first limited with two claims; later ready with four selected
  claims from four sources, two requirements and two questions. Only public/synthetic context
  was used. Separate primary-page inspection notes disclose source/date interpretation limits.
- Four synthetic samples are allowlisted, including ready/context-only/partial-source cases.
  Three dedicated replay tests verify no new model/Tavily calls and preservation of original
  fixed-evidence/model provenance. Exports and desktop/mobile screenshots are in `submission/demo/`.
- `submission/DiscoveryBrief-review.pptx` is a ten-slide review package; the previous draft is
  preserved. Native PowerPoint rendering/final human visual review remains outstanding.
- Added MIT license, dependency notices, architecture, Docker app/Compose configuration and
  PowerShell tasks. Docker daemon was unavailable; no container-run success is claimed.
- No public repository publication, deployment, organizer submission or receipt verification.
  Fallback remains disabled. Do not call the application production-ready or claim accuracy.

## Implemented and checked

- Created application directory and copied the full plan and application instructions.
- Request validation, timezone checks, public research context allowlist, basic query construction, quote/hash checks, preliminary evidence approval gates and bounded HTTP adapters.
- The frontend supports a canonical synthetic fixture and a saved sample replay; a live form is available only when explicitly enabled.
- Offline suite: 63 tests passed, including fixture API/runner, saved-sample replay, report exports, manifest access, browser coverage and preliminary evaluation checks. These include mocked HTTP and do not prove live model or full workflow correctness.
- `npm run build`: passed for frontend scaffold. After updating the test dependency, `npm install` reported zero vulnerabilities.
- `discoverybrief doctor`: runs without network calls; reports presence, not contents, of credentials.
- HTML, Markdown, JSON and optional one-page PDF exports are implemented for stored runs; synthetic PDF checks passed, while coverage across all layouts remains incomplete.
- The fixture example loaded in a 390-pixel Chromium viewport without horizontal overflow; screenshot in ignored `data/preview-mobile.png`.
- The local API accepts only the exact canonical synthetic request in fixture mode; it queues, stores, and serves a bounded brief. A separate live handler and live form are implemented behind `RESEARCH_MODE=live` plus `ENABLE_LIVE_RUNS=1`; the switch remains off in the current setup and the path is not release-verified. Public demo serves only saved synthetic replay runs from a separate data directory. Chromium tests at 390 px exercised the fixture run and a mocked live form without horizontal overflow.
- An experimental role workflow is connected to the gated API, but does not yet satisfy M2/M3. An offline scripted fixture exercises its basic path. Identity/temporal/quality rules, failure behavior and full end-to-end coverage still need work. It deliberately cannot claim `ready`.

## Integration and known blockers

- One explicitly enabled Tavily Search live smoke returned HTTP success and 5 results. Extract returned one success and one failure in the same response; usage metadata was present. This does not validate the full research workflow.
- Official Bifrost launcher started transport v1.5.0 on localhost using a Bynara custom-provider configuration. Docker CLI exists but its daemon was not running.
- Initial model test mistakenly used the Bynara URL as the gateway and returned 401; corrected the local `BIFROST_BASE_URL` to point at Bifrost. Next attempt reached Bifrost but returned 404; changed provider base path. After increasing timeout, primary `step-5-preview` returned HTTP 200 with zero choices and no usage, both with and without tool request. This is invalid model output, not a passing inference. `laguna-s-2.1` returned HTTP 400 for both tested requests. No automatic fallback was tested.
- The user requested a switch from Bynara to a configurable OpenAI-compatible provider. `.env` is configured for `MODEL_PROVIDER_BASE_URL=https://api.tokenrouter.com/v1`, primary `deepseek/deepseek-v4.1-flash-1017`, and fallback `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`; the user confirmed entering the provider key. The previous Bynara settings remain locally for reference. No credentials are recorded here.
- The Bifrost startup script generates a custom-provider configuration from `.env`; `custom/` is added to gateway model names. With the configured TokenRouter key, one basic call returned a response and one tool call returned a nonempty submission, both with usage fields. A synthetic schema smoke validated Planner, Analyst and Verifier; Composer and Auditor initially hit HTTP 429, then each passed on a later individual retry. This validates payload shape only, not semantic correctness or full pipeline behavior.
- `scripts/spike_live_pipeline.py`, 9 Nov, public OpenAI target plus synthetic RFP: 5 Search, 2 Extract and 6 Bifrost requests attempted. The experimental run completed `context_only` because semantic verification was unavailable; zero public claims and zero requirement summaries were approved. This is an integration/failure observation, not a passing release run. The run used private-safe public/synthetic input and did not record detailed cost.
- Fixed-evidence/live-model experiments produced `context_only` or `needs_input`; a later run identified invalid verifier schema (`model_type@entity`), and another hit HTTP 429. Repair diagnostics and verifier instructions were tightened. A configurable `MODEL_MIN_INTERVAL_SECONDS=15` now spaces model requests within a client; it is a mitigation and has not yet been validated in a full run.
- A subsequent fixed-evidence/live-model run returned `limited` with one source-backed finding and one RFP requirement; the auditor returned invalid JSON and neutral template questions were used. This is a single synthetic development run, not an accuracy evaluation. Another API live run failed at analysis; Bifrost's corresponding logs showed HTTP 503. Live creation remains switched off by default.
- Fixture runs now produce manifest-backed JSON, Markdown, HTML, PDF when available, plus evidence/trace snapshots. Dense synthetic PDF output passed a one-page check without reducing the minimum font size; coverage of all required layouts is still incomplete.
- Replay now loads a previously saved synthetic fixture result from `demo_runs/sagara.json`; it does not execute fixture model/research clients or call the network. Original fixture metrics are retained separately from replay metrics. Public demo exposes only replay records from its separate data directory.
- A controlled fallback spike using a deliberately invalid primary returned HTTP 503; no fallback success or route was observed, so fallback remains disabled. HTTP 429 was also observed; no assumption is made about future availability or cost.
- Bifrost `/api/config` reports `disable_content_logging=true` and `allow_per_request_content_storage_override=false`. Actual log storage and any downstream provider retention have not been audited. Use only public/synthetic context for live tests.
- End-to-end live inference, fallback, complete usage accounting, general PDF behavior and content logging remain unverified. Fixture tests do not count as these results.
- Ten synthetic fixed-evidence evaluation case specifications and preliminary labels were prepared before model outputs. `scripts/evaluate_frozen.py` is an initial opt-in Bifrost-only baseline/candidate runner; its output needs human review. One E01 baseline attempt failed HTTP 503 while the gateway was still configured for the prior provider, so that attempt is invalid for quality evaluation. No valid comparison or quality metrics have been produced; labels/runner still require review against all evaluation criteria.
- On 9 Nov, the current local `.env` was found to have been changed to the OpenAI-compatible `https://api.kryptonlab.id/v1`, primary `gpt-6-luna`, fallback `beam-1.0`. The old running Bifrost instance still pointed at TokenRouter; it was restarted without altering `.env`, and `/api/providers` confirmed the custom provider URL now points to KryptonLab. A single basic primary-model call returned nonempty content; five separate synthetic schema calls validated the Planner, Analyst, Verifier, Composer and Auditor payload shapes. These checks do not verify fallback or the complete workflow.
- A subsequent public OpenAI/synthetic RFP API run through Tavily and the current gateway reached `completed` and returned a brief, but only `context_only`, with zero approved claims and requirements and two neutral questions. It used 6 searches, 2 extract requests and 5 model requests; the ledger reported 13 Tavily credits and token usage. This proves a bounded integration path, not useful evidence quality or release readiness. A later code change supplies the full RFP to the verifier and deterministically aligns unique exact requirement quotes; that change requires its own live check.
- After that RFP change, a fixed-synthetic-evidence/live-model run produced `context_only` with two approved requirements and no claims. One candidate was rejected because its date quote did not parse to the reviewed date, and another was marked historical. The gate was subsequently extended to recognize additional unambiguous English date formats and the verifier prompt clarified; whether that addresses this specific rejection has not been established.
- A further fixed-synthetic-evidence/live-model run after the date/prompt changes returned `limited` with one approved claim and two approved requirements, using five Bifrost calls and no Tavily calls. Model outputs vary; this single development observation does not isolate the effect of the change and is not the labeled baseline comparison.
- A subsequent public OpenAI/synthetic RFP API run after these changes completed with quality `limited`, four claims with evidence references, two requirements and two questions; all displayed claims pointed to one source. The run used six searches, two extracts and five model requests; the ledger reported 14 Tavily credits, 17,065 input tokens and 2,136 output tokens. The sanitized bundle is `data/spikes/live-brief.json`. The preceding context-only bundle was preserved at `data/spikes/live-brief-before-grounding-fix.json`. Neither run is an independent semantic accuracy or cost evaluation; model pricing is unknown.
- `submission/DiscoveryBrief-draft.pptx` is an eight-slide draft generated with system Python and `python-pptx` 1.0.2 via `python scripts/build_deck.py`; the file opens as a PowerPoint package and contains text on all slides. Its evaluation slide includes the mechanical result and pending human review. This optional presentation dependency is not part of the application lockfile. Visual rendering and final review remain required, including an update after human judging.
- Preliminary fixed-evidence runs E01–E04 and the E05 baseline were collected, then stopped after discovering mismatched baseline/candidate display limits. Those outputs remain in `data/eval-krypton/evaluation/` but are not a fair quality comparison. E01 candidate was `limited` against target `ready`; E02 completed against expected `needs_input`. The baseline prompt was corrected to four items per category for a fresh run; independent review and aggregate evaluation remain pending. See `eval/results.md`.
- The Analyst's proposed entity candidates are now passed to the Verifier and considered in the source-backed ambiguity check. Offline tests cover a verifier that omits an alternative previously found by the Analyst. A single E02 fixed-evidence/live-model retest then returned `needs_input` as expected; broader behavior and false-positive rate are unverified.
- A corrected fixed-evidence run generated 20 output records across the ten cases with one model and implementation fingerprint. Ten baseline outputs parsed; 9/10 candidate status/quality pairs matched their predeclared cases (E01 remained `limited` against `ready`). The 20 records reported 48,744 input and 15,478 output tokens, no Tavily calls and unknown model cost. Independent human evaluation of evidence, questions and the baseline remains pending; the 9/10 is not semantic accuracy. Raw synthetic outputs are in `data/eval-v2/evaluation/`.

## Still required

Complete and validate canonical schemas, M0/M1 criteria, deterministic identity/date/reference/ranking gates, five-role workflow, storage/API/queue/UI interactions, exports, actual evaluation, docs, deck, and submission package. The present evidence helper is preliminary and must not be treated as a complete temporal/semantic gate.


English default follow-up: rebuilt/recreated the local app container, verified actual browser defaults (UI and report en), switched id/en successfully, and confirmed live_enabled remains true. Evidence: data/english-default-verification-20261110.json. Source packager also skips Office temporary lock files while the owner's presentation is open.


## English demo video - 10 November 2026

User requested a three-minute demo and selected English. Created
`submission/video/DiscoveryBrief-demo-3min-en.mp4`: exactly 180 seconds, 1920x1080,
30 fps / 5,400 frames, H.264 + AAC 48 kHz. English synthetic narration and burned-in captions,
SRT sidecar, script, poster, checksum and verification metadata provided. Full media decode
passes, representative frames visually inspected; audio measured non-silent with -1.5 dB
peak before final sample-accurate duration correction. Final audio and video are both 180 s.

Actual public-company OpenAI live run with synthetic RFP/notes/participant:
`9441950c-1b9c-4991-aeae-17a0a23ae2d5`, completed/ready in 78.989 seconds,
five searches, two extracts, five model calls, 21,386 input / 2,566 output tokens and 12
reported Tavily credits. Model cost/complete failed-attempt usage remain unknown. The video
shows four selected findings; the approved ledger has seven claims. This is integration
observed in one run, not semantic accuracy or quality superiority evidence.

Research wait is edited out and identified on screen. Subsequent UI takes reopen the same
completed result to avoid duplicate paid runs; a separately identified context-only synthetic
replay demonstrates missing public evidence and retains its original Indonesian report text.
The closing preview is the actual one-page PDF. All demo meeting context is fictional.
See submission/video/README.md for provenance and retained capture/editing scripts under
ignored data/demo-video-20261110. No app dependencies changed. No publication/submission done.
