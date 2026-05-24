"""
Unit tests for database performance indexes.
"""

from sqlalchemy import text

from app.services import close_database, db as db_module
from app.services.settings import reload_settings


def test_ensure_performance_indexes_creates_send_log_indexes(tmp_path, monkeypatch):
    db_file = tmp_path / "app.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    close_database()
    db_module.db_service._initialized = False
    db_module.db_service.engine = None
    db_module.db_service.settings = reload_settings()

    from app.services import initialize_database

    initialize_database()

    with db_module.db_service.engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'index' AND tbl_name = 'send_logs'"
            )
        ).fetchall()
        index_names = {row[0] for row in rows}

    assert "ix_send_logs_sent_at" in index_names
    assert "ix_send_logs_status" in index_names
    assert "ix_send_logs_account_sent_at" in index_names

    close_database()
    db_module.db_service._initialized = False
    db_module.db_service.engine = None
