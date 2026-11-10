# Live verification — repair session, 9 November 2026

Only public company context and a synthetic SSO/integration RFP were sent. All inference
used the configured local Bifrost transport v1.5.0 and its OpenAI-compatible provider; no
direct-provider bypass or fallback success is claimed. Keys are not recorded here.

| Attempt | Result | Reported usage | Local evidence |
|---|---|---|---|
| First repaired API smoke | completed/limited; 2 approved claims, 2 requirements, 2 questions | 6 Search, 2 Extract, 5 model requests; 14 Tavily credits; 17,329 input / 1,943 output tokens | `data/spikes/live-brief-71578f5a-6650-40c9-a4c4-0d05f4274f4e.json` |
| E01 development check, fixed evidence | completed/ready; 3 developments | No Tavily; 5 model requests; 6,655 input / 1,626 output tokens | `data/eval-gapfix-check/evaluation/E01-candidate.json` |
| Frozen baseline/candidate comparison | 20 records; 10/10 mechanical candidate outcomes match | No Tavily; baseline 10 / candidate 48 model requests; 52,239 input / 14,968 output tokens | `eval/results/2026-11-09-gapfix/` |
| Later API smoke | completed/ready; 4 selected claims from 4 sources, 2 requirements, 2 questions | 6 Search, 2 Extract, 5 model requests; 13 Tavily credits versus 14 reserved; 18,463 input / 2,350 output tokens | `data/spikes/live-brief-ec46b513-3cdb-42b6-be53-8a9975319c33.json` |

These observed calls total 73 model requests, 94,686 input tokens and 20,887 output tokens;
the two API smokes reported 27 Tavily credits. Model monetary cost remains unknown. Counts
are local reported usage, not an account-billing reconciliation or future cost estimate.

The later API smoke reported 97,641 ms in its exported bundle; the runner's terminal
duration can differ slightly because artifact publication/commit follows bundle generation.
Both smokes completed the real API → worker → research → inference → export path. They do
not establish availability/reliability rates or semantic accuracy on other companies.

## Separate source inspection

This was an assistant inspection of primary pages, **not a human evaluation label**:

- The future implementation wording in the robots.txt finding is appropriately framed as
  an announced aim, rather than a completed future action. The primary announcement is dated
  30 October. [OpenAI announcement](https://openai.com/index/helping-websites-express-ai-training-preferences/)
- The local-compacts finding corresponds to the announced commitments for future owned
  campuses, rather than evidence that all such campuses already exist.
  [OpenAI infrastructure announcement](https://openai.com/index/setting-new-standard-responsible-ai-infrastructure/)
- The prototype vulnerability-count finding is supported by the reported experiment;
  this inspection does not independently validate the underlying security research.
  [OpenAI research publication](https://openai.com/index/a-thousand-fewer-paths-to-root/)
- The Google Cloud source describes a private-preview rollout to selected customers.
  The later brief says models were announced, which avoids claiming general availability.
  Browser publication date appeared as 21 October while the Tavily extract displayed
  22 October; its provider timestamp was `Wed, 21 Oct 2026 19:02:45 GMT` (22 October in WIB).
  Timezone is a plausible explanation, not a verified cause of the differing date display.
  RFC2822 provider timestamps are now retained explicitly as provider estimates.
  [Google Cloud announcement](https://cloud.google.com/blog/products/ai-machine-learning/google-cloud-brings-openai-models-to-customers)

Only synthetic sources are included in the public-review demo package. The full live
source snapshots remain in ignored local data, avoiding publication of whole third-party
articles. The source checks do not replace the independent fixed-evidence human review.
