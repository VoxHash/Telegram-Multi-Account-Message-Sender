"""
Build, verify, and extract `.tmas-backup.zip` cloud backup packages.
"""

import base64
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import cast, Any, Dict, Optional, Sequence, Set

from app import __version__
from app.services import get_logger
from app.services.db import backup_database
from app.services.settings import get_settings
from app.utils.crypto import decrypt_data, encrypt_data

from .entity_transfer import (
    ENTITIES_FILENAME,
    VALID_ENTITY_KINDS,
    collect_entities,
)

BACKUP_SCHEMA_VERSION = "1"
BACKUP_FILE_EXTENSION = ".tmas-backup.zip"
MANIFEST_FILENAME = "manifest.json"
DATABASE_FILENAME = "app.db"
SETTINGS_FILENAME = "settings-export.json"
SESSIONS_DIRNAME = "sessions"
PURPOSE_OPERATOR_HANDOFF = "operator_handoff"
PURPOSE_CLOUD_BACKUP = "cloud_backup"
PURPOSE_ENTITY_TRANSFER = "entity_transfer"

EXCLUDED_SETTINGS_KEYS = frozenset(
    {
        "telegram_api_id",
        "telegram_api_hash",
        "sentry_dsn",
        "http_proxy",
        "https_proxy",
        "socks5_proxy",
        "google_drive_client_id",
        "google_drive_client_secret",
    }
)


class BackupPackageError(Exception):
    """Raised when backup package build, verify, or extract fails."""


