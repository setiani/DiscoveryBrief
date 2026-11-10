"""Manifest-only artifacts with atomic writes and workspace path checks."""

import hashlib
import os
import tempfile
from pathlib import Path
from uuid import UUID

from discoverybrief.store import RunStore

MEDIA_TYPES = {
    "brief.json": "application/json",
    "brief.md": "text/markdown; charset=utf-8",
    "brief.html": "text/html; charset=utf-8",
    "brief.pdf": "application/pdf",
    "evidence.json": "application/json",
    "trace.json": "application/json",
}


class ArtifactStore:
    def __init__(self, root: Path, store: RunStore):
        self.root = root.resolve()
        self.store = store

    def _path(self, run_id: str, name: str) -> Path:
        canonical = str(UUID(run_id))
        if canonical != run_id or name not in MEDIA_TYPES:
            raise ValueError("invalid artifact identifier")
        path = self.root / "runs" / canonical / "artifacts" / name
        if not path.resolve().is_relative_to(self.root):
            raise ValueError("artifact path escapes data directory")
        return path

    def write(self, run_id: str, name: str, content: bytes) -> None:
        path = self._path(run_id, name)
        if self.store.artifact(run_id, name) is not None:
            raise ValueError("artifact already exists")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.resolve().is_relative_to(self.root):
            raise ValueError("artifact path escapes data directory")
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=path.parent, prefix=".pending-", delete=False
            ) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            self.store.save_artifact(
                run_id,
                name,
                path.relative_to(self.root).as_posix(),
                hashlib.sha256(content).hexdigest(),
                len(content),
                MEDIA_TYPES[name],
            )
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)

    def resolve(self, run_id: str, name: str) -> tuple[Path, dict] | None:
        path = self._path(run_id, name)
        entry = self.store.artifact(run_id, name)
        if not entry or self.store.get(run_id)["status"] != "completed":
            return None
        if (
            entry["relative_path"] != path.relative_to(self.root).as_posix()
            or not path.is_file()
        ):
            return None
        content = path.read_bytes()
        if (
            len(content) != entry["size_bytes"]
            or hashlib.sha256(content).hexdigest() != entry["sha256"]
        ):
            return None
        return path, entry
