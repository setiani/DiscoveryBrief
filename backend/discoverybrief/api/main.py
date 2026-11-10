"""Local HTTP interface; live creation remains disabled pending release checks."""

import json
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from time import monotonic
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from discoverybrief.artifacts import ArtifactStore
from discoverybrief.bundle import canonical_bundle, warning_message
from discoverybrief.clients import BifrostClient, CallBudget, TavilyClient
from discoverybrief.clock import SystemClock
from discoverybrief.config import Settings
from discoverybrief.contracts import BriefBundle, RunView
from discoverybrief.fixture import FIXTURES, sample
from discoverybrief.fixtures import FixtureModel, FixtureResearch
from discoverybrief.pipeline import run_live
from discoverybrief.publish import publish_artifacts
from discoverybrief.reporting import render_sample_html
from discoverybrief.runner import RunRunner
from discoverybrief.schemas import RunRequest
from discoverybrief.store import Conflict, QueueFull, RunStore

WEB_DIST = Path(__file__).resolve().parents[3] / "web" / "dist"
REPLAY_SAMPLE = Path(__file__).resolve().parents[3] / "demo_runs" / "sagara.json"
SAMPLES = {
    "sagara": (
        REPLAY_SAMPLE,
        FIXTURES / "request.json",
        "Canonical synthetic limited example",
    ),
    "ready": (
        REPLAY_SAMPLE.parent / "ready.json",
        REPLAY_SAMPLE.parent / "ready-request.json",
        "Three distinct synthetic developments",
    ),
    "context-only": (
        REPLAY_SAMPLE.parent / "context-only.json",
        REPLAY_SAMPLE.parent / "context-only-request.json",
        "No verified news; attributed user context",
    ),
    "partial-source": (
        REPLAY_SAMPLE.parent / "partial-source.json",
        REPLAY_SAMPLE.parent / "partial-source-request.json",
        "Partial extraction and an ambiguous requirement",
    ),
}
MAX_REQUEST_BYTES = 65536


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "retryable": code == "QUEUE_FULL",
                "stage": None,
                "details": [],
            }
        },
    )


