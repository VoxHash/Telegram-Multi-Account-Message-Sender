"""
Proton Drive cloud provider for backup upload, list, download, and delete.

Wraps the official ``proton-drive`` CLI (out-of-process). Auth is the CLI's
OS keyring session (``proton-drive auth login``) — TMAS never stores Proton
credentials. Same integration style as VoxHash ``proton-drive-desktop``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence

from app.services import get_logger
from app.services.settings import get_settings

from .backup_package import BACKUP_FILE_EXTENSION
from .network import (
    format_drive_unavailable_error,
    format_offline_error,
    is_network_exception,
)
from .provider_base import CloudProvider, RemoteBackupItem

DEFAULT_PROTON_DRIVE_FOLDER = "/my-files/TMAS/backups"
DEFAULT_CLI_NAME = "proton-drive"
# Auth / short list ops.
DEFAULT_TIMEOUT_SECONDS = 180
# Upload / download of backup packages.
TRANSFER_TIMEOUT_SECONDS = 3600

_ALREADY_EXISTS_RE = re.compile(
    r"already exists|name already|duplicate|"
    r"with that name already exists|code[=:\s]*2500",
    re.IGNORECASE,
)
_NEED_LOGIN_RE = re.compile(r"need to login|not logged in|please log in", re.IGNORECASE)

# Optional injectable runner for unit tests:
# ``(argv, *, timeout, json_out) -> Any`` where argv excludes the binary name.
CliRunner = Callable[..., Any]


class ProtonDriveError(Exception):
    """Raised when Proton Drive CLI operations fail."""


class ProtonDriveProvider(CloudProvider):
    """CLI-backed ``CloudProvider`` for Proton Drive (official ``proton-drive``)."""

    def __init__(
        self,
        *,
        binary: Optional[str] = None,
        runner: Optional[CliRunner] = None,
    ) -> None:
        self.logger = get_logger()
        self._binary_override = binary
        self._runner = runner
        self._verified = False

    @property
    def provider_name(self) -> str:
        return "Proton Drive"

    def is_configured(self) -> bool:
        """Return True when a CLI runner is injected or the binary resolves."""
        if self._runner is not None:
            return True
        try:
            self.resolve_binary(self._binary_override)
            return True
        except ProtonDriveError:
            return False

    @classmethod
    def cli_available(cls) -> bool:
        """Return True when the official CLI binary can be resolved (no runner)."""
        try:
            cls.resolve_binary()
            return True
        except ProtonDriveError:
            return False

    @staticmethod
    def resolve_binary(explicit: Optional[str] = None) -> str:
        """
        Resolve the ``proton-drive`` executable path.

        Order: constructor/settings ``PROTON_DRIVE_CLI``, ``PROTON_DRIVE_BIN``,
        ``PATH``, then ``~/.local/bin/proton-drive``.
        """
        candidates: List[str] = []
        if explicit:
            candidates.append(explicit)
        settings = get_settings()
        configured = (getattr(settings, "proton_drive_cli", None) or "").strip()
        if configured:
            candidates.append(configured)
        # Compat with proton-drive-desktop env name.
        env_bin = (os.environ.get("PROTON_DRIVE_BIN") or "").strip()
        if env_bin:
            candidates.append(env_bin)

        for candidate in candidates:
            path = Path(candidate).expanduser()
            if path.is_file():
                return str(path)

        found = shutil.which(DEFAULT_CLI_NAME)
        if found:
            return found
        home = Path.home() / ".local" / "bin" / DEFAULT_CLI_NAME
        if home.is_file():
            return str(home)
        raise ProtonDriveError(
            "Official proton-drive CLI not found. Install from "
            "https://proton.me/support/drive-cli and ensure it is on PATH "
            "(or set PROTON_DRIVE_CLI to the binary). Then run: "
            "proton-drive auth login"
        )

    def authenticate(self) -> bool:
        """Verify CLI presence and an active keyring session (list ``/``)."""
        if not self.is_configured():
            raise ProtonDriveError(
                "Official proton-drive CLI not found. Install from "
                "https://proton.me/support/drive-cli, set PROTON_DRIVE_CLI if needed, "
                "then run: proton-drive auth login"
            )
        try:
            self._run(["filesystem", "list", "/"], timeout=DEFAULT_TIMEOUT_SECONDS)
        except ProtonDriveError:
            raise
        except Exception as exc:
            raise _map_proton_exception(exc, operation="authentication") from exc

        self._verified = True
        self.logger.info("Proton Drive CLI session verified")
        return True

    def is_authenticated(self) -> bool:
        """Return True when the CLI session verifies (list root succeeds)."""
        if self._verified:
            return True
        if not self.is_configured():
            return False
        try:
            return self.authenticate()
        except ProtonDriveError:
            return False

    def upload(self, local_path: Path, remote_name: str) -> str:
        """Upload a backup package; return the remote POSIX path as remote id."""
        self._require_authenticated()
        local_path = Path(local_path)
        if not local_path.is_file():
            raise ProtonDriveError(f"Local backup package not found: {local_path}")

        folder = _normalize_folder(get_settings().proton_drive_folder)
        name = Path(remote_name).name
        remote_path = f"{folder}/{name}"
        self._ensure_folder(folder)

        try:
            self._run(
                [
                    "filesystem",
                    "upload",
                    "-f",
                    "replace",
                    "-d",
                    "merge",
                    "-t",
                    str(local_path),
                    folder,
                ],
                json_out=False,
                timeout=TRANSFER_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            raise _map_proton_exception(exc, operation="backup upload") from exc

        self.logger.info(f"Uploaded backup to Proton Drive: {remote_path}")
        return remote_path

    def download(self, remote_id: str, local_path: Path) -> Path:
        """Download a remote Proton Drive path to ``local_path``."""
        self._require_authenticated()
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        remote_id = str(remote_id).strip()
        if not remote_id:
            raise ProtonDriveError("Remote Proton Drive path is empty")

        with tempfile.TemporaryDirectory() as temp_dir:
            dest_dir = Path(temp_dir)
            try:
                self._run(
                    [
                        "filesystem",
                        "download",
                        "-f",
                        "skip",
                        "-d",
                        "merge",
                        remote_id,
                        str(dest_dir),
                    ],
                    json_out=False,
                    timeout=TRANSFER_TIMEOUT_SECONDS,
                )
            except Exception as exc:
                raise _map_proton_exception(exc, operation="backup download") from exc

            downloaded = _find_downloaded_file(dest_dir, Path(remote_id).name)
            if downloaded is None:
                raise ProtonDriveError(
                    f"Proton Drive download produced no file for {remote_id}"
                )
            local_path.write_bytes(downloaded.read_bytes())

        self.logger.info(f"Downloaded Proton Drive backup {remote_id} to {local_path}")
        return local_path

    def list_backups(self) -> List[RemoteBackupItem]:
        """List ``.tmas-backup.zip`` files under the configured Proton Drive folder."""
        self._require_authenticated()
        folder = _normalize_folder(get_settings().proton_drive_folder)
        try:
            entries = self._list_entries(folder)
        except ProtonDriveError as exc:
            detail = str(exc).lower()
            if "not found" in detail or "does not exist" in detail or "2501" in detail:
                return []
            raise
        except Exception as exc:
            raise _map_proton_exception(exc, operation="listing backups") from exc

        items: List[RemoteBackupItem] = []
        for entry in entries:
            if str(entry.get("type") or "") != "file":
                continue
            name = _node_name(entry)
            if not name.endswith(BACKUP_FILE_EXTENSION):
                continue
            path = f"{folder}/{name}"
            size = _file_size_bytes(entry)
            items.append(
                RemoteBackupItem(
                    remote_id=path,
                    name=name,
                    size_bytes=size,
                    created_at=_parse_proton_timestamp(
                        entry.get("creationTime") or entry.get("modificationTime")
                    ),
                )
            )
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def delete(self, remote_id: str) -> bool:
        """Trash then permanently delete a remote backup path."""
        self._require_authenticated()
        remote_id = str(remote_id).strip()
        name = Path(remote_id).name
        try:
            self._run(
                ["filesystem", "trash", remote_id],
                json_out=False,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
        except Exception as exc:
            raise _map_proton_exception(exc, operation="deleting backup") from exc

        # Best-effort permanent remove from /trash (CLI delete is trash-only).
        try:
            trash_entries = self._list_entries("/trash")
            for entry in trash_entries:
                if _node_name(entry) != name:
                    continue
                trash_path = f"/trash/{name}"
                self._run(
                    ["filesystem", "delete", trash_path],
                    json_out=False,
                    timeout=DEFAULT_TIMEOUT_SECONDS,
                )
                break
        except ProtonDriveError:
            # Trash succeeded; permanent delete is optional cleanup.
            self.logger.info(
                f"Trashed Proton Drive backup {remote_id} (permanent delete skipped)"
            )
            return True

        self.logger.info(f"Deleted Proton Drive backup {remote_id}")
        return True

    def disconnect(self) -> None:
        """Clear in-memory auth state (CLI keyring session is unchanged)."""
        self._verified = False

    def _ensure_folder(self, folder: str) -> None:
        """Create nested folders under ``/my-files`` when missing (idempotent)."""
        folder = _normalize_folder(folder)
        parts = [p for p in folder.strip("/").split("/") if p]
        if not parts:
            return
        # Skip creating top-level sections like my-files / devices.
        for index in range(1, len(parts)):
            parent = "/" + "/".join(parts[:index])
            name = parts[index]
            child = f"{parent}/{name}"
            try:
                existing = {_node_name(e) for e in self._list_entries(parent)}
            except ProtonDriveError:
                existing = set()
            if name in existing:
                continue
            try:
                self._run(
                    ["filesystem", "create-folder", parent, name],
                    json_out=False,
                    timeout=DEFAULT_TIMEOUT_SECONDS,
                )
            except ProtonDriveError as exc:
                if _ALREADY_EXISTS_RE.search(str(exc)):
                    continue
                # Race / eventual consistency: list child; if reachable, ok.
                try:
                    self._list_entries(child)
                except ProtonDriveError:
                    raise ProtonDriveError(
                        f"Could not create Proton Drive folder {child}: {exc}"
                    ) from exc

    def _list_entries(self, path: str) -> List[dict[str, Any]]:
        data = self._run(
            ["filesystem", "list", path],
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        if data is None:
            return []
        if isinstance(data, list):
            return [e for e in data if isinstance(e, dict)]
        raise ProtonDriveError(f"Unexpected list payload for {path}")

    def _require_authenticated(self) -> None:
        if not self.is_authenticated():
            raise ProtonDriveError(
                "Proton Drive is not authenticated. Install the official CLI, "
                "run `proton-drive auth login`, then Verify Proton Drive Session."
            )

    def _run(
        self,
        args: Sequence[str],
        *,
        json_out: bool = True,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> Any:
        if self._runner is not None:
            return self._runner(list(args), timeout=timeout, json_out=json_out)

        binary = self.resolve_binary(self._binary_override)
        cmd = [binary, *args]
        if json_out:
            cmd.append("-j")
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProtonDriveError(
                format_drive_unavailable_error("proton-drive CLI timed out")
                .replace("Google Drive", "Proton Drive")
                .replace("googleapis.com", "proton.me")
            ) from exc
        except FileNotFoundError as exc:
            raise ProtonDriveError(
                "Official proton-drive CLI not found. Install from "
                "https://proton.me/support/drive-cli or set PROTON_DRIVE_CLI."
            ) from exc
        except OSError as exc:
            raise _map_proton_exception(exc, operation="CLI invoke") from exc

        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        combined = "\n".join(x for x in (stdout, stderr) if x)
        if proc.returncode != 0:
            if _NEED_LOGIN_RE.search(combined):
                raise ProtonDriveError(
                    "Proton Drive CLI session missing. Run: proton-drive auth login "
                    "(browser sign-in; credentials stay in the OS keyring)."
                )
            raise ProtonDriveError(combined or f"proton-drive exited {proc.returncode}")

        if not json_out:
            return stdout
        if not stdout or stdout in ("undefined", "null"):
            return None
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ProtonDriveError(
                f"Invalid JSON from proton-drive: {stdout[:400]}"
            ) from exc


def _normalize_folder(folder: Optional[str]) -> str:
    text = (folder or DEFAULT_PROTON_DRIVE_FOLDER).strip() or DEFAULT_PROTON_DRIVE_FOLDER
    if not text.startswith("/"):
        text = f"/my-files/{text.lstrip('/')}"
    return text.rstrip("/") or DEFAULT_PROTON_DRIVE_FOLDER


def _result_value(value: Any) -> str:
    if isinstance(value, dict):
        if value.get("ok") and value.get("value"):
            return str(value["value"])
        nested = value.get("value")
        if isinstance(nested, str):
            return nested
        return ""
    if isinstance(value, str):
        return value
    return ""


def _node_name(node: dict[str, Any]) -> str:
    return _result_value(node.get("name")) or ""


def _file_size_bytes(entry: dict[str, Any]) -> int:
    revision = entry.get("activeRevision")
    if isinstance(revision, dict):
        claimed = revision.get("claimedSize")
        if isinstance(claimed, int):
            return claimed
        storage = revision.get("storageSize")
        if isinstance(storage, int):
            return storage
    total = entry.get("totalStorageSize")
    if isinstance(total, int):
        return total
    return 0


def _parse_proton_timestamp(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _find_downloaded_file(dest_dir: Path, expected_name: str) -> Optional[Path]:
    direct = dest_dir / expected_name
    if direct.is_file():
        return direct
    files = [p for p in dest_dir.rglob("*") if p.is_file()]
    if len(files) == 1:
        return files[0]
    for path in files:
        if path.name == expected_name:
            return path
    return None


def _map_proton_exception(exc: BaseException, *, operation: str) -> ProtonDriveError:
    """Map low-level failures to clear ProtonDriveError messages."""
    if isinstance(exc, ProtonDriveError):
        return exc
    if is_network_exception(exc):
        return ProtonDriveError(format_offline_error(operation))
    detail = str(exc).strip() or exc.__class__.__name__
    if _NEED_LOGIN_RE.search(detail):
        return ProtonDriveError(
            "Proton Drive CLI session missing. Run: proton-drive auth login"
        )
    lowered = detail.lower()
    if any(
        token in lowered
        for token in (
            "503",
            "500",
            "502",
            "504",
            "service unavailable",
            "internal error",
            "timed out",
            "timeout",
        )
    ):
        return ProtonDriveError(
            format_drive_unavailable_error(detail)
            .replace("Google Drive", "Proton Drive")
            .replace("googleapis.com", "proton.me")
        )
    return ProtonDriveError(f"Proton Drive {operation} failed: {detail}")