class BackupPackageBuilder:
    """Creates and validates application backup packages for cloud upload."""

    def __init__(self) -> None:
        self.logger = get_logger()

    @staticmethod
    def generate_filename(timestamp: Optional[datetime] = None) -> str:
        """Generate a standard backup archive filename."""
        ts = timestamp or datetime.now(timezone.utc)
        stamp = ts.strftime("%Y%m%d_%H%M%S")
        return f"telegram-sender-backup-{stamp}{BACKUP_FILE_EXTENSION}"

    @staticmethod
    def generate_handoff_filename(timestamp: Optional[datetime] = None) -> str:
        """Generate a filename for single-operator handoff packages."""
        ts = timestamp or datetime.now(timezone.utc)
        stamp = ts.strftime("%Y%m%d_%H%M%S")
        return f"telegram-sender-handoff-{stamp}{BACKUP_FILE_EXTENSION}"

    @staticmethod
    def generate_entities_filename(timestamp: Optional[datetime] = None) -> str:
        """Generate a filename for selective template/campaign packages."""
        ts = timestamp or datetime.now(timezone.utc)
        stamp = ts.strftime("%Y%m%d_%H%M%S")
        return f"telegram-sender-entities-{stamp}{BACKUP_FILE_EXTENSION}"

    def build(
        self,
        output_path: Path,
        *,
        password: Optional[str] = None,
        include_settings: bool = True,
        include_sessions: bool = False,
        purpose: Optional[str] = None,
        entity_kinds: Optional[Sequence[str]] = None,
    ) -> Path:
        """
        Build a backup package at ``output_path``.

        When ``password`` is set, the zip payload is encrypted (AES via Fernet + PBKDF2).
        When ``include_sessions`` is True, Telethon session files under ``sessions_dir``
        are packaged for machine-to-machine operator handoff.
        When ``entity_kinds`` is set (``templates`` / ``campaigns``), build a selective
        package with ``entities.json`` and omit the full database and sessions.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        kinds: Optional[Set[str]] = None
        if entity_kinds is not None:
            kinds = {str(k).strip().lower() for k in entity_kinds if str(k).strip()}
            if not kinds:
                raise BackupPackageError("entity_kinds must include templates and/or campaigns")
            unknown = kinds - VALID_ENTITY_KINDS
            if unknown:
                raise BackupPackageError(f"Unknown entity kinds: {sorted(unknown)}")

        with tempfile.TemporaryDirectory() as temp_dir:
            staging_dir = Path(temp_dir) / "package"
            staging_dir.mkdir(parents=True, exist_ok=True)

            files_meta: Dict[str, Dict[str, Any]] = {}
            effective_purpose: Optional[str] = purpose

            if kinds is not None:
                entities_payload = collect_entities(kinds)
                entities_path = staging_dir / ENTITIES_FILENAME
                entities_path.write_text(
                    json.dumps(entities_payload, indent=2),
                    encoding="utf-8",
                )
                files_meta[ENTITIES_FILENAME] = self._file_metadata(entities_path)
                effective_purpose = purpose or PURPOSE_ENTITY_TRANSFER
                include_sessions = False
            else:
                db_backup_path = staging_dir / DATABASE_FILENAME
                backup_database(db_backup_path)
                files_meta[DATABASE_FILENAME] = self._file_metadata(db_backup_path)

                if include_settings:
                    settings_path = staging_dir / SETTINGS_FILENAME
                    settings_path.write_text(
                        json.dumps(self._export_safe_settings(), indent=2),
                        encoding="utf-8",
                    )
                    files_meta[SETTINGS_FILENAME] = self._file_metadata(settings_path)

                if include_sessions:
                    files_meta.update(self._stage_session_files(staging_dir))

            manifest: Dict[str, Any] = {
                "schema_version": BACKUP_SCHEMA_VERSION,
                "app_version": __version__,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "encrypted": bool(password),
                "include_sessions": bool(include_sessions) if kinds is None else False,
                "files": files_meta,
            }
            if kinds is not None:
                manifest["entity_kinds"] = sorted(kinds)
                manifest["default_import_mode"] = "merge"
            if effective_purpose:
                manifest["purpose"] = effective_purpose
            manifest_path = staging_dir / MANIFEST_FILENAME
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            zip_bytes = self._create_zip_bytes(staging_dir)

        if password:
            payload = encrypt_data(base64.b64encode(zip_bytes).decode("ascii"), password)
            output_path.write_text(payload, encoding="utf-8")
        else:
            output_path.write_bytes(zip_bytes)

        self.logger.info(f"Backup package created: {output_path}")
        return output_path

    def verify(self, package_path: Path, *, password: Optional[str] = None) -> Dict[str, Any]:
        """Validate package integrity and return the manifest."""
        package_path = Path(package_path)
        if not package_path.exists():
            raise BackupPackageError(f"Package not found: {package_path}")

        zip_bytes = self._read_package_bytes(package_path, password)

        try:
            archive = zipfile.ZipFile(BytesIO(zip_bytes), "r")
        except zipfile.BadZipFile as exc:
            raise BackupPackageError("Invalid or corrupted backup package") from exc

        with archive:
            if MANIFEST_FILENAME not in archive.namelist():
                raise BackupPackageError("Manifest missing from backup package")

            manifest = json.loads(archive.read(MANIFEST_FILENAME).decode("utf-8"))
            self._validate_manifest(manifest)

            for filename, meta in manifest["files"].items():
                if filename not in archive.namelist():
                    raise BackupPackageError(f"Expected file missing from package: {filename}")

                content = archive.read(filename)
                digest = hashlib.sha256(content).hexdigest()
                if digest != meta["sha256"]:
                    raise BackupPackageError(f"Checksum mismatch for {filename}")

        return cast(Dict[str, Any], manifest)

    def extract(
        self,
        package_path: Path,
        output_dir: Path,
        *,
        password: Optional[str] = None,
    ) -> Dict[str, Path]:
        """Extract package files into ``output_dir`` and return paths by filename."""
        package_path = Path(package_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest = self.verify(package_path, password=password)
        zip_bytes = self._read_package_bytes(package_path, password)
        extracted: Dict[str, Path] = {}

        with zipfile.ZipFile(BytesIO(zip_bytes), "r") as archive:
            for filename in manifest["files"]:
                target = output_dir / filename
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(filename) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted[filename] = target

        return extracted

    def _read_package_bytes(self, package_path: Path, password: Optional[str]) -> bytes:
        raw = package_path.read_bytes()
        if password:
            try:
                decrypted_b64 = decrypt_data(raw.decode("utf-8"), password)
            except ValueError as exc:
                raise BackupPackageError("Invalid password or corrupted encrypted package") from exc
            try:
                return base64.b64decode(decrypted_b64.encode("ascii"))
            except Exception as exc:
                raise BackupPackageError("Decrypted package payload is invalid") from exc

        if not zipfile.is_zipfile(BytesIO(raw)):
            raise BackupPackageError(
                "Package is not a valid zip archive; a password may be required"
            )
        return raw

    @staticmethod
    def _create_zip_bytes(staging_dir: Path) -> bytes:
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in sorted(staging_dir.rglob("*")):
                if file_path.is_file():
                    archive.write(
                        file_path,
                        arcname=file_path.relative_to(staging_dir).as_posix(),
                    )
        return buffer.getvalue()

    def _stage_session_files(self, staging_dir: Path) -> Dict[str, Dict[str, Any]]:
        """Copy Telethon session files into the package staging tree."""
        settings = get_settings()
        sessions_src = Path(settings.sessions_dir)
        meta: Dict[str, Dict[str, Any]] = {}
        if not sessions_src.is_dir():
            return meta

        sessions_staging = staging_dir / SESSIONS_DIRNAME
        for src in sorted(sessions_src.rglob("*")):
            if not src.is_file():
                continue
            rel = src.relative_to(sessions_src)
            dest = sessions_staging / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            arcname = f"{SESSIONS_DIRNAME}/{rel.as_posix()}"
            meta[arcname] = self._file_metadata(dest)
        return meta

    @staticmethod
    def _file_metadata(path: Path) -> Dict[str, Any]:
        data = path.read_bytes()
        return {
            "sha256": hashlib.sha256(data).hexdigest(),
            "size_bytes": len(data),
        }

    @staticmethod
    def _export_safe_settings() -> Dict[str, Any]:
        settings = get_settings()
        exported: Dict[str, Any] = {}
        for key, value in settings.model_dump().items():
            if key in EXCLUDED_SETTINGS_KEYS:
                continue
            if isinstance(value, datetime):
                exported[key] = value.isoformat()
            elif hasattr(value, "value"):
                exported[key] = value.value
            else:
                exported[key] = value
        return exported

    @staticmethod
    def _validate_manifest(manifest: Dict[str, Any]) -> None:
        if manifest.get("schema_version") != BACKUP_SCHEMA_VERSION:
            raise BackupPackageError(
                f"Unsupported backup schema: {manifest.get('schema_version')}"
            )
        if "files" not in manifest or not isinstance(manifest["files"], dict):
            raise BackupPackageError("Invalid manifest: missing files section")
        has_db = DATABASE_FILENAME in manifest["files"]
        has_entities = ENTITIES_FILENAME in manifest["files"]
        if not has_db and not has_entities:
            raise BackupPackageError(
                "Invalid manifest: app.db or entities.json entry required"
            )
