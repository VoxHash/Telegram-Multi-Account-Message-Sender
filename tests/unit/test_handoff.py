"""
Unit tests for Phase 4 single-operator handoff export/import.
"""

import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.cloud import (
    PURPOSE_OPERATOR_HANDOFF,
    SESSIONS_DIRNAME,
    BackupPackageBuilder,
    CloudBackupService,
    CloudBackupServiceError,
)
from app.services.cloud.backup_package import DATABASE_FILENAME
from app.services.handoff import parse_handoff_argv, run_handoff_cli


@pytest.fixture
def file_db(tmp_path, monkeypatch):
    """SQLite file database for backup_database()."""
    from app.services import close_database, db as db_module
    from app.services.settings import reload_settings

    db_file = tmp_path / "app.db"
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    (sessions_dir / "session_+10000000000.session").write_bytes(b"telethon-session")

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path / "app_data"))
    monkeypatch.setenv("SESSIONS_DIR", str(sessions_dir))
    close_database()
    db_module.db_service._initialized = False
    db_module.db_service.engine = None
    db_module.db_service.settings = reload_settings()

    from app.services import initialize_database

    initialize_database()
    yield {"db": db_file, "sessions": sessions_dir}
    close_database()
    db_module.db_service._initialized = False
    db_module.db_service.engine = None


class TestParseHandoffArgv:
    def test_detects_export(self):
        is_h, action, path, password, include_sessions, entities, mode = parse_handoff_argv(
            ["telegram-sender", "handoff-export", "/tmp/out.tmas-backup.zip", "-p", "secret"]
        )
        assert is_h is True
        assert action == "export"
        assert path == Path("/tmp/out.tmas-backup.zip")
        assert password == "secret"
        assert include_sessions is True
        assert entities is None
        assert mode is None

    def test_detects_import_and_no_sessions(self):
        is_h, action, path, password, include_sessions, entities, mode = parse_handoff_argv(
            [
                "telegram-sender",
                "handoff-import",
                "./pkg.tmas-backup.zip",
                "--no-sessions",
            ]
        )
        assert is_h is True
        assert action == "import"
        assert path == Path("./pkg.tmas-backup.zip")
        assert password is None
        # --no-sessions only affects export; flag still parsed for argv consistency
        assert include_sessions is False
        assert entities is None
        assert mode is None

    def test_non_handoff_argv(self):
        is_h, *_ = parse_handoff_argv(["telegram-sender", "web-monitor"])
        assert is_h is False

    def test_help_action(self):
        is_h, action, *_ = parse_handoff_argv(["telegram-sender", "handoff-export", "--help"])
        assert is_h is True
        assert action == "help"


class TestHandoffPackage:
    def test_build_includes_sessions_and_purpose(self, file_db, tmp_path):
        builder = BackupPackageBuilder()
        output = tmp_path / "handoff.tmas-backup.zip"
        builder.build(
            output,
            include_settings=True,
            include_sessions=True,
            purpose=PURPOSE_OPERATOR_HANDOFF,
        )

        assert zipfile.is_zipfile(output)
        manifest = builder.verify(output)
        assert manifest["purpose"] == PURPOSE_OPERATOR_HANDOFF
        assert manifest["include_sessions"] is True
        assert DATABASE_FILENAME in manifest["files"]
        session_keys = [k for k in manifest["files"] if k.startswith(f"{SESSIONS_DIRNAME}/")]
        assert session_keys
        assert any("session_+10000000000.session" in k for k in session_keys)

    def test_export_local_package_writes_file(self, file_db, tmp_path):
        service = CloudBackupService()
        out = tmp_path / "operator-handoff.tmas-backup.zip"
        built = service.export_local_package(out, password=None, include_sessions=True)
        assert built == out
        assert out.exists()
        manifest = BackupPackageBuilder().verify(out)
        assert manifest["purpose"] == PURPOSE_OPERATOR_HANDOFF

    def test_export_appends_extension(self, file_db, tmp_path):
        service = CloudBackupService()
        built = service.export_local_package(tmp_path / "move-me", include_sessions=False)
        assert str(built).endswith(".tmas-backup.zip")
        assert built.exists()

    def test_import_restores_sessions(self, file_db, tmp_path, monkeypatch):
        service = CloudBackupService()
        package = tmp_path / "handoff.tmas-backup.zip"
        service.export_local_package(package, include_sessions=True)

        dest_sessions = tmp_path / "dest_sessions"
        dest_sessions.mkdir()
        app_data = tmp_path / "dest_app_data"
        app_data.mkdir()

        monkeypatch.setattr(
            service,
            "settings",
            MagicMock(app_data_dir=str(app_data), sessions_dir=str(dest_sessions)),
        )

        with patch(
            "app.services.cloud.cloud_backup_service.backup_database"
        ) as mock_backup:
            with patch(
                "app.services.cloud.cloud_backup_service.restore_database"
            ) as mock_restore:

                def _snap(path):
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                    Path(path).write_bytes(b"pre")
                    return Path(path)

                mock_backup.side_effect = _snap
                pre = service.restore_from_local_package(package)

        assert pre.exists()
        mock_restore.assert_called_once()
        restored = list(dest_sessions.rglob("*.session"))
        assert len(restored) == 1
        assert restored[0].read_bytes() == b"telethon-session"

    def test_restore_rejects_unsafe_session_path(self, tmp_path):
        service = CloudBackupService()
        service.settings = MagicMock(
            app_data_dir=str(tmp_path / "app_data"),
            sessions_dir=str(tmp_path / "sessions"),
        )
        with pytest.raises(CloudBackupServiceError, match="Unsafe session path"):
            service._restore_session_files(
                {f"{SESSIONS_DIRNAME}/../evil.session": tmp_path / "x"}
            )


class TestHandoffCli:
    def test_run_export_cli_with_explicit_empty_password_flag(self, file_db, tmp_path):
        out = tmp_path / "cli-handoff.tmas-backup.zip"
        with patch("app.services.handoff.getpass.getpass", side_effect=AssertionError):
            code = run_handoff_cli(
                [
                    "telegram-sender",
                    "handoff-export",
                    str(out),
                    "--password=",
                ]
            )
        assert code == 0
        assert out.exists()

    def test_run_import_cli(self, file_db, tmp_path):
        package = tmp_path / "pkg.tmas-backup.zip"
        CloudBackupService().export_local_package(package, include_sessions=True)
        pre = tmp_path / "pre.db"
        pre.write_bytes(b"x")

        with patch("app.services.handoff.getpass.getpass", side_effect=AssertionError):
            with patch(
                "app.services.handoff.CloudBackupService.restore_from_local_package",
                return_value=pre,
            ) as mock_imp:
                code = run_handoff_cli(
                    [
                        "telegram-sender",
                        "handoff-import",
                        str(package),
                        "--password=",
                    ]
                )
        assert code == 0
        mock_imp.assert_called_once()

    def test_run_help(self, capsys):
        code = run_handoff_cli(["telegram-sender", "handoff-export", "--help"])
        assert code == 0
        assert "handoff-export" in capsys.readouterr().out

    def test_missing_path(self, capsys):
        code = run_handoff_cli(["telegram-sender", "handoff-import"])
        assert code == 2
