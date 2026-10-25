"""
Unit tests for OneDrive cloud provider and CloudBackupService OneDrive paths.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud.backup_package import DATABASE_FILENAME
from app.services.cloud.cloud_backup_service import CloudBackupService, CloudBackupServiceError
from app.services.cloud.onedrive_provider import (
    OneDriveError,
    OneDriveProvider,
    _encode_path,
    _map_onedrive_exception,
    _normalize_folder,
    _parse_graph_timestamp,
)
from app.services.cloud.network import is_offline_error_message
from app.services.cloud.provider_base import RemoteBackupItem


def _settings(*, token="od.TEST_TOKEN", folder="TMAS/backups", app_data_dir="/tmp/app_data"):
    return MagicMock(
        onedrive_access_token=token,
        onedrive_folder=folder,
        app_data_dir=app_data_dir,
    )


class TestOneDriveHelpers:
    def test_normalize_folder(self):
        assert _normalize_folder(None) == "TMAS/backups"
        assert _normalize_folder("/TMAS/backups/") == "TMAS/backups"
        assert _normalize_folder("TMAS\\backups") == "TMAS/backups"

    def test_encode_path(self):
        assert _encode_path("TMAS/backups") == "TMAS/backups"
        assert " " not in _encode_path("My Folder/file.zip")
        assert "%20" in _encode_path("My Folder/file.zip")

    def test_parse_graph_timestamp(self):
        aware = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
        assert _parse_graph_timestamp(aware) == aware
        naive = datetime(2026, 10, 24, 12, 0)
        assert _parse_graph_timestamp(naive).tzinfo is not None
        parsed = _parse_graph_timestamp("2026-10-24T12:00:00Z")
        assert parsed.year == 2026

    def test_map_onedrive_exception_offline(self):
        mapped = _map_onedrive_exception(
            ConnectionError("failed to establish a new connection"),
            operation="backup upload",
        )
        assert isinstance(mapped, OneDriveError)
        assert is_offline_error_message(str(mapped))


class TestOneDriveProvider:
    def test_is_configured_requires_token(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.onedrive_provider.get_settings",
            lambda: _settings(token=None),
        )
        assert OneDriveProvider.is_configured() is False

        monkeypatch.setattr(
            "app.services.cloud.onedrive_provider.get_settings",
            lambda: _settings(),
        )
        assert OneDriveProvider.is_configured() is True

    def test_authenticate_me_drive(self, monkeypatch):
        calls = []

        def client(method, url, *, headers, data, expect_json=True):
            calls.append((method, url, headers.get("Authorization")))
            assert url.endswith("/me/drive")
            return {"id": "b!drive", "driveType": "personal"}

        monkeypatch.setattr(
            "app.services.cloud.onedrive_provider.get_settings",
            lambda: _settings(),
        )
        provider = OneDriveProvider(client=client)
        assert provider.authenticate() is True
        assert provider._verified is True
        assert calls and calls[0][2] == "Bearer od.TEST_TOKEN"

    def test_authenticate_requires_config(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.onedrive_provider.get_settings",
            lambda: _settings(token=None),
        )
        provider = OneDriveProvider(client=MagicMock())
        with pytest.raises(OneDriveError, match="OneDrive access token is required"):
            provider.authenticate()

    def test_upload_download_list_delete(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "app.services.cloud.onedrive_provider.get_settings",
            lambda: _settings(),
        )

        state = {"uploaded": None, "folders": {"TMAS", "TMAS/backups"}}

        def client(method, url, *, headers, data, expect_json=True):
            if method == "GET" and "/me/drive/root:/" in url and ":/children" not in url:
                # Folder existence check
                return {"id": "folder-id", "folder": {}}
            if method == "PUT" and ":/content" in url:
                state["uploaded"] = data
                return {
                    "id": "item-abc",
                    "name": "pkg.tmas-backup.zip",
                    "size": len(data or b""),
                    "file": {},
                }
            if method == "GET" and "/items/" in url and url.endswith("/content"):
                assert expect_json is False
                return state["uploaded"] or b"zip-bytes"
            if method == "GET" and ":/children" in url:
                return {
                    "value": [
                        {
                            "id": "item-abc",
                            "name": "pkg.tmas-backup.zip",
                            "size": 9,
                            "file": {},
                            "createdDateTime": "2026-10-24T12:00:00Z",
                        },
                        {
                            "id": "item-txt",
                            "name": "notes.txt",
                            "size": 1,
                            "file": {},
                        },
                        {
                            "id": "folder-other",
                            "name": "other",
                            "folder": {},
                        },
                    ]
                }
            if method == "DELETE" and "/items/" in url:
                return b""
            raise AssertionError(f"unexpected {method} {url}")

        provider = OneDriveProvider(client=client)
        provider._verified = True

        local = tmp_path / "pkg.tmas-backup.zip"
        local.write_bytes(b"zip-bytes")

        remote_id = provider.upload(local, "pkg.tmas-backup.zip")
        assert remote_id == "item-abc"
        assert state["uploaded"] == b"zip-bytes"

        out = tmp_path / "out.zip"
        provider.download(remote_id, out)
        assert out.read_bytes() == b"zip-bytes"

        items = provider.list_backups()
        assert len(items) == 1
        assert items[0].remote_id == "item-abc"
        assert items[0].name == "pkg.tmas-backup.zip"

        assert provider.delete(remote_id) is True

    def test_list_backups_missing_folder_returns_empty(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.onedrive_provider.get_settings",
            lambda: _settings(),
        )

        def client(method, url, *, headers, data, expect_json=True):
            raise OneDriveError("HTTP 404: itemNotFound: The resource could not be found.")

        provider = OneDriveProvider(client=client)
        provider._verified = True
        assert provider.list_backups() == []

    def test_disconnect_clears_verified(self):
        provider = OneDriveProvider(client=MagicMock(return_value={}))
        provider._verified = True
        provider.disconnect()
        assert provider._verified is False


class TestCloudBackupServiceOneDrive:
    @pytest.fixture
    def mock_onedrive(self):
        provider = MagicMock()
        provider.is_authenticated.return_value = True
        provider.upload.return_value = "item-remote-1"
        provider.list_backups.return_value = [
            RemoteBackupItem(
                remote_id="item-remote-1",
                name="remote.tmas-backup.zip",
                size_bytes=2048,
                created_at=datetime.now(timezone.utc),
            )
        ]
        return provider

    @pytest.fixture
    def mock_builder(self):
        builder = MagicMock()
        builder.build.return_value = Path("/tmp/backup.tmas-backup.zip")
        return builder

    def test_backup_requires_connection(self, mock_onedrive, mock_builder):
        mock_onedrive.is_authenticated.return_value = False
        service = CloudBackupService(
            onedrive_provider=mock_onedrive, package_builder=mock_builder
        )
        with pytest.raises(CloudBackupServiceError, match="Verify OneDrive credentials"):
            service.backup_to_onedrive()

    def test_backup_uploads_package(self, mock_onedrive, mock_builder):
        service = CloudBackupService(
            onedrive_provider=mock_onedrive, package_builder=mock_builder
        )
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=True,
        ):
            with patch(
                "app.services.cloud.cloud_backup_service.BackupPackageBuilder.generate_filename",
                return_value="telegram-sender-backup-test.tmas-backup.zip",
            ):
                remote_id = service.backup_to_onedrive(password="secret")
        assert remote_id == "item-remote-1"
        mock_onedrive.upload.assert_called_once()

    def test_list_fails_fast_when_offline(self, mock_onedrive, mock_builder):
        service = CloudBackupService(
            onedrive_provider=mock_onedrive, package_builder=mock_builder
        )
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=False,
        ):
            with pytest.raises(CloudBackupServiceError) as exc_info:
                service.list_onedrive_backups()
        assert is_offline_error_message(str(exc_info.value))
        mock_onedrive.list_backups.assert_not_called()

    def test_restore_from_onedrive(self, mock_onedrive, mock_builder, tmp_path, monkeypatch):
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
        service = CloudBackupService(
            onedrive_provider=mock_onedrive, package_builder=mock_builder
        )

        def _fake_backup_database(backup_path):
            path = Path(backup_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"pre-restore-db")
            return path

        def _fake_download(_remote_id, local_path):
            Path(local_path).write_bytes(b"zip")
            return Path(local_path)

        mock_onedrive.download.side_effect = _fake_download

        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=True,
        ):
            with patch(
                "app.services.cloud.cloud_backup_service.backup_database",
                side_effect=_fake_backup_database,
            ):
                with patch(
                    "app.services.cloud.cloud_backup_service.restore_database"
                ) as mock_restore:
                    pre_restore = service.restore_from_onedrive("item-remote-1")

        assert pre_restore.exists()
        mock_restore.assert_called_once_with(db_path)
