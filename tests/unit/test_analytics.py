"""
Unit tests for analytics collection and reporting.
"""

from datetime import datetime, timedelta

from app.core.analytics import AnalyticsCollector, CampaignAnalytics
from app.models import Account, AccountStatus, Campaign, CampaignStatus, SendLog, SendStatus


class TestAnalyticsCollector:
    """Tests for AnalyticsCollector."""

    def test_collect_campaign_analytics_success_rate(self):
        campaign = Campaign(
            name="Analytics Campaign",
            message_text="Hello",
            total_recipients=100,
            sent_count=80,
            failed_count=20,
            skipped_count=0,
            start_time_actual=datetime.utcnow() - timedelta(hours=1),
            end_time_actual=datetime.utcnow(),
        )
        campaign.id = 1

        stats = AnalyticsCollector().collect_campaign_analytics(campaign)

        assert stats.campaign_id == 1
        assert stats.campaign_name == "Analytics Campaign"
        assert stats.success_rate == 80.0
        assert stats.duration_minutes is not None
        assert stats.duration_minutes > 0

    def test_collect_campaign_analytics_zero_attempts(self):
        campaign = Campaign(
            name="Empty Campaign",
            message_text="Hello",
            total_recipients=10,
            sent_count=0,
            failed_count=0,
            skipped_count=0,
        )
        campaign.id = 2

        stats = AnalyticsCollector().collect_campaign_analytics(campaign)

        assert stats.success_rate == 0.0
        assert stats.duration_minutes is None

    def test_collect_account_analytics(self):
        account = Account(
            name="Analytics Account",
            phone_number="+15550001111",
            api_id=1,
            api_hash="hash",
            session_path="session_analytics",
            status=AccountStatus.ONLINE,
            total_messages_sent=90,
            total_messages_failed=10,
        )
        account.id = 3

        stats = AnalyticsCollector().collect_account_analytics(account)

        assert stats.account_id == 3
        assert stats.success_rate == 90.0
        assert stats.total_messages_sent == 90
        assert stats.total_messages_failed == 10

    def test_collect_send_log_analytics_empty(self):
        result = AnalyticsCollector().collect_send_log_analytics([])

        assert result["total_logs"] == 0
        assert result["success_rate"] == 0.0
        assert result["status_counts"] == {}

    def test_collect_send_log_analytics_with_logs(self):
        logs = [
            SendLog(
                account_id=1,
                message_text="ok",
                status=SendStatus.SENT,
                duration_ms=100,
                sent_at=datetime.utcnow(),
            ),
            SendLog(
                account_id=1,
                message_text="fail",
                status=SendStatus.FAILED,
                error_message="timeout",
                duration_ms=200,
                sent_at=datetime.utcnow(),
            ),
        ]

        result = AnalyticsCollector().collect_send_log_analytics(logs)

        assert result["total_logs"] == 2
        assert result["average_duration_ms"] == 150.0
        assert SendStatus.SENT in result["status_counts"]
        assert SendStatus.FAILED in result["status_counts"]


class TestCampaignAnalytics:
    """Tests for CampaignAnalytics reporting."""

    def test_generate_campaign_report_completion_rate(self):
        campaign = Campaign(
            name="Report Campaign",
            message_text="Hi",
            status=CampaignStatus.COMPLETED,
            total_recipients=50,
            sent_count=40,
            failed_count=5,
            skipped_count=5,
        )
        campaign.id = 10

        send_logs = [
            SendLog(
                account_id=1,
                campaign_id=10,
                message_text="m1",
                status=SendStatus.SENT,
                completed_at=datetime.utcnow(),
            ),
            SendLog(
                account_id=2,
                campaign_id=10,
                message_text="m2",
                status=SendStatus.FAILED,
                completed_at=datetime.utcnow(),
            ),
        ]

        collector = AnalyticsCollector()
        report = CampaignAnalytics(collector).generate_campaign_report(campaign, send_logs)

        assert report["campaign"]["id"] == 10
        assert report["campaign"]["completion_rate"] == 90.0
        assert report["performance"]["sent_count"] == 40
        assert report["performance"]["failed_count"] == 5
        assert 1 in report["accounts"]
        assert 2 in report["accounts"]
