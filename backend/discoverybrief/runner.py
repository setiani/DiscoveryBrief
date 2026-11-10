"""Single-process bounded runner; unfinished work is never resumed automatically."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from time import monotonic

import httpx

from discoverybrief.clock import Clock
from discoverybrief.schemas import RunRequest
from discoverybrief.store import Conflict, RunStore

Handler = Callable[[RunRequest, object, Callable[[str], None], str], Awaitable[dict]]
logger = logging.getLogger("discoverybrief.runner")


class RunRunner:
    def __init__(
        self,
        store: RunStore,
        clock: Clock,
        handler: Handler,
        timeout_seconds: float = 300,
    ):
        if not 0 < timeout_seconds <= 300:
            raise ValueError("worker timeout must be between zero and 300 seconds")
        self.timeout_seconds = timeout_seconds
        self.store, self.clock, self.handler = store, clock, handler
        self._worker: asyncio.Task | None = None
        self._active: asyncio.Task | None = None
        self._active_id: str | None = None
        self._wake = asyncio.Event()

    async def start(self) -> int:
        if self._worker:
            raise RuntimeError("runner already started")
        interrupted = self.store.interrupt_unfinished(self.clock.now())
        self._worker = asyncio.create_task(self._run())
        return interrupted

    def create(
        self, request: RunRequest, research_mode: str = "fixture"
    ) -> tuple[str, bool]:
        if self._worker is None:
            raise RuntimeError("runner not started")
        result = self.store.create(request, self.clock.now(), research_mode)
        self._wake.set()
        return result

    def cancel(self, run_id: str) -> str:
        status = self.store.cancel(run_id, self.clock.now())
        if self._active_id == run_id and self._active:
            self._active.cancel()
        return status

    async def close(self) -> None:
        if self._active:
            self._active.cancel()
        if self._worker:
            self._worker.cancel()
            try:
                await self._worker
            except asyncio.CancelledError:
                pass
        self._worker = None

    async def _run(self) -> None:
        while True:
            self._wake.clear()
            claimed = self.store.claim_next(self.clock.now())
            if claimed is None:
                await self._wake.wait()
                continue
            run_id, request, created_at = claimed
            self._active_id = run_id
            started = monotonic()

            def on_stage(stage: str, current_run_id: str = run_id) -> None:
                self.store.update_stage(current_run_id, stage, self.clock.now())

            self._active = asyncio.create_task(
                asyncio.wait_for(
                    self.handler(request, created_at, on_stage, run_id),
                    timeout=self.timeout_seconds,
                )
            )
            try:
                result = await self._active
                status = result.get("status")
                if status not in ("completed", "needs_input"):
                    raise ValueError("invalid pipeline outcome")
                result.setdefault("metrics", {})["duration_ms"] = round(
                    (monotonic() - started) * 1000
                )
                self.store.finish(run_id, status, self.clock.now(), result=result)
            except asyncio.CancelledError:
                if asyncio.current_task().cancelling():
                    raise
            except Conflict:
                # A concurrent cancellation wins over a late completion.
                pass
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Run %s provider returned HTTP %s", run_id, exc.response.status_code
                )
                try:
                    self.store.finish(
                        run_id,
                        "failed",
                        self.clock.now(),
                        error_code="PROVIDER_UNAVAILABLE",
                    )
                except Conflict:
                    pass
            except httpx.HTTPError as exc:
                logger.warning("Run %s provider failed: %s", run_id, type(exc).__name__)
                try:
                    self.store.finish(
                        run_id,
                        "failed",
                        self.clock.now(),
                        error_code="PROVIDER_UNAVAILABLE",
                    )
                except Conflict:
                    pass
            except (ValueError, RuntimeError) as exc:
                logger.warning("Run %s failed: %s", run_id, type(exc).__name__)
                try:
                    self.store.finish(
                        run_id,
                        "failed",
                        self.clock.now(),
                        error_code=(
                            str(exc)
                            if str(exc) in {"BUDGET_LIMIT", "RUN_TIMEOUT"}
                            else "INVALID_MODEL_OUTPUT"
                        ),
                    )
                except Conflict:
                    pass
            except TimeoutError:
                try:
                    self.store.finish(
                        run_id, "failed", self.clock.now(), error_code="RUN_TIMEOUT"
                    )
                except Conflict:
                    pass
            except Exception as exc:  # noqa: BLE001 -- worker boundary must preserve a safe terminal state
                logger.warning("Run %s failed: %s", run_id, type(exc).__name__)
                try:
                    self.store.finish(
                        run_id, "failed", self.clock.now(), error_code="INTERNAL_ERROR"
                    )
                except Conflict:
                    pass
            finally:
                duration = round((monotonic() - started) * 1000)
                current = self.store.ledger(run_id, "metrics")
                snapshot = self.store.ledger(run_id, "pipeline")
                saved = (
                    current[-1]
                    if current
                    else (snapshot[-1].get("metrics", {}) if snapshot else {})
                )
                self.store.checkpoint(
                    run_id, "metrics", "current", {**saved, "duration_ms": duration}
                )
                self._active = None
                self._active_id = None
