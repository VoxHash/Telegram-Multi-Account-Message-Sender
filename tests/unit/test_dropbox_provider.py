"""
Unit tests for Dropbox cloud provider and CloudBackupService Dropbox paths.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud.backup_package import DATABASE_FILENAME
from app.services.cloud.cloud_backup_service import CloudBackupService, CloudBackupServiceError
from app.services.cloud.dropbox_provider import (
    DropboxError,
    DropboxProvider,
    _map_dropbox_exception,
    _normalize_folder,
    _parse_dropbox_timestamp,
)
from app.services.cloud.network import is_offline_error_message
from app.services.cloud.provider_base import RemoteBackupItem


def _settings(*, token="sl.TEST_TOKEN", folder="/TMAS/backups", app_data_dir="/tmp/app_data"):
    return MagicMock(
        dropbox_access_token=token,
        dropbox_folder=folder,
        app_data_dir=app_data_dir,
    )


class TestDropboxHelpers:
    def test_normalize_folder(self):
        assert _normalize_folder(None) == "/TMAS/backups"
        assert _normalize_folder("TMAS/backups") == "/TMAS/backups"
        assert _normalize_folder("/TMAS/backups/") == "/TMAS/backups"

    def test_parse_dropbox_timestamp(self):
        aware = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
        assert _parse_dropbox_timestamp(aware) == aware
        naive = datetime(2026, 10, 24, 12, 0)
        assert _parse_dropbox_timestamp(naive).tzinfo is not None
        parsed = _parse_dropbox_timestamp("2026-10-24T12:00:00Z")
        assert parsed.year == 2026

    def test_map_dropbox_exception_offline(self):
        mapped = _map_dropbox_exception(
            ConnectionError("failed to establish a new connection"),
            operation="backup upload",
        )
        assert isinstance(mapped, DropboxError)
        assert is_offline_error_message(str(mapped))


class TestDropboxProvider:
    def test_is_configured_requires_token(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.dropbox_provider.get_settings",
            lambda: _settings(token=None),
        )
        assert DropboxProvider.is_configured() is False

        monkeypatch.setattr(
            "app.services.cloud.dropbox_provider.get_settings",
            lambda: _settings(),
        )
        assert DropboxProvider.is_configured() is True

    def test_authenticate_get_current_account(self, monkeypatch):
        calls = []

        def client(method, url, *, headers, data, expect_json=True):
            calls.append((method, url, headers.get("Authorization")))
            assert "users/get_current_account" in url
            return {"account_id": "dbid:test", "email": "user@example.com"}

        monkeypatch.setattr(
            "app.services.cloud.dropbox_provider.get_settings",
            lambda: _settings(),
        )
        provider = DropboxProvider(client=client)
        assert provider.authenticate() is True
        assert provider._verified is True
        assert calls and calls[0][2] == "Bearer sl.TEST_TOKEN"

    def test_authenticate_requires_config(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.dropbox_provider.get_settings",
            lambda: _settings(token=None),
        )
        provider = DropboxProvider(client=MagicMock())
        with pytest.raises(DropboxError, match="Dropbox access token is required"):
            provider.authenticate()

    def test_upload_download_list_delete(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "app.services.cloud.dropbox_provider.get_settings",
            lambda: _settings(),
        )

        state = {"uploaded": None}

        def client(method, url, *, headers, data, expect_json=True):
            if "files/upload" in url:
                state["uploaded"] = data
                return {
                    "name": "pkg.tmas-backup.zip",
                    "path_display": "/TMAS/backups/pkg.tmas-backup.zip",
                    "size": len(data or b""),
                }
            if "files/download" in url:
                assert expect_json is False
                return state["uploaded"] or b"zip-bytes"
            if "files/list_folder/continue" in url:
                return {"entries": [], "cursor": "c2", "has_more": False}
            if "files/list_folder" in url:
                return {
                    "entries": [
                        {
                            ".tag": "file",
                            "name": "pkg.tmas-backup.zip",
                            "path_display": "/TMAS/backups/pkg.tmas-backup.zip",
                            "size": 9,
                            "server_modified": "2026-10-24T12:00:00Z",
                        },
                        {
                            ".tag": "file",
                            "name": "notes.txt",
                            "path_display": "/TMAS/backups/notes.txt",
                            "size": 1,
                        },
                        {
                            ".tag": "folder",
                            "name": "other",
                            "path_display": "/TMAS/backups/other",
                        },
                    ],
                    "cursor": "c1",
                    "has_more": False,
                }
            if "files/delete_v2" in url:
                return {"metadata": {"name": "pkg.tmas-backup.zip"}}
            raise AssertionError(f"unexpected url: {url}")

        provider = DropboxProvider(client=client)
        provider._verified = True

        local = tmp_path / "pkg.tmas-backup.zip"
        local.write_bytes(b"zip-bytes")

        path = provider.upload(local, "pkg.tmas-backup.zip")
        assert path == "/TMAS/backups/pkg.tmas-backup.zip"
        assert state["uploaded"] == b"zip-bytes"

        out = tmp_path / "out.zip"
        provider.download(path, out)
        assert out.read_bytes() == b"zip-bytes"

        items = provider.list_backups()
        assert len(items) == 1
        assert items[0].remote_id == path
        assert items[0].name == "pkg.tmas-backup.zip"

        assert provider.delete(path) is True

    def test_list_backups_missing_folder_returns_empty(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.dropbox_provider.get_settings",
            lambda: _settings(),
        )

        def client(method, url, *, headers, data, expect_json=True):
            raise DropboxError("HTTP 409: path/not_found/")

        provider = DropboxProvider(client=client)
        provider._verified = True
        assert provider.list_backups() == []

    def test_disconnect_clears_verified(self):
        provider = DropboxProvider(client=MagicMock(return_value={}))
        provider._verified = True
        provider.disconnect()
        assert provider._verified is False


class TestCloudBackupServiceDropbox:
    @pytest.fixture
    def mock_dropbox(self):
        provider = MagicMock()
        provider.is_authenticated.return_value = True
        provider.upload.return_value = "/TMAS/backups/remote.tmas-backup.zip"
        provider.list_backups.return_value = [
            RemoteBackupItem(
                remote_id="/TMAS/backups/remote.tmas-backup.zip",
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

    def test_backup_requires_connection(self, mock_dropbox, mock_builder):
        mock_dropbox.is_authenticated.return_value = False
        service = CloudBackupService(
            dropbox_provider=mock_dropbox, package_builder=mock_builder
        )
        with pytest.raises(CloudBackupServiceError, match="Verify Dropbox credentials"):
            service.backup_to_dropbox()

    def test_backup_uploads_package(self, mock_dropbox, mock_builder):
        service = CloudBackupService(
            dropbox_provider=mock_dropbox, package_builder=mock_builder
        )
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=True,
        ):
            with patch(
                "app.services.cloud.cloud_backup_service.BackupPackageBuilder.generate_filename",
                return_value="telegram-sender-backup-test.tmas-backup.zip",
            ):
                remote_id = service.backup_to_dropbox(password="secret")
        assert remote_id == "/TMAS/backups/remote.tmas-backup.zip"
        mock_dropbox.upload.assert_called_once()

    def test_list_fails_fast_when_offline(self, mock_dropbox, mock_builder):
        service = CloudBackupService(
            dropbox_provider=mock_dropbox, package_builder=mock_builder
        )
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=False,
        ):
            with pytest.raises(CloudBackupServiceError) as exc_info:
                service.list_dropbox_backups()
        assert is_offline_error_message(str(exc_info.value))
        mock_dropbox.list_backups.assert_not_called()

    def test_restore_from_dropbox(self, mock_dropbox, mock_builder, tmp_path, monkeypatch):
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
            dropbox_provider=mock_dropbox, package_builder=mock_builder
        )

        def _fake_backup_database(backup_path):
            path = Path(backup_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"pre-restore-db")
            return path

        def _fake_download(_remote_id, local_path):
            Path(local_path).write_bytes(b"zip")
            return Path(local_path)

        mock_dropbox.download.side_effect = _fake_download

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
                    pre_restore = service.restore_from_dropbox(
                        "/TMAS/backups/remote.tmas-backup.zip"
                    )

        assert pre_restore.exists()
        mock_restore.assert_called_once_with(db_path)
