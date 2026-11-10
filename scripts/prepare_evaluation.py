"""Curate only synthetic evaluation outputs; preserve originals and leave human labels blank."""

import argparse
import json
from pathlib import Path
from statistics import median

from discoverybrief.config import Settings

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("records", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
if args.output.exists():
    raise SystemExit("Output exists; choose a new version")
root = Path(__file__).resolve().parents[1]
dataset = json.loads((root / "eval/dataset.json").read_text(encoding="utf-8"))
settings = Settings.load()
secrets = [
    value
    for value in (
        settings.tavily_api_key,
        settings.model_provider_api_key,
        settings.bifrost_virtual_key,
    )
    if len(value) >= 8
]
records = []
for case in dataset["cases"]:
    for system in ("baseline", "candidate"):
        path = args.records / f"{case['case_id']}-{system}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("mode") != "frozen_research" or not dataset.get("synthetic"):
            raise SystemExit("Only synthetic fixed-evidence records are eligible")
        for call in record.get("calls", []):
            call.pop("provider_request_id", None)
        content = json.dumps(record, ensure_ascii=False, indent=2)
        if any(secret in content for secret in secrets):
            raise SystemExit("Credential detected; export blocked without printing it")
        records.append((path.name, record, content))
args.output.mkdir(parents=True)
for name, _, content in records:
    (args.output / name).write_text(content + "\n", encoding="utf-8")
rows = []
for case in dataset["cases"]:
    record = next(
        record
        for _, record, _ in records
        if record["case_id"] == case["case_id"] and record["system"] == "candidate"
    )
    result = record.get("result", {})
    matched = result.get("status") == case["expected_outcome"] and (
        result.get("status") != "completed"
        or result.get("quality") == case.get("expected_quality")
    )
    rows.append(
        {
            "case_id": case["case_id"],
            "status": result.get("status"),
            "quality": result.get("quality"),
            "expected_status": case["expected_outcome"],
            "expected_quality": case.get("expected_quality"),
            "outcome_match": matched,
        }
    )
summary = {
    "mode": "frozen_research",
    "synthetic": True,
    "records": len(records),
    "candidate_outcomes": rows,
    "mechanical_outcome_matches": sum(row["outcome_match"] for row in rows),
    "case_count": len(rows),
    "semantic_accuracy": None,
    "independent_human_review": "pending",
    "input_tokens": sum(
        record["usage"]["llm_input_tokens"] or 0 for _, record, _ in records
    ),
    "output_tokens": sum(
        record["usage"]["llm_output_tokens"] or 0 for _, record, _ in records
    ),
    "reported_model_cost": None,
    "tavily_requests": 0,
    "implementation_sha256": sorted(
        {r["implementation_sha256"] for _, r, _ in records}
    ),
    "dataset_sha256": sorted({r.get("dataset_sha256") for _, r, _ in records}),
    "latency_median_seconds": {
        system: median(
            r["elapsed_seconds"] for _, r, _ in records if r["system"] == system
        )
        for system in ("baseline", "candidate")
    },
    "model_calls": {
        system: sum(
            len(r.get("calls", [])) for _, r, _ in records if r["system"] == system
        )
        for system in ("baseline", "candidate")
    },
}
(args.output / "summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"Curated {len(records)} synthetic records; no human judgments supplied.")
