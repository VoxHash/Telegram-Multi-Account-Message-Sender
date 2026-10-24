"""
Unit tests for the optional read-only web companion.
"""

from __future__ import annotations

import json
import threading
from http.client import HTTPConnection
from typing import Any, Dict
from unittest.mock import patch

import pytest

from app.services.settings import Settings
from app.services.web_companion import (
    ALLOWED_METHODS,
    READ_ONLY_API_PATHS,
    WebCompanionServer,
    make_snapshot_builders,
    parse_web_monitor_argv,
)


def _builders() -> Dict[str, Any]:
    return {
        "/api/status": lambda: {"ok": True, "read_only": True},
        "/api/accounts": lambda: {"summary": {"total": 0}, "accounts": []},
        "/api/campaigns": lambda: {"summary": {"campaign_count": 0}, "campaigns": []},
        "/api/activity": lambda: {"limit": 50, "activity": []},
        "/api/overview": lambda: {"generated_at": "2026-10-24T00:00:00Z", "accounts": []},
    }


@pytest.fixture
def companion_server():
    server = WebCompanionServer(
        host="127.0.0.1",
        port=0,  # ephemeral
        snapshot_builders=_builders(),
    )
    # ThreadingHTTPServer with port 0 — bind then read actual port
    from http.server import ThreadingHTTPServer
    from app.services.web_companion import WebCompanionHandler

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), WebCompanionHandler)
    httpd.snapshot_builders = _builders()  # type: ignore[attr-defined]
    server._httpd = httpd
    server.port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    server._thread = thread
    try:
        yield server
    finally:
        server.stop()


def _request(server: WebCompanionServer, method: str, path: str, body: bytes | None = None):
    conn = HTTPConnection("127.0.0.1", server.port, timeout=5)
    headers = {"Content-Type": "application/json"} if body is not None else {}
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, dict(resp.getheaders()), data


class TestParseWebMonitorArgv:
    def test_detects_web_monitor(self):
        is_web, host, port = parse_web_monitor_argv(["prog", "web-monitor"])
        assert is_web is True
        assert host is None
        assert port is None

    def test_host_port_flags(self):
        is_web, host, port = parse_web_monitor_argv(
            ["prog", "web-companion", "--host", "127.0.0.1", "--port", "9001"]
        )
        assert is_web is True
        assert host == "127.0.0.1"
        assert port == 9001

    def test_non_web_mode(self):
        is_web, _, _ = parse_web_monitor_argv(["prog", "--help"])
        assert is_web is False


class TestReadOnlyApiPaths:
    def test_expected_get_endpoints(self):
        assert "/api/status" in READ_ONLY_API_PATHS
        assert "/api/accounts" in READ_ONLY_API_PATHS
        assert "/api/campaigns" in READ_ONLY_API_PATHS
        assert "/api/activity" in READ_ONLY_API_PATHS
        assert "/api/overview" in READ_ONLY_API_PATHS
        # No mutating pseudo-paths registered
        for banned in ("/api/send", "/api/campaigns/start", "/api/control", "/api/write"):
            assert banned not in READ_ONLY_API_PATHS

    def test_allowed_methods_are_safe(self):
        assert ALLOWED_METHODS == {"GET", "HEAD", "OPTIONS"}
        for banned in ("POST", "PUT", "PATCH", "DELETE"):
            assert banned not in ALLOWED_METHODS


class TestWebCompanionHttp:
    def test_get_status_json(self, companion_server):
        status, headers, body = _request(companion_server, "GET", "/api/status")
        assert status == 200
        assert "application/json" in headers.get("Content-Type", "")
        payload = json.loads(body.decode("utf-8"))
        assert payload["ok"] is True
        assert payload["read_only"] is True

    def test_get_index_html(self, companion_server):
        status, headers, body = _request(companion_server, "GET", "/")
        assert status == 200
        assert "text/html" in headers.get("Content-Type", "")
        assert b"Read-only" in body or b"read-only" in body.lower()

    def test_post_rejected(self, companion_server):
        status, headers, body = _request(
            companion_server, "POST", "/api/status", body=b'{"x":1}'
        )
        assert status == 405
        assert any(k.lower() == "allow" for k in headers)
        payload = json.loads(body.decode("utf-8"))
        assert payload["error"] == "method_not_allowed"

    def test_put_patch_delete_rejected(self, companion_server):
        for method in ("PUT", "PATCH", "DELETE"):
            status, _, body = _request(companion_server, method, "/api/campaigns", body=b"{}")
            assert status == 405, method
            assert json.loads(body.decode("utf-8"))["error"] == "method_not_allowed"

    def test_unknown_api_path_404(self, companion_server):
        status, _, body = _request(companion_server, "GET", "/api/send")
        assert status == 404
        assert json.loads(body.decode("utf-8"))["error"] == "not_found"

    def test_all_registered_get_routes_ok(self, companion_server):
        for path in sorted(READ_ONLY_API_PATHS):
            status, _, body = _request(companion_server, "GET", path)
            assert status == 200, path
            assert isinstance(json.loads(body.decode("utf-8")), dict)


class TestSettingsWebCompanion:
    def test_defaults_and_url(self, tmp_path, monkeypatch):
        for key in (
            "WEB_COMPANION_ENABLED",
            "WEB_COMPANION_HOST",
            "WEB_COMPANION_PORT",
            "APP_DATA_DIR",
            "SESSIONS_DIR",
            "LOGS_DIR",
            "CONTENT_DIR",
            "DATABASE_URL",
        ):
            monkeypatch.delenv(key, raising=False)
        s = Settings(
            app_data_dir=str(tmp_path / "d"),
            sessions_dir=str(tmp_path / "s"),
            logs_dir=str(tmp_path / "l"),
            content_dir=str(tmp_path / "c"),
            database_url=f"sqlite:///{tmp_path / 't.db'}",
        )
        assert s.web_companion_enabled is False
        assert s.web_companion_host == "127.0.0.1"
        assert s.web_companion_port == 8765
        assert s.get_web_companion_url() == "http://127.0.0.1:8765"

    def test_make_snapshot_builders_keys(self):
        builders = make_snapshot_builders()
        assert set(builders.keys()) == READ_ONLY_API_PATHS


class TestCliWebMonitorDispatch:
    def test_main_dispatches_web_monitor(self):
        import app.cli as cli

        with patch.object(cli, "run_web_monitor_cli", return_value=0) as run_web:
            with patch.object(cli.sys, "argv", ["telegram-sender", "web-monitor"]):
                with pytest.raises(SystemExit) as exited:
                    cli.main()
            assert exited.value.code == 0
            run_web.assert_called_once()
