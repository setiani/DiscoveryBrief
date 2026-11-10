# Running DiscoveryBrief locally on Windows

Verified on Windows with Podman 6.1.4, WSL, and Docker Compose v5.7.0 on 10 November 2026.
The same Dockerfile was built and run with Podman; Docker Desktop itself was not tested.

All commands below run from your own clone of the repository. Replace the example path
`C:\Projects\DiscoveryBrief` with the directory where you cloned it:

```powershell
Set-Location C:\Projects\DiscoveryBrief
```

## First-time setup

Install Python 3.11+, Node.js 20.19+ or 22.12+, and uv. Prepare the Python environment and
create the configuration file without overwriting an existing one:

```powershell
uv sync --extra dev --extra pdf --frozen
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

For live research, configure `TAVILY_API_KEY`, `MODEL_PROVIDER_BASE_URL`,
`MODEL_PROVIDER_API_KEY`, and the exact `MODEL_PRIMARY` ID in `.env`. `MODEL_FALLBACK` is
optional. Credentials remain local and are ignored by Git. See the [README](../README.md)
for configuration details and the difference between model and gateway endpoints.

## Option 1: app and Bifrost containers

Open PowerShell from the repository root:

```powershell
podman machine list
# Run only if your existing machine is not running:
# podman machine start
podman info

# Generate gateway configuration without embedding the provider API key.
uv run python scripts/start_bifrost.py --prepare-only
$env:DISCOVERYBRIEF_MODE = 'local'
$env:RESEARCH_MODE = 'live'
$env:ENABLE_LIVE_RUNS = '1'
podman build --format docker -t discoverybrief-app .
podman compose --profile live up -d --no-build
podman compose --profile live ps
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

Open **http://127.0.0.1:8000/**. The health response should show `live_enabled: true`.
Enter a real company and official domain, a future meeting time, a goal, a report language,
and an optional plain-text RFP. Create the brief, inspect its evidence, and download exports.
Live runs may consume Tavily credits and paid model usage. Synthetic replays make no new
external calls. `limited` and `context_only` are legitimate outcomes when evidence is sparse.

The configured `beam-1.0` fallback passed a structured-routing test on the development setup.
Primary and fallback used the same provider; this does not establish whole-provider outage
recovery or fallback semantic quality. Choose models supported by your own provider/account.

After changing `.env`, regenerate the gateway configuration with `--prepare-only` and rerun
Compose with `--force-recreate`. Do not run native services on ports 8000/8080 at the same
time as these containers.

Stop services without deleting their stored results:

```powershell
podman compose --profile live stop
```

To restart live mode, set the three environment variables above again, then run:

```powershell
podman compose --profile live up -d --no-build
```

Those environment settings apply only to the current PowerShell terminal. The development
Windows host's Compose builder could not read a local cache directory, so the verified
workflow builds with Podman and starts Compose with `--no-build`.

Results are stored in the app's named volume. Its default name is `discoverybrief_app_data`;
it can differ if you change the Compose project name or repository directory name. Avoid
`down -v` if you want to preserve results. Both published ports bind to loopback only.

## Read-only demo without paid API calls

The app can display approved synthetic replays without starting Bifrost or providing API keys:

```powershell
$env:DISCOVERYBRIEF_MODE = 'public_demo'
$env:RESEARCH_MODE = 'fixture'
$env:ENABLE_LIVE_RUNS = '0'
podman build --format docker -t discoverybrief-app .
podman compose up -d --no-build app
```

Open the same local URL and select a synthetic example. To switch back to live mode, repeat
the live environment settings and startup commands under option 1.

## Option 2: native Python and Node.js

Stop Compose services first to avoid port conflicts. From the repository root:

```powershell
uv sync --extra dev --extra pdf --frozen
uv run playwright install chromium
npm --prefix web ci
npm --prefix web run build
npm install --no-save --prefix data/bifrost-runtime @maximhq/bifrost@1.6.3
```

In terminal 1, start the gateway:

```powershell
uv run python scripts/start_bifrost.py
```

In terminal 2, from the repository root:

```powershell
$env:DISCOVERYBRIEF_MODE = 'local'
$env:RESEARCH_MODE = 'live'
$env:ENABLE_LIVE_RUNS = '1'
$env:BIFROST_BASE_URL = 'http://127.0.0.1:8080/v1'
uv run uvicorn discoverybrief.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Open **http://127.0.0.1:8000/**. Ctrl+C stops each terminal's service. `APP_DATA_DIR` in `.env`
controls native run storage, which is separate from the container volume.

## Diagnostics

- `podman info` must succeed before starting Compose.
- Check occupied ports with `Get-NetTCPConnection -State Listen -LocalPort 8000,8080`.
- Read application logs with `podman compose logs --tail 100 app`; use `bifrost` for gateway
  logs. Do not publish credentials, private context, or unredacted configuration/logs.
- If `live_enabled` is false, set all three live environment variables before `compose up`.
  Provider/Tavily credentials and `MODEL_PRIMARY` must also be present in `.env`.
- To run the paid fallback check, execute:
  `podman compose exec -e ENABLE_LIVE_TESTS=1 app python scripts/spike_fallback.py`.
- The read-only container check is:
  `uv run python scripts/verify_container.py --base-url http://127.0.0.1:8000`.
  It requires dev dependencies, installed Chromium, and a server in `public_demo` mode.