def create_app(
    *,
    data_dir: Path | None = None,
    clock=None,
    mode: str | None = None,
    research_mode: str | None = None,
    allow_live: bool | None = None,
    live_handler=None,
) -> FastAPI:
    settings = Settings.load()
    app_clock = clock or SystemClock()
    app_mode = mode or settings.mode
    app_research = research_mode or settings.research_mode
    app_data = data_dir or settings.data_dir
    if app_mode not in {"local", "public_demo"}:
        raise ValueError("unsupported application mode")
    if app_mode == "public_demo":
        app_data = app_data / "public-demo"
    if app_research not in {"fixture", "live"}:
        raise ValueError("unsupported research mode")
    requested_live = settings.enable_live_runs if allow_live is None else allow_live
    credentials_ready = bool(
        settings.tavily_api_key
        and settings.model_primary
        and settings.model_provider_api_key
    )
    live_enabled = bool(
        app_mode == "local"
        and app_research == "live"
        and requested_live
        and (credentials_ready or live_handler is not None)
    )

    async def fixture_handler(
        request: RunRequest,
        created_at: datetime,
        on_stage,
        selected_mode: str = "fixture",
        on_checkpoint=None,
    ) -> dict:
        # Source snapshots are fixed at the example's original date; never imply new research.
        return await run_live(
            request,
            datetime(2026, 11, 8, 3, tzinfo=UTC),
            FixtureResearch(),
            FixtureModel(),
            CallBudget(),
            research_mode=selected_mode,
            on_stage=on_stage,
            on_checkpoint=on_checkpoint,
        )

    async def configured_live_handler(
        request: RunRequest, created_at: datetime, on_stage, run_id: str
    ) -> dict:
        if live_handler is not None:
            return await live_handler(request, created_at, on_stage)
        budget = CallBudget()

        def on_call(call):
            application.state.store.checkpoint(run_id, "calls", call["call_id"], call)
            application.state.store.record_call_event(run_id, call)
            from discoverybrief.pipeline import metrics

            application.state.store.checkpoint(
                run_id, "metrics", "current", metrics(budget)
            )

        budget.ledger.on_call = on_call
        research = TavilyClient(settings.tavily_api_key, budget)
        model = BifrostClient(
            settings.bifrost_base_url,
            settings.model_primary,
            budget,
            settings.bifrost_virtual_key,
            fallback_model=settings.model_fallback,
            min_interval_seconds=settings.model_min_interval_seconds,
        )
        return await run_live(
            request,
            created_at,
            research,
            model,
            budget,
            research_mode="live",
            on_stage=on_stage,
            on_checkpoint=lambda snapshot: application.state.store.checkpoint(
                run_id, "pipeline", "current", snapshot
            ),
        )

    async def managed_handler(
        request: RunRequest, created_at: datetime, on_stage, run_id: str
    ) -> dict:
        started = monotonic()
        selected_mode = application.state.store.get(run_id)["research_mode"]
        if selected_mode == "replay":
            sample_ids = application.state.store.ledger(run_id, "sample")
            sample_id = sample_ids[-1]["sample_id"] if sample_ids else "sagara"
            result = json.loads(SAMPLES[sample_id][0].read_text(encoding="utf-8"))
            if result.get("synthetic") is not True or result.get(
                "research_mode"
            ) not in {"fixture", "frozen_research"}:
                raise ValueError("unapproved replay artifact")
            result["original_metrics"] = result.get("metrics", {})
            result["original_research_mode"] = result["research_mode"]
            result["research_mode"] = "replay"
            result["metrics"] = {
                "duration_ms": None,
                "search_requests": 0,
                "extract_requests": 0,
                "extract_url_attempts": 0,
                "llm_requests": 0,
                "llm_input_tokens": None,
                "llm_output_tokens": None,
                "tavily_credits_reported": None,
                "tavily_credits_reserved": 0,
                "estimated_model_cost_microusd": None,
                "usage_complete": False,
            }
        elif selected_mode == "fixture":
            result = await fixture_handler(
                request,
                created_at,
                on_stage,
                selected_mode,
                lambda snapshot: application.state.store.checkpoint(
                    run_id, "pipeline", "current", snapshot
                ),
            )
        else:
            result = await configured_live_handler(
                request, created_at, on_stage, run_id
            )
        application.state.store.checkpoint(run_id, "pipeline", "current", result)
        result.setdefault("metrics", {})["duration_ms"] = round(
            (monotonic() - started) * 1000
        )
        if result.get("status") == "completed":
            on_stage("rendering")
        await publish_artifacts(request, result, application.state.artifacts, run_id)
        return result

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        store = RunStore(app_data / "runs.db")
        runner = RunRunner(store, app_clock, managed_handler)
        await runner.start()
        application.state.store = store
        application.state.runner = runner
        application.state.artifacts = ArtifactStore(app_data, store)
        try:
            yield
        finally:
            await runner.close()
            store.close()

    application = FastAPI(title="DiscoveryBrief", version="0.1.0", lifespan=lifespan)

    @application.middleware("http")
    async def correlation(request, call_next):
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = str(uuid4())
        if response.status_code == 429:
            response.headers["Retry-After"] = "5"
        return response

    @application.get("/api/health")
    async def health() -> dict:
        return {
            "status": "ok",
            "schema_version": "1.0",
            "mode": app_mode,
            "live_enabled": live_enabled,
        }

    @application.get("/api/config/public")
    async def public_config() -> dict:
        return {
            "mode": app_mode,
            "research_mode": app_research,
            "live_enabled": live_enabled,
            "languages": ["id", "en"],
            "max_rfp_chars": 12000,
            "sample_ids": [key for key, value in SAMPLES.items() if value[0].is_file()],
        }

    @application.get("/api/samples/{sample_id}")
    async def synthetic_sample(sample_id: str):
        if sample_id == "sagara":
            return sample()
        if sample_id not in SAMPLES or not SAMPLES[sample_id][0].is_file():
            return error(404, "NOT_FOUND", "Sample not found.")
        from discoverybrief.bundle import build_bundle

        result = json.loads(SAMPLES[sample_id][0].read_text(encoding="utf-8"))
        request = RunRequest.model_validate_json(
            SAMPLES[sample_id][1].read_text(encoding="utf-8")
        )
        view = build_bundle(request, result)
        view["findings"] = view.pop("claims")
        return view

    @application.get("/api/samples")
    async def list_samples() -> dict:
        return {
            "items": [
                {
                    "sample_id": key,
                    "company_name": "Sagara Insurance",
                    "synthetic": True,
                    "description": value[2],
                }
                for key, value in SAMPLES.items()
                if value[0].is_file()
            ]
        }

    @application.post("/api/samples/{sample_id}/replay")
    async def replay_sample(sample_id: str):
        if sample_id not in SAMPLES or not SAMPLES[sample_id][0].is_file():
            return error(404, "NOT_FOUND", "Sample not found.")
        request = RunRequest.model_validate_json(
            SAMPLES[sample_id][1].read_text(encoding="utf-8")
        )
        request = request.model_copy(update={"client_request_id": None})
        try:
            run_id, _ = application.state.runner.create(request, "replay")
            application.state.store.checkpoint(
                run_id, "sample", "id", {"sample_id": sample_id}
            )
        except QueueFull:
            return error(429, "QUEUE_FULL", "The local queue is full; try again later.")
        return JSONResponse(
            status_code=202,
            content={
                "run_id": run_id,
                "status": "queued",
                "status_url": f"/api/runs/{run_id}",
                "research_mode": "replay",
            },
        )

    @application.get("/api/samples/sagara/request")
    async def synthetic_request() -> dict:
        return {
            "synthetic": True,
            "request": RunRequest.model_validate_json(
                (FIXTURES / "request.json").read_text(encoding="utf-8")
            ).model_dump(mode="json"),
        }

    @application.get("/api/samples/sagara/brief.html", response_class=HTMLResponse)
    async def synthetic_sample_html() -> str:
        return render_sample_html(sample())

    @application.post("/api/runs")
    async def create_run(request: Request):
        if app_mode != "local":
            return error(403, "DEMO_READ_ONLY", "Public demo does not create runs.")
        if app_research == "live" and not live_enabled:
            return error(
                503, "LIVE_NOT_READY", "Live run creation is not available yet."
            )
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > MAX_REQUEST_BYTES:
                return error(
                    413, "REQUEST_TOO_LARGE", "Request body exceeds the limit."
                )
        try:
            parsed = RunRequest.model_validate_json(bytes(body))
            duplicate = application.state.store.find_duplicate(parsed)
            if duplicate:
                return JSONResponse(
                    status_code=200,
                    content={
                        "run_id": duplicate,
                        "status": application.state.store.get(duplicate)["status"],
                        "status_url": f"/api/runs/{duplicate}",
                        "research_mode": application.state.store.get(duplicate)[
                            "research_mode"
                        ],
                    },
                )
            if app_research == "fixture":
                example = RunRequest.model_validate_json(
                    (FIXTURES / "request.json").read_text(encoding="utf-8")
                )
                if parsed.model_dump(
                    exclude={"client_request_id"}
                ) != example.model_dump(exclude={"client_request_id"}):
                    return error(
                        422,
                        "FIXTURE_ONLY",
                        "Only the canonical synthetic example is available in fixture mode.",
                    )
            elif parsed.company_domain and parsed.company_domain.endswith(".example"):
                return error(
                    422,
                    "VALIDATION_ERROR",
                    "Synthetic domains cannot be used in live research.",
                )
            run_id, created = application.state.runner.create(parsed, app_research)
        except ValidationError:
            return error(422, "VALIDATION_ERROR", "Meeting input is invalid.")
        except QueueFull:
            return error(429, "QUEUE_FULL", "The local queue is full; try again later.")
        except Conflict:
            return error(
                409,
                "IDEMPOTENCY_CONFLICT",
                "Request identifier was already used for different input.",
            )
        except ValueError:
            return error(
                422, "VALIDATION_ERROR", "Meeting time is outside the supported range."
            )
        return JSONResponse(
            status_code=202 if created else 200,
            content={
                "run_id": run_id,
                "status": application.state.store.get(run_id)["status"],
                "status_url": f"/api/runs/{run_id}",
                "research_mode": app_research,
            },
        )

    @application.get("/api/runs/{run_id}", response_model=RunView)
    async def get_run(run_id: UUID):
        record = application.state.store.get(str(run_id))
        if record is None:
            return error(404, "NOT_FOUND", "Run not found.")
        if app_mode != "local" and record["research_mode"] != "replay":
            return error(
                403, "DEMO_READ_ONLY", "Public demo exposes approved samples only."
            )
        result = application.state.store.result(str(run_id))
        checkpoints = application.state.store.ledger(str(run_id), "pipeline")
        partial = result or (checkpoints[-1] if checkpoints else {})
        stored_metrics = application.state.store.ledger(str(run_id), "metrics")
        parsed_request = application.state.store.request(str(run_id))
        record.update(
            {
                key: partial.get(key)
                for key in ("entity", "knowledge_cutoff", "window_start", "window_end")
            }
        )
        if record["knowledge_cutoff"] is None:
            record["knowledge_cutoff"] = min(
                datetime.fromisoformat(record["created_at"]), parsed_request.meeting_at
            ).isoformat()
        if record["window_start"] is None:
            record["window_start"] = (
                parsed_request.meeting_at - timedelta(days=30)
            ).isoformat()
        record["window_end"] = record["knowledge_cutoff"]
        record["warnings"] = [
            w
            if isinstance(w, dict)
            else {
                "code": w,
                "message": warning_message(w, parsed_request.language),
                "affected_ids": [],
            }
            for w in partial.get("warnings", [])
        ]
        record["metrics"] = (
            stored_metrics[-1] if stored_metrics else partial.get("metrics", {})
        )
        record["error"] = (
            {
                "code": record["error_code"],
                "message": "Run could not finish.",
                "retryable": record["error_code"]
                in ("PROVIDER_UNAVAILABLE", "RUN_TIMEOUT"),
                "stage": "finished",
            }
            if record["error_code"]
            else None
        )
        if record.get("entity"):
            entity = record["entity"]
            record["entity"] = {
                key: value
                for key, value in entity.items()
                if key
                in {
                    "status",
                    "company_name",
                    "domain",
                    "candidate_companies",
                    "basis_source_ids",
                    "notes",
                }
            }
        record["quality"] = result.get("quality") if result else None
        if result and record["status"] == "completed":
            record["brief"] = canonical_bundle(parsed_request, result, str(run_id))[
                "brief"
            ]
        record["artifacts"] = (
            application.state.store.artifact_names(str(run_id))
            if record["status"] == "completed"
            else []
        )
        if result and record["status"] == "needs_input":
            entity = result.get("entity") or {}
            record["entity"] = {
                "status": entity.get("status"),
                "candidate_companies": entity.get("candidate_companies", []),
            }
        return record

    @application.get("/api/runs/{run_id}/evidence")
    async def get_evidence(run_id: UUID):
        key = str(run_id)
        record = application.state.store.get(key)
        if not record:
            return error(404, "NOT_FOUND", "Run not found.")
        if app_mode != "local" and record["research_mode"] != "replay":
            return error(403, "DEMO_READ_ONLY", "Only approved samples are available.")
        snapshots = application.state.store.ledger(key, "pipeline")
        result = application.state.store.result(key) or (
            snapshots[-1] if snapshots else {}
        )
        return {
            name: result.get(name, [])
            for name in (
                "sources",
                "candidates",
                "reviews",
                "requirement_candidates",
                "requirement_reviews",
                "claims",
                "requirements",
                "rejections",
                "composer_proposals",
                "premise_reviews",
                "search_results",
            )
        }

    @application.get("/api/runs")
    async def list_runs(limit: int = 20):
        if app_mode != "local":
            return error(
                403, "DEMO_READ_ONLY", "Public demo exposes approved samples only."
            )
        try:
            items = application.state.store.list_runs(limit)
        except ValueError:
            return error(422, "VALIDATION_ERROR", "Limit must be between 1 and 50.")
        for item in items:
            result = application.state.store.result(item["run_id"])
            item["quality"] = result.get("quality") if result else None
        return {"items": items, "next_cursor": None}

    @application.get("/api/runs/{run_id}/events")
    async def get_events(run_id: UUID, after: int = 0):
        if after < 0:
            return error(422, "VALIDATION_ERROR", "Event cursor must be nonnegative.")
        record = application.state.store.get(str(run_id))
        if record is None:
            return error(404, "NOT_FOUND", "Run not found.")
        if app_mode != "local" and record["research_mode"] != "replay":
            return error(
                403, "DEMO_READ_ONLY", "Public demo exposes approved samples only."
            )
        items = application.state.store.events(str(run_id), after)
        return {
            "events": items,
            "next_seq": items[-1]["seq"] if items else after,
            "terminal": record["status"]
            in ("completed", "failed", "cancelled", "needs_input"),
        }

    @application.get("/api/runs/{run_id}/brief", response_model=BriefBundle)
    async def get_brief(run_id: UUID):
        key = str(run_id)
        record = application.state.store.get(key)
        if record is None:
            return error(404, "NOT_FOUND", "Run not found.")
        if app_mode != "local" and record["research_mode"] != "replay":
            return error(
                403, "DEMO_READ_ONLY", "Public demo exposes approved samples only."
            )
        result = application.state.store.result(key)
        if record["status"] != "completed" or result is None:
            return error(409, "STATE_CONFLICT", "A completed brief is not available.")
        try:
            return canonical_bundle(application.state.store.request(key), result, key)
        except (ValueError, KeyError, TypeError):
            return error(
                500, "INVALID_BRIEF", "Brief references could not be verified."
            )

    @application.post("/api/runs/{run_id}/cancel")
    async def cancel_run(run_id: UUID):
        if app_mode != "local":
            return error(403, "DEMO_READ_ONLY", "Public demo is read-only.")
        try:
            return {
                "run_id": str(run_id),
                "status": application.state.runner.cancel(str(run_id)),
            }
        except KeyError:
            return error(404, "NOT_FOUND", "Run not found.")
        except Conflict:
            return error(409, "STATE_CONFLICT", "Run is already finished.")

    @application.get("/api/runs/{run_id}/artifacts/{name}")
    async def download_artifact(run_id: UUID, name: str):
        if app_mode != "local":
            record = application.state.store.get(str(run_id))
            if not record or record["research_mode"] != "replay":
                return error(404, "NOT_FOUND", "Artifact is not available.")
        try:
            resolved = application.state.artifacts.resolve(str(run_id), name)
        except (ValueError, OSError):
            resolved = None
        if not resolved:
            return error(404, "NOT_FOUND", "Artifact is not available.")
        path, entry = resolved
        return FileResponse(path, media_type=entry["media_type"], filename=name)

    if (WEB_DIST / "assets").is_dir():
        application.mount(
            "/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets"
        )

    @application.get("/", include_in_schema=False)
    async def frontend():
        if not (WEB_DIST / "index.html").is_file():
            return {"message": "Build the frontend with npm --prefix web run build."}
        return FileResponse(WEB_DIST / "index.html")

    return application


app = create_app()
