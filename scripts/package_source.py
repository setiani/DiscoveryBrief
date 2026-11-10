"""Build a local review archive from authored files, excluding keys and runtime state."""

import hashlib
import os
import zipfile
from pathlib import Path

from discoverybrief.config import Settings

root = Path(__file__).resolve().parents[1]
Settings.load()  # Credentials are only used as in-memory leak canaries, never printed.
secrets = [
    value.encode()
    for key, value in os.environ.items()
    if any(part in key for part in ("API_KEY", "VIRTUAL_KEY", "SECRET"))
    and len(value) >= 12
]
excluded = {
    "data",
    ".env",
    ".venv",
    ".git",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}
files = []
for directory, folders, names in os.walk(root):
    folders[:] = [
        name
        for name in folders
        if name not in excluded and not name.endswith(".egg-info")
    ]
    for name in names:
        path = Path(directory) / name
        if (
            name in excluded
            or name.startswith("~$")
            or path.suffix in {".zip", ".sha256", ".pyc"}
        ):
            continue
        content = path.read_bytes()
        if any(secret in content for secret in secrets):
            raise SystemExit(
                "Credential detected in source package; export blocked without printing the value"
            )
        files.append(path)
destination = root / "submission/DiscoveryBrief-source-review.zip"
with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):
        archive.write(path, Path("discoverybrief") / path.relative_to(root))
digest = hashlib.sha256(destination.read_bytes()).hexdigest()
destination.with_suffix(".zip.sha256").write_text(
    digest + "  " + destination.name + "\n", encoding="utf-8"
)
print(
    f"Review archive: {destination}; {len(files)} authored artifacts; SHA256 {digest}"
)
