import importlib.util

import pytest
from discoverybrief.fixture import sample
from discoverybrief.reporting import render_sample_html


@pytest.mark.slow
def test_synthetic_sample_pdf_is_one_page(tmp_path):
    if importlib.util.find_spec("playwright") is None:
        pytest.skip("PDF extra not installed")
    from discoverybrief.pdf import render_pdf
    from pypdf import PdfReader

    output = tmp_path / "sample.pdf"
    render_pdf(render_sample_html(sample()), output)
    pdf = PdfReader(str(output))
    assert len(pdf.pages) == 1
    assert "Sagara Insurance" in (pdf.pages[0].extract_text() or "")


@pytest.mark.slow
def test_bundle_pdf_keeps_readable_single_page(tmp_path):
    if importlib.util.find_spec("playwright") is None:
        pytest.skip("PDF extra not installed")
    from io import BytesIO

    from discoverybrief.pdf import bundle_pdf
    from pypdf import PdfReader

    claim = {
        "claim_id": "c1",
        "statement": "Sagara announced an agent portal pilot.",
        "evidence": [{"source_id": "s1", "quote": "A pilot was announced."}],
    }
    bundle = {
        "company_name": "Sagara Insurance",
        "meeting_at": "2026-11-12T10:00:00+07:00",
        "knowledge_cutoff": "2026-11-08T03:00:00Z",
        "language": "id",
        "research_mode": "fixture",
        "quality": "limited",
        "warnings": [],
        "context_summary": [],
        "claims": [claim],
        "requirements": [],
        "questions": [{"text": "Apa tujuannya?"}, {"text": "Apa batasannya?"}],
        "hypotheses": [],
        "unknowns": [],
        "sources": [
            {
                "source_id": "s1",
                "title": "Pengumuman",
                "url": "https://news.example/pilot",
            }
        ],
    }
    selected, content = bundle_pdf(bundle)
    pdf = PdfReader(BytesIO(content))
    assert len(pdf.pages) == 1 and len(selected["questions"]) >= 2
    assert "Sagara Insurance" in (pdf.pages[0].extract_text() or "")


@pytest.mark.slow
def test_dense_bundle_is_pruned_without_shrinking_or_clipping():
    if importlib.util.find_spec("playwright") is None:
        pytest.skip("PDF extra not installed")
    from io import BytesIO

    from discoverybrief.pdf import bundle_pdf
    from discoverybrief.reporting import render_bundle_html
    from pypdf import PdfReader

    sentences = "Informasi sintetis untuk membahas cakupan dan integrasi. "
    claims = [
        {
            "claim_id": f"c{i}",
            "statement": (sentences * 4)[:180],
            "evidence": [{"source_id": f"s{i}", "quote": "synthetic"}],
        }
        for i in range(4)
    ]
    sources = [
        {
            "source_id": f"s{i}",
            "title": "Synthetic source",
            "url": f"https://news.example/item{i}",
        }
        for i in range(4)
    ]
    bundle = {
        "company_name": "Sagara Insurance",
        "meeting_at": "2026-11-12T10:00:00+07:00",
        "knowledge_cutoff": "2026-11-08T03:00:00Z",
        "language": "id",
        "research_mode": "fixture",
        "quality": "limited",
        "warnings": [],
        "context_summary": [],
        "claims": claims,
        "requirements": [{"summary": (sentences * 3)[:140]} for _ in range(4)],
        "questions": [{"text": (sentences * 4)[:180]} for _ in range(4)],
        "hypotheses": [{"text": (sentences * 3)[:140]} for _ in range(2)],
        "unknowns": [{"text": (sentences * 2)[:100]} for _ in range(3)],
        "sources": sources,
    }
    selected, content = bundle_pdf(bundle)
    assert len(PdfReader(BytesIO(content)).pages) == 1
    assert len(selected["questions"]) >= 2
    assert "font:10pt" in render_bundle_html(selected)
    assert len(selected["claims"]) <= 4


@pytest.mark.slow
@pytest.mark.parametrize("language", ["id", "en"])
@pytest.mark.parametrize("no_news", [False, True])
def test_TC27_TC28_maximum_fields_in_both_languages(language, no_news):
    from io import BytesIO

    from discoverybrief.pdf import bundle_pdf
    from pypdf import PdfReader

    sentence = "Discuss ownership, acceptance criteria and integration constraints. "
    bundle = {
        "company_name": ("Synthetic company name " * 10)[:160],
        "meeting_at": "2026-11-12T10:00:00+07:00",
        "knowledge_cutoff": "2026-11-08T03:00:00Z",
        "language": language,
        "research_mode": "fixture",
        "quality": "context_only" if no_news else "limited",
        "warnings": [],
        "context_summary": [
            {"text": (sentence * 9)[:500]},
            {"text": (sentence * 4)[:203]},
            {"text": (sentence * 4)[:203]},
        ],
        "claims": []
        if no_news
        else [
            {
                "claim_id": f"c{i}",
                "statement": (sentence * 3)[:180],
                "evidence": [{"source_id": f"s{i}"}],
            }
            for i in range(4)
        ],
        "sources": [
            {
                "source_id": f"s{i}",
                "title": (sentence * 5)[:300],
                "url": "https://news.example/" + "synthetic/" * 50 + str(i),
            }
            for i in range(4)
        ],
        "requirements": [{"summary": (sentence * 3)[:140]} for _ in range(4)],
        "questions": [{"text": (sentence * 3)[:180]} for _ in range(4)],
        "hypotheses": [{"text": (sentence * 3)[:140]} for _ in range(2)],
        "unknowns": [{"text": (sentence * 2)[:120]} for _ in range(3)],
    }
    selected, content = bundle_pdf(bundle)
    assert len(PdfReader(BytesIO(content)).pages) == 1
    assert len(selected["questions"]) >= 2
