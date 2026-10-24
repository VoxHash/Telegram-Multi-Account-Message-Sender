"""
S3-compatible cloud provider for backup upload, list, download, and delete.

Works with Amazon S3 and compatible endpoints (MinIO, Cloudflare R2, Wasabi,
Backblaze B2 S3 API, etc.) via optional ``boto3``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

from app.services import get_logger
from app.services.settings import get_settings

from .backup_package import BACKUP_FILE_EXTENSION
from .network import (
    format_drive_unavailable_error,
    format_offline_error,
    is_network_exception,
)
from .provider_base import CloudProvider, RemoteBackupItem

DEFAULT_S3_PREFIX = "tmas/backups/"
DEFAULT_S3_REGION = "us-east-1"


class S3CompatibleError(Exception):
    """Raised when S3-compatible storage operations fail."""


class S3CompatibleProvider(CloudProvider):
    """S3 / S3-compatible implementation of ``CloudProvider``."""

    def __init__(self, client: Optional[Any] = None) -> None:
        self.logger = get_logger()
        self._client = client
        self._verified = client is not None

    @property
    def provider_name(self) -> str:
        return "S3-Compatible"

    @staticmethod
    def is_configured() -> bool:
        """Return True when required S3 settings are present."""
        settings = get_settings()
        return bool(
            settings.s3_access_key_id
            and settings.s3_secret_access_key
            and settings.s3_bucket
        )

    def authenticate(self) -> bool:
        """Validate credentials by calling ``head_bucket`` on the configured bucket."""
        if not self.is_configured():
            raise S3CompatibleError(
                "S3 credentials are required. Set S3_ACCESS_KEY_ID, "
                "S3_SECRET_ACCESS_KEY, and S3_BUCKET in .env "
                "(optional: S3_ENDPOINT_URL, S3_REGION, S3_PREFIX)"
            )

        client = self._require_or_build_client()
        settings = get_settings()
        try:
            client.head_bucket(Bucket=settings.s3_bucket)
        except Exception as exc:
            raise _map_s3_exception(exc, operation="authentication") from exc

        self._verified = True
        self.logger.info(
            f"S3 authentication successful (bucket={settings.s3_bucket})"
        )
        return True

    def is_authenticated(self) -> bool:
        """Return True when credentials verify against the configured bucket."""
        if self._verified and self._client is not None:
            return True
        if not self.is_configured():
            return False
        try:
            return self.authenticate()
        except S3CompatibleError:
            return False

    def upload(self, local_path: Path, remote_name: str) -> str:
        """Upload a backup package; return the object key as remote id."""
        client = self._require_client()
        settings = get_settings()
        key = self._object_key(remote_name)
        try:
            client.upload_file(str(local_path), settings.s3_bucket, key)
        except Exception as exc:
            raise _map_s3_exception(exc, operation="backup upload") from exc

        self.logger.info(f"Uploaded backup to S3: {key}")
        return key

    def download(self, remote_id: str, local_path: Path) -> Path:
        """Download a remote object key to ``local_path``."""
        client = self._require_client()
        settings = get_settings()
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            client.download_file(settings.s3_bucket, remote_id, str(local_path))
        except Exception as exc:
            raise _map_s3_exception(exc, operation="backup download") from exc

        self.logger.info(f"Downloaded S3 backup {remote_id} to {local_path}")
        return local_path

    def list_backups(self) -> List[RemoteBackupItem]:
        """List ``.tmas-backup.zip`` objects under the configured prefix."""
        client = self._require_client()
        settings = get_settings()
        prefix = _normalize_prefix(settings.s3_prefix)
        items: List[RemoteBackupItem] = []

        try:
            paginator = client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=settings.s3_bucket, Prefix=prefix):
                for obj in page.get("Contents") or []:
                    key = str(obj.get("Key") or "")
                    if not key.endswith(BACKUP_FILE_EXTENSION):
                        continue
                    items.append(
                        RemoteBackupItem(
                            remote_id=key,
                            name=Path(key).name,
                            size_bytes=int(obj.get("Size") or 0),
                            created_at=_parse_s3_timestamp(obj.get("LastModified")),
                        )
                    )
        except Exception as exc:
            raise _map_s3_exception(exc, operation="listing backups") from exc

        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def delete(self, remote_id: str) -> bool:
        """Delete a remote backup object."""
        client = self._require_client()
        settings = get_settings()
        try:
            client.delete_object(Bucket=settings.s3_bucket, Key=remote_id)
        except Exception as exc:
            raise _map_s3_exception(exc, operation="deleting backup") from exc
        self.logger.info(f"Deleted S3 backup {remote_id}")
        return True

    def disconnect(self) -> None:
        """Clear the in-memory client (env credentials are unchanged)."""
        self._client = None
        self._verified = False

    def _object_key(self, remote_name: str) -> str:
        settings = get_settings()
        prefix = _normalize_prefix(settings.s3_prefix)
        name = Path(remote_name).name
        return f"{prefix}{name}"

    def _require_client(self) -> Any:
        if self._client is None:
            if not self.is_authenticated():
                raise S3CompatibleError("S3 is not authenticated")
        if self._client is None:
            raise S3CompatibleError("S3 is not authenticated")
        return self._client

    def _require_or_build_client(self) -> Any:
        if self._client is not None:
            return self._client
        self._client = _build_s3_client()
        return self._client


def _normalize_prefix(prefix: Optional[str]) -> str:
    text = (prefix or DEFAULT_S3_PREFIX).strip().lstrip("/")
    if not text:
        text = DEFAULT_S3_PREFIX
    if not text.endswith("/"):
        text = f"{text}/"
    return text


def _parse_s3_timestamp(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _build_s3_client() -> Any:
    boto3, Config = _import_boto_deps()
    settings = get_settings()
    region = (settings.s3_region or DEFAULT_S3_REGION).strip() or DEFAULT_S3_REGION
    endpoint = (settings.s3_endpoint_url or "").strip() or None

    client_kwargs: dict[str, Any] = {
        "service_name": "s3",
        "aws_access_key_id": settings.s3_access_key_id,
        "aws_secret_access_key": settings.s3_secret_access_key,
        "region_name": region,
    }
    if endpoint:
        client_kwargs["endpoint_url"] = endpoint
        client_kwargs["config"] = Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        )
    else:
        client_kwargs["config"] = Config(signature_version="s3v4")

    return boto3.client(**client_kwargs)


def _import_boto_deps() -> tuple[Any, Any]:
    try:
        import boto3
        from botocore.config import Config
    except ImportError as exc:
        raise S3CompatibleError(
            "S3 support requires optional dependencies. "
            "Install with: pip install 'telegram-multi-account-sender[cloud]'"
        ) from exc
    return boto3, Config


def _map_s3_exception(exc: BaseException, *, operation: str) -> S3CompatibleError:
    """Map low-level network/API failures to clear S3CompatibleError messages."""
    if isinstance(exc, S3CompatibleError):
        return exc
    if is_network_exception(exc):
        return S3CompatibleError(format_offline_error(operation))
    detail = str(exc).strip() or exc.__class__.__name__
    lowered = detail.lower()
    if any(
        token in lowered
        for token in (
            "503",
            "500",
            "502",
            "504",
            "slowdown",
            "service unavailable",
            "internal error",
        )
    ):
        # Reuse Drive marker so GUI offline UX still triggers for provider outages.
        return S3CompatibleError(
            format_drive_unavailable_error(detail).replace(
                "Google Drive", "S3-compatible storage"
            ).replace("googleapis.com", "your S3 endpoint")
        )
    return S3CompatibleError(f"S3 {operation} failed: {detail}")
