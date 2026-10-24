"""
Unit tests for campaign analytics CSV/JSON export.
"""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import json

from app.core.analytics import AnalyticsCollector, CampaignAnalytics


def _campaign(**overrides):
    defaults = {
        "id": 1,
        "name": "Launch",
        "status": SimpleNamespace(value="completed"),
        "total_recipients": 10,
        "sent_count": 8,
        "failed_count": 2,
        "skipped_count": 0,
        "start_time_actual": datetime(2026, 10, 1, 12, 0, 0),
        "end_time_actual": datetime(2026, 10, 1, 12, 30, 0),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _send_log(**overrides):
    defaults = {
        "account_id": 5,
        "status": SimpleNamespace(value="sent"),
        "duration_ms": 120,
        "error_message": None,
        "completed_at": datetime(2026, 10, 1, 12, 15, 0),
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestAnalyticsExport:
    def setup_method(self):
        self.collector = AnalyticsCollector()
        self.analytics = CampaignAnalytics(self.collector)

    def test_export_analytics_json_writes_file(self, tmp_path: Path):
        campaign = _campaign()
        logs = [_send_log(), _send_log(status=SimpleNamespace(value="failed"), error_message="flood")]
        report = self.analytics.generate_campaign_report(campaign, logs)
        out = tmp_path / "report.json"

        assert self.analytics.export_analytics_json(report, out) is True
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["campaign"]["name"] == "Launch"
        assert payload["performance"]["sent_count"] == 8
        assert "generated_at" in payload

    def test_export_analytics_csv_overview(self, tmp_path: Path):
        overview = self.analytics.build_overview_export(
            [_campaign(), _campaign(id=2, name="Follow-up", sent_count=3, failed_count=1)],
            {1: [_send_log()], 2: []},
        )
        out = tmp_path / "overview.csv"
        assert self.analytics.export_analytics_csv(overview, out) is True
        text = out.read_text(encoding="utf-8")
        assert "campaign_id" in text
        assert "Launch" in text
        assert "Follow-up" in text
        assert "overall_success_rate" in text or "summary.overall_success_rate" in text

    def test_build_overview_export_summary_math(self):
        overview = self.analytics.build_overview_export(
            [
                _campaign(sent_count=8, failed_count=2),
                _campaign(id=2, name="B", sent_count=2, failed_count=0),
            ]
        )
        assert overview["summary"]["campaign_count"] == 2
        assert overview["summary"]["total_sent"] == 10
        assert overview["summary"]["total_failed"] == 2
        assert abs(overview["summary"]["overall_success_rate"] - (10 / 12 * 100)) < 0.01
