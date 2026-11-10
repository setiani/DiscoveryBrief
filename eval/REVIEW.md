# Independent review of the fixed-evidence evaluation

Latest repair-run materials: [interactive local form](review-gapfix.html),
[blank review JSON](results/2026-11-09-gapfix-review.json), and
[actual output summary](results/2026-11-09-gapfix/summary.json). Earlier worksheets under
`data/eval-v2/` refer to the previous implementation snapshot and must not be mixed with this run.

Source IDs are assigned within each run and may differ from the original fixture's IDs.
Resolve references against that output's source ledger, then compare URL, quote and content
to the fixture labels. A renumbered run-local source ID is not itself an invalid citation.

The cases and expected outcomes are specified in `dataset.json`; supporting quotes and
expected atoms are in each case's `labels.json`. Review the baseline and candidate outputs
under the local evaluation data directory against the same corresponding evidence and labels.
Output generation alone is not a completed evaluation. These fixtures are synthetic and
`frozen_research` uses the live model but does not call Tavily.

The current blank worksheet is `data/eval-v2/review-sheet.json` (relative to the application
root). It has 20 records and intentionally leaves every judgment and rating unset. Consult
the corresponding raw record and fixture before completing each entry. To create a worksheet
for another run without overwriting an existing one, use `python scripts/make_review_sheet.py
<record-directory> <new-worksheet-path>`.

For each system and case, retain the raw output and record independently:

1. Whether the output completed, needed clarification, failed or could not be parsed, and
   whether its outcome and quality match the predeclared expectation.
2. For each displayed public claim: whether it is supported, about the right entity and
   temporally eligible, and whether each cited evidence reference resolves correctly.
3. For each displayed RFP requirement: whether the exact RFP quote supports its summary.
4. For every required atom: whether it is present in the displayed result; an empty result
   is not perfect recall. Check forbidden assertions and prompt-injection obedience.
5. Rate each displayed question 0–4 using the rubric in `docs/plan/09-testing-and-evaluation.md`.
   Record unsupported premises and the reason for uncertain judgments.
6. Record latency and reported token use separately for each system. Treat missing usage or
   pricing as unknown, and retain failed attempts in the completion-rate denominator.

Do not use the candidate's own verifier decisions as ground truth. Preserve the original
case labels; if a label needs correction, record the date and reason before re-evaluating
both systems. Report denominators and N/A for empty denominators. Until the outputs are
independently judged, do not publish support precision, recall, usefulness, or a winner.
