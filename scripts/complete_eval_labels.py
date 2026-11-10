"""Add source references to the initial, not-yet-run synthetic labels once."""

import json
from pathlib import Path

for directory in sorted(Path("eval/fixtures").glob("E[0-9][0-9]")):
    path = directory / "labels.json"
    labels = json.loads(path.read_text(encoding="utf-8"))
    if "source_evidence" in labels:
        raise SystemExit(f"Labels already expanded: {directory.name}")
    research = json.loads((directory / "research.json").read_text(encoding="utf-8"))
    labels["source_evidence"] = [
        {
            "source_id": s["source_id"],
            "source_title": s["title"],
            "quote": s["text"],
            "event_on": s["event_on"],
            "published_on": s["published_on"],
        }
        for s in research["sources"]
    ]
    labels["question_rating_guidance"] = (
        "Rate each displayed question 0–4 for relevance, specificity and unsupported "
        "premises; independent human judgment required."
    )
    path.write_text(
        json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
