"""Export allowlisted synthetic evaluation cases as honest replay samples."""

import argparse
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from discoverybrief.bundle import canonical_bundle
from discoverybrief.schemas import RunRequest

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("records", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
for case, slug in [
    ("E01", "ready"),
    ("E03", "context-only"),
    ("E10", "partial-source"),
]:
    record = json.loads(
        (args.records / f"{case}-candidate.json").read_text(encoding="utf-8")
    )
    fixture = json.loads(
        (root / f"eval/fixtures/{case}/research.json").read_text(encoding="utf-8")
    )
    if fixture.get("synthetic") is not True or record.get("mode") != "frozen_research":
        raise SystemExit("Only approved synthetic fixed evidence is allowed")
    request = RunRequest.model_validate_json(
        (root / f"eval/fixtures/{case}/request.json").read_text(encoding="utf-8")
    )
    result = record["result"]
    if result.get("status") != "completed":
        raise SystemExit("Sample must be completed")
    result["synthetic"] = True
    result["provenance"] = {
        "case_id": case,
        "implementation_sha256": record["implementation_sha256"],
        "original_mode": "frozen_research",
        "human_review": "pending",
        "note": "Synthetic evidence and live inference; replay performs no new calls.",
    }
    canonical_bundle(
        request, result, str(uuid5(NAMESPACE_URL, f"discoverybrief/{slug}"))
    )
    destination = root / "demo_runs" / f"{slug}.json"
    if destination.exists():
        raise SystemExit(
            "Existing sample preserved; use an explicitly reviewed replacement"
        )
    destination.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "demo_runs" / f"{slug}-request.json").write_text(
        request.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    print("Prepared synthetic replay:", slug)
