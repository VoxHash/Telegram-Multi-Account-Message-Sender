"""
Session and credential storage posture review / hardening.

Desktop installs keep Telethon sessions, ``.env`` secrets, and the SQLite DB on
local disk. This module reports world-readable paths and can tighten POSIX
permissions (``0o700`` dirs / ``0o600`` files). Windows has no equivalent chmod
semantics; the review still lists sensitive paths for operator awareness.
"""

from __future__ import annotations

import os
import stat
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

# Sensitive filenames operators commonly leave next to the app.
ENV_CANDIDATES = (".env", ".env.local")
SESSION_SUFFIXES = (".session", ".session-journal")
DIR_MODE = 0o700
FILE_MODE = 0o600


@dataclass
class Finding:
    """One storage posture observation."""

    severity: str  # ok | info | warn | critical
    path: str
    kind: str
    message: str
    mode: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        return asdict(self)


@dataclass
class PostureReport:
    """Aggregate review of credential / session storage."""

    findings: List[Finding] = field(default_factory=list)
    hardened: List[str] = field(default_factory=list)
    platform: str = field(default_factory=lambda: sys.platform)
    supports_posix_modes: bool = field(
        default_factory=lambda: sys.platform != "win32"
    )

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity in ("warn", "critical"))

    def to_dict(self) -> Dict[str, object]:
        return {
            "platform": self.platform,
            "supports_posix_modes": self.supports_posix_modes,
            "warning_count": self.warning_count,
            "hardened": list(self.hardened),
            "findings": [f.to_dict() for f in self.findings],
        }


def _mode_octal(path: Path) -> Optional[str]:
    try:
        return oct(stat.S_IMODE(path.stat().st_mode))
    except OSError:
        return None


def _is_group_or_world_accessible(path: Path) -> bool:
    try:
        mode = stat.S_IMODE(path.stat().st_mode)
    except OSError:
        return False
    return bool(mode & (stat.S_IRWXG | stat.S_IRWXO))


def _default_sessions_dir() -> Path:
    try:
        from app.services.settings import get_settings

        return Path(get_settings().get_sessions_path())
    except Exception:
        return Path("app_data") / "sessions"


def _default_app_data_dir() -> Path:
    try:
        from app.services.settings import get_settings

        return Path(get_settings().app_data_dir)
    except Exception:
        return Path("app_data")


def _iter_session_files(sessions_dir: Path) -> Iterable[Path]:
    if not sessions_dir.is_dir():
        return []
    out: List[Path] = []
    for path in sessions_dir.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name.endswith(SESSION_SUFFIXES) or name.endswith(".session"):
            out.append(path)
    return out


def _review_path(
    path: Path,
    *,
    kind: str,
    missing_severity: str = "info",
    missing_message: str,
    present_ok_message: str,
) -> Finding:
    if not path.exists():
        return Finding(
            severity=missing_severity,
            path=str(path),
            kind=kind,
            message=missing_message,
        )
    mode = _mode_octal(path)
    if sys.platform == "win32":
        return Finding(
            severity="info",
            path=str(path),
            kind=kind,
            message=(
                f"{present_ok_message} Present on Windows — protect the user "
                "profile / NTFS ACLs; POSIX chmod hardening is skipped."
            ),
            mode=mode,
        )
    if _is_group_or_world_accessible(path):
        return Finding(
            severity="warn",
            path=str(path),
            kind=kind,
            message=(
                f"{present_ok_message} Group/other bits are set "
                f"(mode {mode}). On a shared machine this may leak credentials."
            ),
            mode=mode,
        )
    return Finding(
        severity="ok",
        path=str(path),
        kind=kind,
        message=f"{present_ok_message} Owner-only mode {mode}.",
        mode=mode,
    )


