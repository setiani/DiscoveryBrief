"""Browser regression for English defaults and intact bilingual saved evidence."""

from urllib.parse import urlsplit

import pytest
from discoverybrief.api.main import create_app
from fastapi.testclient import TestClient
from playwright.sync_api import expect, sync_playwright


@pytest.mark.slow
def test_english_sample_controls_and_preserved_historical_quotes(tmp_path):
    app = create_app(data_dir=tmp_path, mode="public_demo", research_mode="fixture")
    with TestClient(app) as client, sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))

        def route_handler(route):
            request = route.request
            if not request.url.startswith("http://discoverybrief.local/"):
                return route.abort()
            response = client.request(
                request.method,
                urlsplit(request.url).path,
                content=request.post_data,
                headers={
                    "Content-Type": request.headers.get(
                        "content-type", "application/json"
                    )
                },
            )
            route.fulfill(
                status=response.status_code,
                body=response.content,
                headers={
                    "Content-Type": response.headers.get("content-type", "text/plain")
                },
            )

        page.route("**/*", route_handler)
        page.goto("http://discoverybrief.local/", wait_until="networkidle")
        expect(page.locator("html")).to_have_attribute("lang", "en")
        expect(page.locator('select[name="language"]')).to_have_value("en")
        expect(page.get_by_role("button", name="Run offline example")).to_be_enabled()
        expect(
            page.get_by_role("button", name="View synthetic example")
        ).to_be_visible()
        page.locator('select[aria-label="Synthetic sample"]').select_option("ready")
        page.get_by_role("button", name="Run offline example").click()
        result = page.get_by_role(
            "heading", name="Sagara Insurance \u00b7 Synthetic example"
        ).locator("..")
        expect(result).to_contain_text("Mode: replay", timeout=20000)
        expect(result).to_contain_text("Quality: ready")
        result.get_by_text("Inspect evidence and RFP quotations", exact=True).click()
        quotes = result.locator("blockquote").all_text_contents()
        assert any("integrasi dengan sistem existing" in quote for quote in quotes)
        page.locator("header select").select_option("id")
        expect(
            page.get_by_role("button", name="Jalankan contoh offline")
        ).to_be_visible()
        page.locator("header select").select_option("en")
        expect(page.get_by_role("button", name="Run offline example")).to_be_visible()
        assert result.locator("blockquote").all_text_contents() == quotes
        assert not errors
        browser.close()
