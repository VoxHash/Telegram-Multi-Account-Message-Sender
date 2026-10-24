"""
Unit tests for the optional read-only web companion.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime
from http.client import HTTPConnection
from types import SimpleNamespace
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from app.services.settings import Settings
from app.services.web_companion import (
    ALLOWED_METHODS,
    READ_ONLY_API_PATHS,
    WebCompanionHandler,
    WebCompanionServer,
    aggregate_campaign_bars,
    aggregate_health_breakdown,
    aggregate_hourly_activity,
    aggregate_status_breakdown,
    extract_request_token,
    generate_companion_token,
    is_loopback_host,
    make_snapshot_builders,
    parse_web_monitor_argv,
    require_token_for_bind,
    tokens_match,
)


def _builders() -> Dict[str, Any]:
    return {
        "/api/status": lambda: {"ok": True, "read_only": True},
        "/api/accounts": lambda: {"summary": {"total": 0}, "accounts": []},
        "/api/campaigns": lambda: {"summary": {"campaign_count": 0}, "campaigns": []},
        "/api/activity": lambda: {"limit": 50, "activity": []},
        "/api/overview": lambda: {
            "generated_at": "2026-10-24T00:00:00Z",
            "accounts": [],
            "charts": {"activity_hourly": [], "status_breakdown": []},
        },
        "/api/charts": lambda: {
            "window_hours": 24,
            "activity_hourly": [],
            "status_breakdown": [],
            "campaign_bars": [],
            "health_breakdown": [],
        },
    }


def _start_server(auth_token: Optional[str] = None) -> WebCompanionServer:
    from http.server import ThreadingHTTPServer

    server = WebCompanionServer(
        host="127.0.0.1",
        port=0,
        snapshot_builders=_builders(),
        auth_token=auth_token,
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), WebCompanionHandler)
    httpd.snapshot_builders = _builders()  # type: ignore[attr-defined]
    httpd.auth_token = auth_token  # type: ignore[attr-defined]
    server._httpd = httpd
    server.port = httpd.server_address[1]
    server.auth_token = auth_token
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    server._thread = thread
    return server


@pytest.fixture
def companion_server():
    server = _start_server(auth_token=None)
    try:
        yield server
    finally:
        server.stop()


@pytest.fixture
def authed_companion_server():
    token = "test-companion-secret-token"
    server = _start_server(auth_token=token)
    try:
        yield server, token
    finally:
        server.stop()


def _request(
    server: WebCompanionServer,
    method: str,
    path: str,
    body: bytes | None = None,
    headers: Optional[Dict[str, str]] = None,
):
    conn = HTTPConnection("127.0.0.1", server.port, timeout=5)
    req_headers = dict(headers or {})
    if body is not None and "Content-Type" not in req_headers:
        req_headers["Content-Type"] = "application/json"
    conn.request(method, path, body=body, headers=req_headers)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, dict(resp.getheaders()), data


class TestParseWebMonitorArgv:
    def test_detects_web_monitor(self):
        is_web, host, port, token = parse_web_monitor_argv(["prog", "web-monitor"])
        assert is_web is True
        assert host is None
        assert port is None
        assert token is None

    def test_host_port_flags(self):
        is_web, host, port, token = parse_web_monitor_argv(
            ["prog", "web-companion", "--host", "127.0.0.1", "--port", "9001"]
        )
        assert is_web is True
        assert host == "127.0.0.1"
        assert port == 9001
        assert token is None

    def test_token_flag(self):
        is_web, host, port, token = parse_web_monitor_argv(
            ["prog", "web-monitor", "--host", "0.0.0.0", "--token", "abc123"]
        )
        assert is_web is True
        assert host == "0.0.0.0"
        assert token == "abc123"
        assert port is None

    def test_token_equals_form(self):
        is_web, _, _, token = parse_web_monitor_argv(
            ["prog", "web-monitor", "--token=secret-value"]
        )
        assert is_web is True
        assert token == "secret-value"

    def test_non_web_mode(self):
        is_web, _, _, _ = parse_web_monitor_argv(["prog", "--help"])
        assert is_web is False


class TestAuthHelpers:
    def test_loopback_hosts(self):
        assert is_loopback_host("127.0.0.1")
        assert is_loopback_host("localhost")
        assert is_loopback_host("::1")
        assert not is_loopback_host("0.0.0.0")
        assert not is_loopback_host("192.168.1.10")

    def test_require_token_for_non_loopback(self):
        with pytest.raises(ValueError, match="WEB_COMPANION_TOKEN"):
            require_token_for_bind("0.0.0.0", None)
        require_token_for_bind("0.0.0.0", "secret")  # ok
        require_token_for_bind("127.0.0.1", None)  # ok

    def test_tokens_match_constant_time(self):
        assert tokens_match("abc", "abc")
        assert not tokens_match("abc", "abd")
        assert not tokens_match("abc", None)
        assert not tokens_match(None, "abc")

    def test_extract_bearer_and_header_and_query(self):
        assert extract_request_token({"Authorization": "Bearer tok1"}, "") == "tok1"
        assert extract_request_token({"X-TMAS-Token": "tok2"}, "") == "tok2"
        assert extract_request_token({}, "token=tok3") == "tok3"
        assert extract_request_token({}, "") is None

    def test_generate_token_length(self):
        token = generate_companion_token()
        assert isinstance(token, str)
        assert len(token) >= 32


class TestReadOnlyApiPaths:
    def test_expected_get_endpoints(self):
        assert "/api/status" in READ_ONLY_API_PATHS
        assert "/api/accounts" in READ_ONLY_API_PATHS
        assert "/api/campaigns" in READ_ONLY_API_PATHS
        assert "/api/activity" in READ_ONLY_API_PATHS
        assert "/api/overview" in READ_ONLY_API_PATHS
        assert "/api/charts" in READ_ONLY_API_PATHS
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
        assert b"Live charts" in body or b"chart-activity" in body

    def test_get_charts_json(self, companion_server):
        status, headers, body = _request(companion_server, "GET", "/api/charts")
        assert status == 200
        assert "application/json" in headers.get("Content-Type", "")
        payload = json.loads(body.decode("utf-8"))
        assert "activity_hourly" in payload
        assert "status_breakdown" in payload
        assert "campaign_bars" in payload
        assert "health_breakdown" in payload

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


class TestWebCompanionAuth:
    def test_rejects_without_token(self, authed_companion_server):
        server, _token = authed_companion_server
        status, headers, body = _request(server, "GET", "/api/status")
        assert status == 401
        assert "www-authenticate" in {k.lower() for k in headers}
        assert json.loads(body.decode("utf-8"))["error"] == "unauthorized"

    def test_accepts_bearer(self, authed_companion_server):
        server, token = authed_companion_server
        status, _, body = _request(
            server, "GET", "/api/status", headers={"Authorization": f"Bearer {token}"}
        )
        assert status == 200
        assert json.loads(body.decode("utf-8"))["ok"] is True

    def test_accepts_x_tmas_token(self, authed_companion_server):
        server, token = authed_companion_server
        status, _, body = _request(
            server, "GET", "/api/overview", headers={"X-TMAS-Token": token}
        )
        assert status == 200
        assert "accounts" in json.loads(body.decode("utf-8"))

    def test_accepts_query_token(self, authed_companion_server):
        server, token = authed_companion_server
        status, _, body = _request(server, "GET", f"/api/status?token={token}")
        assert status == 200
        assert json.loads(body.decode("utf-8"))["ok"] is True

    def test_rejects_wrong_token(self, authed_companion_server):
        server, _token = authed_companion_server
        status, _, body = _request(
            server, "GET", "/api/status", headers={"Authorization": "Bearer wrong"}
        )
        assert status == 401
        assert json.loads(body.decode("utf-8"))["error"] == "unauthorized"

    def test_html_requires_token_when_configured(self, authed_companion_server):
        server, token = authed_companion_server
        status, _, _ = _request(server, "GET", "/")
        assert status == 401
        status_ok, headers, body = _request(server, "GET", f"/?token={token}")
        assert status_ok == 200
        assert "text/html" in headers.get("Content-Type", "")
        assert b"Bearer token" in body or b"token" in body.lower()

    def test_start_refuses_non_loopback_without_token(self):
        server = WebCompanionServer(host="0.0.0.0", port=0, snapshot_builders=_builders())
        with pytest.raises(ValueError, match="WEB_COMPANION_TOKEN"):
            server.start(background=True)


class TestSettingsWebCompanion:
    def test_defaults_and_url(self, tmp_path, monkeypatch):
        for key in (
            "WEB_COMPANION_ENABLED",
            "WEB_COMPANION_HOST",
            "WEB_COMPANION_PORT",
            "WEB_COMPANION_TOKEN",
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
        assert s.web_companion_token is None
        assert s.is_web_companion_token_configured() is False
        assert s.get_web_companion_url() == "http://127.0.0.1:8765"

    def test_url_includes_token_query(self, tmp_path, monkeypatch):
        for key in (
            "WEB_COMPANION_ENABLED",
            "WEB_COMPANION_HOST",
            "WEB_COMPANION_PORT",
            "WEB_COMPANION_TOKEN",
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
            web_companion_token="sec ret/token",
        )
        assert s.is_web_companion_token_configured() is True
        url = s.get_web_companion_url()
        assert url.startswith("http://127.0.0.1:8765/?token=")
        assert "sec" in url or "%20" in url or "%2F" in url

    def test_make_snapshot_builders_keys(self):
        builders = make_snapshot_builders()
        assert set(builders.keys()) == READ_ONLY_API_PATHS


class TestChartAggregators:
    def test_hourly_activity_buckets(self):
        now = datetime(2026, 10, 24, 15, 30, 0)
        logs = [
            SimpleNamespace(status="sent", sent_at=datetime(2026, 10, 24, 15, 10, 0)),
            SimpleNamespace(status="sent", sent_at=datetime(2026, 10, 24, 15, 20, 0)),
            SimpleNamespace(status="failed", sent_at=datetime(2026, 10, 24, 14, 5, 0)),
            SimpleNamespace(status="skipped", completed_at=datetime(2026, 10, 24, 14, 40, 0)),
            SimpleNamespace(status="sent", sent_at=datetime(2026, 10, 23, 10, 0, 0)),  # outside
        ]
        series = aggregate_hourly_activity(logs, hours=3, now=now)
        assert len(series) == 3
        by_label = {row["label"]: row for row in series}
        assert by_label["15:00"]["sent"] == 2
        assert by_label["14:00"]["failed"] == 1
        assert by_label["14:00"]["other"] == 1
        assert by_label["13:00"]["total"] == 0

    def test_status_breakdown_sorted(self):
        logs = [
            SimpleNamespace(status="sent"),
            SimpleNamespace(status="sent"),
            SimpleNamespace(status="failed"),
        ]
        items = aggregate_status_breakdown(logs)
        assert items[0]["key"] == "sent"
        assert items[0]["count"] == 2
        assert items[1]["key"] == "failed"
        assert items[1]["count"] == 1
        assert items[0]["color"]

    def test_campaign_bars_top_by_attempted(self):
        campaigns = [
            SimpleNamespace(id=1, name="low", sent_count=1, failed_count=0),
            SimpleNamespace(id=2, name="high", sent_count=10, failed_count=2),
            SimpleNamespace(id=3, name="mid", sent_count=3, failed_count=1),
        ]
        bars = aggregate_campaign_bars(campaigns, limit=2)
        assert len(bars) == 2
        assert bars[0]["label"] == "high"
        assert bars[0]["sent"] == 10
        assert bars[0]["failed"] == 2
        assert bars[1]["label"] == "mid"

    def test_health_breakdown(self):
        accounts = [
            {"health_status": "good"},
            {"health_status": "good"},
            {"health_status": "warning"},
            {"health_status": "offline"},
        ]
        items = aggregate_health_breakdown(accounts)
        by_key = {row["key"]: row["count"] for row in items}
        assert by_key["good"] == 2
        assert by_key["warning"] == 1
        assert by_key["offline"] == 1


class TestCliWebMonitorDispatch:
    def test_main_dispatches_web_monitor(self):
        import app.cli as cli

        with patch.object(cli, "run_web_monitor_cli", return_value=0) as run_web:
            with patch.object(cli.sys, "argv", ["telegram-sender", "web-monitor"]):
                with pytest.raises(SystemExit) as exited:
                    cli.main()
            assert exited.value.code == 0
            run_web.assert_called_once()
