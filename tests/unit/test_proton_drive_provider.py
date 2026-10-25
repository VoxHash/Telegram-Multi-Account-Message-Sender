"""
Unit tests for Proton Drive CLI-backed cloud provider and CloudBackupService paths.
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud.backup_package import DATABASE_FILENAME
from app.services.cloud.cloud_backup_service import CloudBackupService, CloudBackupServiceError
from app.services.cloud.network import is_offline_error_message
from app.services.cloud.proton_drive_provider import (
    DEFAULT_PROTON_DRIVE_FOLDER,
    ProtonDriveError,
    ProtonDriveProvider,
    _map_proton_exception,
    _node_name,
    _normalize_folder,
    _parse_proton_timestamp,
)
from app.services.cloud.provider_base import RemoteBackupItem


def _settings(
    *,
    cli=None,
    folder="/my-files/TMAS/backups",
    app_data_dir="/tmp/app_data",
):
    return MagicMock(
        proton_drive_cli=cli,
        proton_drive_folder=folder,
        app_data_dir=app_data_dir,
    )


class TestProtonDriveHelpers:
    def test_normalize_folder(self):
        assert _normalize_folder(None) == DEFAULT_PROTON_DRIVE_FOLDER
        assert _normalize_folder("TMAS/backups") == "/my-files/TMAS/backups"
        assert _normalize_folder("/my-files/TMAS/backups/") == "/my-files/TMAS/backups"

    def test_parse_proton_timestamp(self):
        aware = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)
        assert _parse_proton_timestamp(aware) == aware
        parsed = _parse_proton_timestamp("2026-10-25T12:00:00Z")
        assert parsed.year == 2026

    def test_node_name(self):
        assert _node_name({"name": {"ok": True, "value": "a.tmas-backup.zip"}}) == (
            "a.tmas-backup.zip"
        )
        assert _node_name({"name": "plain"}) == "plain"

    def test_map_proton_exception_offline(self):
        mapped = _map_proton_exception(
            ConnectionError("failed to establish a new connection"),
            operation="backup upload",
        )
        assert isinstance(mapped, ProtonDriveError)
        assert is_offline_error_message(str(mapped))

    def test_map_need_login(self):
        mapped = _map_proton_exception(
            RuntimeError("You need to login first"),
            operation="authentication",
        )
        assert "auth login" in str(mapped)


class TestProtonDriveProvider:
    def test_is_configured_with_runner(self):
        provider = ProtonDriveProvider(runner=lambda *a, **k: [])
        assert provider.is_configured() is True

    def test_authenticate_lists_root(self, monkeypatch):
        calls = []

        def runner(args, *, timeout, json_out):
            calls.append((list(args), json_out))
            assert args[:3] == ["filesystem", "list", "/"]
            return [{"path": "/my-files"}]

        monkeypatch.setattr(
            "app.services.cloud.proton_drive_provider.get_settings",
            lambda: _settings(),
        )
        provider = ProtonDriveProvider(runner=runner)
        assert provider.authenticate() is True
        assert provider._verified is True
        assert calls

    def test_authenticate_need_login(self, monkeypatch):
        def runner(args, *, timeout, json_out):
            raise ProtonDriveError("You need to login first")

        monkeypatch.setattr(
            "app.services.cloud.proton_drive_provider.get_settings",
            lambda: _settings(),
        )
        provider = ProtonDriveProvider(runner=runner)
        with pytest.raises(ProtonDriveError, match="need to login|auth login"):
            provider.authenticate()

    def test_upload_download_list_delete(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "app.services.cloud.proton_drive_provider.get_settings",
            lambda: _settings(),
        )
        state = {"uploaded": None, "folders": {"/my-files": {"TMAS"}, "/my-files/TMAS": {"backups"}}}

        def runner(args, *, timeout, json_out):
            if args[:2] == ["filesystem", "list"]:
                path = args[2]
                if path == "/my-files/TMAS/backups":
                    if state["uploaded"] is None:
                        return []
                    return [
                        {
                            "type": "file",
                            "name": {"ok": True, "value": "pkg.tmas-backup.zip"},
                            "creationTime": "2026-10-25T12:00:00Z",
                            "activeRevision": {"claimedSize": len(state["uploaded"])},
                        },
                        {
                            "type": "file",
                            "name": {"ok": True, "value": "notes.txt"},
                            "activeRevision": {"claimedSize": 1},
                        },
                    ]
                if path == "/trash":
                    return [
                        {
                            "type": "file",
                            "name": {"ok": True, "value": "pkg.tmas-backup.zip"},
                        }
                    ]
                names = state["folders"].get(path, set())
                return [
                    {"type": "folder", "name": {"ok": True, "value": n}} for n in names
                ]
            if args[:2] == ["filesystem", "upload"]:
                local = Path(args[-2])
                state["uploaded"] = local.read_bytes()
                return ""
            if args[:2] == ["filesystem", "download"]:
                dest = Path(args[-1])
                dest.mkdir(parents=True, exist_ok=True)
                (dest / "pkg.tmas-backup.zip").write_bytes(state["uploaded"] or b"")
                return ""
            if args[:2] == ["filesystem", "trash"]:
                return ""
            if args[:2] == ["filesystem", "delete"]:
                return ""
            if args[:2] == ["filesystem", "create-folder"]:
                parent, name = args[2], args[3]
                state["folders"].setdefault(parent, set()).add(name)
                return ""
            raise AssertionError(f"unexpected args: {args}")

        provider = ProtonDriveProvider(runner=runner)
        provider._verified = True

        local = tmp_path / "pkg.tmas-backup.zip"
        local.write_bytes(b"zip-bytes")

        path = provider.upload(local, "pkg.tmas-backup.zip")
        assert path == "/my-files/TMAS/backups/pkg.tmas-backup.zip"
        assert state["uploaded"] == b"zip-bytes"

        out = tmp_path / "out.zip"
        provider.download(path, out)
        assert out.read_bytes() == b"zip-bytes"

        items = provider.list_backups()
        assert len(items) == 1
        assert items[0].remote_id == path
        assert items[0].name == "pkg.tmas-backup.zip"
        assert items[0].size_bytes == 9

        assert provider.delete(path) is True

    def test_list_missing_folder_returns_empty(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.cloud.proton_drive_provider.get_settings",
            lambda: _settings(),
        )

        def runner(args, *, timeout, json_out):
            raise ProtonDriveError("node not found (code 2501)")

        provider = ProtonDriveProvider(runner=runner)
        provider._verified = True
        assert provider.list_backups() == []

    def test_disconnect_clears_verified(self):
        provider = ProtonDriveProvider(runner=lambda *a, **k: [])
        provider._verified = True
        provider.disconnect()
        assert provider._verified is False


class TestCloudBackupServiceProtonDrive:
    @pytest.fixture
    def mock_proton(self):
        provider = MagicMock()
        provider.is_authenticated.return_value = True
        provider.is_configured.return_value = True
        provider.upload.return_value = "/my-files/TMAS/backups/remote.tmas-backup.zip"
        provider.list_backups.return_value = [
            RemoteBackupItem(
                remote_id="/my-files/TMAS/backups/remote.tmas-backup.zip",
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

    def test_backup_requires_connection(self, mock_proton, mock_builder):
        mock_proton.is_authenticated.return_value = False
        service = CloudBackupService(
            proton_drive_provider=mock_proton, package_builder=mock_builder
        )
        with pytest.raises(
            CloudBackupServiceError, match="Verify Proton Drive CLI session"
        ):
            service.backup_to_proton_drive()

    def test_backup_uploads_package(self, mock_proton, mock_builder):
        service = CloudBackupService(
            proton_drive_provider=mock_proton, package_builder=mock_builder
        )
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=True,
        ):
            with patch(
                "app.services.cloud.cloud_backup_service.BackupPackageBuilder.generate_filename",
                return_value="telegram-sender-backup-test.tmas-backup.zip",
            ):
                remote_id = service.backup_to_proton_drive(password="secret")
        assert remote_id == "/my-files/TMAS/backups/remote.tmas-backup.zip"
        mock_proton.upload.assert_called_once()

    def test_list_fails_fast_when_offline(self, mock_proton, mock_builder):
        service = CloudBackupService(
            proton_drive_provider=mock_proton, package_builder=mock_builder
        )
        with patch(
            "app.services.cloud.cloud_backup_service.check_network_available",
            return_value=False,
        ):
            with pytest.raises(CloudBackupServiceError) as exc_info:
                service.list_proton_drive_backups()
        assert is_offline_error_message(str(exc_info.value))
        mock_proton.list_backups.assert_not_called()

    def test_restore_from_proton_drive(
        self, mock_proton, mock_builder, tmp_path, monkeypatch
    ):
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
            proton_drive_provider=mock_proton, package_builder=mock_builder
        )

        def _fake_backup_database(backup_path):
            path = Path(backup_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"pre-restore-db")
            return path

        def _fake_download(_remote_id, local_path):
            Path(local_path).write_bytes(b"zip")
            return Path(local_path)

        mock_proton.download.side_effect = _fake_download

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
                    pre_restore = service.restore_from_proton_drive(
                        "/my-files/TMAS/backups/remote.tmas-backup.zip"
                    )

        assert pre_restore.exists()
        mock_restore.assert_called_once_with(db_path)
