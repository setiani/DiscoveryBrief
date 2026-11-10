"""Launch the locally installed official Bifrost launcher without printing credentials."""

import json
import os
import subprocess
import sys
from pathlib import Path

from discoverybrief.config import load_dotenv
from discoverybrief.gateway_config import gateway_config

root = Path(__file__).resolve().parent.parent
os.chdir(root)
load_dotenv(root / ".env")
appdir = root / "data/bifrost"
appdir.mkdir(parents=True, exist_ok=True)
(appdir / "config.json").write_text(
    json.dumps(gateway_config(os.getenv("MODEL_PROVIDER_BASE_URL", "")), indent=2),
    encoding="utf-8",
)
if "--prepare-only" in sys.argv:
    print("Bifrost config prepared without embedding API keys.")
    raise SystemExit(0)
if not os.getenv("MODEL_PROVIDER_API_KEY"):
    raise SystemExit("MODEL_PROVIDER_API_KEY is missing in .env")
launcher = root / "data/bifrost-runtime/node_modules/@maximhq/bifrost/bin.js"
if not launcher.is_file():
    raise SystemExit("Install @maximhq/bifrost@1.6.3 in data/bifrost-runtime first")
subprocess.run(
    [
        "node",
        str(launcher),
        "--transport-version",
        "v1.5.0",
        "-app-dir",
        str(appdir),
        "-host",
        "127.0.0.1",
        "-port",
        "8080",
    ],
    check=True,
)
