"""
Unit tests for Google Drive cloud provider (MVP-2, mocked API).
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud import GoogleDriveError, GoogleDriveProvider
from app.services.cloud.token_store import DriveTokenStore


@pytest.fixture
def token_store(tmp_path):
    return DriveTokenStore(cloud_dir=tmp_path / "cloud")


@pytest.fixture
def provider(token_store):
    return GoogleDriveProvider(token_store=token_store)


@pytest.fixture
def mock_google_deps():
    mock_credentials = MagicMock()
    mock_credentials.valid = True
    mock_credentials.expired = False
    mock_credentials.token = "access-token"
    mock_credentials.refresh_token = "refresh-token"
    mock_credentials.token_uri = "https://oauth2.googleapis.com/token"
    mock_credentials.client_id = "client-id"
    mock_credentials.client_secret = "client-secret"
    mock_credentials.scopes = ["https://www.googleapis.com/auth/drive.file"]

    mock_service = MagicMock()
    mock_files = MagicMock()
    mock_service.files.return_value = mock_files

    with patch(
        "app.services.cloud.google_drive._import_google_deps",
        return_value=(
            MagicMock(),
            MagicMock(from_authorized_user_info=MagicMock(return_value=mock_credentials)),
            MagicMock(),
            MagicMock(return_value=mock_service),
            MagicMock(),
        ),
    ):
        yield {
            "credentials": mock_credentials,
            "service": mock_service,
            "files": mock_files,
        }


class TestDriveTokenStore:
    def test_save_and_load_round_trip(self, token_store):
        token_store.save({"token": "abc", "refresh_token": "def"})
        loaded = token_store.load()
        assert loaded["token"] == "abc"
        assert loaded["refresh_token"] == "def"

    def test_clear_removes_token(self, token_store):
        token_store.save({"token": "abc"})
        token_store.clear()
        assert token_store.load() is None


class TestGoogleDriveProvider:
    def test_authenticate_requires_client_credentials(self, provider, token_store, mock_google_deps):
        with patch("app.services.cloud.google_drive.get_settings") as mock_settings:
            mock_settings.return_value.google_drive_client_id = None
            mock_settings.return_value.google_drive_client_secret = None
            with pytest.raises(GoogleDriveError, match="client ID and secret"):
                provider.authenticate()

    def test_authenticate_uses_stored_token(self, provider, token_store, mock_google_deps):
        token_store.save(
            {
                "token": "stored",
                "refresh_token": "refresh",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": "id",
                "client_secret": "secret",
                "scopes": ["https://www.googleapis.com/auth/drive.file"],
            }
        )

        mock_google_deps["files"].list.return_value.execute.side_effect = [
            {"files": [{"id": "root-folder"}]},
            {"files": [{"id": "backup-folder"}]},
        ]

        with patch("app.services.cloud.google_drive.get_settings") as mock_settings:
            mock_settings.return_value.google_drive_client_id = "id"
            mock_settings.return_value.google_drive_client_secret = "secret"
            assert provider.authenticate() is True

        assert provider.is_authenticated() is True

    def test_upload_returns_remote_file_id(self, provider, token_store, mock_google_deps, tmp_path):
        token_store.save({"token": "stored", "refresh_token": "refresh"})
        provider._service = mock_google_deps["service"]
        provider._backup_folder_id = "backup-folder"

        local_file = tmp_path / "backup.tmas-backup.zip"
        local_file.write_bytes(b"zip-data")

        create_mock = mock_google_deps["files"].create.return_value
        create_mock.execute.return_value = {
            "id": "file-123",
            "name": "backup.tmas-backup.zip",
            "size": "8",
            "createdTime": "2026-05-24T12:00:00.000Z",
        }

        remote_id = provider.upload(local_file, "backup.tmas-backup.zip")
        assert remote_id == "file-123"
        create_mock.execute.assert_called_once()

    def test_list_backups_maps_remote_items(self, provider, mock_google_deps):
        provider._service = mock_google_deps["service"]
        provider._backup_folder_id = "backup-folder"

        mock_google_deps["files"].list.return_value.execute.return_value = {
            "files": [
                {
                    "id": "file-1",
                    "name": "telegram-sender-backup-20260524.tmas-backup.zip",
                    "size": "1024",
                    "createdTime": "2026-05-24T12:00:00.000Z",
                }
            ]
        }

        items = provider.list_backups()
        assert len(items) == 1
        assert items[0].remote_id == "file-1"
        assert items[0].size_bytes == 1024
        assert items[0].created_at.tzinfo is not None

    def test_download_writes_local_file(self, provider, mock_google_deps, tmp_path):
        provider._service = mock_google_deps["service"]
        provider._backup_folder_id = "backup-folder"

        get_media = mock_google_deps["files"].get_media.return_value
        get_media.execute.return_value = b"backup-bytes"

        target = tmp_path / "downloaded.tmas-backup.zip"
        result = provider.download("file-1", target)

        assert result == target
        assert target.read_bytes() == b"backup-bytes"

    def test_delete_calls_drive_api(self, provider, mock_google_deps):
        provider._service = mock_google_deps["service"]
        assert provider.delete("file-1") is True
        mock_google_deps["files"].delete.assert_called_once_with(fileId="file-1")

    def test_missing_google_deps_raises_clear_error(self, provider):
        with patch(
            "app.services.cloud.google_drive._import_google_deps",
            side_effect=GoogleDriveError("missing deps"),
        ):
            with pytest.raises(GoogleDriveError, match="missing deps"):
                provider.authenticate()
