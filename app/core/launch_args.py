"""
Parse desktop / CLI launch arguments for file associations.

Used when the OS opens ``*.tmas-backup.zip`` via MIME / UTI handlers.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

# Keep in sync with app.services.cloud.backup_package.BACKUP_FILE_EXTENSION
# (duplicated here to avoid importing services from core launch paths).
BACKUP_PACKAGE_SUFFIX = ".tmas-backup.zip"


def is_backup_package_path(path: Path | str) -> bool:
    """Return True when the path name ends with the backup package suffix."""
    name = Path(path).name.lower()
    return name.endswith(BACKUP_PACKAGE_SUFFIX)


def find_backup_package_arg(argv: Sequence[str]) -> Optional[Path]:
    """
    Return the first positional argv path that looks like a TMAS backup package.

    Skips the program name (``argv[0]``) and flag-like tokens starting with ``-``.
    Does not require the file to exist (associations may pass a path before copy).
    """
    for raw in list(argv)[1:]:
        if not raw or raw.startswith("-"):
            continue
        candidate = Path(raw).expanduser()
        if is_backup_package_path(candidate):
            return candidate
    return None


def resolve_existing_backup_package(argv: Sequence[str]) -> Optional[Path]:
    """Like ``find_backup_package_arg`` but only returns an existing file."""
    found = find_backup_package_arg(argv)
    if found is None:
        return None
    resolved = found.resolve()
    if resolved.is_file():
        return resolved
    return None


def filter_qt_argv(argv: Sequence[str]) -> List[str]:
    """
    Return argv suitable for QApplication when a backup path was consumed.

    Keeps the program name and non-backup positional/flag arguments.
    """
    if not argv:
        return []
    result: List[str] = [argv[0]]
    for raw in list(argv)[1:]:
        if raw and not raw.startswith("-") and is_backup_package_path(raw):
            continue
        result.append(raw)
    return result
