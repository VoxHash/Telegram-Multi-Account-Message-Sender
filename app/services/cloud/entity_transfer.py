"""
Selective template/campaign export and merge-or-replace import (Phase 4).

Full-workspace handoff still uses ``app.db`` + sessions. This module ships
``entities.json`` packages for templates and campaigns only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from sqlmodel import select

from app.models import Campaign, CampaignStatus, CampaignTemplate, MessageTemplate
from app.services.db import get_session
from app.services import get_logger

ENTITIES_FILENAME = "entities.json"
ENTITIES_SCHEMA_VERSION = "1"

ENTITY_TEMPLATES = "templates"
ENTITY_CAMPAIGNS = "campaigns"
VALID_ENTITY_KINDS = frozenset({ENTITY_TEMPLATES, ENTITY_CAMPAIGNS})

IMPORT_MODE_MERGE = "merge"
IMPORT_MODE_REPLACE = "replace"
VALID_IMPORT_MODES = frozenset({IMPORT_MODE_MERGE, IMPORT_MODE_REPLACE})

# Runtime / progress fields reset on import so drafts do not carry stale stats.
_CAMPAIGN_RESET_ON_IMPORT = frozenset(
    {
        "sent_count",
        "failed_count",
        "skipped_count",
        "progress_percentage",
        "start_time_actual",
        "end_time_actual",
        "last_activity",
        "last_recurrence_run",
        "next_recurrence_run",
        "recurrence_count_current",
        "status",
    }
)


class EntityTransferError(Exception):
    """Raised when selective entity export/import fails."""


def parse_entity_kinds(raw: Optional[str | Sequence[str]]) -> Optional[Set[str]]:
    """
    Parse ``templates,campaigns`` / ``all`` into a frozenset of kinds.

    Returns ``None`` when no selective filter is requested (full-workspace export).
    """
    if raw is None:
        return None
    if isinstance(raw, str):
        tokens = [t.strip().lower() for t in raw.replace(";", ",").split(",") if t.strip()]
    else:
        tokens = [str(t).strip().lower() for t in raw if str(t).strip()]

    if not tokens:
        return None
    if "all" in tokens:
        return set(VALID_ENTITY_KINDS)

    kinds: Set[str] = set()
    for tok in tokens:
        if tok in ("template", "templates", "message_templates", "campaign_templates"):
            kinds.add(ENTITY_TEMPLATES)
        elif tok in ("campaign", "campaigns"):
            kinds.add(ENTITY_CAMPAIGNS)
        else:
            raise EntityTransferError(
                f"Unknown entity kind '{tok}'. Use: templates, campaigns, or all"
            )
    return kinds


def normalize_import_mode(mode: Optional[str]) -> str:
    """Return ``merge`` or ``replace``; default ``merge`` for entity packages."""
    if mode is None or not str(mode).strip():
        return IMPORT_MODE_MERGE
    normalized = str(mode).strip().lower()
    if normalized not in VALID_IMPORT_MODES:
        raise EntityTransferError(
            f"Unknown import mode '{mode}'. Use: merge or replace"
        )
    return normalized


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)


def _row_to_dict(row: Any, *, exclude: Optional[Iterable[str]] = None) -> Dict[str, Any]:
    skip = set(exclude or ())
    data = row.model_dump()
    return {k: _json_safe(v) for k, v in data.items() if k not in skip}


def collect_entities(kinds: Set[str]) -> Dict[str, Any]:
    """Load selected entities from the live database into an ``entities.json`` payload."""
    if not kinds:
        raise EntityTransferError("At least one entity kind is required")
    unknown = kinds - VALID_ENTITY_KINDS
    if unknown:
        raise EntityTransferError(f"Unknown entity kinds: {sorted(unknown)}")

    payload: Dict[str, Any] = {
        "schema_version": ENTITIES_SCHEMA_VERSION,
        "kinds": sorted(kinds),
        "message_templates": [],
        "campaign_templates": [],
        "campaigns": [],
    }

    with get_session() as session:
        if ENTITY_TEMPLATES in kinds:
            message_rows = session.exec(
                select(MessageTemplate).where(MessageTemplate.is_deleted == False)  # noqa: E712
            ).all()
            payload["message_templates"] = [
                _row_to_dict(mt, exclude={"id"}) for mt in message_rows
            ]
            campaign_tmpl_rows = session.exec(
                select(CampaignTemplate).where(CampaignTemplate.is_deleted == False)  # noqa: E712
            ).all()
            # Keep source id for campaign remapping by template_id → name
            payload["campaign_templates"] = []
            for ct in campaign_tmpl_rows:
                item = _row_to_dict(ct)
                item["_export_id"] = ct.id
                payload["campaign_templates"].append(item)

        if ENTITY_CAMPAIGNS in kinds:
            campaign_rows = session.exec(
                select(Campaign).where(Campaign.is_deleted == False)  # noqa: E712
            ).all()
            for camp in campaign_rows:
                item = _row_to_dict(camp, exclude={"id"})
                item["_source_template_id"] = camp.template_id
                # Drop live recipient list FK — lists are not part of selective export
                item["recipient_list_id"] = None
                payload["campaigns"].append(item)

    return payload


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _apply_fields(target: Any, data: Dict[str, Any], *, skip: Set[str]) -> None:
    for key, value in data.items():
        if key in skip or key.startswith("_"):
            continue
        if not hasattr(target, key):
            continue
        if isinstance(getattr(type(target), key, None), property):
            continue
        if key.endswith("_at") or key in {
            "start_time",
            "end_time",
            "start_time_actual",
            "end_time_actual",
            "last_activity",
            "last_used",
            "deleted_at",
            "recurrence_end_date",
            "last_recurrence_run",
            "next_recurrence_run",
        }:
            setattr(target, key, _parse_datetime(value))
        else:
            setattr(target, key, value)


def _find_by_name(session: Any, model: Any, name: str) -> Any:
    return session.exec(
        select(model).where(
            model.name == name,
            model.is_deleted == False,  # noqa: E712
        )
    ).first()


def _soft_delete_all(session: Any, model: Any) -> int:
    rows = session.exec(
        select(model).where(model.is_deleted == False)  # noqa: E712
    ).all()
    count = 0
    now = _utc_now()
    for row in rows:
        row.is_deleted = True
        row.deleted_at = now
        session.add(row)
        count += 1
    return count


def import_entities(
    payload: Dict[str, Any],
    *,
    mode: str = IMPORT_MODE_MERGE,
) -> Dict[str, int]:
    """
    Merge or replace templates/campaigns from an ``entities.json`` payload.

    ``merge``: upsert by ``name`` (non-deleted).
    ``replace``: soft-delete existing rows of imported kinds, then insert all.
    """
    mode = normalize_import_mode(mode)
    if payload.get("schema_version") != ENTITIES_SCHEMA_VERSION:
        raise EntityTransferError(
            f"Unsupported entities schema: {payload.get('schema_version')}"
        )

    kinds = set(payload.get("kinds") or [])
    if not kinds:
        # Infer from non-empty collections for older/hand-built payloads
        if payload.get("message_templates") or payload.get("campaign_templates"):
            kinds.add(ENTITY_TEMPLATES)
        if payload.get("campaigns"):
            kinds.add(ENTITY_CAMPAIGNS)
    unknown = kinds - VALID_ENTITY_KINDS
    if unknown:
        raise EntityTransferError(f"Unknown entity kinds in payload: {sorted(unknown)}")
    if not kinds:
        raise EntityTransferError("entities.json contains no importable kinds")

    stats = {
        "message_templates_upserted": 0,
        "campaign_templates_upserted": 0,
        "campaigns_upserted": 0,
        "soft_deleted": 0,
    }
    logger = get_logger()

    with get_session() as session:
        if mode == IMPORT_MODE_REPLACE:
            if ENTITY_CAMPAIGNS in kinds:
                stats["soft_deleted"] += _soft_delete_all(session, Campaign)
            if ENTITY_TEMPLATES in kinds:
                stats["soft_deleted"] += _soft_delete_all(session, MessageTemplate)
                stats["soft_deleted"] += _soft_delete_all(session, CampaignTemplate)

        template_id_map: Dict[int, int] = {}

        if ENTITY_TEMPLATES in kinds:
            for raw in payload.get("message_templates") or []:
                if not isinstance(raw, dict) or not raw.get("name"):
                    continue
                name = str(raw["name"])
                existing = None if mode == IMPORT_MODE_REPLACE else _find_by_name(
                    session, MessageTemplate, name
                )
                now = _utc_now()
                row = existing or MessageTemplate(
                    name=name,
                    body=str(raw.get("body") or ""),
                    created_at=now,
                    updated_at=now,
                )
                _apply_fields(
                    row,
                    raw,
                    skip={"id", "name"},
                )
                row.is_deleted = False
                row.deleted_at = None
                row.updated_at = now
                session.add(row)
                session.flush()
                stats["message_templates_upserted"] += 1

            for raw in payload.get("campaign_templates") or []:
                if not isinstance(raw, dict) or not raw.get("name"):
                    continue
                name = str(raw["name"])
                export_id = raw.get("_export_id")
                existing = None if mode == IMPORT_MODE_REPLACE else _find_by_name(
                    session, CampaignTemplate, name
                )
                now = _utc_now()
                row = existing or CampaignTemplate(
                    name=name,
                    message_text=str(raw.get("message_text") or ""),
                    created_at=now,
                    updated_at=now,
                )
                _apply_fields(row, raw, skip={"id", "name", "_export_id"})
                row.is_deleted = False
                row.deleted_at = None
                row.updated_at = now
                session.add(row)
                session.flush()
                if export_id is not None:
                    try:
                        template_id_map[int(export_id)] = int(row.id)  # type: ignore[arg-type]
                    except (TypeError, ValueError):
                        pass
                stats["campaign_templates_upserted"] += 1

        if ENTITY_CAMPAIGNS in kinds:
            for raw in payload.get("campaigns") or []:
                if not isinstance(raw, dict) or not raw.get("name"):
                    continue
                name = str(raw["name"])
                existing = None if mode == IMPORT_MODE_REPLACE else _find_by_name(
                    session, Campaign, name
                )
                now = _utc_now()
                row = existing or Campaign(
                    name=name,
                    message_text=str(raw.get("message_text") or ""),
                    created_at=now,
                    updated_at=now,
                )
                skip = {"id", "name", "_source_template_id", "recipient_list_id"}
                if mode == IMPORT_MODE_MERGE and existing is not None:
                    # Keep local progress when merging onto an existing campaign
                    skip |= _CAMPAIGN_RESET_ON_IMPORT
                _apply_fields(row, raw, skip=skip)
                if mode == IMPORT_MODE_REPLACE or existing is None:
                    row.status = CampaignStatus.DRAFT
                    row.sent_count = 0
                    row.failed_count = 0
                    row.skipped_count = 0
                    row.progress_percentage = 0.0
                    row.start_time_actual = None
                    row.end_time_actual = None
                    row.last_activity = None

                source_tid = raw.get("_source_template_id")
                if source_tid is not None:
                    try:
                        mapped = template_id_map.get(int(source_tid))
                        row.template_id = mapped
                    except (TypeError, ValueError):
                        row.template_id = None
                else:
                    row.template_id = None
                row.recipient_list_id = None
                row.is_deleted = False
                row.deleted_at = None
                row.updated_at = now
                session.add(row)
                stats["campaigns_upserted"] += 1

        session.commit()

    logger.info(f"Entity import ({mode}) complete: {stats}")
    return stats


def summarize_entities(payload: Dict[str, Any]) -> Tuple[int, int, int]:
    """Return counts of (message_templates, campaign_templates, campaigns)."""
    return (
        len(payload.get("message_templates") or []),
        len(payload.get("campaign_templates") or []),
        len(payload.get("campaigns") or []),
    )
