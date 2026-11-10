"""Reproduce from a new source copy, new venv and npm install; preserve every attempt."""

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

root = Path(__file__).resolve().parents[1]
stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
destination = root / "data" / f"reproduction-{stamp}"
ignored = {
    ".env",
    ".venv",
    ".git",
    "data",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}
shutil.copytree(
    root,
    destination,
    ignore=lambda directory, names: [
        name for name in names if name in ignored or name.endswith(".egg-info")
    ],
)
env = {
    key: value
    for key, value in os.environ.items()
    if not key.startswith(
        ("MODEL_", "BIFROST_", "TAVILY_", "ENABLE_LIVE_", "DISCOVERYBRIEF_")
    )
    and key
    not in {"APP_DATA_DIR", "VIRTUAL_ENV", "PYTHONPATH", "UV_PROJECT_ENVIRONMENT"}
}
env["UV_CACHE_DIR"] = str(root / "data/uv-reproduction-pristine-cache")
env["RESEARCH_MODE"] = "fixture"
env["APP_DATA_DIR"] = str(destination / "data")
npm = shutil.which("npm.cmd") or shutil.which("npm")
uv = shutil.which("uv")
if not npm or not uv:
    raise SystemExit("uv and npm are required")
commands = [
    [uv, "sync", "--extra", "dev", "--extra", "pdf", "--frozen"],
    [npm, "--prefix", "web", "ci"],
    [npm, "--prefix", "web", "run", "build"],
    [uv, "run", "discoverybrief", "doctor"],
    [
        uv,
        "run",
        "discoverybrief",
        "run",
        "--input",
        "tests/fixtures/request.json",
        "--mode",
        "fixture",
    ],
    [uv, "run", "pytest", "-q"],
    [npm, "--prefix", "web", "run", "test"],
]
records = []
for index, command in enumerate(commands, 1):
    print("Running:", " ".join(command[1:]), flush=True)
    with (destination / f"check-{index:02d}.log").open("w", encoding="utf-8") as log:
        run = subprocess.run(
            command,
            cwd=destination,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    records.append(
        {
            "command": [Path(command[0]).name, *command[1:]],
            "exit_code": run.returncode,
            "log": f"check-{index:02d}.log",
        }
    )
    (destination / "verification.json").write_text(
        json.dumps(
            {
                "source_copy": str(destination),
                "credentials_copied": False,
                "new_venv": True,
                "browser_cache": "existing host Chromium cache reused",
                "checks": records,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if run.returncode:
        raise SystemExit(
            f"Check {index} failed; see {destination}/check-{index:02d}.log"
        )
print("Clean-source verification passed:", destination, flush=True)
