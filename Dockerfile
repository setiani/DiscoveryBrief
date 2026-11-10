FROM node:22.16.0-bookworm-slim AS web
WORKDIR /build/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.11.13-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 APP_DATA_DIR=/data DISCOVERYBRIEF_MODE=public_demo RESEARCH_MODE=fixture
COPY pyproject.toml uv.lock README.md ./
COPY backend/ backend/
RUN pip install --no-cache-dir uv==0.10.11 && uv sync --frozen --extra pdf --no-dev && .venv/bin/python -m playwright install --with-deps chromium
ENV PATH="/app/.venv/bin:$PATH"
COPY tests/fixtures/ tests/fixtures/
COPY demo_runs/ demo_runs/
COPY scripts/ scripts/
COPY eval/ eval/
COPY --from=web /build/web/dist web/dist
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"
CMD ["uvicorn", "discoverybrief.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
