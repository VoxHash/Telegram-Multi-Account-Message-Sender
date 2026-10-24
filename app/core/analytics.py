"""
Analytics and reporting for campaigns and accounts.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union

from ..models import Account, Campaign, SendLog
from ..services.logger import get_logger

JsonPrimitive = Union[str, int, float, bool, None]
AnalyticsPayload = Dict[str, Any]
PathLike = Union[str, Path]


@dataclass
class CampaignStats:
    """Campaign statistics."""

    campaign_id: int
    campaign_name: str
    total_recipients: int
    sent_count: int
    failed_count: int
    skipped_count: int
    success_rate: float
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_minutes: Optional[float]


@dataclass
class AccountStats:
    """Account statistics."""

    account_id: int
    account_name: str
    total_messages_sent: int
    total_messages_failed: int
    success_rate: float
    last_activity: Optional[datetime]
    status: str


def _json_default(value: Any) -> Any:
    """Serialize datetime/date and nested mappings for JSON export."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, set):
        return sorted(value)
    if hasattr(value, "value"):
        return value.value
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _flatten_for_csv(prefix: str, value: Any, rows: List[List[Any]]) -> None:
    """Recursively flatten nested dict/list structures into Metric/Value rows."""
    if isinstance(value, Mapping):
        for key, nested in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            _flatten_for_csv(next_prefix, nested, rows)
        return
    if isinstance(value, (list, tuple)):
        if not value:
            rows.append([prefix, ""])
            return
        if all(not isinstance(item, (Mapping, list, tuple)) for item in value):
            rows.append([prefix, "; ".join(str(item) for item in value)])
            return
        for index, item in enumerate(value):
            _flatten_for_csv(f"{prefix}[{index}]", item, rows)
        return
    if isinstance(value, datetime):
        rows.append([prefix, value.isoformat()])
        return
    if isinstance(value, date):
        rows.append([prefix, value.isoformat()])
        return
    rows.append([prefix, value])


class AnalyticsCollector:
    """Collects and processes analytics data."""

    def __init__(self) -> None:
        """Initialize analytics collector."""
        self.logger = get_logger()

    def collect_campaign_analytics(self, campaign: Campaign) -> CampaignStats:
        """Collect analytics for a campaign."""
        total_attempted = campaign.sent_count + campaign.failed_count
        success_rate = (campaign.sent_count / total_attempted * 100) if total_attempted > 0 else 0.0

        duration_minutes: Optional[float] = None
        if campaign.start_time_actual and campaign.end_time_actual:
            duration = campaign.end_time_actual - campaign.start_time_actual
            duration_minutes = duration.total_seconds() / 60

        return CampaignStats(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            total_recipients=campaign.total_recipients,
            sent_count=campaign.sent_count,
            failed_count=campaign.failed_count,
            skipped_count=campaign.skipped_count,
            success_rate=success_rate,
            start_time=campaign.start_time_actual,
            end_time=campaign.end_time_actual,
            duration_minutes=duration_minutes,
        )

    def collect_account_analytics(self, account: Account) -> AccountStats:
        """Collect analytics for an account."""
        total_attempted = account.total_messages_sent + account.total_messages_failed
        success_rate = (
            (account.total_messages_sent / total_attempted * 100) if total_attempted > 0 else 0.0
        )
        status = account.status.value if hasattr(account.status, "value") else str(account.status)

        return AccountStats(
            account_id=account.id,
            account_name=account.name,
            total_messages_sent=account.total_messages_sent,
            total_messages_failed=account.total_messages_failed,
            success_rate=success_rate,
            last_activity=account.last_activity,
            status=status,
        )

    def collect_send_log_analytics(self, send_logs: List[SendLog]) -> Dict[str, Any]:
        """Collect analytics from send logs."""
        if not send_logs:
            return {
                "total_logs": 0,
                "status_counts": {},
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "error_summary": {},
            }

        status_counts: Dict[str, int] = defaultdict(int)
        durations: List[float] = []
        errors: Dict[str, int] = defaultdict(int)

        for log in send_logs:
            status = log.status.value if hasattr(log.status, "value") else str(log.status)
            status_counts[status] += 1

            if log.duration_ms:
                durations.append(float(log.duration_ms))

            if status == "failed" and log.error_message:
                errors[log.error_message] += 1

        total_logs = len(send_logs)
        successful = status_counts.get("sent", 0)
        success_rate = (successful / total_logs * 100) if total_logs > 0 else 0.0
        average_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total_logs": total_logs,
            "status_counts": dict(status_counts),
            "success_rate": success_rate,
            "average_duration_ms": average_duration,
            "error_summary": dict(errors),
        }


