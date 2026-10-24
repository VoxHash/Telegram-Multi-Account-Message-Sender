"""
Unit tests for S3-compatible cloud provider and CloudBackupService S3 paths.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud.backup_package import DATABASE_FILENAME
from app.services.cloud.cloud_backup_service import CloudBackupService, CloudBackupServiceError
from app.services.cloud.network import is_offline_error_message
from app.services.cloud.provider_base import RemoteBackupItem
from app.services.cloud.s3_compatible import (
    S3CompatibleError,
    S3CompatibleProvider,
    _map_s3_exception,
    _normalize_prefix,
    _parse_s3_timestamp,
)


def _settings(
    *,
    access_key="AKIAEXAMPLE",
    secret="secret",
    bucket="tmas-backups",
    region="us-east-1",
    endpoint=None,
    prefix="tmas/backups/",
    app_data_dir="/tmp/app_data",
):
    return MagicMock(
        s3_access_key_id=access_key,
        s3_secret_access_key=secret,
        s3_bucket=bucket,
        s3_region=region,
        s3_endpoint_url=endpoint,
        s3_prefix=prefix,
        app_data_dir=app_data_dir,
    )


class TestS3Helpers:
    def test_normalize_prefix(self):
        assert _normalize_prefix(None) == "tmas/backups/"
        assert _normalize_prefix("backups") == "backups/"
        assert _normalize_prefix("/tmas/backups/") == "tmas/backups/"

    def test_parse_s3_timestamp(self):
        aware = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
        assert _parse_s3_timestamp(aware) == aware
        naive = datetime(2026, 10, 24, 12, 0)
        assert _parse_s3_timestamp(naive).tzinfo is not None

    def test_map_s3_exception_offline(self):
        mapped = _map_s3_exception(
            ConnectionError("failed to establish a new connection"),
            operation="backup upload",
        )
        assert isinstance(mapped, S3CompatibleError)
        assert is_offline_error_message(str(mapped))


class TestS3CompatibleProvider:
    def test_is_configured_requires_keys(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.s3_compatible.get_settings",
            lambda: _settings(access_key=None, secret=None, bucket=None),
        )
        assert S3CompatibleProvider.is_configured() is False

        monkeypatch.setattr(
            "app.services.cloud.s3_compatible.get_settings",
            lambda: _settings(),
        )
        assert S3CompatibleProvider.is_configured() is True

    def test_authenticate_head_bucket(self, monkeypatch):
        client = MagicMock()
        monkeypatch.setattr(
            "app.services.cloud.s3_compatible.get_settings",
            lambda: _settings(),
        )
        provider = S3CompatibleProvider(client=client)
        assert provider.authenticate() is True
        client.head_bucket.assert_called_once_with(Bucket="tmas-backups")

    def test_authenticate_requires_config(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.s3_compatible.get_settings",
            lambda: _settings(access_key=None, secret=None, bucket=None),
        )
        provider = S3CompatibleProvider(client=MagicMock())
        with pytest.raises(S3CompatibleError, match="S3 credentials are required"):
            provider.authenticate()

    def test_upload_download_list_delete(self, monkeypatch, tmp_path):
        client = MagicMock()
        monkeypatch.setattr(
            "app.services.cloud.s3_compatible.get_settings",
            lambda: _settings(),
        )
        provider = S3CompatibleProvider(client=client)
        provider._verified = True

        local = tmp_path / "pkg.tmas-backup.zip"
        local.write_bytes(b"zip-bytes")

        key = provider.upload(local, "pkg.tmas-backup.zip")
        assert key == "tmas/backups/pkg.tmas-backup.zip"
        client.upload_file.assert_called_once()

        out = tmp_path / "out.zip"
        provider.download(key, out)
        client.download_file.assert_called_once_with("tmas-backups", key, str(out))

        client.get_paginator.return_value.paginate.return_value = [
            {
                "Contents": [
                    {
                        "Key": "tmas/backups/pkg.tmas-backup.zip",
                        "Size": 9,
                        "LastModified": datetime(2026, 10, 24, tzinfo=timezone.utc),
                    },
                    {"Key": "tmas/backups/notes.txt", "Size": 1},
                ]
            }
        ]
        items = provider.list_backups()
        assert len(items) == 1
        assert items[0].remote_id == key
        assert items[0].name == "pkg.tmas-backup.zip"

        assert provider.delete(key) is True
        client.delete_object.assert_called_once_with(Bucket="tmas-backups", Key=key)

    def test_disconnect_clears_client(self):
        provider = S3CompatibleProvider(client=MagicMock())
        provider.disconnect()
        assert provider._client is None
        assert provider._verified is False


class TestCloudBackupServiceS3:
    @pytest.fixture
    def mock_s3(self):
        provider = MagicMock()
        provider.is_authenticated.return_value = True
        provider.upload.return_value = "tmas/backups/remote.tmas-backup.zip"
        provider.list_backups.return_value = [
            RemoteBackupItem(
                remote_id="tmas/backups/remote.tmas-backup.zip",
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

    def test_backup_requires_connection(self, mock_s3, mock_builder):
        mock_s3.is_authenticated.return_value = False
        service = CloudBackupService(s3_provider=mock_s3, package_builder=mock_builder)
        with pytest.raises(CloudBackupServiceError, match="Verify S3 credentials"):
            service.backup_to_s3()

    def test_backup_uploads_package(self, mock_s3, mock_builder):
        service = CloudBackupService(s3_provider=mock_s3, package_builder=mock_builder)
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=True,
        ):
            with patch(
                "app.services.cloud.cloud_backup_service.BackupPackageBuilder.generate_filename",
                return_value="telegram-sender-backup-test.tmas-backup.zip",
            ):
                remote_id = service.backup_to_s3(password="secret")
        assert remote_id == "tmas/backups/remote.tmas-backup.zip"
        mock_s3.upload.assert_called_once()

    def test_list_fails_fast_when_offline(self, mock_s3, mock_builder):
        service = CloudBackupService(s3_provider=mock_s3, package_builder=mock_builder)
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=False,
        ):
            with pytest.raises(CloudBackupServiceError) as exc_info:
                service.list_s3_backups()
        assert is_offline_error_message(str(exc_info.value))
        mock_s3.list_backups.assert_not_called()

    def test_restore_from_s3(self, mock_s3, mock_builder, tmp_path, monkeypatch):
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
        service = CloudBackupService(s3_provider=mock_s3, package_builder=mock_builder)

        def _fake_backup_database(backup_path):
            path = Path(backup_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"pre-restore-db")
            return path

        def _fake_download(_remote_id, local_path):
            Path(local_path).write_bytes(b"zip")
            return Path(local_path)

        mock_s3.download.side_effect = _fake_download

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
                    pre_restore = service.restore_from_s3(
                        "tmas/backups/remote.tmas-backup.zip"
                    )

        assert pre_restore.exists()
        mock_restore.assert_called_once_with(db_path)
