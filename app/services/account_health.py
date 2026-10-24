"""
Account health monitoring service.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum

from ..models import Account, AccountStatus, SendLog, SendStatus
from ..services.db import get_session
from ..services.logger import get_logger
from sqlmodel import select, func


class HealthStatus(str, Enum):
    """Account health status."""

    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


def _status_value(status: Any) -> str:
    """Normalize AccountStatus / string to lowercase value."""
    if hasattr(status, "value"):
        return str(status.value).lower()
    return str(status).lower()


class AccountHealthMonitor:
    """Monitors account health and performance."""

    def __init__(self):
        """Initialize account health monitor."""
        self.logger = get_logger()

    def check_account_health(self, account: Account) -> Dict[str, Any]:
        """Check health status of an account."""
        success_rate = account.get_success_rate()
        total_attempted = account.total_messages_sent + account.total_messages_failed
        status_value = _status_value(account.status)

        health_data: Dict[str, Any] = {
            "account_id": account.id,
            "account_name": account.name,
            "status": account.status,
            "health_status": HealthStatus.OFFLINE.value,
            "score": 0.0,
            "metrics": {},
            "warnings": [],
            "recommendations": [],
        }

        recent_failures = 0
        recent_total = 0
        recent_error_rate: Optional[float] = None

        with get_session() as session:
            since = datetime.utcnow() - timedelta(hours=24)
            recent_failures = (
                session.exec(
                    select(func.count(SendLog.id)).where(
                        SendLog.account_id == account.id,
                        SendLog.sent_at >= since,
                        SendLog.status == SendStatus.FAILED,
                    )
                ).first()
                or 0
            )
            recent_total = (
                session.exec(
                    select(func.count(SendLog.id)).where(
                        SendLog.account_id == account.id,
                        SendLog.sent_at >= since,
                    )
                ).first()
                or 0
            )
            if recent_total > 0:
                recent_error_rate = (recent_failures / recent_total) * 100

        health_data["metrics"] = {
            "success_rate": success_rate,
            "total_sent": account.total_messages_sent,
            "total_failed": account.total_messages_failed,
            "total_attempted": total_attempted,
            "recent_failures": recent_failures,
            "recent_total": recent_total,
            "recent_error_rate": recent_error_rate,
            "last_activity": account.last_activity.isoformat() if account.last_activity else None,
            "warmup_complete": account.is_warmup_complete(),
            "warmup_enabled": account.warmup_enabled,
            "is_active": account.is_active,
            "has_proxy": bool(account.proxy_host and account.proxy_port),
            "can_send": account.can_send_message(),
        }

        # Inactive accounts are not usable even if "online"
        if not account.is_active:
            health_data["health_status"] = HealthStatus.CRITICAL.value
            health_data["score"] = 0.0
            health_data["warnings"].append("Account is marked inactive")
            health_data["recommendations"].append(
                "Re-enable the account in Accounts before using it in campaigns"
            )
            return health_data

        # Non-online statuses: clear signals + actionable next steps
        if status_value != AccountStatus.ONLINE.value:
            return self._health_for_non_online(account, health_data, status_value)

        # Online: start from 100 and apply deductions
        score = 100.0

        if total_attempted == 0:
            health_data["recommendations"].append(
                "Send a test message to establish a baseline success rate"
            )
        elif success_rate < 50:
            score -= 30
            health_data["warnings"].append(f"Low success rate: {success_rate:.1f}%")
            health_data["recommendations"].append(
                "Reduce sending rate or review message content and recipient quality"
            )
        elif success_rate < 80:
            score -= 15
            health_data["warnings"].append(f"Moderate success rate: {success_rate:.1f}%")
            health_data["recommendations"].append(
                "Consider lowering send rate or checking recent error logs"
            )

        if account.last_activity:
            hours_since_activity = (
                datetime.utcnow() - account.last_activity
            ).total_seconds() / 3600
            if hours_since_activity > 24:
                score -= 20
                health_data["warnings"].append(
                    f"No activity for {hours_since_activity:.1f} hours"
                )
                health_data["recommendations"].append(
                    "Reconnect or send a test message to confirm the session is healthy"
                )
            elif hours_since_activity > 12:
                score -= 10
                health_data["warnings"].append(
                    f"Quiet for {hours_since_activity:.1f} hours"
                )
        else:
            score -= 5
            health_data["recommendations"].append(
                "No recorded activity yet — authorize and test the connection"
            )

        if account.warmup_enabled and not account.is_warmup_complete():
            score -= 10
            remaining = max(
                0, account.warmup_target_messages - account.warmup_messages_sent
            )
            health_data["warnings"].append(
                f"Warmup incomplete ({account.warmup_messages_sent}/{account.warmup_target_messages})"
            )
            health_data["recommendations"].append(
                f"Finish warmup ({remaining} message(s) left) before heavy campaign use"
            )

        if recent_error_rate is not None:
            if recent_error_rate > 20:
                score -= 25
                health_data["warnings"].append(
                    f"High 24h error rate: {recent_error_rate:.1f}%"
                )
                health_data["recommendations"].append(
                    "Pause campaigns for this account and review send logs"
                )
            elif recent_error_rate > 10:
                score -= 10
                health_data["warnings"].append(
                    f"Elevated 24h error rate: {recent_error_rate:.1f}%"
                )
                health_data["recommendations"].append(
                    "Review error logs and tighten rate limits"
                )

        if account.error_message:
            score -= 15
            health_data["warnings"].append(f"Last error: {account.error_message}")
            health_data["recommendations"].append(
                "Clear the error by testing the connection from the Accounts tab"
            )

        if not account.proxy_host or not account.proxy_port:
            # Soft signal only — many users run without proxies
            health_data["recommendations"].append(
                "Optional: configure a proxy to isolate account traffic"
            )

        score = max(0.0, min(100.0, score))
        health_data["score"] = score
        health_data["health_status"] = self._score_to_status(score).value

        # Deduplicate recommendations while preserving order
        seen = set()
        unique_recs = []
        for rec in health_data["recommendations"]:
            if rec not in seen:
                seen.add(rec)
                unique_recs.append(rec)
        health_data["recommendations"] = unique_recs

        return health_data

    def _health_for_non_online(
        self, account: Account, health_data: Dict[str, Any], status_value: str
    ) -> Dict[str, Any]:
        """Build health payload for offline / error / suspended / connecting accounts."""
        if status_value == AccountStatus.ERROR.value:
            health_data["health_status"] = HealthStatus.CRITICAL.value
            health_data["score"] = 10.0
            health_data["warnings"].append("Account is in error state")
            if account.error_message:
                health_data["warnings"].append(account.error_message)
            health_data["recommendations"].append(
                "Open Accounts → Test Connection, then re-authorize if needed"
            )
        elif status_value == AccountStatus.SUSPENDED.value:
            health_data["health_status"] = HealthStatus.CRITICAL.value
            health_data["score"] = 5.0
            health_data["warnings"].append("Account is suspended")
            health_data["recommendations"].append(
                "Do not send until the suspension is resolved; rotate to another account"
            )
        elif status_value == AccountStatus.CONNECTING.value:
            health_data["health_status"] = HealthStatus.WARNING.value
            health_data["score"] = 55.0
            health_data["warnings"].append("Account is still connecting")
            health_data["recommendations"].append(
                "Wait for the connection to finish, or reconnect from Accounts"
            )
        else:
            # offline or unknown
            health_data["health_status"] = HealthStatus.OFFLINE.value
            health_data["score"] = 0.0
            health_data["warnings"].append("Account is not online")
            health_data["recommendations"].append(
                "Connect the account from the Accounts tab before starting campaigns"
            )
            if account.error_message:
                health_data["warnings"].append(f"Last error: {account.error_message}")

        return health_data

    @staticmethod
    def _score_to_status(score: float) -> HealthStatus:
        """Map numeric score to HealthStatus for online accounts."""
        if score >= 90:
            return HealthStatus.EXCELLENT
        if score >= 75:
            return HealthStatus.GOOD
        if score >= 50:
            return HealthStatus.WARNING
        return HealthStatus.CRITICAL

    def get_all_accounts_health(self) -> List[Dict[str, Any]]:
        """Get health status for all accounts, worst score first."""
        with get_session() as session:
            query = select(Account).where(Account.is_deleted.is_(False))
            accounts = list(session.exec(query).all())

        results = [self.check_account_health(account) for account in accounts]
        results.sort(key=lambda item: (item.get("score", 0.0), item.get("account_name", "")))
        return results

    def get_health_summary(self, health_rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Aggregate health metrics for dashboard summary cards."""
        rows = health_rows if health_rows is not None else self.get_all_accounts_health()
        total = len(rows)
        if total == 0:
            return {
                "total": 0,
                "average_score": 0.0,
                "excellent": 0,
                "good": 0,
                "warning": 0,
                "critical": 0,
                "offline": 0,
                "needs_attention": 0,
                "healthy": 0,
            }

        counts = {
            HealthStatus.EXCELLENT.value: 0,
            HealthStatus.GOOD.value: 0,
            HealthStatus.WARNING.value: 0,
            HealthStatus.CRITICAL.value: 0,
            HealthStatus.OFFLINE.value: 0,
        }
        score_sum = 0.0
        for row in rows:
            status = row.get("health_status", HealthStatus.OFFLINE.value)
            if status in counts:
                counts[status] += 1
            score_sum += float(row.get("score", 0.0))

        needs_attention = (
            counts[HealthStatus.WARNING.value]
            + counts[HealthStatus.CRITICAL.value]
            + counts[HealthStatus.OFFLINE.value]
        )
        healthy = counts[HealthStatus.EXCELLENT.value] + counts[HealthStatus.GOOD.value]

        return {
            "total": total,
            "average_score": score_sum / total,
            "excellent": counts[HealthStatus.EXCELLENT.value],
            "good": counts[HealthStatus.GOOD.value],
            "warning": counts[HealthStatus.WARNING.value],
            "critical": counts[HealthStatus.CRITICAL.value],
            "offline": counts[HealthStatus.OFFLINE.value],
            "needs_attention": needs_attention,
            "healthy": healthy,
        }

    def get_account_performance_metrics(self, account_id: int, days: int = 7) -> Dict[str, Any]:
        """Get performance metrics for an account over a period."""
        with get_session() as session:
            account = session.get(Account, account_id)
            if not account:
                return {}

            since = datetime.utcnow() - timedelta(days=days)

            query = select(SendLog).where(
                SendLog.account_id == account_id, SendLog.sent_at >= since
            )
            logs = session.exec(query).all()

            total_sent = sum(1 for log in logs if log.status == SendStatus.SENT)
            total_failed = sum(1 for log in logs if log.status == SendStatus.FAILED)
            total = len(logs)

            daily_stats: Dict[str, Dict[str, int]] = {}
            for log in logs:
                if log.sent_at:
                    day = log.sent_at.date().isoformat()
                    if day not in daily_stats:
                        daily_stats[day] = {"sent": 0, "failed": 0}
                    if log.status == SendStatus.SENT:
                        daily_stats[day]["sent"] += 1
                    elif log.status == SendStatus.FAILED:
                        daily_stats[day]["failed"] += 1

            hourly_stats: Dict[int, Dict[str, int]] = {}
            for log in logs:
                if log.sent_at:
                    hour = log.sent_at.hour
                    if hour not in hourly_stats:
                        hourly_stats[hour] = {"sent": 0, "failed": 0}
                    if log.status == SendStatus.SENT:
                        hourly_stats[hour]["sent"] += 1
                    elif log.status == SendStatus.FAILED:
                        hourly_stats[hour]["failed"] += 1

            return {
                "account_id": account_id,
                "account_name": account.name,
                "period_days": days,
                "total_sent": total_sent,
                "total_failed": total_failed,
                "total": total,
                "success_rate": (total_sent / total * 100) if total > 0 else 0.0,
                "daily_breakdown": daily_stats,
                "hourly_breakdown": hourly_stats,
                "average_per_day": total / days if days > 0 else 0,
            }
