from discoverybrief.api.main import create_app
from fastapi.testclient import TestClient


def test_sample_is_explicitly_synthetic_and_excludes_wrong_entity(tmp_path):
    with TestClient(create_app(data_dir=tmp_path)) as client:
        data = client.get("/api/samples/sagara").json()
    assert data["synthetic"] is True
    assert data["research_mode"] == "fixture"
    assert data["quality"] == "limited"
    assert len(data["findings"]) == 1
    assert len(data["questions"]) == 3
    assert "Logistics" not in str(data)
    assert data["requirements"][0]["quote"].startswith("Portal harus")


def test_sample_html_escapes_model_or_user_text():
    from discoverybrief.fixture import sample
    from discoverybrief.reporting import render_sample_html

    brief = sample()
    brief["company_name"] = "<script>alert(1)</script>"
    html = render_sample_html(brief)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
