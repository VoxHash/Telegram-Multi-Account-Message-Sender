"""
Orchestrates local backup packages and Google Drive upload/restore.
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from app.services import get_logger
from app.services.db import backup_database, restore_database
from app.services.settings import get_settings

from .backup_package import (
    DATABASE_FILENAME,
    BackupPackageBuilder,
    BackupPackageError,
)
from .google_drive import GoogleDriveError, GoogleDriveProvider
from .network import check_network_available, format_offline_error
from .provider_base import RemoteBackupItem


class CloudBackupServiceError(Exception):
    """Raised when cloud backup orchestration fails."""


class CloudBackupService:
    """High-level API for cloud backup and restore operations."""

    def __init__(
        self,
        provider: Optional[GoogleDriveProvider] = None,
        package_builder: Optional[BackupPackageBuilder] = None,
    ) -> None:
        self.logger = get_logger()
        self.settings = get_settings()
        self.provider = provider or GoogleDriveProvider()
        self.package_builder = package_builder or BackupPackageBuilder()

    def _require_online(self, operation: str) -> None:
        """Fail fast with offline-friendly messaging when the network is down."""
        if not check_network_available():
            raise CloudBackupServiceError(format_offline_error(operation))

    def connect_google_drive(self) -> None:
        """Authenticate with Google Drive."""
        self._require_online("Google Drive connect")
        try:
            if not self.provider.authenticate():
                raise CloudBackupServiceError("Google Drive authentication failed")
        except GoogleDriveError as exc:
            raise CloudBackupServiceError(str(exc)) from exc

    def disconnect_google_drive(self) -> None:
        """Remove stored Google Drive credentials."""
        self.provider.disconnect()

    def is_google_drive_connected(self) -> bool:
        """Return True when Google Drive credentials are available."""
        return self.provider.is_authenticated()

    def backup_to_google_drive(self, password: Optional[str] = None) -> str:
        """Build a backup package and upload it to Google Drive."""
        if not self.is_google_drive_connected():
            raise CloudBackupServiceError("Connect to Google Drive before creating a backup")
        self._require_online("cloud backup upload")

        filename = BackupPackageBuilder.generate_filename()
        with tempfile.TemporaryDirectory() as temp_dir:
            package_path = Path(temp_dir) / filename
            try:
                self.package_builder.build(package_path, password=password, include_settings=True)
            except BackupPackageError as exc:
                raise CloudBackupServiceError(str(exc)) from exc

            try:
                remote_id = self.provider.upload(package_path, filename)
            except GoogleDriveError as exc:
                raise CloudBackupServiceError(str(exc)) from exc

        self.logger.info(f"Cloud backup uploaded: {filename} ({remote_id})")
        return remote_id

    def list_google_drive_backups(self) -> List[RemoteBackupItem]:
        """List backup packages stored on Google Drive."""
        if not self.is_google_drive_connected():
            raise CloudBackupServiceError("Connect to Google Drive to list backups")
        self._require_online("listing cloud backups")
        try:
            return self.provider.list_backups()
        except GoogleDriveError as exc:
            raise CloudBackupServiceError(str(exc)) from exc

    def _snapshot_and_restore_package(
        self, package_path: Path, password: Optional[str] = None, *, source_label: str
    ) -> Path:
        """Verify a local package, snapshot the DB, restore app.db, return snapshot path."""
        if not package_path.is_file():
            raise CloudBackupServiceError(f"Backup package not found: {package_path}")

        app_data = Path(self.settings.app_data_dir)
        app_data.mkdir(parents=True, exist_ok=True)
        pre_restore_path = app_data / (
            f"pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.db"
        )

        try:
            backup_database(pre_restore_path)
        except Exception as exc:
            raise CloudBackupServiceError(f"Failed to create pre-restore snapshot: {exc}") from exc

        with tempfile.TemporaryDirectory() as temp_dir:
            extract_dir = Path(temp_dir) / "extracted"
            try:
                self.package_builder.verify(package_path, password=password)
                extracted = self.package_builder.extract(
                    package_path, extract_dir, password=password
                )
            except BackupPackageError as exc:
                raise CloudBackupServiceError(
                    f"{exc} Pre-restore snapshot kept at: {pre_restore_path}"
                ) from exc

            database_file = extracted.get(DATABASE_FILENAME)
            if not database_file or not database_file.exists():
                raise CloudBackupServiceError(
                    "Backup package does not contain app.db. "
                    f"Pre-restore snapshot kept at: {pre_restore_path}"
                )

            try:
                restore_database(database_file)
            except Exception as exc:
                raise CloudBackupServiceError(
                    f"Database restore failed: {exc}. "
                    f"Pre-restore snapshot kept at: {pre_restore_path}"
                ) from exc

        self.logger.info(f"Restored database from {source_label}")
        return pre_restore_path

    def restore_from_local_package(
        self, package_path: Path, password: Optional[str] = None
    ) -> Path:
        """
        Restore from a local ``.tmas-backup.zip`` (file association / offline path).

        Does not require network or Google Drive. Returns the pre-restore DB snapshot path.
        """
        return self._snapshot_and_restore_package(
            Path(package_path),
            password=password,
            source_label=f"local package {package_path}",
        )

    def restore_from_google_drive(
        self, remote_id: str, password: Optional[str] = None
    ) -> Path:
        """
        Download a remote backup, verify it, snapshot the current DB, and restore.

        Returns the path to the pre-restore local database snapshot.
        Raises before modifying the local database when offline / Drive unreachable.
        Local DB is untouched until the package downloads successfully.
        """
        if not self.is_google_drive_connected():
            raise CloudBackupServiceError("Connect to Google Drive before restoring")
        # Probe network before download so offline restores leave DB untouched.
        self._require_online("cloud restore")

        with tempfile.TemporaryDirectory() as temp_dir:
            package_path = Path(temp_dir) / "restore-package.tmas-backup.zip"
            try:
                self.provider.download(remote_id, package_path)
            except GoogleDriveError as exc:
                raise CloudBackupServiceError(str(exc)) from exc

            return self._snapshot_and_restore_package(
                package_path,
                password=password,
                source_label=f"Google Drive backup {remote_id}",
            )
