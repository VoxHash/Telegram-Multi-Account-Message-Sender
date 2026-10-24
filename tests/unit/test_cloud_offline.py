"""
Unit tests for offline / unreachable Drive messaging.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud.cloud_backup_service import CloudBackupService, CloudBackupServiceError
from app.services.cloud.google_drive import GoogleDriveError, _map_drive_exception
from app.services.cloud.network import (
    OFFLINE_ERROR_MARKER,
    format_offline_error,
    is_network_exception,
    is_offline_error_message,
)
from app.services.cloud.provider_base import RemoteBackupItem


@pytest.fixture
def mock_provider():
    provider = MagicMock()
    provider.is_authenticated.return_value = True
    provider.upload.return_value = "remote-123"
    provider.list_backups.return_value = [
        RemoteBackupItem(
            remote_id="remote-123",
            name="telegram-sender-backup-20260524.tmas-backup.zip",
            size_bytes=2048,
            created_at=datetime.now(timezone.utc),
        )
    ]
    return provider


@pytest.fixture
def mock_builder():
    builder = MagicMock()
    builder.build.return_value = Path("/tmp/backup.tmas-backup.zip")
    return builder


class TestNetworkHelpers:
    def test_format_offline_error_marker(self):
        message = format_offline_error("cloud restore")
        assert OFFLINE_ERROR_MARKER in message
        assert "cloud restore" in message
        assert is_offline_error_message(message)

    def test_is_network_exception_detects_connection_error(self):
        assert is_network_exception(ConnectionError("failed to establish a new connection"))
        assert is_network_exception(TimeoutError("timed out"))
        assert not is_network_exception(ValueError("bad password"))

    def test_map_drive_exception_offline(self):
        mapped = _map_drive_exception(ConnectionError("NameResolutionError"), operation="backup download")
        assert isinstance(mapped, GoogleDriveError)
        assert is_offline_error_message(str(mapped))


class TestCloudBackupOffline:
    def test_restore_fails_fast_when_offline(self, mock_provider, mock_builder):
        service = CloudBackupService(provider=mock_provider, package_builder=mock_builder)
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=False,
        ):
            with pytest.raises(CloudBackupServiceError) as exc_info:
                service.restore_from_google_drive("remote-123")

        assert is_offline_error_message(str(exc_info.value))
        mock_provider.download.assert_not_called()

    def test_list_fails_fast_when_offline(self, mock_provider, mock_builder):
        service = CloudBackupService(provider=mock_provider, package_builder=mock_builder)
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=False,
        ):
            with pytest.raises(CloudBackupServiceError) as exc_info:
                service.list_google_drive_backups()

        assert OFFLINE_ERROR_MARKER in str(exc_info.value)

    def test_restore_download_failure_preserves_snapshot_path(
        self, mock_provider, mock_builder, tmp_path, monkeypatch
    ):
        service = CloudBackupService(provider=mock_provider, package_builder=mock_builder)
        app_data = tmp_path / "app_data"
        monkeypatch.setattr(
            "app.services.cloud.cloud_backup_service.get_settings",
            lambda: MagicMock(app_data_dir=str(app_data)),
        )
        service = CloudBackupService(provider=mock_provider, package_builder=mock_builder)

        def _fake_backup_database(backup_path):
            path = Path(backup_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"pre-restore-db")
            return path

        mock_provider.download.side_effect = GoogleDriveError(
            format_offline_error("backup download")
        )

        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=True,
        ):
            with patch(
                "app.services.cloud.cloud_backup_service.backup_database",
                side_effect=_fake_backup_database,
            ):
                with pytest.raises(CloudBackupServiceError) as exc_info:
                    service.restore_from_google_drive("remote-123")

        message = str(exc_info.value)
        assert is_offline_error_message(message)
        assert "Pre-restore snapshot kept at:" in message
