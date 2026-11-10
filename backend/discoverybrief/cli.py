import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Annotated

import typer

from discoverybrief.config import Settings
from discoverybrief.fixture import FIXTURES
from discoverybrief.schemas import RunRequest

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """DiscoveryBrief development and evaluation commands."""


@app.command()
def doctor(live: bool = False) -> None:
    """Check local configuration without making network calls."""
    settings = Settings.load()
    typer.echo(f"mode: {settings.mode}; research: {settings.research_mode}")
    typer.echo(f"Tavily key configured: {bool(settings.tavily_api_key)}")
    typer.echo(f"Bifrost model configured: {bool(settings.model_primary)}")
    typer.echo(
        f"Model provider key configured: {bool(settings.model_provider_api_key)}"
    )
    if not live:
        typer.echo("No network calls were made.")
        return
    if not settings.enable_live_tests:
        raise typer.BadParameter("Set ENABLE_LIVE_TESTS=1 for paid connectivity checks")
    from discoverybrief.clients import BifrostClient, CallBudget

    async def check():
        budget = CallBudget()
        response = await BifrostClient(
            settings.bifrost_base_url,
            settings.model_primary,
            budget,
            settings.bifrost_virtual_key,
            fallback_model=settings.model_fallback,
        ).complete([{"role": "user", "content": "Reply with OK."}], 16)
        if not response.get("choices"):
            raise RuntimeError("invalid model response")
        typer.echo("Bifrost model connectivity passed; no private context was sent.")

    asyncio.run(check())


@app.command()
def run(
    input: Annotated[Path, typer.Option("--input", exists=True)], mode: str = "fixture"
) -> None:
    """Run the same persisted, bounded workflow used by the API."""
    if mode not in {"fixture", "live"}:
        raise typer.BadParameter("Choose fixture or live")
    request = RunRequest.model_validate_json(input.read_text(encoding="utf-8"))
    expected = RunRequest.model_validate_json(
        (FIXTURES / "request.json").read_text(encoding="utf-8")
    )
    if mode == "fixture" and request.model_dump(
        exclude={"client_request_id"}
    ) != expected.model_dump(exclude={"client_request_id"}):
        raise typer.BadParameter(
            "Only the canonical synthetic input is supported; no arbitrary brief is generated"
        )
    settings = Settings.load()
    if mode == "live" and not settings.enable_live_tests:
        raise typer.BadParameter("Set ENABLE_LIVE_TESTS=1 for paid live execution")
    from fastapi.testclient import TestClient

    from discoverybrief.api.main import create_app

    with TestClient(
        create_app(mode="local", research_mode=mode, allow_live=mode == "live")
    ) as client:
        created = client.post("/api/runs", json=request.model_dump(mode="json"))
        if created.status_code not in {200, 202}:
            raise typer.BadParameter(created.json()["error"]["message"])
        run_id = created.json()["run_id"]
        deadline = time.monotonic() + 310
        while time.monotonic() < deadline:
            record = client.get(f"/api/runs/{run_id}").json()
            if record["status"] in {"completed", "failed", "needs_input", "cancelled"}:
                if record["status"] != "completed":
                    typer.echo(json.dumps(record, ensure_ascii=False))
                    raise typer.Exit(1)
                typer.echo(
                    json.dumps(
                        client.get(f"/api/runs/{run_id}/brief").json(),
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return
            time.sleep(0.1)
        raise typer.BadParameter("Run timed out")


@app.command()
def evaluate(dataset: Path = Path("eval/dataset.json"), mode: str = "fixture") -> None:
    """Validate fixed cases offline, or run explicitly enabled frozen-model evaluation."""
    if mode == "frozen_research":
        root = Path(__file__).resolve().parents[2]
        completed = subprocess.run(
            [
                sys.executable,
                str(root / "scripts/evaluate_frozen.py"),
                "--dataset",
                str(dataset.resolve()),
            ],
            check=False,
        )
        raise typer.Exit(completed.returncode)
    if mode != "fixture":
        raise typer.BadParameter("Choose fixture or frozen_research")
    from discoverybrief.frozen_research import FrozenResearch

    index = json.loads(dataset.read_text(encoding="utf-8"))
    for case in index["cases"]:
        directory = dataset.parent / "fixtures" / case["case_id"]
        RunRequest.model_validate_json(
            (directory / "request.json").read_text(encoding="utf-8")
        )
        FrozenResearch(
            json.loads((directory / "research.json").read_text(encoding="utf-8"))
        )
    typer.echo(
        json.dumps(
            {
                "mode": "fixture",
                "validated_cases": len(index["cases"]),
                "quality_evaluation": "not_run",
                "external_calls": 0,
            }
        )
    )


@app.command("build-demo")
def build_demo(
    run: Annotated[str, typer.Option("--run")],
    output: Annotated[Path, typer.Option("--output")],
) -> None:
    """Export a completed repository-controlled synthetic run, never private live data."""
    from discoverybrief.store import RunStore

    store = RunStore(Settings.load().data_dir / "runs.db")
    try:
        record = store.get(run)
        result = store.result(run)
        if (
            not record
            or record["status"] != "completed"
            or not result
            or result.get("research_mode") not in {"fixture", "replay"}
        ):
            raise typer.BadParameter(
                "Only completed synthetic fixture/replay runs can be exported"
            )
        actual = store.request(run).model_dump(exclude={"client_request_id"})
        expected = RunRequest.model_validate_json(
            (FIXTURES / "request.json").read_text(encoding="utf-8")
        ).model_dump(exclude={"client_request_id"})
        if actual != expected:
            raise typer.BadParameter(
                "Input is not the approved canonical synthetic request"
            )
        result["synthetic"] = True
        if output.exists():
            raise typer.BadParameter(
                "Output exists; choose a new path to preserve prior artifacts"
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        typer.echo(f"Synthetic sample exported: {output}")
    finally:
        store.close()
