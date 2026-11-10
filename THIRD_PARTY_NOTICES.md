# Dependency and asset attribution

DiscoveryBrief application code is MIT licensed. Dependencies retain their own licenses;
this file does not relicense them. Exact Python and JavaScript versions are recorded in
`uv.lock` and `web/package-lock.json`.

| Component | Role | License family / notice |
|---|---|---|
| FastAPI, Uvicorn, Pydantic, Typer, httpx, Jinja2 | Backend, contracts and reporting | Permissive licenses; see installed distribution metadata |
| SQLite, Python standard library | Local persistence and runtime | SQLite public domain / Python license |
| Vite, TypeScript, Vitest | Frontend build and testing | MIT / Apache-2.0 / MIT respectively |
| Playwright, Chromium, pypdf | Browser/PDF rendering and verification | Apache-2.0; Chromium includes multiple licenses; BSD-3-Clause |
| Bifrost OSS | External model gateway | Apache-2.0; distributed separately |
| Tavily | Hosted Search/Extract API | Service terms; not bundled source code |
| pytest, Ruff, uv | Development tooling | MIT; MIT; MIT/Apache-2.0 respectively |
| python-pptx | Optional presentation generation | MIT; optional tool, not required to run the app |

The interface names system fallback fonts; no external web font or image is downloaded by
reports. All shipped company/news/RFP demo fixtures are synthetic and originate in this
workspace's DiscoveryBrief plan or evaluation fixtures. Bifrost/Tavily trademarks belong to
their respective owners. Live web source text remains third-party material: published demo
samples use synthetic sources, and a live research result is not a redistribution license.

To inspect installed Python license metadata without network access:

```powershell
uv run python scripts/dependency_licenses.py
```

For redistribution, preserve the relevant dependency notices and Chromium's bundled notices.
