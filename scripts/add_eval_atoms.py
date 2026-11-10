"""Add predeclared supported fact atoms to the unrun synthetic labels once."""

import json
from pathlib import Path

root = Path("eval/fixtures")
for directory in sorted(root.glob("E[0-9][0-9]")):
    path = directory / "labels.json"
    labels = json.loads(path.read_text(encoding="utf-8"))
    if "required_atoms" in labels:
        raise SystemExit(f"Atoms already exist: {directory.name}")
    sources = {
        source["source_id"]: source
        for source in json.loads(
            (directory / "research.json").read_text(encoding="utf-8")
        )["sources"]
    }
    labels["required_atoms"] = [
        {
            "key": key,
            "entity": "Sagara Insurance",
            "source_id": source_id,
            "supporting_quote": sources[source_id]["text"],
            "event_on": sources[source_id]["event_on"],
        }
        for key, source_id in (
            ("pilot", "s0001"),
            ("partnership", "s0008"),
            ("appointment", "s0009"),
        )
        if key in labels["required_fact_keys"]
    ]
    path.write_text(
        json.dumps(labels, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
