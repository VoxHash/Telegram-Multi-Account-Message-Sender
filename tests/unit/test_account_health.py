"""
Unit tests for AccountHealthMonitor scoring and summary.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models import Account, AccountStatus
from app.services.account_health import AccountHealthMonitor, HealthStatus


def _make_account(**overrides) -> Account:
    data = {
        "id": 1,
        "name": "Test Account",
        "phone_number": "+15551234567",
        "api_id": 12345,
        "api_hash": "hash",
        "session_path": "sessions/test",
        "status": AccountStatus.ONLINE,
        "is_active": True,
        "warmup_enabled": False,
        "warmup_messages_sent": 0,
        "warmup_target_messages": 5,
        "total_messages_sent": 100,
        "total_messages_failed": 5,
        "last_activity": datetime.utcnow() - timedelta(hours=1),
        "error_message": None,
        "proxy_host": "127.0.0.1",
        "proxy_port": 1080,
    }
    data.update(overrides)
    return Account(**data)


@pytest.fixture
def monitor():
    return AccountHealthMonitor()


@pytest.fixture
def mock_empty_logs():
    """Patch get_session so recent send-log counts are zero."""
    session = MagicMock()
    session.__enter__ = MagicMock(return_value=session)
    session.__exit__ = MagicMock(return_value=False)
    session.exec.return_value.first.return_value = 0
    with patch("app.services.account_health.get_session", return_value=session):
        yield session


class TestAccountHealthScoring:
    def test_online_healthy_account_scores_excellent(self, monitor, mock_empty_logs):
        account = _make_account()
        result = monitor.check_account_health(account)

        assert result["health_status"] == HealthStatus.EXCELLENT.value
        assert result["score"] >= 90
        assert result["warnings"] == []
        assert result["metrics"]["success_rate"] == pytest.approx(95.238, rel=1e-2)

    def test_zero_send_history_does_not_flag_low_success(self, monitor, mock_empty_logs):
        account = _make_account(total_messages_sent=0, total_messages_failed=0)
        result = monitor.check_account_health(account)

        assert result["score"] >= 75
        assert not any("success rate" in w.lower() for w in result["warnings"])
        assert any("baseline" in r.lower() for r in result["recommendations"])

    def test_offline_account_is_offline_with_action(self, monitor, mock_empty_logs):
        account = _make_account(status=AccountStatus.OFFLINE)
        result = monitor.check_account_health(account)

        assert result["health_status"] == HealthStatus.OFFLINE.value
        assert result["score"] == 0.0
        assert any("not online" in w.lower() for w in result["warnings"])
        assert any("connect" in r.lower() for r in result["recommendations"])

    def test_error_account_is_critical(self, monitor, mock_empty_logs):
        account = _make_account(
            status=AccountStatus.ERROR,
            error_message="AUTH_KEY_UNREGISTERED",
        )
        result = monitor.check_account_health(account)

        assert result["health_status"] == HealthStatus.CRITICAL.value
        assert result["score"] < 50
        assert any("AUTH_KEY_UNREGISTERED" in w for w in result["warnings"])
        assert any("test connection" in r.lower() for r in result["recommendations"])

    def test_suspended_account_is_critical(self, monitor, mock_empty_logs):
        account = _make_account(status=AccountStatus.SUSPENDED)
        result = monitor.check_account_health(account)

        assert result["health_status"] == HealthStatus.CRITICAL.value
        assert any("suspended" in w.lower() for w in result["warnings"])

    def test_inactive_account_is_critical(self, monitor, mock_empty_logs):
        account = _make_account(is_active=False)
        result = monitor.check_account_health(account)

        assert result["health_status"] == HealthStatus.CRITICAL.value
        assert result["score"] == 0.0
        assert any("inactive" in w.lower() for w in result["warnings"])

    def test_low_success_rate_adds_warning(self, monitor, mock_empty_logs):
        account = _make_account(total_messages_sent=20, total_messages_failed=80)
        result = monitor.check_account_health(account)

        assert result["score"] < 75
        assert any("low success rate" in w.lower() for w in result["warnings"])

    def test_incomplete_warmup_warning(self, monitor, mock_empty_logs):
        account = _make_account(
            warmup_enabled=True,
            warmup_messages_sent=1,
            warmup_target_messages=5,
        )
        result = monitor.check_account_health(account)

        assert any("warmup" in w.lower() for w in result["warnings"])
        assert any("warmup" in r.lower() for r in result["recommendations"])

    def test_stale_activity_warning(self, monitor, mock_empty_logs):
        account = _make_account(last_activity=datetime.utcnow() - timedelta(hours=30))
        result = monitor.check_account_health(account)

        assert any("no activity" in w.lower() for w in result["warnings"])
        assert result["score"] < 90

    def test_high_recent_error_rate(self, monitor):
        session = MagicMock()
        session.__enter__ = MagicMock(return_value=session)
        session.__exit__ = MagicMock(return_value=False)
        # First call: failures=5, second: total=10 → 50% error rate
        session.exec.return_value.first.side_effect = [5, 10]

        account = _make_account()
        with patch("app.services.account_health.get_session", return_value=session):
            result = monitor.check_account_health(account)

        assert any("error rate" in w.lower() for w in result["warnings"])
        assert result["metrics"]["recent_error_rate"] == pytest.approx(50.0)
        assert result["score"] <= 75


class TestHealthSummary:
    def test_empty_summary(self, monitor):
        summary = monitor.get_health_summary([])
        assert summary["total"] == 0
        assert summary["average_score"] == 0.0
        assert summary["needs_attention"] == 0

    def test_summary_counts_statuses(self, monitor):
        rows = [
            {"health_status": HealthStatus.EXCELLENT.value, "score": 95},
            {"health_status": HealthStatus.GOOD.value, "score": 80},
            {"health_status": HealthStatus.WARNING.value, "score": 60},
            {"health_status": HealthStatus.CRITICAL.value, "score": 20},
            {"health_status": HealthStatus.OFFLINE.value, "score": 0},
        ]
        summary = monitor.get_health_summary(rows)

        assert summary["total"] == 5
        assert summary["excellent"] == 1
        assert summary["good"] == 1
        assert summary["warning"] == 1
        assert summary["critical"] == 1
        assert summary["offline"] == 1
        assert summary["healthy"] == 2
        assert summary["needs_attention"] == 3
        assert summary["average_score"] == pytest.approx(51.0)

    def test_score_to_status_boundaries(self):
        assert AccountHealthMonitor._score_to_status(90) == HealthStatus.EXCELLENT
        assert AccountHealthMonitor._score_to_status(75) == HealthStatus.GOOD
        assert AccountHealthMonitor._score_to_status(50) == HealthStatus.WARNING
        assert AccountHealthMonitor._score_to_status(49.9) == HealthStatus.CRITICAL
