import asyncio
from datetime import UTC, datetime

from discoverybrief.clock import FrozenClock
from discoverybrief.runner import RunRunner
from discoverybrief.schemas import RunRequest
from discoverybrief.store import RunStore
from test_contracts import fixture


def test_runner_serializes_and_persists_results(tmp_path):
    async def scenario():
        store = RunStore(tmp_path / "runs.db")
        clock = FrozenClock(datetime(2026, 11, 8, 3, tzinfo=UTC))
        active = 0
        max_active = 0

        async def handler(request, created_at, on_stage, run_id):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0)
            active -= 1
            return {"status": "completed", "quality": "limited"}

        runner = RunRunner(store, clock, handler)
        assert await runner.start() == 0
        data = fixture()
        data["client_request_id"] = None
        request = RunRequest.model_validate(data)
        first, _ = runner.create(request)
        second, _ = runner.create(request)
        for _ in range(100):
            if store.get(second)["status"] == "completed":
                break
            await asyncio.sleep(0.001)
        assert store.result(first)["quality"] == "limited"
        assert store.result(second)["status"] == "completed"
        assert max_active == 1
        await runner.close()
        store.close()

    asyncio.run(scenario())


def test_worker_deadline_also_covers_the_rendering_stage(tmp_path):
    async def scenario():
        store = RunStore(tmp_path / "deadline.db")

        async def handler(request, created_at, on_stage, run_id):
            on_stage("rendering")
            await asyncio.Event().wait()

        runner = RunRunner(
            store,
            FrozenClock(datetime(2026, 11, 8, 3, tzinfo=UTC)),
            handler,
            timeout_seconds=0.03,
        )
        await runner.start()
        run_id, _ = runner.create(RunRequest.model_validate(fixture()))
        for _ in range(200):
            if store.get(run_id)["status"] == "failed":
                break
            await asyncio.sleep(0.005)
        assert store.get(run_id)["error_code"] == "RUN_TIMEOUT"
        await runner.close()
        store.close()

    asyncio.run(scenario())


def test_cancellation_does_not_publish_late_result(tmp_path):
    async def scenario():
        store = RunStore(tmp_path / "cancel.db")
        clock = FrozenClock(datetime(2026, 11, 8, 3, tzinfo=UTC))
        entered = asyncio.Event()

        async def handler(request, created_at, on_stage, run_id):
            entered.set()
            await asyncio.Event().wait()
            return {"status": "completed"}

        runner = RunRunner(store, clock, handler)
        await runner.start()
        run_id, _ = runner.create(RunRequest.model_validate(fixture()))
        await asyncio.wait_for(entered.wait(), timeout=1)
        assert runner.cancel(run_id) == "cancelled"
        await asyncio.sleep(0)
        assert store.get(run_id)["status"] == "cancelled"
        assert store.result(run_id) is None
        await runner.close()
        store.close()

    asyncio.run(scenario())
