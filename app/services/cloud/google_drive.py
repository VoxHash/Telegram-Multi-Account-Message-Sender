"""
Google Drive cloud provider for backup upload, list, download, and delete.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.services import get_logger
from app.services.settings import get_settings

from .backup_package import BACKUP_FILE_EXTENSION
from .provider_base import CloudProvider, RemoteBackupItem
from .token_store import DriveTokenStore

GOOGLE_DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
APP_ROOT_FOLDER = "Telegram Multi-Account Message Sender"
BACKUPS_FOLDER = "backups"


class GoogleDriveError(Exception):
    """Raised when Google Drive operations fail."""


class GoogleDriveProvider(CloudProvider):
    """Google Drive implementation of ``CloudProvider``."""

    def __init__(self, token_store: Optional[DriveTokenStore] = None):
        self.logger = get_logger()
        self.token_store = token_store or DriveTokenStore()
        self._credentials = None
        self._service = None
        self._backup_folder_id: Optional[str] = None

    @property
    def provider_name(self) -> str:
        return "Google Drive"

    def authenticate(self) -> bool:
        """Authenticate via stored token or interactive OAuth desktop flow."""
        Request, Credentials, InstalledAppFlow, build, _MediaFileUpload = _import_google_deps()
        settings = get_settings()

        if not settings.google_drive_client_id or not settings.google_drive_client_secret:
            raise GoogleDriveError(
                "Google Drive client ID and secret are required. "
                "Set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET in .env"
            )

        credentials = None
        token_data = self.token_store.load()
        if token_data:
            credentials = Credentials.from_authorized_user_info(token_data, GOOGLE_DRIVE_SCOPES)

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        elif not credentials or not credentials.valid:
            flow = InstalledAppFlow.from_client_config(
                {
                    "installed": {
                        "client_id": settings.google_drive_client_id,
                        "client_secret": settings.google_drive_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": ["http://localhost"],
                    }
                },
                GOOGLE_DRIVE_SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        self.token_store.save(_credentials_to_dict(credentials))
        self._credentials = credentials
        self._service = build("drive", "v3", credentials=credentials, cache_discovery=False)
        self._backup_folder_id = self._ensure_backup_folder_id()
        self.logger.info("Google Drive authentication successful")
        return True

    def is_authenticated(self) -> bool:
        """Return True when a valid Drive service is available."""
        if self._service is not None:
            return True
        token_data = self.token_store.load()
        if not token_data:
            return False
        try:
            return self.authenticate()
        except GoogleDriveError:
            return False

    def upload(self, local_path: Path, remote_name: str) -> str:
        """Upload a backup package to the Drive backups folder."""
        service = self._require_service()
        folder_id = self._require_backup_folder_id()
        MediaFileUpload = _import_google_deps()[-1]

        media = MediaFileUpload(str(local_path), resumable=True)
        metadata = {"name": remote_name, "parents": [folder_id]}
        created = (
            service.files()
            .create(body=metadata, media_body=media, fields="id,name,size,createdTime")
            .execute()
        )
        file_id = created["id"]
        self.logger.info(f"Uploaded backup to Google Drive: {remote_name} ({file_id})")
        return file_id

    def download(self, remote_id: str, local_path: Path) -> Path:
        """Download a remote backup file to ``local_path``."""
        service = self._require_service()
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        request = service.files().get_media(fileId=remote_id)
        content = request.execute()
        local_path.write_bytes(content)
        self.logger.info(f"Downloaded Google Drive backup {remote_id} to {local_path}")
        return local_path

    def list_backups(self) -> List[RemoteBackupItem]:
        """List ``.tmas-backup.zip`` files in the Drive backups folder."""
        service = self._require_service()
        folder_id = self._require_backup_folder_id()

        query = (
            f"'{folder_id}' in parents and trashed=false "
            f"and name contains '{BACKUP_FILE_EXTENSION}'"
        )
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id,name,size,createdTime)",
                orderBy="createdTime desc",
            )
            .execute()
        )

        items: List[RemoteBackupItem] = []
        for file_meta in response.get("files", []):
            created_at = _parse_drive_timestamp(file_meta.get("createdTime"))
            items.append(
                RemoteBackupItem(
                    remote_id=file_meta["id"],
                    name=file_meta.get("name", ""),
                    size_bytes=int(file_meta.get("size", 0)),
                    created_at=created_at,
                )
            )
        return items

    def delete(self, remote_id: str) -> bool:
        """Permanently delete a remote backup file."""
        service = self._require_service()
        service.files().delete(fileId=remote_id).execute()
        self.logger.info(f"Deleted Google Drive backup {remote_id}")
        return True

    def disconnect(self) -> None:
        """Clear local credentials and reset the client."""
        self.token_store.clear()
        self._credentials = None
        self._service = None
        self._backup_folder_id = None

    def _require_service(self):
        if self._service is None:
            if not self.is_authenticated():
                raise GoogleDriveError("Google Drive is not authenticated")
        return self._service

    def _require_backup_folder_id(self) -> str:
        if self._backup_folder_id is None:
            self._backup_folder_id = self._ensure_backup_folder_id()
        return self._backup_folder_id

    def _ensure_backup_folder_id(self) -> str:
        service = self._require_service()
        root_id = self._find_or_create_folder(service, APP_ROOT_FOLDER, parent_id="root")
        return self._find_or_create_folder(service, BACKUPS_FOLDER, parent_id=root_id)

    @staticmethod
    def _find_or_create_folder(service, name: str, *, parent_id: str) -> str:
        escaped_name = name.replace("'", "\\'")
        query = (
            f"name = '{escaped_name}' and '{parent_id}' in parents "
            f"and mimeType = 'application/vnd.google-apps.folder' and trashed=false"
        )
        response = service.files().list(q=query, spaces="drive", fields="files(id)").execute()
        files = response.get("files", [])
        if files:
            return files[0]["id"]

        metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        created = service.files().create(body=metadata, fields="id").execute()
        return created["id"]


def _import_google_deps() -> Tuple[Any, Any, Any, Any, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise GoogleDriveError(
            "Google Drive support requires optional dependencies. "
            "Install with: pip install 'telegram-multi-account-sender[cloud]'"
        ) from exc
    return Request, Credentials, InstalledAppFlow, build, MediaFileUpload


def _credentials_to_dict(credentials) -> Dict[str, Any]:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes or GOOGLE_DRIVE_SCOPES),
    }


def _parse_drive_timestamp(value: Optional[str]) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)
