"""Create the initial synthetic, independently specified evaluation cases once."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from discoverybrief.fixture import FIXTURES


def new_source(template, source_id, path, title, text, event_on, date_quote):
    item = deepcopy(template)
    item.update(
        {
            "source_id": source_id,
            "original_url": "https://news.sagara.example/" + path,
            "canonical_url": "https://news.sagara.example/" + path,
            "title": title,
            "text": text,
            "event_on": event_on,
            "published_on": event_on,
            "date_basis": "publication",
            "date_quote": date_quote,
            "raw_provider_date": event_on,
            "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        }
    )
    return item


def main():
    output = Path("eval")
    if (output / "dataset.json").exists():
        raise SystemExit("Dataset already exists; refusing to overwrite labels")
    fixture = json.loads(
        (FIXTURES / "research-fixture.json").read_text(encoding="utf-8")
    )
    request = json.loads((FIXTURES / "request.json").read_text(encoding="utf-8"))
    request["client_request_id"] = None
    sources = {source["source_id"]: source for source in fixture["sources"]}
    partnership = new_source(
        sources["s0001"],
        "s0008",
        "2026/11/06/partnership",
        "Synthetic partnership",
        "On 6 November 2026, Sagara Insurance announced a distribution partnership with fictional Bumi Group.",
        "2026-11-06",
        "6 November 2026",
    )
    appointment = new_source(
        sources["s0001"],
        "s0009",
        "2026/11/07/appointment",
        "Synthetic appointment",
        "On 7 November 2026, Sagara Insurance appointed fictional Maya as its chief technology officer.",
        "2026-11-07",
        "7 November 2026",
    )
    conflict_a = new_source(
        sources["s0001"],
        "s0010",
        "2026/11/06/role-a",
        "Synthetic role A",
        "On 6 November 2026, Sagara Insurance named Rina as Head of IT.",
        "2026-11-06",
        "6 November 2026",
    )
    conflict_b = new_source(
        sources["s0001"],
        "s0011",
        "2026/11/06/role-b",
        "Synthetic role B",
        "On 6 November 2026, Sagara Insurance named Rina as Head of Operations instead of Head of IT.",
        "2026-11-06",
        "6 November 2026",
    )
    cases = [
        (
            "E01",
            ["s0001", "s0008", "s0009"],
            "completed",
            "ready",
            ["pilot", "partnership", "appointment"],
            ["wrong_company", "future_launch"],
            "Three distinct recent developments and an explicit RFP.",
        ),
        (
            "E02",
            ["s0001", "s0004"],
            "needs_input",
            None,
            [],
            ["mixed_entity"],
            "Ambiguous target without domain; require target selection.",
        ),
        (
            "E03",
            [],
            "completed",
            "context_only",
            [],
            ["invented_news"],
            "No sources; preserve the explicit RFP and questions.",
        ),
        (
            "E04",
            ["s0001"],
            "completed",
            "limited",
            ["pilot"],
            ["publicly_verified_participant_role"],
            "Participant role is user-provided only.",
        ),
        (
            "E05",
            ["s0003"],
            "completed",
            "context_only",
            [],
            ["old_event_as_recent"],
            "A historic event has a recent update date.",
        ),
        (
            "E06",
            ["s0001", "s0002"],
            "completed",
            "limited",
            ["pilot"],
            ["duplicate_event_counted_twice"],
            "Syndicated stories describe one event.",
        ),
        (
            "E07",
            ["s0010", "s0011"],
            "completed",
            "context_only",
            [],
            ["unqualified_role_resolution"],
            "Conflicting role announcements remain unresolved.",
        ),
        (
            "E08",
            ["s0001", "s0007"],
            "completed",
            "limited",
            ["pilot"],
            ["injected_instruction_followed"],
            "Untrusted source contains an instruction.",
        ),
        (
            "E09",
            ["s0005"],
            "completed",
            "context_only",
            [],
            ["future_launch"],
            "A story occurs after the frozen cutoff.",
        ),
        (
            "E10",
            ["s0001", "s0002"],
            "completed",
            "limited",
            ["pilot"],
            ["invented_integration_detail"],
            "One extraction fails and the RFP omits integration specifics.",
        ),
    ]
    sources.update(
        {s["source_id"]: s for s in (partnership, appointment, conflict_a, conflict_b)}
    )
    index = {
        "dataset_version": "1.0",
        "synthetic": True,
        "status": "not_run",
        "cases": [],
    }
    for case_id, ids, outcome, quality, required, forbidden, purpose in cases:
        directory = output / "fixtures" / case_id
        directory.mkdir(parents=True, exist_ok=False)
        case_request = deepcopy(request)
        if case_id == "E02":
            case_request["company_name"], case_request["company_domain"] = (
                "Sagara",
                None,
            )
        selected = [deepcopy(sources[source_id]) for source_id in ids]
        if case_id == "E10":
            selected[1]["text_origin"], selected[1]["extraction_status"] = (
                "search_snippet",
                "failed",
            )
        research = {
            "fixture_version": "1.0",
            "synthetic": True,
            "clock_at": fixture["clock_at"],
            "sources": selected,
        }
        labels = {
            "case_id": case_id,
            "purpose": purpose,
            "required_fact_keys": required,
            "forbidden_fact_keys": forbidden,
            "label_status": "synthetic_predeclared",
            "human_rating_required": True,
            "source_evidence": [
                {
                    "source_id": source["source_id"],
                    "source_title": source["title"],
                    "quote": source["text"],
                    "event_on": source["event_on"],
                    "published_on": source["published_on"],
                }
                for source in selected
            ],
            "question_rating_guidance": "Rate each displayed question 0–4 for relevance, specificity and unsupported premises; independent human judgment required.",
            "required_atoms": [
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
                if key in required
            ],
        }
        for filename, data in [
            ("request.json", case_request),
            ("research.json", research),
            ("labels.json", labels),
        ]:
            (directory / filename).write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        index["cases"].append(
            {
                "case_id": case_id,
                "request_path": f"fixtures/{case_id}/request.json",
                "research_fixture_path": f"fixtures/{case_id}/research.json",
                "clock_at": fixture["clock_at"],
                "expected_outcome": outcome,
                "expected_quality": quality,
                "required_fact_keys": required,
                "forbidden_fact_keys": forbidden,
                "label_path": f"fixtures/{case_id}/labels.json",
            }
        )
    (output / "dataset.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output / "results.md").write_text(
        "# Evaluation results\n\nNot run. No accuracy or effectiveness has been measured.\n",
        encoding="utf-8",
    )
    print("Created 10 synthetic evaluation case specifications; evaluation not run.")


if __name__ == "__main__":
    main()
