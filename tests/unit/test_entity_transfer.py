"""
Unit tests for Phase 4 selective entity export and merge-on-import.
"""

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models import Campaign, CampaignTemplate, MessageTemplate
from app.services.cloud import (
    PURPOSE_ENTITY_TRANSFER,
    BackupPackageBuilder,
    CloudBackupService,
    CloudBackupServiceError,
)
from app.services.cloud.backup_package import DATABASE_FILENAME
from app.services.cloud.entity_transfer import (
    ENTITIES_FILENAME,
    EntityTransferError,
    collect_entities,
    import_entities,
    parse_entity_kinds,
)
from app.services.db import get_session
from app.services.handoff import parse_handoff_argv, run_handoff_cli


@pytest.fixture
def file_db(tmp_path, monkeypatch):
    """SQLite file database with sample templates and campaigns."""
    from app.services import close_database, db as db_module
    from app.services.settings import reload_settings

    db_file = tmp_path / "app.db"
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir()
    app_data = tmp_path / "app_data"
    app_data.mkdir()

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("APP_DATA_DIR", str(app_data))
    monkeypatch.setenv("SESSIONS_DIR", str(sessions_dir))
    close_database()
    db_module.db_service._initialized = False
    db_module.db_service.engine = None
    db_module.db_service.settings = reload_settings()

    from app.services import initialize_database

    initialize_database()

    now = datetime.now(timezone.utc)
    with get_session() as session:
        mt = MessageTemplate(
            name="Welcome",
            body="Hello {name}",
            created_at=now,
            updated_at=now,
        )
        ct = CampaignTemplate(
            name="Promo preset",
            message_text="Buy now",
            created_at=now,
            updated_at=now,
        )
        session.add(mt)
        session.add(ct)
        session.commit()
        session.refresh(ct)
        camp = Campaign(
            name="Spring sale",
            message_text="Spring deal",
            template_id=ct.id,
            created_at=now,
            updated_at=now,
        )
        session.add(camp)
        session.commit()

    yield {"db": db_file, "sessions": sessions_dir, "app_data": app_data}
    close_database()
    db_module.db_service._initialized = False
    db_module.db_service.engine = None


class TestParseEntityKinds:
    def test_all_and_aliases(self):
        assert parse_entity_kinds("all") == {"templates", "campaigns"}
        assert parse_entity_kinds("templates,campaigns") == {"templates", "campaigns"}
        assert parse_entity_kinds(["campaign"]) == {"campaigns"}

    def test_none_means_full_export(self):
        assert parse_entity_kinds(None) is None

    def test_unknown_raises(self):
        with pytest.raises(EntityTransferError, match="Unknown entity kind"):
            parse_entity_kinds("accounts")


class TestParseHandoffArgvEntities:
    def test_entities_and_mode_flags(self):
        is_h, action, path, password, include_sessions, entities, mode = parse_handoff_argv(
            [
                "telegram-sender",
                "handoff-export",
                "/tmp/out.tmas-backup.zip",
                "--entities",
                "templates,campaigns",
                "--mode",
                "merge",
                "-p",
                "secret",
            ]
        )
        assert is_h is True
        assert action == "export"
        assert path == Path("/tmp/out.tmas-backup.zip")
        assert password == "secret"
        assert entities == "templates,campaigns"
        assert mode == "merge"
        assert include_sessions is True


class TestSelectivePackage:
    def test_build_entities_only_no_database(self, file_db, tmp_path):
        builder = BackupPackageBuilder()
        output = tmp_path / "entities.tmas-backup.zip"
        builder.build(
            output,
            entity_kinds=["templates", "campaigns"],
            purpose=PURPOSE_ENTITY_TRANSFER,
        )

        assert zipfile.is_zipfile(output)
        manifest = builder.verify(output)
        assert manifest["purpose"] == PURPOSE_ENTITY_TRANSFER
        assert ENTITIES_FILENAME in manifest["files"]
        assert DATABASE_FILENAME not in manifest["files"]
        assert set(manifest["entity_kinds"]) == {"templates", "campaigns"}

        with zipfile.ZipFile(output) as zf:
            payload = json.loads(zf.read(ENTITIES_FILENAME))
        assert len(payload["message_templates"]) == 1
        assert payload["message_templates"][0]["name"] == "Welcome"
        assert len(payload["campaign_templates"]) == 1
        assert len(payload["campaigns"]) == 1

    def test_export_local_package_entities(self, file_db, tmp_path):
        service = CloudBackupService()
        built = service.export_local_package(
            tmp_path / "sel",
            entity_kinds=["templates"],
        )
        assert str(built).endswith(".tmas-backup.zip")
        info = service.inspect_local_package(built)
        assert info["has_entities"] is True
        assert info["has_database"] is False
        assert "templates" in info["entity_kinds"]


