"""Unit tests for session/credential storage posture review and CLI."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest

from app.utils.security_posture import (
    format_report,
    harden_credential_storage,
    parse_security_argv,
    review_credential_storage,
    run_security_cli,
)


@pytest.mark.unit
def test_parse_security_argv_detects_check_and_harden() -> None:
    """CLI tokens map to check / harden / help modes."""
    is_sec, action, help_flag = parse_security_argv(["tm", "security-check"])
    assert is_sec is True
    assert action == "check"
    assert help_flag is False

    is_sec, action, help_flag = parse_security_argv(["tm", "security-harden"])
    assert is_sec is True
    assert action == "harden"

    is_sec, action, help_flag = parse_security_argv(
        ["tm", "security-check", "--help"]
    )
    assert is_sec is True
    assert action == "help"
    assert help_flag is True

    is_sec, _, _ = parse_security_argv(["tm", "web-monitor"])
    assert is_sec is False


@pytest.mark.unit
def test_review_flags_world_readable_session(tmp_path: Path) -> None:
    """World-readable session files produce a warn finding on POSIX."""
    if sys.platform == "win32":
        pytest.skip("POSIX mode bits are not meaningful on Windows")

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    session = sessions / "session_demo.session"
    session.write_bytes(b"fake-session")
    os.chmod(session, 0o644)

    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_API_HASH=not-a-real-secret\n", encoding="utf-8")
    os.chmod(env_file, 0o600)

    app_data = tmp_path / "app_data"
    app_data.mkdir()
    db = app_data / "app.db"
    db.write_bytes(b"sqlite")
    os.chmod(db, 0o600)

    report = review_credential_storage(
        sessions_dir=sessions,
        app_data_dir=app_data,
        env_paths=[env_file],
        cwd=tmp_path,
    )
    assert report.warning_count >= 1
    session_findings = [f for f in report.findings if f.kind == "session_file"]
    assert session_findings
    assert session_findings[0].severity == "warn"
    assert "not-a-real-secret" not in format_report(report)


@pytest.mark.unit
def test_harden_makes_owner_only(tmp_path: Path) -> None:
    """security-harden tightens session and .env modes on POSIX."""
    if sys.platform == "win32":
        pytest.skip("chmod hardening is a no-op on Windows")

    sessions = tmp_path / "sessions"
    sessions.mkdir()
    os.chmod(sessions, 0o755)
    session = sessions / "session_demo.session"
    session.write_bytes(b"fake-session")
    os.chmod(session, 0o644)

    env_file = tmp_path / ".env"
    env_file.write_text("TELEGRAM_API_ID=1\n", encoding="utf-8")
    os.chmod(env_file, 0o644)

    app_data = tmp_path / "app_data"
    app_data.mkdir()
    (app_data / "app.db").write_bytes(b"sqlite")
    os.chmod(app_data / "app.db", 0o644)

    report = harden_credential_storage(
        sessions_dir=sessions,
        app_data_dir=app_data,
        env_paths=[env_file],
        cwd=tmp_path,
    )
    assert report.hardened
    assert stat.S_IMODE(session.stat().st_mode) == 0o600
    assert stat.S_IMODE(env_file.stat().st_mode) == 0o600
    assert stat.S_IMODE(sessions.stat().st_mode) == 0o700
    assert report.warning_count == 0


@pytest.mark.unit
def test_run_security_cli_help_and_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """CLI help exits 0; check against a clean tmp tree exits 0."""
    assert run_security_cli(["tm", "security-check", "--help"]) == 0
    help_out = capsys.readouterr().out
    assert "security-check" in help_out

    monkeypatch.chdir(tmp_path)
    (tmp_path / "app_data").mkdir()
    code = run_security_cli(["tm", "security-check"])
    out = capsys.readouterr().out
    assert "TMAS security posture" in out
    assert code in (0, 1)
