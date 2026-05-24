"""
Unit tests for OneDrive cloud provider (MVP-4, mocked API).
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud import OneDriveError, OneDriveProvider
from app.services.cloud.token_store import OneDriveTokenStore


@pytest.fixture
def token_store(tmp_path):
    return OneDriveTokenStore(cloud_dir=tmp_path / "cloud")


@pytest.fixture
def provider(token_store):
    return OneDriveProvider(token_store=token_store)


@pytest.fixture
def mock_onedrive_deps():
    mock_msal_app = MagicMock()
    mock_msal_app.get_accounts.return_value = []
    mock_msal_app.acquire_token_interactive.return_value = {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "Files.ReadWrite.AppFolder",
    }
    mock_msal_app.get_accounts.side_effect = [
        [],
        [{"username": "user@example.com"}],
    ]

    mock_msal = MagicMock()
    mock_msal.PublicClientApplication.return_value = mock_msal_app

    mock_requests = MagicMock()
    exists_response = MagicMock(status_code=200)
    create_response = MagicMock(status_code=201)
    upload_response = MagicMock(status_code=201)
    upload_response.json.return_value = {"id": "file-123"}

    mock_requests.get.return_value = exists_response
    mock_requests.post.side_effect = [create_response, create_response, upload_response]

    with patch(
        "app.services.cloud.onedrive._import_onedrive_deps",
        return_value=(mock_msal, mock_requests),
    ):
        yield {
            "msal": mock_msal,
            "requests": mock_requests,
            "upload_response": upload_response,
        }


class TestOneDriveTokenStore:
    def test_save_and_load_round_trip(self, token_store):
        token_store.save({"access_token": "abc", "refresh_token": "def"})
        loaded = token_store.load()
        assert loaded["access_token"] == "abc"
        assert loaded["refresh_token"] == "def"


class TestOneDriveProvider:
    def test_authenticate_requires_client_id(self, provider, mock_onedrive_deps):
        with patch("app.services.cloud.onedrive.get_settings") as mock_settings:
            mock_settings.return_value.onedrive_client_id = None
            mock_settings.return_value.onedrive_tenant_id = "common"
            with pytest.raises(OneDriveError, match="client ID"):
                provider.authenticate()

    def test_authenticate_stores_token(self, provider, token_store, mock_onedrive_deps):
        with patch("app.services.cloud.onedrive.get_settings") as mock_settings:
            mock_settings.return_value.onedrive_client_id = "client-id"
            mock_settings.return_value.onedrive_tenant_id = "common"
            assert provider.authenticate() is True

        assert token_store.load() is not None
        assert provider.is_authenticated() is True

    def test_upload_returns_remote_file_id(self, provider, mock_onedrive_deps, tmp_path):
        provider._access_token = "token"
        provider._backup_folder_path = "Telegram Multi-Account Message Sender/backups"

        upload_response = MagicMock(status_code=201)
        upload_response.json.return_value = {"id": "file-123"}
        mock_onedrive_deps["requests"].put.return_value = upload_response

        local_file = tmp_path / "backup.tmas-backup.zip"
        local_file.write_bytes(b"zip-data")

        remote_id = provider.upload(local_file, "backup.tmas-backup.zip")
        assert remote_id == "file-123"

    def test_list_backups_maps_remote_items(self, provider, mock_onedrive_deps):
        provider._access_token = "token"
        provider._backup_folder_path = "Telegram Multi-Account Message Sender/backups"

        list_response = MagicMock(status_code=200)
        list_response.json.return_value = {
            "value": [
                {
                    "id": "file-1",
                    "name": "telegram-sender-backup-20260524.tmas-backup.zip",
                    "size": 1024,
                    "createdDateTime": "2026-05-24T12:00:00.000Z",
                }
            ]
        }
        mock_onedrive_deps["requests"].get.return_value = list_response

        items = provider.list_backups()
        assert len(items) == 1
        assert items[0].remote_id == "file-1"
        assert items[0].size_bytes == 1024
        assert items[0].created_at.tzinfo is not None

    def test_download_writes_local_file(self, provider, mock_onedrive_deps, tmp_path):
        provider._access_token = "token"
        download_response = MagicMock(status_code=200)
        download_response.content = b"backup-bytes"
        mock_onedrive_deps["requests"].get.return_value = download_response

        target = tmp_path / "downloaded.tmas-backup.zip"
        result = provider.download("file-1", target)

        assert result == target
        assert target.read_bytes() == b"backup-bytes"

    def test_delete_calls_graph_api(self, provider, mock_onedrive_deps):
        provider._access_token = "token"
        delete_response = MagicMock(status_code=204)
        mock_onedrive_deps["requests"].delete.return_value = delete_response

        assert provider.delete("file-1") is True
        mock_onedrive_deps["requests"].delete.assert_called_once()