class CampaignAnalytics:
    """Campaign-specific analytics and reporting."""

    def __init__(self, analytics_collector: AnalyticsCollector) -> None:
        """Initialize campaign analytics."""
        self.analytics_collector = analytics_collector
        self.logger = get_logger()

    def generate_campaign_report(
        self, campaign: Campaign, send_logs: List[SendLog]
    ) -> AnalyticsPayload:
        """Generate comprehensive campaign report."""
        campaign_stats = self.analytics_collector.collect_campaign_analytics(campaign)
        log_analytics = self.analytics_collector.collect_send_log_analytics(send_logs)

        completion_rate = (
            (campaign_stats.sent_count + campaign_stats.failed_count)
            / campaign_stats.total_recipients
            * 100
            if campaign_stats.total_recipients > 0
            else 0.0
        )

        account_stats: Dict[Any, Dict[str, int]] = defaultdict(
            lambda: {"sent": 0, "failed": 0, "skipped": 0}
        )
        for log in send_logs:
            status = log.status.value if hasattr(log.status, "value") else str(log.status)
            if status in account_stats[log.account_id]:
                account_stats[log.account_id][status] += 1
            else:
                account_stats[log.account_id][status] = (
                    account_stats[log.account_id].get(status, 0) + 1
                )

        hourly_stats: Dict[int, Dict[str, int]] = defaultdict(
            lambda: {"sent": 0, "failed": 0, "skipped": 0}
        )
        for log in send_logs:
            if log.completed_at:
                hour = log.completed_at.hour
                status = log.status.value if hasattr(log.status, "value") else str(log.status)
                if status in hourly_stats[hour]:
                    hourly_stats[hour][status] += 1
                else:
                    hourly_stats[hour][status] = hourly_stats[hour].get(status, 0) + 1

        campaign_status = (
            campaign.status.value if hasattr(campaign.status, "value") else str(campaign.status)
        )

        return {
            "campaign": {
                "id": campaign_stats.campaign_id,
                "name": campaign_stats.campaign_name,
                "status": campaign_status,
                "total_recipients": campaign_stats.total_recipients,
                "completion_rate": completion_rate,
            },
            "performance": {
                "sent_count": campaign_stats.sent_count,
                "failed_count": campaign_stats.failed_count,
                "skipped_count": campaign_stats.skipped_count,
                "success_rate": campaign_stats.success_rate,
                "duration_minutes": campaign_stats.duration_minutes,
            },
            "timing": {
                "start_time": campaign_stats.start_time,
                "end_time": campaign_stats.end_time,
                "hourly_breakdown": {str(hour): stats for hour, stats in hourly_stats.items()},
            },
            "accounts": {str(account_id): stats for account_id, stats in account_stats.items()},
            "logs": log_analytics,
            "generated_at": datetime.utcnow(),
        }

    def generate_account_report(
        self, account: Account, send_logs: List[SendLog]
    ) -> AnalyticsPayload:
        """Generate account performance report."""
        account_stats = self.analytics_collector.collect_account_analytics(account)
        log_analytics = self.analytics_collector.collect_send_log_analytics(send_logs)

        daily_stats: Dict[date, Dict[str, int]] = defaultdict(
            lambda: {"sent": 0, "failed": 0, "skipped": 0}
        )
        for log in send_logs:
            if log.completed_at:
                day = log.completed_at.date()
                status = log.status.value if hasattr(log.status, "value") else str(log.status)
                if status in daily_stats[day]:
                    daily_stats[day][status] += 1
                else:
                    daily_stats[day][status] = daily_stats[day].get(status, 0) + 1

        hourly_stats: Dict[int, Dict[str, int]] = defaultdict(
            lambda: {"sent": 0, "failed": 0, "skipped": 0}
        )
        for log in send_logs:
            if log.completed_at:
                hour = log.completed_at.hour
                status = log.status.value if hasattr(log.status, "value") else str(log.status)
                if status in hourly_stats[hour]:
                    hourly_stats[hour][status] += 1
                else:
                    hourly_stats[hour][status] = hourly_stats[hour].get(status, 0) + 1

        return {
            "account": {
                "id": account_stats.account_id,
                "name": account_stats.account_name,
                "status": account_stats.status,
                "last_activity": account_stats.last_activity,
            },
            "performance": {
                "total_sent": account_stats.total_messages_sent,
                "total_failed": account_stats.total_messages_failed,
                "success_rate": account_stats.success_rate,
            },
            "daily_breakdown": {str(day): stats for day, stats in daily_stats.items()},
            "hourly_breakdown": {str(hour): stats for hour, stats in hourly_stats.items()},
            "logs": log_analytics,
            "generated_at": datetime.utcnow(),
        }

    def build_overview_export(
        self,
        campaigns: Iterable[Campaign],
        send_logs_by_campaign: Optional[Mapping[int, List[SendLog]]] = None,
    ) -> AnalyticsPayload:
        """Build a multi-campaign analytics payload suitable for CSV/JSON export."""
        send_logs_by_campaign = send_logs_by_campaign or {}
        campaign_reports: List[AnalyticsPayload] = []
        summary_rows: List[Dict[str, Any]] = []

        for campaign in campaigns:
            logs = list(send_logs_by_campaign.get(campaign.id, []))
            report = self.generate_campaign_report(campaign, logs)
            campaign_reports.append(report)
            summary_rows.append(
                {
                    "campaign_id": report["campaign"]["id"],
                    "campaign_name": report["campaign"]["name"],
                    "status": report["campaign"]["status"],
                    "total_recipients": report["campaign"]["total_recipients"],
                    "sent_count": report["performance"]["sent_count"],
                    "failed_count": report["performance"]["failed_count"],
                    "skipped_count": report["performance"]["skipped_count"],
                    "success_rate": report["performance"]["success_rate"],
                    "completion_rate": report["campaign"]["completion_rate"],
                }
            )

        total_sent = sum(row["sent_count"] for row in summary_rows)
        total_failed = sum(row["failed_count"] for row in summary_rows)
        attempted = total_sent + total_failed
        overall_success = (total_sent / attempted * 100) if attempted else 0.0

        return {
            "export_type": "campaign_analytics_overview",
            "generated_at": datetime.utcnow(),
            "summary": {
                "campaign_count": len(summary_rows),
                "total_sent": total_sent,
                "total_failed": total_failed,
                "overall_success_rate": overall_success,
            },
            "campaigns": summary_rows,
            "reports": campaign_reports,
        }

    def export_analytics_csv(self, data: AnalyticsPayload, filename: PathLike) -> bool:
        """Export analytics data to CSV (flattened key/value plus campaign summary table)."""
        path = Path(filename)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)

                # Prefer a tabular campaigns section when present (overview export).
                campaigns = data.get("campaigns")
                if isinstance(campaigns, list) and campaigns and isinstance(campaigns[0], Mapping):
                    headers = list(campaigns[0].keys())
                    writer.writerow(headers)
                    for row in campaigns:
                        writer.writerow([row.get(header, "") for header in headers])
                    writer.writerow([])

                writer.writerow(["Metric", "Value"])
                flat_rows: List[List[Any]] = []
                # Avoid duplicating the campaigns table in the flat section.
                flat_source = {key: value for key, value in data.items() if key != "campaigns"}
                if "reports" in flat_source:
                    # Keep overview JSON-friendly detail out of a huge flat dump; summarize count.
                    reports = flat_source.pop("reports")
                    flat_source["reports_count"] = len(reports) if isinstance(reports, list) else 0
                _flatten_for_csv("", flat_source, flat_rows)
                for metric, value in flat_rows:
                    writer.writerow([metric, value])

                # Legacy single-campaign shape helpers
                hourly = None
                if isinstance(data.get("hourly_breakdown"), Mapping):
                    hourly = data["hourly_breakdown"]
                elif isinstance(data.get("timing"), Mapping):
                    timing = data["timing"]
                    if isinstance(timing.get("hourly_breakdown"), Mapping):
                        hourly = timing["hourly_breakdown"]
                if hourly:
                    writer.writerow([])
                    writer.writerow(["Hour", "Sent", "Failed", "Skipped"])
                    for hour, stats in sorted(hourly.items(), key=lambda item: str(item[0])):
                        if isinstance(stats, Mapping):
                            writer.writerow(
                                [
                                    hour,
                                    stats.get("sent", 0),
                                    stats.get("failed", 0),
                                    stats.get("skipped", 0),
                                ]
                            )

            self.logger.info(f"Analytics exported to {path}")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to export analytics CSV: {exc}")
            return False

    def export_analytics_json(self, data: AnalyticsPayload, filename: PathLike) -> bool:
        """Export analytics data to JSON with ISO timestamps."""
        path = Path(filename)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, default=_json_default, ensure_ascii=False)
                handle.write("\n")
            self.logger.info(f"Analytics exported to {path}")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to export analytics JSON: {exc}")
            return False

    def stats_to_dict(self, stats: Union[CampaignStats, AccountStats]) -> Dict[str, Any]:
        """Convert a stats dataclass to a JSON-serializable dict."""
        return asdict(stats)
