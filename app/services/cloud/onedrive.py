"""
Microsoft OneDrive cloud provider for backup upload, list, download, and delete.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from app.services import get_logger
from app.services.settings import get_settings

from .backup_package import BACKUP_FILE_EXTENSION
from .provider_base import CloudProvider, RemoteBackupItem
from .token_store import OneDriveTokenStore

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
ONEDRIVE_SCOPES = ["Files.ReadWrite.AppFolder"]
APP_ROOT_FOLDER = "Telegram Multi-Account Message Sender"
BACKUPS_FOLDER = "backups"
SIMPLE_UPLOAD_MAX_BYTES = 4 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 3200 * 1024


class OneDriveError(Exception):
    """Raised when OneDrive operations fail."""


class OneDriveProvider(CloudProvider):
    """OneDrive implementation of ``CloudProvider`` using Microsoft Graph."""

    def __init__(self, token_store: Optional[OneDriveTokenStore] = None):
        self.logger = get_logger()
        self.token_store = token_store or OneDriveTokenStore()
        self._access_token: Optional[str] = None
        self._backup_folder_path: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "OneDrive"

    def authenticate(self) -> bool:
        """Authenticate via stored token or interactive OAuth desktop flow."""
        msal, requests = _import_onedrive_deps()
        settings = get_settings()

        if not settings.onedrive_client_id:
            raise OneDriveError(
                "OneDrive client ID is required. Set ONEDRIVE_CLIENT_ID in .env"
            )

        authority = f"https://login.microsoftonline.com/{settings.onedrive_tenant_id}"
        app = msal.PublicClientApplication(settings.onedrive_client_id, authority=authority)

        result: Optional[Dict[str, Any]] = None
        token_data = self.token_store.load()
        if token_data:
            account = token_data.get("account")
            accounts = app.get_accounts(username=account.get("username") if account else None)
            if accounts:
                result = app.acquire_token_silent(ONEDRIVE_SCOPES, account=accounts[0])

        if not result:
            result = app.acquire_token_interactive(scopes=ONEDRIVE_SCOPES)

        if not result or "access_token" not in result:
            message = (result or {}).get("error_description", "OneDrive authentication failed")
            raise OneDriveError(message)

        self.token_store.save(_token_result_to_dict(result, app))
        self._access_token = result["access_token"]
        self._backup_folder_path = self._ensure_backup_folder_path(requests)
        self.logger.info("OneDrive authentication successful")
        return True

    def is_authenticated(self) -> bool:
        if self._access_token:
            return True
        if not self.token_store.load():
            return False
        try:
            return self.authenticate()
        except OneDriveError:
            return False

    def upload(self, local_path: Path, remote_name: str) -> str:
        requests = _import_onedrive_deps()[1]
        self._require_access_token()
        backup_path = self._require_backup_folder_path()
        remote_path = f"{backup_path}/{remote_name}"
        file_size = local_path.stat().st_size

        if file_size <= SIMPLE_UPLOAD_MAX_BYTES:
            return self._simple_upload(requests, remote_path, local_path)

        return self._session_upload(requests, remote_path, local_path, file_size)

    def download(self, remote_id: str, local_path: Path) -> Path:
        requests = _import_onedrive_deps()[1]
        self._require_access_token()
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        response = requests.get(
            f"{GRAPH_BASE}/me/drive/items/{remote_id}/content",
            headers=self._headers(),
            timeout=120,
        )
        if response.status_code >= 400:
            raise OneDriveError(f"OneDrive download failed: {response.text}")

        local_path.write_bytes(response.content)
        self.logger.info(f"Downloaded OneDrive backup {remote_id} to {local_path}")
        return local_path

    def list_backups(self) -> List[RemoteBackupItem]:
        requests = _import_onedrive_deps()[1]
        self._require_access_token()
        backup_path = self._require_backup_folder_path()
        url = self._item_url(backup_path, action="children")

        response = requests.get(url, headers=self._headers(), timeout=60)
        if response.status_code >= 400:
            raise OneDriveError(f"OneDrive list failed: {response.text}")

        items: List[RemoteBackupItem] = []
        for entry in response.json().get("value", []):
            name = entry.get("name", "")
            if not name.endswith(BACKUP_FILE_EXTENSION):
                continue
            items.append(
                RemoteBackupItem(
                    remote_id=entry["id"],
                    name=name,
                    size_bytes=int(entry.get("size", 0)),
                    created_at=_parse_graph_timestamp(entry.get("createdDateTime")),
                )
            )

        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def delete(self, remote_id: str) -> bool:
        requests = _import_onedrive_deps()[1]
        self._require_access_token()
        response = requests.delete(
            f"{GRAPH_BASE}/me/drive/items/{remote_id}",
            headers=self._headers(),
            timeout=60,
        )
        if response.status_code >= 400:
            raise OneDriveError(f"OneDrive delete failed: {response.text}")

        self.logger.info(f"Deleted OneDrive backup {remote_id}")
        return True

    def disconnect(self) -> None:
        self.token_store.clear()
        self._access_token = None
        self._backup_folder_path = None

    def _simple_upload(self, requests, remote_path: str, local_path: Path) -> str:
        url = self._item_url(remote_path, action="content")
        response = requests.put(
            url,
            headers=self._headers(),
            data=local_path.read_bytes(),
            timeout=120,
        )
        if response.status_code >= 400:
            raise OneDriveError(f"OneDrive upload failed: {response.text}")

        remote_id = response.json()["id"]
        self.logger.info(f"Uploaded backup to OneDrive: {local_path.name} ({remote_id})")
        return remote_id

    def _session_upload(
        self, requests, remote_path: str, local_path: Path, file_size: int
    ) -> str:
        session_url = self._item_url(remote_path, action="createUploadSession")
        session_response = requests.post(
            session_url,
            headers=self._headers({"Content-Type": "application/json"}),
            json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
            timeout=60,
        )
        if session_response.status_code >= 400:
            raise OneDriveError(f"OneDrive upload session failed: {session_response.text}")

        upload_url = session_response.json()["uploadUrl"]
        remote_id = None

        with local_path.open("rb") as handle:
            offset = 0
            while offset < file_size:
                chunk = handle.read(UPLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                end = offset + len(chunk) - 1
                headers = {
                    "Content-Length": str(len(chunk)),
                    "Content-Range": f"bytes {offset}-{end}/{file_size}",
                }
                chunk_response = requests.put(upload_url, headers=headers, data=chunk, timeout=120)
                if chunk_response.status_code not in (200, 201, 202):
                    raise OneDriveError(f"OneDrive chunk upload failed: {chunk_response.text}")
                if chunk_response.status_code in (200, 201):
                    remote_id = chunk_response.json()["id"]
                offset += len(chunk)

        if not remote_id:
            raise OneDriveError("OneDrive upload session did not return a file id")

        self.logger.info(f"Uploaded backup to OneDrive: {local_path.name} ({remote_id})")
        return remote_id

    def _ensure_backup_folder_path(self, requests) -> str:
        root_path = APP_ROOT_FOLDER
        backup_path = f"{APP_ROOT_FOLDER}/{BACKUPS_FOLDER}"

        if not self._path_exists(requests, root_path):
            self._create_folder(requests, "", APP_ROOT_FOLDER)
        if not self._path_exists(requests, backup_path):
            self._create_folder(requests, root_path, BACKUPS_FOLDER)

        return backup_path

    def _path_exists(self, requests, relative_path: str) -> bool:
        response = requests.get(
            self._item_url(relative_path),
            headers=self._headers(),
            timeout=60,
        )
        return response.status_code == 200

    def _create_folder(self, requests, parent_path: str, folder_name: str) -> None:
        if parent_path:
            url = self._item_url(parent_path, action="children")
        else:
            url = f"{GRAPH_BASE}/me/drive/special/approot/children"

        response = requests.post(
            url,
            headers=self._headers({"Content-Type": "application/json"}),
            json={
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "rename",
            },
            timeout=60,
        )
        if response.status_code >= 400:
            raise OneDriveError(f"OneDrive folder creation failed: {response.text}")

    def _item_url(self, relative_path: str, action: str = "") -> str:
        encoded = quote(relative_path, safe="/")
        suffix = f":{action}" if action else ""
        return f"{GRAPH_BASE}/me/drive/special/approot:/{encoded}{suffix}"

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"Authorization": f"Bearer {self._access_token}"}
        if extra:
            headers.update(extra)
        return headers

    def _require_access_token(self) -> None:
        if not self._access_token:
            if not self.is_authenticated():
                raise OneDriveError("OneDrive is not authenticated")

    def _require_backup_folder_path(self) -> str:
        if self._backup_folder_path is None:
            requests = _import_onedrive_deps()[1]
            self._backup_folder_path = self._ensure_backup_folder_path(requests)
        return self._backup_folder_path


def _import_onedrive_deps() -> Tuple[Any, Any]:
    try:
        import msal
        import requests
    except ImportError as exc:
        raise OneDriveError(
            "OneDrive support requires optional dependencies. "
            "Install with: pip install 'telegram-multi-account-sender[cloud]'"
        ) from exc
    return msal, requests


def _token_result_to_dict(result: Dict[str, Any], app) -> Dict[str, Any]:
    account = None
    accounts = app.get_accounts()
    if accounts:
        account = accounts[0]
    return {
        "access_token": result.get("access_token"),
        "refresh_token": result.get("refresh_token"),
        "expires_in": result.get("expires_in"),
        "token_type": result.get("token_type"),
        "scope": result.get("scope"),
        "account": account,
    }


def _parse_graph_timestamp(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)
