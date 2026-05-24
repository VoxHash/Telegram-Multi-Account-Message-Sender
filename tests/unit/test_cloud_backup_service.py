"""
Unit tests for CloudBackupService orchestration.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud.backup_package import DATABASE_FILENAME
from app.services.cloud.cloud_backup_service import CloudBackupService, CloudBackupServiceError
from app.services.cloud.provider_base import RemoteBackupItem


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.provider_name = "Google Drive"
    provider.is_authenticated.return_value = True
    provider.upload.return_value = "remote-123"
    provider.list_backups.return_value = [
        RemoteBackupItem(
            remote_id="remote-123",
            name="telegram-sender-backup-20260524.tmas-backup.zip",
            size_bytes=2048,
            created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
    ]
    return provider


@pytest.fixture
def mock_builder():
    builder = MagicMock()
    builder.build.return_value = Path("/tmp/backup.tmas-backup.zip")
    return builder


class TestCloudBackupService:
    def test_backup_requires_connection(self, mock_provider, mock_builder):
        mock_provider.is_authenticated.return_value = False
        service = CloudBackupService(google_provider=mock_provider, package_builder=mock_builder)

        with pytest.raises(CloudBackupServiceError, match="Connect to Google Drive"):
            service.backup_to_google_drive()

    def test_backup_uploads_package(self, mock_provider, mock_builder, tmp_path):
        service = CloudBackupService(google_provider=mock_provider, package_builder=mock_builder)

        with patch(
            "app.services.cloud.cloud_backup_service.BackupPackageBuilder.generate_filename",
            return_value="telegram-sender-backup-test.tmas-backup.zip",
        ):
            remote_id = service.backup_to_google_drive(password="secret")

        assert remote_id == "remote-123"
        mock_builder.build.assert_called_once()
        mock_provider.upload.assert_called_once()

    def test_restore_creates_pre_restore_snapshot(
        self, mock_provider, mock_builder, tmp_path, monkeypatch
    ):
        service = CloudBackupService(google_provider=mock_provider, package_builder=mock_builder)

        package_path = tmp_path / "package.tmas-backup.zip"
        package_path.write_bytes(b"zip")
        db_path = tmp_path / "extracted" / DATABASE_FILENAME
        db_path.parent.mkdir(parents=True)
        db_path.write_bytes(b"sqlite-data")

        mock_builder.verify.return_value = {"schema_version": "1"}
        mock_builder.extract.return_value = {DATABASE_FILENAME: db_path}

        app_data = tmp_path / "app_data"
        monkeypatch.setattr(
            "app.services.cloud.cloud_backup_service.get_settings",
            lambda: MagicMock(app_data_dir=str(app_data)),
        )
        service = CloudBackupService(google_provider=mock_provider, package_builder=mock_builder)

        def _fake_backup_database(backup_path):
            path = Path(backup_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"pre-restore-db")
            return path

        with patch(
            "app.services.cloud.cloud_backup_service.backup_database",
            side_effect=_fake_backup_database,
        ):
            with patch("app.services.cloud.cloud_backup_service.restore_database") as mock_restore:
                def _fake_download(_remote_id, local_path):
                    Path(local_path).write_bytes(b"zip")
                    return Path(local_path)

                mock_provider.download.side_effect = _fake_download
                pre_restore = service.restore_from_google_drive("remote-123")

        assert pre_restore.exists()
        assert pre_restore.parent == app_data
        mock_restore.assert_called_once_with(db_path)
