"""One-page PDF output; refuse multipage output rather than clipping or shrinking."""

from copy import deepcopy
from io import BytesIO
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

from discoverybrief.reporting import render_bundle_html


def render_pdf(html: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.route("**/*", lambda route: route.abort())
                page.set_content(html, wait_until="load")
                page.pdf(
                    path=str(temporary),
                    format="A4",
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
        if len(PdfReader(str(temporary)).pages) != 1:
            raise ValueError("report does not fit on one page")
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def bundle_pdf(bundle: dict) -> tuple[dict, bytes]:
    """Fit a selected bundle by dropping lower-priority items, never shrinking text."""
    selected = deepcopy(bundle)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.route("**/*", lambda route: route.abort())
            for _ in range(20):
                page.set_content(render_bundle_html(selected), wait_until="load")
                content = page.pdf(
                    format="A4", print_background=True, prefer_css_page_size=True
                )
                if len(PdfReader(BytesIO(content)).pages) == 1:
                    return selected, content
                if selected.get("hypotheses"):
                    selected["hypotheses"].pop()
                elif len(selected.get("questions", [])) > 2:
                    selected["questions"].pop()
                elif len(selected.get("requirements", [])) > 2:
                    selected["requirements"].pop()
                elif len(selected.get("claims", [])) > 2 or selected.get("claims"):
                    selected["claims"].pop()
                else:
                    raise ValueError("report cannot fit within minimum readable layout")
                selected["overflow_note"] = (
                    "Sebagian isi tidak tampil pada halaman ini; lihat detail lengkap."
                    if selected["language"] == "id"
                    else "Some items were omitted from this page; see full details."
                )
            raise ValueError("report selection did not converge")
        finally:
            browser.close()
