# DiscoveryBrief

Evidence-based preparation for enterprise discovery meetings: recent company developments,
literal RFP requirements, questions, tentative hypotheses and unknowns in a one-page brief.

**Local workflow implemented; release review in progress.** Offline regression checks and a
public-company live smoke have passed. Independent human quality evaluation and a final
presentation review remain required. Dockerfile/Compose were verified on this host using
Podman 6.1.4 (10 November); see [container/fallback checks](docs/container-fallback-verification-2026-11-10.md). No deployment,
public repository publication or hackathon submission is claimed.

See [architecture](docs/architecture.md), [repair status](docs/remediation-status.md),
[evaluation](eval/results.md), [license](LICENSE) and [dependency notices](THIRD_PARTY_NOTICES.md).

## Current development setup

Requirements: Python 3.11+, Node.js 20.19+ or 22.12+, and uv. From this directory:

```powershell
uv sync --extra dev --extra pdf --frozen
uv run playwright install chromium
npm --prefix web ci
uv run discoverybrief doctor
uv run discoverybrief run --input tests/fixtures/request.json --mode fixture
uv run pytest
npm --prefix web run build
```

Copy `.env.example` to `.env` when starting from a fresh checkout. The user's local `.env` is git-ignored. Set `TAVILY_API_KEY`, `MODEL_PROVIDER_BASE_URL`, `MODEL_PROVIDER_API_KEY`, and the exact provider model ID in `MODEL_PRIMARY`; `MODEL_FALLBACK` is optional. The model provider is configurable. `BIFROST_BASE_URL` identifies the local gateway, not the provider endpoint. Gateway-bound model IDs use the `custom/` prefix; the provider-specific ID can itself contain a slash. Never place keys in frontend variables, source code, or demo files.

Docker Compose includes app and Bifrost services. This Windows host uses Podman 6.1.4
with Docker Compose v5.7.0; Docker Desktop itself was not tested. The verified local gateway transport is v1.5.0, launched by
the npm wrapper `@maximhq/bifrost@1.6.3`. These are separate component version numbers.
Bifrost binds to loopback. See [progress](docs/progress.md) for the recorded checks.

For local development without Docker, the initial gateway launcher setup is:

```powershell
npm install --no-save --prefix data/bifrost-runtime @maximhq/bifrost@1.6.3
uv run python scripts/start_bifrost.py
```

It reads the provider settings from `.env`, writes a gateway configuration without embedding the key, and keeps the gateway on `127.0.0.1:8080`. Restart it after changing provider settings. For the current sample UI, build the frontend and start the backend in a separate terminal:

```powershell
npm --prefix web run build
uv run uvicorn discoverybrief.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Open `http://127.0.0.1:8000/` to view the synthetic sample. Live smoke tests use public input and require `ENABLE_LIVE_TESTS=1`; provider and Tavily charges or rate limits may apply.

The synthetic samples can be opened through the frontend or `GET /api/samples`.
The CLI and API use the same persisted runner. Fixture mode accepts the canonical synthetic
request and uses its historical research clock even when run months later. Local live creation
requires `RESEARCH_MODE=live` and `ENABLE_LIVE_RUNS=1`; the default stays off. Run the live
checks with public/synthetic input. Remote model-provider processing still applies.

## Development status

Ten synthetic fixed-evidence cases and an initial comparison runner are in `eval/` and `scripts/evaluate_frozen.py`. The runner requires `ENABLE_LIVE_TESTS=1`, a running Bifrost gateway and a configured provider; it can incur model charges and stops after a provider/pipeline error. `--case E01 --system baseline` limits it to one baseline attempt. Outputs go to the ignored local data directory, are never overwritten, and require independent human review. Use a fresh `APP_DATA_DIR` for a separately identified new run, and retain earlier attempts. All ten output pairs have been generated; human review and the complete baseline quality comparison remain outstanding. See [evaluation results](eval/results.md).

See [progress](docs/progress.md) and [implementation plan](docs/plan/README.md). No independently
measured accuracy, production readiness, public deployment, or completed submission is claimed.

## Modes and paid execution

| Mode | Research | Inference | Purpose |
|---|---|---|---|
| fixture | Scripted synthetic sources | Scripted roles | Offline workflow/contract checks |
| replay | Saved approved sample | None | Display prior results, with original metrics separate |
| frozen_research | Fixed synthetic evidence | Live through Bifrost | Baseline/candidate evaluation |
| live | Tavily Search + Extract | Live through Bifrost | Company research |

Enable live work in your local `.env`, start Bifrost, then restart the backend. Changing provider
settings requires restarting Bifrost as well. Keep the app on `127.0.0.1` with one worker.
Do not expose Bifrost's admin dashboard. Configured MODEL_FALLBACK now reaches the API,
CLI doctor and evaluation clients. Recovery from an unavailable model to beam-1.0 was verified
on the current provider on Windows and in Compose. This does not establish provider outage
failover or fallback semantic quality; missing failed-attempt usage remains unknown.