def review_credential_storage(
    *,
    sessions_dir: Optional[Path] = None,
    app_data_dir: Optional[Path] = None,
    env_paths: Optional[Sequence[Path]] = None,
    cwd: Optional[Path] = None,
) -> PostureReport:
    """
    Inspect Telethon session dirs, ``.env`` files, and the SQLite DB for
    overly broad permissions. Does not print secret values.
    """
    root = cwd or Path.cwd()
    sessions = Path(sessions_dir) if sessions_dir else _default_sessions_dir()
    if not sessions.is_absolute():
        sessions = (root / sessions).resolve()
    app_data = Path(app_data_dir) if app_data_dir else _default_app_data_dir()
    if not app_data.is_absolute():
        app_data = (root / app_data).resolve()

    report = PostureReport()
    report.findings.append(
        Finding(
            severity="info",
            path=str(sessions),
            kind="threat_model",
            message=(
                "Telethon .session files are bearer credentials. Anyone who can "
                "read them can impersonate the account. Prefer a dedicated OS "
                "user; avoid shared home directories and untrusted proxies that "
                "terminate TLS."
            ),
        )
    )

    report.findings.append(
        _review_path(
            sessions,
            kind="sessions_dir",
            missing_message="Sessions directory does not exist yet (ok until first login).",
            present_ok_message="Sessions directory.",
        )
    )

    for session_file in _iter_session_files(sessions):
        report.findings.append(
            _review_path(
                session_file,
                kind="session_file",
                missing_message="missing",
                present_ok_message="Telethon session file.",
            )
        )

    candidates = (
        list(env_paths)
        if env_paths is not None
        else [root / name for name in ENV_CANDIDATES]
    )
    for env_path in candidates:
        report.findings.append(
            _review_path(
                env_path,
                kind="env_file",
                missing_message="No .env at this path (secrets may live only in the process environment).",
                present_ok_message=(
                    ".env holds API hashes, AI/cloud tokens, and similar secrets."
                ),
            )
        )

    db_path = app_data / "app.db"
    report.findings.append(
        _review_path(
            db_path,
            kind="database",
            missing_message="SQLite database not created yet.",
            present_ok_message=(
                "SQLite DB may store proxy usernames/passwords and account metadata."
            ),
        )
    )

    cloud_dir = app_data / "cloud"
    if cloud_dir.exists():
        report.findings.append(
            _review_path(
                cloud_dir,
                kind="cloud_tokens",
                missing_message="unused",
                present_ok_message="Cloud token/cache directory.",
            )
        )

    return report


def harden_credential_storage(
    *,
    sessions_dir: Optional[Path] = None,
    app_data_dir: Optional[Path] = None,
    env_paths: Optional[Sequence[Path]] = None,
    cwd: Optional[Path] = None,
) -> PostureReport:
    """
    Apply owner-only POSIX permissions to sessions, ``.env``, and ``app.db``.

    Returns a fresh review after hardening. On Windows, reports info findings
    only (no chmod).
    """
    root = cwd or Path.cwd()
    sessions = Path(sessions_dir) if sessions_dir else _default_sessions_dir()
    if not sessions.is_absolute():
        sessions = (root / sessions).resolve()
    app_data = Path(app_data_dir) if app_data_dir else _default_app_data_dir()
    if not app_data.is_absolute():
        app_data = (root / app_data).resolve()

    report = PostureReport()
    if not report.supports_posix_modes:
        report.findings.append(
            Finding(
                severity="info",
                path=str(sessions),
                kind="harden",
                message=(
                    "POSIX permission hardening is not applied on Windows. "
                    "Restrict the profile folder via NTFS ACLs instead."
                ),
            )
        )
        reviewed = review_credential_storage(
            sessions_dir=sessions,
            app_data_dir=app_data,
            env_paths=env_paths,
            cwd=root,
        )
        report.findings.extend(reviewed.findings)
        return report

    targets: List[Tuple[Path, int]] = []
    if sessions.exists():
        targets.append((sessions, DIR_MODE if sessions.is_dir() else FILE_MODE))
        for session_file in _iter_session_files(sessions):
            targets.append((session_file, FILE_MODE))
    candidates = (
        list(env_paths)
        if env_paths is not None
        else [root / name for name in ENV_CANDIDATES]
    )
    for env_path in candidates:
        if env_path.is_file():
            targets.append((env_path, FILE_MODE))
    db_path = app_data / "app.db"
    if db_path.is_file():
        targets.append((db_path, FILE_MODE))
    cloud_dir = app_data / "cloud"
    if cloud_dir.is_dir():
        targets.append((cloud_dir, DIR_MODE))
        for child in cloud_dir.rglob("*"):
            if child.is_dir():
                targets.append((child, DIR_MODE))
            elif child.is_file():
                targets.append((child, FILE_MODE))

    for path, mode in targets:
        try:
            os.chmod(path, mode)
            report.hardened.append(f"{path} -> {oct(mode)}")
        except OSError as exc:
            report.findings.append(
                Finding(
                    severity="warn",
                    path=str(path),
                    kind="harden",
                    message=f"Failed to chmod: {exc}",
                )
            )

    reviewed = review_credential_storage(
        sessions_dir=sessions,
        app_data_dir=app_data,
        env_paths=env_paths,
        cwd=root,
    )
    report.findings.extend(reviewed.findings)
    return report


