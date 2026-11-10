"""Render shipped synthetic replays through the real API and browser for review."""

import time
from pathlib import Path
from tempfile import TemporaryDirectory

from discoverybrief.api.main import create_app
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
output = root / "submission/demo"
output.mkdir(parents=True, exist_ok=True)
with (
    TemporaryDirectory(prefix="discoverybrief-render-") as temporary,
    TestClient(create_app(data_dir=Path(temporary), mode="public_demo")) as client,
):
    for slug in ["ready", "context-only", "partial-source"]:
        run_id = client.post(f"/api/samples/{slug}/replay").json()["run_id"]
        for _ in range(6000):
            state = client.get(f"/api/runs/{run_id}").json()
            if state["status"] in {"completed", "failed"}:
                break
            time.sleep(0.01)
        if state["status"] != "completed":
            raise RuntimeError("Replay failed")
        for name in [
            "brief.json",
            "brief.html",
            "brief.pdf",
            "evidence.json",
            "trace.json",
        ]:
            response = client.get(f"/api/runs/{run_id}/artifacts/{name}")
            if response.status_code == 200:
                (output / f"{slug}-{name}").write_bytes(response.content)
        print("Rendered", slug, state["quality"], flush=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        def route_handler(route):
            from urllib.parse import urlsplit

            request = route.request
            path = urlsplit(request.url).path
            if not request.url.startswith("http://discoverybrief.local/"):
                return route.abort()
            response = client.request(
                request.method,
                path,
                content=request.post_data,
                headers={
                    "Content-Type": request.headers.get(
                        "content-type", "application/json"
                    )
                },
            )
            return route.fulfill(
                status=response.status_code,
                body=response.content,
                headers={
                    "Content-Type": response.headers.get(
                        "content-type", "application/octet-stream"
                    )
                },
            )

        for width in [1280, 390]:
            page = browser.new_page(viewport={"width": width, "height": 960})
            page.route("**/*", route_handler)
            page.goto("http://discoverybrief.local/", wait_until="domcontentloaded")
            page.locator('select[aria-label="Synthetic sample"]').select_option("ready")
            page.get_by_role("button", name="Run offline example").click()
            page.get_by_text("Mode replay", exact=False).wait_for(timeout=20000)
            if page.evaluate(
                "document.documentElement.scrollWidth > window.innerWidth"
            ):
                raise RuntimeError("Horizontal overflow")
            page.locator(".sample:visible").last.screenshot(
                path=str(output / f"ready-ui-{width}.png")
            )
            page.close()
        browser.close()
print("Reviewable synthetic demo artifacts:", output)
