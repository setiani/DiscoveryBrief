# Implementation-agent instructions for DiscoveryBrief

These instructions apply to the DiscoveryBrief application in this directory.
The original planning snapshot lives in ../discoverybrief-plan; actual implementation and
verification status lives in docs/progress.md and docs/remediation-status.md.

## Read first

Read docs/plan/README.md and the milestone in 11-milestones-and-agent-tasks.md.
Read the referenced contracts before editing the corresponding module.

## Product invariants

1. **Evidence before assertions.** Public factual text comes from approved claims and
   renderable references, never from unconstrained composer prose.
2. **User context is attributed.** Participant roles, notes, and RFP text remain user-provided
   unless independently supported. A missing public profile is not a failed product.
3. **Requirements are verbatim-grounded.** Each extracted requirement points to exact
   Unicode character offsets in the submitted RFP.
4. **Time is explicit.** Use aware datetimes and an injected clock. Date calculations and
   ranking scores are code, not model output.
5. **Unknown is allowed.** Empty search results, undated sources, semantic uncertainty,
   and entity ambiguity have defined outcomes. Do not invent filler.
6. **One-page brief is distinct from evidence detail.** Do not shrink text to hide overflow.
7. **Models never execute arbitrary code.** Use validated structured submissions and a
   finite workflow. No arbitrary URLs, shell commands, SQL, file paths, or tool names from a model.
8. **All live model calls pass through Bifrost.** All web research uses the Tavily adapter.
   Never silently bypass Bifrost to recover from a failed gateway.
9. **Private context is not a search query.** Query generation does not receive RFP text,
   meeting notes, raw meeting goal, or participant list.
10. **No misleading demo.** Fixture/replay and live results have visible labels and separate metrics.

## Engineering constraints

- Python 3.11+, FastAPI, Pydantic v2, httpx, SQLite; Vite + TypeScript, no frontend framework.
- Keep one backend worker process. See restart recovery; do not promise a durable job queue.
- Use pathlib and argument arrays for subprocess. Support Windows PowerShell and Docker.
- Keep provider/model/version configurable. Pin resolved dependencies and Bifrost release.
- API keys only from environment; never commit .env or runtime run records.
- Offline tests default. Paid live tests require the explicit live-test switch and configured keys.
- Unknown/missing token usage is null, not zero. Monetary estimates are labeled estimates.
- No new frameworks, vector database, distributed queue, social scraper, CRM, or OAuth unless
  the MVP is accepted and the user authorizes that scope.
- Prefer useful contract, boundary, integration, and end-to-end tests over trivial implementation tests.

## Milestone completion

Run the checks listed for the milestone. Record the exact command, outcome, and artifact path.
Do not mark live integration complete from mocks. Do not mark accuracy targets achieved
without the evaluation report and raw outputs.

Maintain a progress note so another agent can continue without rediscovering decisions.
Report blockers precisely, continue independent authorized work, and ask for missing
credentials only when live work actually requires them. Public publication/submission
is performed only under the user's applicable authorization.
