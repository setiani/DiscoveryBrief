# Machine-readable planning examples

These files are **synthetic**, authored for this plan. Organizations/domains and announcements
are fictional. Never call Tavily with .example URLs and never describe the records as real customers.

| File | Use |
|---|---|
| [request.json](request.json) | RunRequest example, scheduled ID-language RFP clarification meeting |
| [research-fixture.json](research-fixture.json) | Normalized SourceRecord examples with valid text hashes |
| [role-outputs.json](role-outputs.json) | Scripted role submissions for a deterministic vertical slice |
| [expectations.json](expectations.json) | Expected key outcomes; not a fabricated measured result |

The wrapper around research-fixture.json is a fixture container, not an API response:
fixture_version, synthetic, clock_at, and sources. Each sources item follows SourceRecord.
Its evidence is deliberately mixed: valid, duplicate, old-updated, wrong entity, future,
undated and injection-bearing text.

role-outputs.json contains output objects before code-assigned IDs, followed by expected
verifier/composer/auditor payloads after deterministic ID assignment. It is an example of a
fixture client script, not a live provider recording. The implementation must still run
all quote/date/entity/reference gates; it must not trust expected outcomes as runtime input.

Canonical fake clock: 8 Nov 2026 at 03:00 UTC. Meeting: 12 Nov at 03:00 UTC.
Only one distinct recent event is eligible, so expected quality is limited, not ready.
The duplicated story is the same event. Create two more distinct valid developments for E01
in the full evaluation dataset.

Hash convention: SHA-256 of UTF-8 normalized source text. RFP offsets use Python code points.
The documentation validation performed when authoring checks JSON, literal spans, hashes,
references and links; it does not execute the future app or verify model behavior.
