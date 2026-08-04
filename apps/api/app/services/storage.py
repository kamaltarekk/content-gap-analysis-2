from __future__ import annotations

from pathlib import Path

from app.core.config import settings


class LocalStorage:
    """Local filesystem storage abstraction.

    Keys are POSIX-style relative paths under a base directory. This is the MVP
    backend for collection snapshots, screenshots, and logs; an S3-compatible
    implementation can satisfy the same surface later.
    """

    def __init__(self, base: Path | str) -> None:
        self.base = Path(base)

    def _path(self, key: str) -> Path:
        target = (self.base / key).resolve()
        base = self.base.resolve()
        # Prevent path traversal outside the storage root.
        if base != target and base not in target.parents:
            raise ValueError(f"Storage key escapes base directory: {key}")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def write_bytes(self, key: str, data: bytes) -> str:
        self._path(key).write_bytes(data)
        return key

    def write_text(self, key: str, text: str) -> str:
        self._path(key).write_text(text, encoding="utf-8")
        return key

    def read_bytes(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def read_text(self, key: str) -> str:
        return self._path(key).read_text(encoding="utf-8")

    def exists(self, key: str) -> bool:
        return (self.base / key).exists()


default_storage = LocalStorage(settings.storage_path)
