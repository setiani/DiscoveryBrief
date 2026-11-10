# Evaluation results

No independently judged baseline/candidate quality comparison has been completed, and no aggregate accuracy or effectiveness has been measured.

## Latest repair evaluation — 9 November 2026

A separate corrected run produced 20 outputs in
[results/2026-11-09-gapfix](results/2026-11-09-gapfix/summary.json): ten ordinary baseline
summaries and ten candidate outcomes, using fixed synthetic evidence and the same configured
model. No Tavily requests were made. Both systems received the explicit historical cutoff
and window, the same bounded evidence passages, and four-item display limits.

| Operational measurement | Observed |
|---|---|
| Candidate terminal/quality outcomes matching predeclared labels | **10/10** |
| E01 | completed/ready; three distinct developments |
| E02 | needs_input; no factual brief |
| E03/E05/E07/E09 | completed/context_only |
| E04/E06/E08/E10 | completed/limited |
| Baseline outputs parsed | 10/10 |
| Model requests | Baseline 10; candidate 48 |
| Median elapsed time, N=10 per system | Baseline 8.69 s; candidate 36.91 s |
| Reported tokens across both systems | 52,239 input; 14,968 output |
| Monetary cost | Unknown; no verified pricing/billing reconciliation |

The candidate used more calls and took longer. Its quality advantage over the baseline
**has not been established**. Outcome matching does not measure support precision, factual
recall, reference entailment, entity/temporal accuracy, injection resistance, or question
usefulness. Those values remain unmeasured until independent review is completed.

Use the [local human review form](review-gapfix.html) or
[blank worksheet](results/2026-11-09-gapfix-review.json). No human ratings have been supplied.
The form hides system identities, shows source evidence/raw results, and downloads a review
JSON without sending data to a service. It is synthetic data and stores no browser-local draft.

All 20 records share the recorded implementation fingerprint
`a6aee3051661453c9b2558df438fa839a3cbaf0842eb47dd61d87f88d3dcccee`.
They preserve the evaluation snapshot; later operational/report-contract fixes and RFC-date
normalization were not a new model-quality experiment. ISO-dated fixtures remain unchanged.
Per-call prompt/schema hashes are retained. Earlier attempts below are retained as history
and are not merged into the new run's denominator.

## Earlier development attempts

On 9 November 2026, one E01 baseline attempt failed with HTTP 503. That attempt used the current model ID against a stale gateway configuration from the preceding provider, so it is an invalid configuration check, not a model-quality result. Its failure record is retained locally under `data/evaluation/E01-baseline.json`. The gateway was then restarted using the current `.env`.

In a separate preliminary run, output was collected for E01–E04 and the E05 baseline before the run was stopped. The baseline had been asked for different item limits from the candidate's display limits, so these outputs must not be used as a fair comparison. They are retained in `data/eval-krypton/evaluation/`. In E01 the candidate completed `limited` with one claim and two requirements, short of the predeclared `ready` target; in E02 it completed instead of requesting clarification. These observations require detailed review and do not establish accuracy or superiority.

The runner was corrected to request four findings, requirements and questions for baseline, matching the candidate's item limits. A fresh run generated all 20 outputs under `data/eval-v2/evaluation/`: ten baseline outputs parsed and ten candidate outcomes were recorded. All records report the same model and implementation fingerprint and are marked pending human review. No Tavily requests were made in this fixed-evidence run.

Mechanical comparison against the predeclared terminal status and quality matched **9/10** candidate cases. E01 returned `completed/limited` against `completed/ready`; E02–E10 matched their expected outcome/quality. This narrow check does not assess factual support, reference validity, requirement grounding, question usefulness, injection resistance or baseline quality. Those judgments and the full baseline comparison remain pending. The 20 records reported 48,744 input and 15,478 output tokens, with usage marked complete; model cost is unknown and not reconciled with provider billing.

A blank 20-record worksheet has been prepared at `data/eval-v2/review-sheet.json`. Instructions are in [REVIEW.md](REVIEW.md); it contains no human judgments yet.

After the entity-candidate handoff was corrected, E02 returned the predeclared `needs_input` outcome. This is one unjudged case, not a measured false-positive or accuracy rate.
