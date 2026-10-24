"""
Dropbox cloud provider for backup upload, list, download, and delete.

Uses the Dropbox HTTP API via stdlib ``urllib`` (no ``dropbox`` SDK) so the
optional ``[cloud]`` extra stays compatible with Python 3.10+.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
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

DEFAULT_DROPBOX_FOLDER = "/TMAS/backups"
API_RPC_URL = "https://api.dropboxapi.com/2"
API_CONTENT_URL = "https://content.dropboxapi.com/2"
# Dropbox simple upload limit is 150 MiB; backup packages are expected below this.
MAX_SIMPLE_UPLOAD_BYTES = 150 * 1024 * 1024


class DropboxError(Exception):
    """Raised when Dropbox operations fail."""


class DropboxProvider(CloudProvider):
    """Dropbox implementation of ``CloudProvider`` (Bearer access token)."""

    def __init__(self, client: Optional[Any] = None) -> None:
        """
        ``client`` is an optional callable ``(method, url, *, headers, data) -> dict|bytes``
        used by unit tests. Production code builds HTTP requests via ``_http_request``.
        """
        self.logger = get_logger()
        self._client = client
        self._verified = client is not None

    @property
    def provider_name(self) -> str:
        return "Dropbox"

    @staticmethod
    def is_configured() -> bool:
        """Return True when a Dropbox access token is present."""
        settings = get_settings()
        return bool((settings.dropbox_access_token or "").strip())

    def authenticate(self) -> bool:
        """Validate the access token with ``users/get_current_account``."""
        if not self.is_configured():
            raise DropboxError(
                "Dropbox access token is required. Set DROPBOX_ACCESS_TOKEN in .env "
                "(optional: DROPBOX_FOLDER). Create an app at "
                "https://www.dropbox.com/developers/apps and generate a token."
            )

        try:
            self._rpc("users/get_current_account", None)
        except DropboxError:
            raise
        except Exception as exc:
            raise _map_dropbox_exception(exc, operation="authentication") from exc

        self._verified = True
        self.logger.info("Dropbox authentication successful")
        return True

    def is_authenticated(self) -> bool:
        """Return True when the configured token verifies against Dropbox."""
        if self._verified and self._client is not None:
            return True
        if self._verified and self.is_configured():
            return True
        if not self.is_configured():
            return False
        try:
            return self.authenticate()
        except DropboxError:
            return False

    def upload(self, local_path: Path, remote_name: str) -> str:
        """Upload a backup package; return the Dropbox path as remote id."""
        self._require_authenticated()
        local_path = Path(local_path)
        remote_path = self._object_path(remote_name)
        size = local_path.stat().st_size
        if size > MAX_SIMPLE_UPLOAD_BYTES:
            raise DropboxError(
                f"Backup package is too large for Dropbox simple upload "
                f"({size} bytes; limit {MAX_SIMPLE_UPLOAD_BYTES})"
            )

        data = local_path.read_bytes()
        api_arg = {
            "path": remote_path,
            "mode": "overwrite",
            "autorename": False,
            "mute": True,
            "strict_conflict": False,
        }
        try:
            result = self._content(
                "files/upload",
                api_arg=api_arg,
                body=data,
                content_type="application/octet-stream",
            )
        except Exception as exc:
            raise _map_dropbox_exception(exc, operation="backup upload") from exc

        path = str(result.get("path_display") or result.get("path_lower") or remote_path)
        self.logger.info(f"Uploaded backup to Dropbox: {path}")
        return path

    def download(self, remote_id: str, local_path: Path) -> Path:
        """Download a remote Dropbox path to ``local_path``."""
        self._require_authenticated()
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            payload = self._content(
                "files/download",
                api_arg={"path": remote_id},
                body=b"",
                content_type=None,
                expect_json=False,
            )
        except Exception as exc:
            raise _map_dropbox_exception(exc, operation="backup download") from exc

        if not isinstance(payload, (bytes, bytearray)):
            raise DropboxError("Dropbox download returned unexpected payload")
        local_path.write_bytes(bytes(payload))
        self.logger.info(f"Downloaded Dropbox backup {remote_id} to {local_path}")
        return local_path

    def list_backups(self) -> List[RemoteBackupItem]:
        """List ``.tmas-backup.zip`` files under the configured Dropbox folder."""
        self._require_authenticated()
        folder = _normalize_folder(get_settings().dropbox_folder)
        items: List[RemoteBackupItem] = []

        try:
            result = self._rpc(
                "files/list_folder",
                {
                    "path": folder,
                    "recursive": False,
                    "include_media_info": False,
                    "include_deleted": False,
                    "include_has_explicit_shared_members": False,
                },
            )
            entries = list(result.get("entries") or [])
            cursor = result.get("cursor")
            while result.get("has_more"):
                result = self._rpc("files/list_folder/continue", {"cursor": cursor})
                entries.extend(result.get("entries") or [])
                cursor = result.get("cursor")
        except DropboxError as exc:
            # Empty folder / path not found → treat as no backups yet.
            if "path/not_found" in str(exc).lower() or "not_found" in str(exc).lower():
                return []
            raise
        except Exception as exc:
            raise _map_dropbox_exception(exc, operation="listing backups") from exc

        for entry in entries:
            if str(entry.get(".tag") or "") != "file":
                continue
            name = str(entry.get("name") or "")
            if not name.endswith(BACKUP_FILE_EXTENSION):
                continue
            path = str(
                entry.get("path_display") or entry.get("path_lower") or f"{folder}/{name}"
            )
            items.append(
                RemoteBackupItem(
                    remote_id=path,
                    name=name,
                    size_bytes=int(entry.get("size") or 0),
                    created_at=_parse_dropbox_timestamp(
                        entry.get("server_modified") or entry.get("client_modified")
                    ),
                )
            )

        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def delete(self, remote_id: str) -> bool:
        """Delete a remote backup path."""
        self._require_authenticated()
        try:
            self._rpc("files/delete_v2", {"path": remote_id})
        except Exception as exc:
            raise _map_dropbox_exception(exc, operation="deleting backup") from exc
        self.logger.info(f"Deleted Dropbox backup {remote_id}")
        return True

    def disconnect(self) -> None:
        """Clear in-memory auth state (``.env`` token is unchanged)."""
        self._verified = False

    def _object_path(self, remote_name: str) -> str:
        folder = _normalize_folder(get_settings().dropbox_folder)
        name = Path(remote_name).name
        return f"{folder}/{name}"

    def _require_authenticated(self) -> None:
        if not self.is_authenticated():
            raise DropboxError("Dropbox is not authenticated")

    def _rpc(self, endpoint: str, body: Optional[dict[str, Any]]) -> dict[str, Any]:
        url = f"{API_RPC_URL}/{endpoint}"
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {_access_token()}",
            "Content-Type": "application/json",
        }
        if body is None:
            # get_current_account expects an empty body with no Content-Type quirks.
            headers.pop("Content-Type", None)
            data = b""
        result = self._dispatch("POST", url, headers=headers, data=data)
        if not isinstance(result, dict):
            raise DropboxError(f"Dropbox RPC {endpoint} returned unexpected payload")
        return result

    def _content(
        self,
        endpoint: str,
        *,
        api_arg: dict[str, Any],
        body: bytes,
        content_type: Optional[str],
        expect_json: bool = True,
    ) -> Any:
        url = f"{API_CONTENT_URL}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {_access_token()}",
            "Dropbox-API-Arg": json.dumps(api_arg, separators=(",", ":")),
        }
        if content_type:
            headers["Content-Type"] = content_type
        result = self._dispatch(
            "POST",
            url,
            headers=headers,
            data=body,
            expect_json=expect_json,
        )
        return result

    def _dispatch(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        data: Optional[bytes],
        expect_json: bool = True,
    ) -> Any:
        if self._client is not None:
            return self._client(
                method, url, headers=headers, data=data, expect_json=expect_json
            )
        return _http_request(
            method, url, headers=headers, data=data, expect_json=expect_json
        )


def _access_token() -> str:
    token = (get_settings().dropbox_access_token or "").strip()
    if not token:
        raise DropboxError("DROPBOX_ACCESS_TOKEN is not set")
    return token


def _normalize_folder(folder: Optional[str]) -> str:
    text = (folder or DEFAULT_DROPBOX_FOLDER).strip() or DEFAULT_DROPBOX_FOLDER
    if not text.startswith("/"):
        text = f"/{text}"
    return text.rstrip("/") or DEFAULT_DROPBOX_FOLDER


def _parse_dropbox_timestamp(value: Any) -> datetime:
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


def _http_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    data: Optional[bytes],
    expect_json: bool = True,
) -> Any:
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        detail = _read_http_error(exc)
        raise DropboxError(detail) from exc
    except Exception as exc:
        raise _map_dropbox_exception(exc, operation="HTTP request") from exc

    if not expect_json:
        return payload
    if not payload:
        return {}
    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise DropboxError("Dropbox returned invalid JSON") from exc


def _read_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    summary = body.strip() or exc.reason or str(exc)
    try:
        parsed = json.loads(body)
        error = parsed.get("error_summary") or parsed.get("error") or summary
        if isinstance(error, dict):
            error = error.get(".tag") or str(error)
        return f"HTTP {exc.code}: {error}"
    except (json.JSONDecodeError, TypeError, AttributeError):
        return f"HTTP {exc.code}: {summary}"


def _map_dropbox_exception(exc: BaseException, *, operation: str) -> DropboxError:
    """Map low-level network/API failures to clear DropboxError messages."""
    if isinstance(exc, DropboxError):
        return exc
    if is_network_exception(exc):
        return DropboxError(format_offline_error(operation))
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
            "internal_error",
            "internal error",
        )
    ):
        return DropboxError(
            format_drive_unavailable_error(detail)
            .replace("Google Drive", "Dropbox")
            .replace("googleapis.com", "api.dropboxapi.com")
        )
    return DropboxError(f"Dropbox {operation} failed: {detail}")