def format_report(report: PostureReport) -> str:
    """Human-readable multi-line summary (no secret values)."""
    lines = [
        f"TMAS security posture ({report.platform})",
        f"POSIX mode hardening supported: {report.supports_posix_modes}",
        f"Warnings/critical: {report.warning_count}",
    ]
    if report.hardened:
        lines.append("Hardened:")
        for item in report.hardened:
            lines.append(f"  - {item}")
    lines.append("Findings:")
    for finding in report.findings:
        mode = f" mode={finding.mode}" if finding.mode else ""
        lines.append(
            f"  [{finding.severity}] {finding.kind}: {finding.path}{mode}"
        )
        lines.append(f"           {finding.message}")
    return "\n".join(lines)


def parse_security_argv(
    argv: Sequence[str],
) -> Tuple[bool, Optional[str], bool]:
    """
    Detect ``security-check`` / ``security-harden`` CLI mode.

    Returns ``(is_security_mode, action, help_requested)``.
    ``action`` is ``check``, ``harden``, or ``help``.
    """
    tokens = list(argv[1:]) if argv else []
    if not tokens:
        return False, None, False

    cmd = tokens[0].lower().replace("_", "-")
    if cmd not in (
        "security-check",
        "security-harden",
        "security-review",
        "sec-check",
        "sec-harden",
    ):
        return False, None, False

    if cmd in ("security-harden", "sec-harden"):
        action: Optional[str] = "harden"
    else:
        action = "check"

    for tok in tokens[1:]:
        if tok in ("-h", "--help"):
            return True, "help", True
        if tok.startswith("-"):
            raise ValueError(f"Unknown security option: {tok}")
    return True, action, False


def _print_security_help() -> None:
    print(
        """TMAS security posture (local credential / session storage)

Review or harden on-disk secrets for proxies and shared-machine threat models.
See SECURITY.md for the full threat model and dependency-audit process.

  telegram-sender security-check
  telegram-sender security-harden

  security-check   Report session/.env/DB permission posture (no secret values)
  security-harden  chmod owner-only on POSIX (sessions, .env, app.db, cloud/)

Exit codes: 0 = no warnings; 1 = warnings/critical findings; 2 = usage error.
"""
    )


def run_security_cli(argv: Sequence[str]) -> int:
    """CLI entry for security-check / security-harden."""
    try:
        is_sec, action, _ = parse_security_argv(argv)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not is_sec:
        return 2
    if action == "help":
        _print_security_help()
        return 0

    if action == "harden":
        report = harden_credential_storage()
    else:
        report = review_credential_storage()

    print(format_report(report))
    return 1 if report.warning_count else 0
