"""
Unit tests for account health monitoring.
"""

from datetime import datetime, timedelta

from app.models import Account, AccountStatus, SendLog, SendStatus
from app.services import get_session
from app.services.account_health import AccountHealthMonitor, HealthStatus


class TestAccountHealthMonitor:
    """Tests for AccountHealthMonitor."""

    def test_offline_account_returns_offline_status(self):
        account = Account(
            name="Offline Account",
            phone_number="+15550002222",
            api_id=1,
            api_hash="hash",
            session_path="session_offline",
            status=AccountStatus.OFFLINE,
        )
        account.id = 1

        health = AccountHealthMonitor().check_account_health(account)

        assert health["health_status"] == HealthStatus.OFFLINE.value
        assert health["score"] == 0.0
        assert "Account is not online" in health["warnings"]

    def test_online_healthy_account(self, temp_db):
        monitor = AccountHealthMonitor()

        with get_session() as session:
            account = Account(
                name="Healthy Account",
                phone_number="+15550003333",
                api_id=1,
                api_hash="hash",
                session_path="session_healthy",
                status=AccountStatus.ONLINE,
                total_messages_sent=100,
                total_messages_failed=0,
                warmup_enabled=False,
                last_activity=datetime.utcnow(),
            )
            session.add(account)
            session.commit()
            session.refresh(account)

            health = monitor.check_account_health(account)

        assert health["health_status"] in (
            HealthStatus.EXCELLENT.value,
            HealthStatus.GOOD.value,
        )
        assert health["score"] >= 75.0
        assert health["metrics"]["success_rate"] == 100.0

    def test_online_account_with_recent_failures(self, temp_db):
        monitor = AccountHealthMonitor()

        with get_session() as session:
            account = Account(
                name="Warning Account",
                phone_number="+15550004444",
                api_id=1,
                api_hash="hash",
                session_path="session_warning",
                status=AccountStatus.ONLINE,
                total_messages_sent=50,
                total_messages_failed=50,
                warmup_enabled=False,
                last_activity=datetime.utcnow(),
            )
            session.add(account)
            session.commit()
            session.refresh(account)

            now = datetime.utcnow()
            for _ in range(8):
                session.add(
                    SendLog(
                        account_id=account.id,
                        message_text="failed",
                        status=SendStatus.FAILED,
                        sent_at=now,
                    )
                )
            for _ in range(2):
                session.add(
                    SendLog(
                        account_id=account.id,
                        message_text="sent",
                        status=SendStatus.SENT,
                        sent_at=now,
                    )
                )
            session.commit()

            health = monitor.check_account_health(account)

        assert health["health_status"] in (
            HealthStatus.WARNING.value,
            HealthStatus.CRITICAL.value,
        )
        assert health["metrics"]["recent_failures"] == 8
        assert health["metrics"]["recent_total"] == 10

    def test_get_account_performance_metrics_unknown_account(self, temp_db):
        metrics = AccountHealthMonitor().get_account_performance_metrics(99999)

        assert metrics == {}

    def test_get_account_performance_metrics_with_logs(self, temp_db):
        monitor = AccountHealthMonitor()

        with get_session() as session:
            account = Account(
                name="Metrics Account",
                phone_number="+15550005555",
                api_id=1,
                api_hash="hash",
                session_path="session_metrics",
                status=AccountStatus.ONLINE,
            )
            session.add(account)
            session.commit()
            session.refresh(account)

            sent_at = datetime.utcnow() - timedelta(days=1)
            session.add(
                SendLog(
                    account_id=account.id,
                    message_text="ok",
                    status=SendStatus.SENT,
                    sent_at=sent_at,
                )
            )
            session.add(
                SendLog(
                    account_id=account.id,
                    message_text="bad",
                    status=SendStatus.FAILED,
                    sent_at=sent_at,
                )
            )
            session.commit()

            metrics = monitor.get_account_performance_metrics(account.id, days=7)

        assert metrics["account_id"] == account.id
        assert metrics["total_sent"] == 1
        assert metrics["total_failed"] == 1
        assert metrics["total"] == 2
        assert metrics["success_rate"] == 50.0

    def test_get_all_accounts_health(self, temp_db):
        with get_session() as session:
            session.add(
                Account(
                    name="Listed Account",
                    phone_number="+15550006666",
                    api_id=1,
                    api_hash="hash",
                    session_path="session_listed",
                    status=AccountStatus.OFFLINE,
                )
            )
            session.commit()

        results = AccountHealthMonitor().get_all_accounts_health()

        listed = [r for r in results if r["account_name"] == "Listed Account"]
        assert len(listed) == 1
        assert listed[0]["health_status"] == HealthStatus.OFFLINE.value
