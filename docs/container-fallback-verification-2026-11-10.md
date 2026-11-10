# Container and fallback verification — 10 November 2026

Actual engine-backed checks, not independent semantic quality evaluation.

Environment: Windows + WSL, Podman 6.1.4, Docker Compose v5.7.0. No `docker` binary or
Docker Desktop was used. Dockerfile base images: Node 22.16.0 and Python 3.11.13;
Chromium installed inside the Linux image, not reused from Windows. Gateway image:
`docker.io/maximhq/bifrost:v1.5.0`.

## Executed container checks

1. `podman build -t discoverybrief:verification-20261110 .` passed. OCI default drops
   Dockerfile HEALTHCHECK, so rebuilt using `podman build --format docker ...` and also
   defined the healthcheck explicitly in Compose for normal Podman builds.
2. `podman compose -p discoverybrief-verify -f compose.yaml -f data/compose-verification.yaml
   --profile live up -d --no-build` started app and Bifrost on loopback 8010/8081 with
   separate test volumes. Image after fallback code repair:
   `5233da2f326d354673687cbf5dd4fc68789d8fdcfa31ed2d489ebda73996b640`.
3. `python scripts/verify_container.py` passed: health/public_demo boundary, UI loaded with
   zero JavaScript errors, ready/context-only/partial-source replay completed, all six exports
   available for each case, each PDF one page. Artifact:
   `data/container-verification-20261110.json`.
4. `podman restart discoverybrief-verify-app-1`: all three stored runs still completed and
   readable. Explicit `podman healthcheck run` passed. Container-to-gateway `/health` = 200.
5. Host Python regression: 85 passed, one FastAPI/Starlette deprecation warning. New tests
   cover API forwarding of fallback settings and resolved-model/incomplete-usage metadata.
   Initial attempt hit sandbox-owned temp/cache permission errors; rerun used a new workspace
   basetemp and disabled pytest cache. A new test initially sent forbidden `.example` live
   domain; corrected to absent domain with offline adapters. No actual research in that test.

The Windows Compose build command failed to stat an existing `.pytest_cache` directory
before sending context. Direct `podman build` succeeds with the same Dockerfile and ignore
rules. The tested host runbook therefore builds with Podman and runs Compose `--no-build`;
this is not a claim that `podman compose build` succeeds on this workspace.

Build logs: `data/container-build-20261110.log`; gateway pull log:
`data/bifrost-container-pull-20261110.log`. Bifrost logged an upstream SQLite migration warning;
its health and inference nevertheless passed. No general migration/upgrade guarantee.

## Actual fallback checks

Fixed MODEL_FALLBACK not reaching API/CLI doctor/evaluation and Compose. Current local
configuration already specifies `beam-1.0`; `.env` was preserved. All inference stays through
Bifrost, with no app transport retry or direct provider bypass. Failed primary/fallback usage
is unobservable, so model_usage_complete remains false even when final usage is reported.

`ENABLE_LIVE_TESTS=1 python scripts/spike_fallback.py` on Windows and the equivalent
`podman exec -e ENABLE_LIVE_TESTS=1 discoverybrief-verify-app-1 python scripts/spike_fallback.py`:

| Condition | Observed |
|---|---|
| Invalid primary, no fallback | HTTP 400; stops |
| Invalid primary, configured beam-1.0 fallback | Valid submit_payload; resolved_model_used=beam-1.0 |
| Invalid primary and invalid fallback | HTTP 400; stops |

Host artifact: `data/spikes/fallback-20261110T052601Z.json`.
Container configured fallback artifact: `data/container-fallback-configured-20261110.json`.
Earlier host/container control checks used known working gpt-6-luna as fallback; these are
retained separately. The initial ordinary completion also recovered to gpt-6-luna.

The gateway exposes the final resolved model, not an entire attempt trail in these responses.
The negative control establishes invalid primary fails alone; positive control changes only
fallback and succeeds. Counts of internal gateway/provider attempts and all-attempt cost are
unknown. No Tavily calls were made during these checks. Provider monetary billing has not been
reconciled. This tests unavailable-model recovery on one provider, not cross-provider outage
failover or semantic correctness of all five roles on the fallback model.

See [Windows runbook](running-locally-windows.md). Human evaluation, presentation review,
public repository publication and organizer submission remain outstanding.


## Final local stack

Test stack stopped without deleting volumes. Native test gateway stopped. Final image
`523d708ba18024a5a01d07e5785a0742d698a60e7346cd4c317d0ac15041edae` was built with
`podman build --format docker -t discoverybrief-app .`. Standard Compose project
`discoverybrief` started with explicit local/live environment and `--profile live up -d --no-build`.
App on 127.0.0.1:8000 is healthy with live_enabled=true; Bifrost on 127.0.0.1:8080 health=200;
browser UI loaded without JavaScript errors. No paid research run created on this final stack.
Evidence: `data/local-compose-live-20261110.json`. Both containers remain running for the owner.
The final image contains the same runtime fallback fix; documentation/package notes were
updated after image context capture. Runtime data is in separate Compose named volumes.
