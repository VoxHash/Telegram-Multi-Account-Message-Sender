"""
Single-operator handoff export/import CLI (Phase 4 desktop).

Desktop remains single-operator; multi-user roles belong to SendGram.
This module moves a workspace between machines via ``.tmas-backup.zip``,
or selectively transfers templates/campaigns with merge-or-replace import.
"""

from __future__ import annotations

import getpass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from app.services.cloud import (
    BACKUP_FILE_EXTENSION,
    PURPOSE_OPERATOR_HANDOFF,
    CloudBackupService,
    CloudBackupServiceError,
)
from app.services.cloud.entity_transfer import (
    EntityTransferError,
    normalize_import_mode,
    parse_entity_kinds,
)


def parse_handoff_argv(
    argv: Sequence[str],
) -> Tuple[
    bool,
    Optional[str],
    Optional[Path],
    Optional[str],
    bool,
    Optional[str],
    Optional[str],
]:
    """
    Detect ``handoff-export`` / ``handoff-import`` CLI mode.

    Returns
    ``(is_handoff_mode, action, path, password, include_sessions, entities, mode)``.
    ``action`` is ``export`` or ``import`` when mode is active.
    ``entities`` is the raw ``--entities`` value (e.g. ``templates,campaigns``).
    ``mode`` is ``merge`` or ``replace`` for import (optional).
    """
    tokens = list(argv[1:]) if argv else []
    if not tokens:
        return False, None, None, None, True, None, None

    cmd = tokens[0].lower().replace("_", "-")
    if cmd not in ("handoff-export", "handoff-import", "export-handoff", "import-handoff"):
        return False, None, None, None, True, None, None

    action = "export" if "export" in cmd else "import"
    path: Optional[Path] = None
    password: Optional[str] = None
    include_sessions = True
    entities: Optional[str] = None
    mode: Optional[str] = None
    i = 1
    positional: List[str] = []

    while i < len(tokens):
        tok = tokens[i]
        if tok in ("--password", "-p") and i + 1 < len(tokens):
            password = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("--password="):
            password = tok.split("=", 1)[1]
            i += 1
            continue
        if tok in ("--no-sessions",):
            include_sessions = False
            i += 1
            continue
        if tok in ("--sessions",):
            include_sessions = True
            i += 1
            continue
        if tok in ("--entities", "-e") and i + 1 < len(tokens):
            entities = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("--entities="):
            entities = tok.split("=", 1)[1]
            i += 1
            continue
        if tok in ("--mode", "-m") and i + 1 < len(tokens):
            mode = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("--mode="):
            mode = tok.split("=", 1)[1]
            i += 1
            continue
        if tok in ("-h", "--help"):
            return True, "help", None, None, True, None, None
        if tok.startswith("-"):
            raise ValueError(f"Unknown handoff option: {tok}")
        positional.append(tok)
        i += 1

    if positional:
        path = Path(positional[0]).expanduser()

    return True, action, path, password, include_sessions, entities, mode


def _print_handoff_help() -> None:
    print(
        """TMAS single-operator handoff (Phase 4)

Desktop stays single-operator. Use these commands to move a workspace between
machines, or to transfer templates/campaigns only. Multi-user roles belong to
SendGram (https://www.sendgram.pro).

  telegram-sender handoff-export <path> [--password SECRET] [--no-sessions]
  telegram-sender handoff-export <path> --entities templates,campaigns
  telegram-sender handoff-import <path> [--password SECRET] [--mode merge|replace]

  path              Output file/dir (export) or package to restore (import)
  --password / -p   Optional encryption password (prompted if omitted on TTY)
  --no-sessions     Full export: database + settings only (omit Telethon sessions)
  --sessions        Include session files (default for full export)
  --entities / -e   Selective export: templates, campaigns, or all
                    (omits database and sessions; package contains entities.json)
  --mode / -m       Import mode: merge (upsert by name) or replace
                    Entity packages default to merge; full DB packages default
                    to replace. Merge requires an entities.json package.

Packages use the same .tmas-backup.zip format as Cloud Backup. Full handoff
exports include session files by default. Treat packages as secret; prefer
--password for off-machine transfer.
"""
    )


def run_handoff_cli(argv: Sequence[str]) -> int:
    """Run handoff-export or handoff-import; return process exit code."""
    try:
        (
            is_handoff,
            action,
            path,
            password,
            include_sessions,
            entities_raw,
            mode_raw,
        ) = parse_handoff_argv(argv)
    except ValueError as exc:
        print(f"Error: {exc}")
        _print_handoff_help()
        return 2

    if not is_handoff:
        raise ValueError("run_handoff_cli requires a handoff-export/import argv")

    if action == "help":
        _print_handoff_help()
        return 0

    if path is None:
        print("Error: path argument is required")
        _print_handoff_help()
        return 2

    entity_kinds = None
    if entities_raw is not None:
        try:
            entity_kinds = parse_entity_kinds(entities_raw)
        except EntityTransferError as exc:
            print(f"Error: {exc}")
            return 2
        if not entity_kinds:
            print("Error: --entities requires templates, campaigns, or all")
            return 2

    import_mode = None
    if mode_raw is not None:
        try:
            import_mode = normalize_import_mode(mode_raw)
        except EntityTransferError as exc:
            print(f"Error: {exc}")
            return 2

    initialize = __import__(
        "app.services.db", fromlist=["initialize_database"]
    ).initialize_database
    initialize()

    if password is None and __import__("sys").stdin.isatty():
        try:
            entered = getpass.getpass(
                "Encryption password (empty for none): "
            )
            password = entered.strip() or None
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled.")
            return 130

    service = CloudBackupService()
    try:
        if action == "export":
            built = service.export_local_package(
                path,
                password=password,
                include_sessions=include_sessions if entity_kinds is None else False,
                purpose=PURPOSE_OPERATOR_HANDOFF,
                entity_kinds=sorted(entity_kinds) if entity_kinds else None,
            )
            print(f"Handoff package written: {built}")
            if entity_kinds:
                print(
                    f"Selective export: {', '.join(sorted(entity_kinds))} "
                    "(entities.json; import with --mode merge or replace)."
                )
            elif include_sessions:
                print(
                    "Included Telethon sessions (single-operator machine transfer). "
                    "Keep this file secret."
                )
            else:
                print("Sessions omitted; re-authenticate accounts after import.")
            return 0

        if not path.is_file():
            print(f"Error: package not found: {path}")
            return 1
        if not str(path).endswith(BACKUP_FILE_EXTENSION) and not path.name.endswith(
            BACKUP_FILE_EXTENSION
        ):
            print(
                f"Warning: expected *{BACKUP_FILE_EXTENSION}; continuing anyway."
            )

        info = service.inspect_local_package(path, password=password)
        if import_mode is None:
            if info.get("has_entities") and not info.get("has_database"):
                import_mode = "merge"
            else:
                import_mode = "replace"

        pre_restore = service.restore_from_local_package(
            path, password=password, mode=import_mode
        )
        print(f"Handoff import complete (mode={import_mode}). Pre-restore DB snapshot: {pre_restore}")
        if info.get("has_entities") and (
            not info.get("has_database") or import_mode == "merge"
        ):
            print(
                "Templates/campaigns were merged or replaced in the current database. "
                "Restart the application to refresh lists."
            )
        else:
            print("Restart the application so all components reload the database.")
        return 0
    except CloudBackupServiceError as exc:
        print(f"Error: {exc}")
        return 1
