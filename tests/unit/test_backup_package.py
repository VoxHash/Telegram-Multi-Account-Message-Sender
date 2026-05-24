"""
Unit tests for cloud backup package builder (MVP-1).
"""

import json
import zipfile
from io import BytesIO
from pathlib import Path
import pytest

from app.services.cloud import (
    BACKUP_SCHEMA_VERSION,
    BackupPackageBuilder,
    BackupPackageError,
)
from app.services.cloud.backup_package import (
    BACKUP_FILE_EXTENSION,
    DATABASE_FILENAME,
    MANIFEST_FILENAME,
    SETTINGS_FILENAME,
)


@pytest.fixture
def file_db(tmp_path, monkeypatch):
    """SQLite file database for backup_database()."""
    from app.services import close_database, db as db_module
    from app.services.settings import reload_settings

    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    close_database()
    db_module.db_service._initialized = False
    db_module.db_service.engine = None
    db_module.db_service.settings = reload_settings()

    from app.services import initialize_database

    initialize_database()
    yield db_file
    close_database()
    db_module.db_service._initialized = False
    db_module.db_service.engine = None


@pytest.fixture
def builder():
    return BackupPackageBuilder()


class TestBackupPackageBuilder:
    """Tests for BackupPackageBuilder."""

    def test_generate_filename_format(self):
        name = BackupPackageBuilder.generate_filename()
        assert name.startswith("telegram-sender-backup-")
        assert name.endswith(BACKUP_FILE_EXTENSION)

    def test_build_and_verify_unencrypted(self, builder, file_db, tmp_path):
        output = tmp_path / "backup.tmas-backup.zip"
        builder.build(output, include_settings=True)

        assert output.exists()
        assert zipfile.is_zipfile(output)

        manifest = builder.verify(output)
        assert manifest["schema_version"] == BACKUP_SCHEMA_VERSION
        assert manifest["encrypted"] is False
        assert DATABASE_FILENAME in manifest["files"]
        assert SETTINGS_FILENAME in manifest["files"]

    def test_extract_returns_database_file(self, builder, file_db, tmp_path):
        package = tmp_path / "backup.tmas-backup.zip"
        extract_dir = tmp_path / "extracted"
        builder.build(package, include_settings=False)

        extracted = builder.extract(package, extract_dir)

        assert DATABASE_FILENAME in extracted
        assert extracted[DATABASE_FILENAME].exists()
        assert extracted[DATABASE_FILENAME].stat().st_size > 0

    def test_build_encrypted_requires_password_to_verify(self, builder, file_db, tmp_path):
        package = tmp_path / "encrypted.tmas-backup.zip"
        builder.build(package, password="secret-backup-pass", include_settings=False)

        assert not zipfile.is_zipfile(package)

        with pytest.raises(BackupPackageError):
            builder.verify(package)

        manifest = builder.verify(package, password="secret-backup-pass")
        assert manifest["encrypted"] is True

    def test_verify_fails_on_checksum_tamper(self, builder, file_db, tmp_path):
        package = tmp_path / "backup.tmas-backup.zip"
        builder.build(package, include_settings=False)

        tampered = tmp_path / "tampered.tmas-backup.zip"
        buffer = BytesIO()
        with zipfile.ZipFile(package, "r") as source:
            manifest = json.loads(source.read(MANIFEST_FILENAME).decode("utf-8"))
            manifest["files"][DATABASE_FILENAME]["sha256"] = "0" * 64
            with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as dest:
                for name in source.namelist():
                    data = source.read(name)
                    if name == MANIFEST_FILENAME:
                        data = json.dumps(manifest, indent=2).encode("utf-8")
                    dest.writestr(name, data)
        tampered.write_bytes(buffer.getvalue())

        with pytest.raises(BackupPackageError):
            builder.verify(tampered)

    def test_verify_fails_on_wrong_password(self, builder, file_db, tmp_path):
        package = tmp_path / "encrypted.tmas-backup.zip"
        builder.build(package, password="correct-password", include_settings=False)

        with pytest.raises(BackupPackageError):
            builder.verify(package, password="wrong-password")

    def test_manifest_lists_checksums_matching_zip(self, builder, file_db, tmp_path):
        package = tmp_path / "backup.tmas-backup.zip"
        builder.build(package, include_settings=True)

        manifest = builder.verify(package)
        with zipfile.ZipFile(package, "r") as archive:
            inner_manifest = json.loads(archive.read(MANIFEST_FILENAME).decode("utf-8"))
            for name, meta in inner_manifest["files"].items():
                content = archive.read(name)
                assert meta["size_bytes"] == len(content)
                assert meta["sha256"] == manifest["files"][name]["sha256"]


class TestCloudProviderInterface:
    """Ensure CloudProvider ABC cannot be instantiated without implementation."""

    def test_cloud_provider_is_abstract(self):
        from app.services.cloud import CloudProvider

        with pytest.raises(TypeError):
            CloudProvider()  # type: ignore[abstract]

    def test_mock_provider_satisfies_interface(self):
        from app.services.cloud import CloudProvider, RemoteBackupItem
        from datetime import datetime, timezone

        class MockProvider(CloudProvider):
            @property
            def provider_name(self) -> str:
                return "mock"

            def authenticate(self) -> bool:
                return True

            def upload(self, local_path: Path, remote_name: str) -> str:
                return "remote-1"

            def download(self, remote_id: str, local_path: Path) -> Path:
                return local_path

            def list_backups(self):
                return [
                    RemoteBackupItem(
                        remote_id="remote-1",
                        name="backup.zip",
                        size_bytes=100,
                        created_at=datetime.now(timezone.utc),
                    )
                ]

            def delete(self, remote_id: str) -> bool:
                return True

        provider = MockProvider()
        assert provider.authenticate() is True
        assert provider.list_backups()[0].remote_id == "remote-1"
