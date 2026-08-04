from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.core.config import settings


class Storage(Protocol):
    """Storage surface shared by the local and S3-compatible backends."""

    def write_bytes(self, key: str, data: bytes) -> str: ...
    def write_text(self, key: str, text: str) -> str: ...
    def read_bytes(self, key: str) -> bytes: ...
    def read_text(self, key: str) -> str: ...
    def exists(self, key: str) -> bool: ...


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


class S3Storage:
    """S3-compatible object storage. boto3 is imported lazily so it is only a
    production dependency; the local MVP never imports it.
    """

    def __init__(
        self,
        bucket: str,
        *,
        prefix: str = "",
        endpoint_url: str | None = None,
        region: str | None = None,
    ) -> None:
        import boto3  # lazy: only needed when the S3 backend is selected

        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self._client = boto3.client("s3", endpoint_url=endpoint_url, region_name=region)

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}/{key}" if self.prefix else key

    def write_bytes(self, key: str, data: bytes) -> str:
        self._client.put_object(Bucket=self.bucket, Key=self._full_key(key), Body=data)
        return key

    def write_text(self, key: str, text: str) -> str:
        return self.write_bytes(key, text.encode("utf-8"))

    def read_bytes(self, key: str) -> bytes:
        obj = self._client.get_object(Bucket=self.bucket, Key=self._full_key(key))
        return obj["Body"].read()

    def read_text(self, key: str) -> str:
        return self.read_bytes(key).decode("utf-8")

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self.bucket, Key=self._full_key(key))
            return True
        except ClientError:
            return False


def get_storage() -> Storage:
    if settings.storage_backend == "s3":
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required when STORAGE_BACKEND=s3")
        return S3Storage(
            settings.s3_bucket,
            prefix=settings.s3_prefix,
            endpoint_url=settings.s3_endpoint_url,
            region=settings.s3_region,
        )
    return LocalStorage(settings.storage_path)


default_storage: Storage = get_storage()
