"""Report mechanical case outcomes; semantic quality still needs independent review."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "eval/dataset.json").read_text(encoding="utf-8"))[
        "cases"
    ]
    present, matched, baseline_present = 0, 0, 0
    for case in cases:
        case_id = case["case_id"]
        path = args.output_dir / f"{case_id}-candidate.json"
        baseline_present += (args.output_dir / f"{case_id}-baseline.json").is_file()
        if not path.is_file():
            print(f"{case_id}: pending")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("mode") != "frozen_research" or data.get("case_id") != case_id:
            raise ValueError("unexpected evaluation record")
        present += 1
        result = data.get("result", {})
        status = result.get("status", data.get("status"))
        quality = result.get("quality")
        correct = (
            status == case["expected_outcome"] and quality == case["expected_quality"]
        )
        matched += correct
        print(
            f"{case_id}: status={status}, quality={quality}, expected_match={correct}"
        )
    print(
        f"candidate outputs: {present}/{len(cases)}; baseline outputs: {baseline_present}/{len(cases)}"
    )
    print(f"mechanical outcome matches: {matched}/{present} (not semantic accuracy)")
    print(
        "Independent review of evidence, requirements, questions and all labels remains required."
    )


if __name__ == "__main__":
    main()
