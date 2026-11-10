"""Create a blank independent-review worksheet from synthetic evaluation records."""

import argparse
import json
from pathlib import Path


def item_text(item):
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for key in ("statement", "summary", "text", "question", "claim"):
            if isinstance(item.get(key), str):
                return item[key]
    return json.dumps(item, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Review worksheet already exists; refusing to overwrite it.")
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / "eval/dataset.json").read_text(encoding="utf-8"))[
        "cases"
    ]
    sheets = []
    for case in cases:
        case_id = case["case_id"]
        labels = json.loads(
            (root / "eval" / case["label_path"]).read_text(encoding="utf-8")
        )
        for system in ("baseline", "candidate"):
            path = args.record_dir / f"{case_id}-{system}.json"
            if not path.is_file():
                continue
            record = json.loads(path.read_text(encoding="utf-8"))
            result = record.get("result", {})
            if system == "baseline":
                parsed = result.get("parsed", {})
                claims, requirements, questions = (
                    parsed.get(key, [])
                    for key in ("findings", "requirements", "questions")
                )
            else:
                selection = result.get("brief_selection", {})
                claim_ids = set(selection.get("finding_ids", []))
                requirement_ids = set(selection.get("requirement_ids", []))
                claims = [
                    item
                    for item in result.get("claims", [])
                    if item.get("claim_id") in claim_ids
                ]
                requirements = [
                    item
                    for item in result.get("requirements", [])
                    if item.get("requirement_id") in requirement_ids
                ]
                questions = selection.get("questions", [])
            sheets.append(
                {
                    "case_id": case_id,
                    "system": system,
                    "review_status": "pending",
                    "raw_record": str(path),
                    "label_path": case["label_path"],
                    "outcome_and_quality_correct": None,
                    "claims": [
                        {
                            "text": item_text(item),
                            "human_supported": None,
                            "entity_correct": None,
                            "temporal_eligible": None,
                            "references_valid": None,
                            "notes": "",
                        }
                        for item in claims
                    ],
                    "requirements": [
                        {"text": item_text(item), "grounded": None, "notes": ""}
                        for item in requirements
                    ],
                    "questions": [
                        {"text": item_text(item), "rating": None, "notes": ""}
                        for item in questions
                    ],
                    "required_atoms": [
                        {"key": atom["key"], "surfaced": None, "notes": ""}
                        for atom in labels["required_atoms"]
                    ],
                    "forbidden_assertions_checked": None,
                    "reviewer_notes": "",
                }
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"status": "pending_independent_review", "records": sheets},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Prepared {len(sheets)} blank records; no human judgments or scores were supplied."
    )


if __name__ == "__main__":
    main()
