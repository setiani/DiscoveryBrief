"""Check a running read-only container over HTTP, without paid research."""

import argparse
import json
import time
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright
from pypdf import PdfReader


def main(base_url):
    records = []
    with httpx.Client(base_url=base_url, timeout=15) as client:
        health = client.get("/api/health").json()
        assert health["mode"] == "public_demo" and health["live_enabled"] is False
        assert client.get("/").status_code == 200
        assert client.post("/api/runs", json={}).status_code == 403
        for slug, quality in [
            ("ready", "ready"),
            ("context-only", "context_only"),
            ("partial-source", "limited"),
        ]:
            response = client.post(f"/api/samples/{slug}/replay")
            response.raise_for_status()
            run_id = response.json()["run_id"]
            deadline = time.monotonic() + 60
            while time.monotonic() < deadline:
                state = client.get(f"/api/runs/{run_id}").json()
                if state["status"] in {"completed", "failed"}:
                    break
                time.sleep(0.2)
            assert state["status"] == "completed", state
            assert state["quality"] == quality
            bundle = client.get(f"/api/runs/{run_id}/brief").json()
            assert bundle["brief"]["research_mode"] == "replay"
            artifacts = {}
            for name in [
                "brief.json",
                "brief.md",
                "brief.html",
                "brief.pdf",
                "evidence.json",
                "trace.json",
            ]:
                artifact = client.get(f"/api/runs/{run_id}/artifacts/{name}")
                artifact.raise_for_status()
                artifacts[name] = len(artifact.content)
                if name.endswith(".json"):
                    artifact.json()
                if name == "brief.pdf":
                    assert len(PdfReader(BytesIO(artifact.content)).pages) == 1
            records.append(
                {
                    "sample": slug,
                    "run_id": run_id,
                    "quality": quality,
                    "pdf_pages": 1,
                    "artifacts_bytes": artifacts,
                }
            )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(base_url, wait_until="networkidle")
        assert page.locator('select[aria-label="Synthetic sample"]').count() == 1
        assert not errors, errors
        browser.close()
    result = {
        "checked_at": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "health": health,
        "ui_javascript_errors": errors,
        "samples": records,
        "passed": True,
    }
    output = Path("data/container-verification-20261110.json")
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    main(parser.parse_args().base_url)
