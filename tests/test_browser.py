"""Browser interaction with intercepted synthetic API responses; no paid calls."""

import importlib.util
import json
from pathlib import Path
from urllib.parse import urlsplit

import pytest

DIST = Path(__file__).resolve().parents[1] / "web" / "dist"


@pytest.mark.slow
def test_live_form_serialization_and_brief_rendering():
    if (
        importlib.util.find_spec("playwright") is None
        or not (DIST / "index.html").exists()
    ):
        pytest.skip("Build frontend and install PDF/browser extra first")
    from playwright.sync_api import sync_playwright

    captured = []
    run_id = "11111111-1111-4111-8111-111111111111"
    brief = {
        "company_name": "Synthetic Co",
        "quality": "context_only",
        "research_mode": "live",
        "knowledge_cutoff": "2026-11-08T03:00:00Z",
        "claims": [],
        "requirements": [],
        "questions": [{"text": "What is the desired outcome?"}],
        "hypotheses": [],
        "unknowns": [],
        "sources": [],
        "warnings": [],
        "metrics": {},
    }

    def route_handler(route):
        request = route.request
        path = urlsplit(request.url).path
        if path == "/api/config/public":
            return route.fulfill(
                json={"mode": "local", "research_mode": "live", "live_enabled": True}
            )
        if path == "/api/runs" and request.method == "POST":
            captured.append(json.loads(request.post_data))
            return route.fulfill(
                status=202, json={"run_id": run_id, "status": "queued"}
            )
        if path == f"/api/runs/{run_id}":
            return route.fulfill(json={"status": "completed", "stage": "finished"})
        if path == f"/api/runs/{run_id}/brief":
            return route.fulfill(json=brief)
        if path == "/":
            return route.fulfill(
                content_type="text/html", body=(DIST / "index.html").read_bytes()
            )
        if path.startswith("/assets/"):
            asset = DIST / path.lstrip("/")
            content_type = "text/css" if asset.suffix == ".css" else "text/javascript"
            return route.fulfill(content_type=content_type, body=asset.read_bytes())
        return route.abort()

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.route("http://localhost/**", route_handler)
        page.goto("http://localhost/", wait_until="domcontentloaded")
        assert page.locator("html").get_attribute("lang") == "en"
        page.locator("header select").select_option("id")
        page.locator("[name=company_name]").fill("Synthetic Co")
        page.locator("[name=company_domain]").fill("synthetic.example.com")
        page.locator("[name=date]").fill("2026-11-12")
        page.locator("[name=time]").fill("10:30")
        page.locator("form details summary").click()
        page.locator("[name=rfp_text]").fill("Synthetic requirement")
        page.locator("[name=participants]").fill("Rina | IT lead")
        page.locator("[name=topic][value=identity]").check()
        page.get_by_role("button", name="Buat discovery brief").click()
        page.get_by_text("What is the desired outcome?").wait_for()
        assert captured[0]["meeting_at"] == "2026-11-12T10:30:00+07:00"
        assert captured[0]["participants"][0]["role"] == "IT lead"
        assert captured[0]["public_topics"] == ["identity"]
        assert not page.evaluate(
            "document.documentElement.scrollWidth > window.innerWidth"
        )
        page.locator("header select").select_option("en")
        assert (
            page.locator(".hero h1").inner_text()
            == "Start the conversation with context."
        )
        assert page.locator("[name=company_name]").input_value() == "Synthetic Co"
        assert len(captured) == 1  # UI translation does not regenerate the report.
        assert page.get_by_role("button", name="Create discovery brief").count() == 1
        page.locator("header select").focus()
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement !== document.body")
        browser.close()
