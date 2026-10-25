"""
OneDrive cloud provider for backup upload, list, download, and delete.

Uses the Microsoft Graph HTTP API via stdlib ``urllib`` (no ``msgraph`` /
``onedrivesdk``) so the optional ``[cloud]`` extra stays compatible with
Python 3.10+.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
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

DEFAULT_ONEDRIVE_FOLDER = "TMAS/backups"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
# Graph simple upload supports up to 250 MiB; backup packages are expected below this.
MAX_SIMPLE_UPLOAD_BYTES = 250 * 1024 * 1024


class OneDriveError(Exception):
    """Raised when OneDrive / Microsoft Graph operations fail."""


class OneDriveProvider(CloudProvider):
    """OneDrive implementation of ``CloudProvider`` (Microsoft Graph Bearer token)."""

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
        return "OneDrive"

    @staticmethod
    def is_configured() -> bool:
        """Return True when a Microsoft Graph access token is present."""
        settings = get_settings()
        return bool((settings.onedrive_access_token or "").strip())

    def authenticate(self) -> bool:
        """Validate the access token with ``GET /me/drive``."""
        if not self.is_configured():
            raise OneDriveError(
                "OneDrive access token is required. Set ONEDRIVE_ACCESS_TOKEN in .env "
                "(optional: ONEDRIVE_FOLDER, default TMAS/backups). Register an app at "
                "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade "
                "with Microsoft Graph delegated permission Files.ReadWrite, then obtain a "
                "user access token."
            )

        try:
            self._api("GET", f"{GRAPH_BASE}/me/drive")
        except OneDriveError:
            raise
        except Exception as exc:
            raise _map_onedrive_exception(exc, operation="authentication") from exc

        self._verified = True
        self.logger.info("OneDrive authentication successful")
        return True

    def is_authenticated(self) -> bool:
        """Return True when the configured token verifies against Microsoft Graph."""
        if self._verified and self._client is not None:
            return True
        if self._verified and self.is_configured():
            return True
        if not self.is_configured():
            return False
        try:
            return self.authenticate()
        except OneDriveError:
            return False

    def upload(self, local_path: Path, remote_name: str) -> str:
        """Upload a backup package; return the Graph drive item id as remote id."""
        self._require_authenticated()
        local_path = Path(local_path)
        size = local_path.stat().st_size
        if size > MAX_SIMPLE_UPLOAD_BYTES:
            raise OneDriveError(
                f"Backup package is too large for OneDrive simple upload "
                f"({size} bytes; limit {MAX_SIMPLE_UPLOAD_BYTES})"
            )

        folder = _normalize_folder(get_settings().onedrive_folder)
        self._ensure_folder(folder)
        name = Path(remote_name).name
        object_path = f"{folder}/{name}"
        data = local_path.read_bytes()
        url = (
            f"{GRAPH_BASE}/me/drive/root:/{_encode_path(object_path)}:/content"
        )
        try:
            result = self._api(
                "PUT",
                url,
                data=data,
                content_type="application/octet-stream",
            )
        except Exception as exc:
            raise _map_onedrive_exception(exc, operation="backup upload") from exc

        if not isinstance(result, dict):
            raise OneDriveError("OneDrive upload returned unexpected payload")
        item_id = str(result.get("id") or "")
        if not item_id:
            raise OneDriveError("OneDrive upload did not return an item id")
        self.logger.info(f"Uploaded backup to OneDrive: {object_path} ({item_id})")
        return item_id

    def download(self, remote_id: str, local_path: Path) -> Path:
        """Download a remote Graph drive item to ``local_path``."""
        self._require_authenticated()
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"{GRAPH_BASE}/me/drive/items/{urllib.parse.quote(remote_id, safe='')}/content"
        try:
            payload = self._api("GET", url, expect_json=False)
        except Exception as exc:
            raise _map_onedrive_exception(exc, operation="backup download") from exc

        if not isinstance(payload, (bytes, bytearray)):
            raise OneDriveError("OneDrive download returned unexpected payload")
        local_path.write_bytes(bytes(payload))
        self.logger.info(f"Downloaded OneDrive backup {remote_id} to {local_path}")
        return local_path

    def list_backups(self) -> List[RemoteBackupItem]:
        """List ``.tmas-backup.zip`` files under the configured OneDrive folder."""
        self._require_authenticated()
        folder = _normalize_folder(get_settings().onedrive_folder)
        items: List[RemoteBackupItem] = []

        url = (
            f"{GRAPH_BASE}/me/drive/root:/{_encode_path(folder)}:/children"
            f"?$select=id,name,size,file,folder,createdDateTime,lastModifiedDateTime"
        )
        try:
            while url:
                result = self._api("GET", url)
                if not isinstance(result, dict):
                    raise OneDriveError("OneDrive list returned unexpected payload")
                for entry in result.get("value") or []:
                    if entry.get("folder") is not None:
                        continue
                    name = str(entry.get("name") or "")
                    if not name.endswith(BACKUP_FILE_EXTENSION):
                        continue
                    item_id = str(entry.get("id") or "")
                    if not item_id:
                        continue
                    items.append(
                        RemoteBackupItem(
                            remote_id=item_id,
                            name=name,
                            size_bytes=int(entry.get("size") or 0),
                            created_at=_parse_graph_timestamp(
                                entry.get("createdDateTime")
                                or entry.get("lastModifiedDateTime")
                            ),
                        )
                    )
                url = result.get("@odata.nextLink") or ""
        except OneDriveError as exc:
            detail = str(exc).lower()
            if "404" in detail or "itemnotfound" in detail or "not found" in detail:
                return []
            raise
        except Exception as exc:
            raise _map_onedrive_exception(exc, operation="listing backups") from exc

        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def delete(self, remote_id: str) -> bool:
        """Delete a remote backup by Graph drive item id."""
        self._require_authenticated()
        url = f"{GRAPH_BASE}/me/drive/items/{urllib.parse.quote(remote_id, safe='')}"
        try:
            self._api("DELETE", url, expect_json=False)
        except Exception as exc:
            raise _map_onedrive_exception(exc, operation="deleting backup") from exc
        self.logger.info(f"Deleted OneDrive backup {remote_id}")
        return True

    def disconnect(self) -> None:
        """Clear in-memory auth state (``.env`` token is unchanged)."""
        self._verified = False

    def _ensure_folder(self, folder: str) -> None:
        """Create folder path segments under the drive root when missing."""
        parts = [p for p in folder.split("/") if p]
        current = ""
        for part in parts:
            current = f"{current}/{part}" if current else part
            try:
                self._api("GET", f"{GRAPH_BASE}/me/drive/root:/{_encode_path(current)}")
                continue
            except OneDriveError as exc:
                if not _is_not_found(exc):
                    raise
            parent = current.rsplit("/", 1)[0] if "/" in current else ""
            if parent:
                create_url = (
                    f"{GRAPH_BASE}/me/drive/root:/{_encode_path(parent)}:/children"
                )
            else:
                create_url = f"{GRAPH_BASE}/me/drive/root/children"
            body = {
                "name": part,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "fail",
            }
            try:
                self._api("POST", create_url, json_body=body)
            except OneDriveError as exc:
                # Race / already exists — verify by path.
                if "nameAlreadyExists" in str(exc) or "409" in str(exc):
                    self._api(
                        "GET", f"{GRAPH_BASE}/me/drive/root:/{_encode_path(current)}"
                    )
                    continue
                raise

    def _require_authenticated(self) -> None:
        if not self.is_authenticated():
            raise OneDriveError("OneDrive is not authenticated")

    def _api(
        self,
        method: str,
        url: str,
        *,
        json_body: Optional[dict[str, Any]] = None,
        data: Optional[bytes] = None,
        content_type: Optional[str] = None,
        expect_json: bool = True,
    ) -> Any:
        headers = {
            "Authorization": f"Bearer {_access_token()}",
        }
        payload: Optional[bytes] = data
        if json_body is not None:
            payload = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif content_type:
            headers["Content-Type"] = content_type
        elif method in ("POST", "PUT", "PATCH") and payload is None:
            payload = b""

        result = self._dispatch(
            method, url, headers=headers, data=payload, expect_json=expect_json
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
    token = (get_settings().onedrive_access_token or "").strip()
    if not token:
        raise OneDriveError("ONEDRIVE_ACCESS_TOKEN is not set")
    return token


def _normalize_folder(folder: Optional[str]) -> str:
    text = (folder or DEFAULT_ONEDRIVE_FOLDER).strip() or DEFAULT_ONEDRIVE_FOLDER
    text = text.replace("\\", "/").strip("/")
    return text or DEFAULT_ONEDRIVE_FOLDER


def _encode_path(path: str) -> str:
    """Encode each path segment for Graph path addressing (keep ``/`` separators)."""
    return "/".join(
        urllib.parse.quote(segment, safe="")
        for segment in path.split("/")
        if segment
    )


def _parse_graph_timestamp(value: Any) -> datetime:
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


def _is_not_found(exc: OneDriveError) -> bool:
    detail = str(exc).lower()
    return "404" in detail or "itemnotfound" in detail or "not found" in detail


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
            status = getattr(response, "status", None) or response.getcode()
    except urllib.error.HTTPError as exc:
        detail = _read_http_error(exc)
        raise OneDriveError(detail) from exc
    except Exception as exc:
        raise _map_onedrive_exception(exc, operation="HTTP request") from exc

    if method == "DELETE" or status == 204:
        return b"" if not expect_json else {}
    if not expect_json:
        return payload
    if not payload:
        return {}
    try:
        return json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise OneDriveError("OneDrive returned invalid JSON") from exc


def _read_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    summary = body.strip() or exc.reason or str(exc)
    try:
        parsed = json.loads(body)
        error = parsed.get("error") or {}
        if isinstance(error, dict):
            code = error.get("code") or ""
            message = error.get("message") or summary
            if code:
                return f"HTTP {exc.code}: {code}: {message}"
            return f"HTTP {exc.code}: {message}"
        return f"HTTP {exc.code}: {error}"
    except (json.JSONDecodeError, TypeError, AttributeError):
        return f"HTTP {exc.code}: {summary}"


def _map_onedrive_exception(exc: BaseException, *, operation: str) -> OneDriveError:
    """Map low-level network/API failures to clear OneDriveError messages."""
    if isinstance(exc, OneDriveError):
        return exc
    if is_network_exception(exc):
        return OneDriveError(format_offline_error(operation))
    detail = str(exc).strip() or exc.__class__.__name__
    lowered = detail.lower()
    if any(
        token in lowered
        for token in (
            "503",
            "500",
            "502",
            "504",
            "service unavailable",
            "internal_error",
            "internal error",
            "throttl",
        )
    ):
        return OneDriveError(
            format_drive_unavailable_error(detail)
            .replace("Google Drive", "OneDrive")
            .replace("googleapis.com", "graph.microsoft.com")
        )
    return OneDriveError(f"OneDrive {operation} failed: {detail}")
