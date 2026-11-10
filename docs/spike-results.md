# Integration and rendering spikes

Recorded 9 November 2026, Asia/Jakarta. These are development observations, not milestone
acceptance or independent quality measurements. See [progress](progress.md) for chronology.

| Check | Command or method | Observed | Remaining limitation |
|---|---|---|---|
| Bifrost/provider | `ENABLE_LIVE_TESTS=1` with `python scripts/spike_provider.py` | Local Bifrost v1.5.0, OpenAI-compatible KryptonLab and `gpt-6-luna` returned nonempty content | One simple call, not quality or uptime evidence |
| Structured roles | `ENABLE_LIVE_TESTS=1` with `python scripts/spike_role_schemas.py` | Five synthetic payload shapes validated separately through Bifrost | Does not establish semantic correctness |
| Fallback (updated 10 Nov) | `scripts/spike_fallback.py`, host and Compose | Invalid primary fails; fallback to configured `beam-1.0` returns validated tool output; both invalid fail | Same provider only; semantic quality and failed-attempt usage unknown. [Details](container-fallback-verification-2026-11-10.md) |
| Tavily Search/Extract | `ENABLE_LIVE_TESTS=1` with `python scripts/spike_live_api.py` using public OpenAI context and synthetic RFP | Latest brief run used six searches, two extracts, five model calls and reported 14 Tavily credits | One development example; no general relevance or quality claim |
| Usage | Same live API run, recorded in the bundle | 17,065 input and 2,136 output tokens reported; model cost unknown | Missing values stay unknown; billing has not been reconciled |
| PDF | `python -m pytest tests/test_pdf.py -q` | Synthetic report rendered as one page with extractable text | Not proof for all languages, long content or environments |
| Content logging | Bifrost `/api/config` | Config reported content logging disabled and per-request override disabled | Actual storage and downstream provider retention are not audited |

The local `.env` contains the active provider configuration and credentials; do not add them
to this document. On a provider change, restart Bifrost and verify that its active custom
provider matches the configured base URL before running a paid test. An earlier stale-gateway
attempt failed HTTP 503 and is retained separately from current-provider results.

PowerShell example for an explicitly enabled, public/synthetic single-call check:

```powershell
$env:ENABLE_LIVE_TESTS = '1'
uv run python scripts/spike_provider.py
Remove-Item Env:ENABLE_LIVE_TESTS
```
