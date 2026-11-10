import pytest
from discoverybrief.exports import markdown_report


def test_markdown_resolves_sources_and_escapes_untrusted_text():
    selection = {
        "finding_ids": ["c1"],
        "requirement_ids": [],
        "questions": [],
        "hypotheses": [],
        "unknowns": [],
    }
    claims = [
        {
            "claim_id": "c1",
            "statement": "Update <script>x</script>",
            "evidence": [{"source_id": "s1"}],
        }
    ]
    sources = [{"source_id": "s1", "canonical_url": "https://news.example/item"}]
    output = markdown_report(
        "Example",
        selection,
        claims,
        [],
        sources,
        mode="fixture",
        quality="limited",
        cutoff="2026-11-08",
    )
    assert "&lt;script&gt;" in output and "<script>" not in output
    assert "[1]: https://news.example/item" in output
    with pytest.raises(ValueError, match="unresolved source"):
        markdown_report(
            "Example",
            selection,
            claims,
            [],
            [],
            mode="fixture",
            quality="limited",
            cutoff="2022026-11-08",
        )