```powershell
# Explicitly enables potentially paid CLI checks in this terminal.
$env:ENABLE_LIVE_TESTS = '1'
uv run discoverybrief doctor --live
uv run discoverybrief run --input public-request.json --mode live
uv run discoverybrief evaluate --dataset eval/dataset.json --mode frozen_research
Remove-Item Env:ENABLE_LIVE_TESTS
```

Use a fresh `APP_DATA_DIR` for a new evaluation attempt; prior outputs are preserved. Reported
Tavily credits and conservative reservations are distinct. Token totals/price/cost remain null
when unknown. Model and Tavily usage coverage are tracked separately. No zero-cost inference
or strict dollar cap is promised.

## Evidence, API and exports

`GET /api/runs/{id}/brief` and `brief.json` use the canonical `BriefBundle` envelope: `brief`,
`claims`, `requirements`, `sources`, `evidence`, `metrics`, `warnings`. `brief.finding_ids` and
`brief.requirement_ids` select page content. The associated approved ledger can contain more
items so PDF pruning does not destroy accepted evidence or question grounding.

`GET /api/runs/{id}/evidence` retains all local source snapshots, candidates, independent reviews
and rejection reasons, including evidence collected before a later failure. Full RFP and notes
are not returned in normal run summaries. HTML, Markdown and PDF share selected content;
JSON/evidence preserve full approved/detail records. PDF failures leave the other formats usable.

Queue capacity is one active plus three waiting runs. Every HTTP attempt and schema repair
counts toward the shared budget. The worker deadline includes publication. Cancellation may
arrive after an external request was billed. Restart marks unfinished work INTERRUPTED without
automatic paid resume. SQLite schema version 1 rejects unsupported newer databases.

## Testing and reproduction

```powershell
./scripts/dev.ps1 test
uv run discoverybrief evaluate --dataset eval/dataset.json --mode fixture
uv run python scripts/verify_clean_setup.py
```

The fixture evaluation command validates dataset contracts without pretending to measure
model quality. The clean-setup script preserves a new source copy, creates a new venv, runs
`npm ci`, builds and tests without copying `.env` or runtime data. Chromium's existing host
cache is reused; this is not a new operating-system or Docker test. Check logs remain under
the specifically named `data/reproduction-*` directory.

Acceptance scenario coverage and remaining human/live checks are tracked in
[acceptance](docs/acceptance.md), not inferred from the number of pytest cases.

## Docker and read-only demos

```powershell
# Local read-only replay; no model credentials needed.
docker compose up --build app
# Optional live gateway setup, after preparing its non-secret configuration.
uv run python scripts/start_bifrost.py --prepare-only
docker compose --profile live up --build
```

Compose defaults to `public_demo` when no local `.env` overrides it. For an explicitly read-only
demo set `DISCOVERYBRIEF_MODE=public_demo` and `ENABLE_LIVE_RUNS=0`; host ports bind loopback.
Dockerfile/Compose passed engine-backed build, HTTP/UI/replay/PDF and restart checks
using Podman on this host. For this machine, use `podman build --format docker -t discoverybrief-app .` followed by
`podman compose up -d --no-build app`; the Windows Compose builder could not stat a local cache directory.
See the Windows runbook for live mode and startup commands.
Public hosting is optional and is not configured by these commands.

## Privacy, retention and limitations

The Planner sees only public research fields. Notes, RFP, goals and participant names never
become public search queries; later inference roles can send them to the configured provider.
User-provided roles remain attributed. Source text is untrusted and rendered as text.
The Verifier and Premise Auditor are model safeguards, not factual guarantees.

Runtime requests/evidence are stored unencrypted in `APP_DATA_DIR` and excluded from source
packages. There is no automatic retention cleanup. Prefer a separate, clearly named data
directory for each sensitive task. To remove that task's stored context, stop the API and
remove that task-specific directory after saving any required exports; do not remove the
gateway directory or unrelated runs. Browser form input stays in memory only.

The Bifrost configuration disables content logging, but this does not establish downstream
provider retention or a compliance certification. Shipped demos contain synthetic data only.
Publish minimal source quotations and links; live access does not grant redistribution rights.

The implementation is a single-owner MVP. Lexical event clustering is approximate. Model
outputs can vary, relevant news may be absent, and a limited/context-only result is legitimate.
Human review of the fixed-evidence comparison remains required before claiming accuracy.



## Menjalankan di mesin Windows ini

Panduan lengkap: [local Windows](docs/running-locally-windows.md). Mesin ini memakai
Podman; jalankan perintah dari direktori `discoverybrief`. Kredensial tetap di `.env`.
Mode live hanya melakukan panggilan berbayar ketika Anda membuat run baru.