class TestMergeAndReplace:
    def test_merge_upserts_by_name(self, file_db):
        payload = collect_entities({"templates", "campaigns"})
        # Change body in payload and add a new template
        payload["message_templates"][0]["body"] = "Updated hello"
        payload["message_templates"].append(
            {
                "name": "Follow-up",
                "body": "Thanks",
                "is_deleted": False,
            }
        )
        stats = import_entities(payload, mode="merge")
        assert stats["message_templates_upserted"] == 2

        with get_session() as session:
            from sqlmodel import select

            rows = session.exec(
                select(MessageTemplate).where(MessageTemplate.is_deleted.is_(False))  # type: ignore[attr-defined]
            ).all()
            by_name = {r.name: r for r in rows}
            assert by_name["Welcome"].body == "Updated hello"
            assert "Follow-up" in by_name

    def test_replace_soft_deletes_then_imports(self, file_db):
        payload = {
            "schema_version": "1",
            "kinds": ["templates"],
            "message_templates": [
                {"name": "OnlyOne", "body": "solo", "is_deleted": False},
            ],
            "campaign_templates": [],
            "campaigns": [],
        }
        import_entities(payload, mode="replace")
        with get_session() as session:
            from sqlmodel import select

            active = session.exec(
                select(MessageTemplate).where(MessageTemplate.is_deleted.is_(False))  # type: ignore[attr-defined]
            ).all()
            assert len(active) == 1
            assert active[0].name == "OnlyOne"

    def test_service_merge_import(self, file_db, tmp_path):
        service = CloudBackupService()
        package = tmp_path / "ent.tmas-backup.zip"
        service.export_local_package(package, entity_kinds=["campaigns", "templates"])

        now = datetime.now(timezone.utc)
        with get_session() as session:
            session.add(
                MessageTemplate(
                    name="LocalOnly",
                    body="keep me",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()

        pre = service.restore_from_local_package(package, mode="merge")
        assert pre.exists()
        with get_session() as session:
            from sqlmodel import select

            names = {
                r.name
                for r in session.exec(
                    select(MessageTemplate).where(MessageTemplate.is_deleted.is_(False))  # type: ignore[attr-defined]
                ).all()
            }
            assert "Welcome" in names
            assert "LocalOnly" in names

    def test_merge_rejects_full_db_package(self, file_db, tmp_path):
        service = CloudBackupService()
        package = tmp_path / "full.tmas-backup.zip"
        service.export_local_package(package, include_sessions=False)
        with pytest.raises(CloudBackupServiceError, match="entities.json"):
            service.restore_from_local_package(package, mode="merge")


class TestHandoffCliEntities:
    def test_export_entities_cli(self, file_db, tmp_path):
        out = tmp_path / "cli-ent.tmas-backup.zip"
        code = run_handoff_cli(
            [
                "telegram-sender",
                "handoff-export",
                str(out),
                "--entities",
                "templates,campaigns",
                "--password=",
            ]
        )
        assert code == 0
        assert out.exists()
        manifest = BackupPackageBuilder().verify(out)
        assert ENTITIES_FILENAME in manifest["files"]

    def test_import_merge_cli(self, file_db, tmp_path):
        package = tmp_path / "pkg.tmas-backup.zip"
        CloudBackupService().export_local_package(
            package, entity_kinds=["templates"]
        )
        code = run_handoff_cli(
            [
                "telegram-sender",
                "handoff-import",
                str(package),
                "--mode",
                "merge",
                "--password=",
            ]
        )
        assert code == 0
