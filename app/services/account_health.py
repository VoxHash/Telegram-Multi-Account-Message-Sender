"""
Account health monitoring service.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from ..models import Account, AccountStatus, SendLog, SendStatus
from ..services import get_logger, get_session
from sqlmodel import select, func


class HealthStatus(str, Enum):
    """Account health status."""
    EXCELLENT = "excellent"
    GOOD = "good"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class AccountHealthMonitor:
    """Monitors account health and performance."""
    
    def __init__(self):
        """Initialize account health monitor."""
        self.logger = get_logger()
    
    def check_account_health(self, account: Account) -> Dict[str, Any]:
        """Check health status of an account."""
        health_data = {
            "account_id": account.id,
            "account_name": account.name,
            "status": account.status,
            "health_status": HealthStatus.OFFLINE.value,
            "score": 0.0,
            "metrics": {},
            "warnings": [],
            "recommendations": []
        }
        
        # Check if account is online
        if account.status != AccountStatus.ONLINE:
            health_data["health_status"] = HealthStatus.OFFLINE.value
            health_data["warnings"].append("Account is not online")
            return health_data
        
        # Calculate health score (0-100)
        score = 100.0
        
        # Check success rate
        success_rate = account.get_success_rate()
        if success_rate < 50:
            score -= 30
            health_data["warnings"].append(f"Low success rate: {success_rate:.1f}%")
        elif success_rate < 80:
            score -= 15
            health_data["warnings"].append(f"Moderate success rate: {success_rate:.1f}%")
        
        # Check recent activity
        if account.last_activity:
            hours_since_activity = (datetime.utcnow() - account.last_activity).total_seconds() / 3600
            if hours_since_activity > 24:
                score -= 20
                health_data["warnings"].append(f"No activity for {hours_since_activity:.1f} hours")
            elif hours_since_activity > 12:
                score -= 10
        
        # Check warmup status
        if account.warmup_enabled and not account.is_warmup_complete():
            score -= 10
            health_data["warnings"].append("Account is still in warmup phase")
        
        # Check error rate
        with get_session() as session:
            # Get recent send logs (last 24 hours)
            since = datetime.utcnow() - timedelta(hours=24)
            query = select(func.count(SendLog.id)).where(
                SendLog.account_id == account.id,
                SendLog.sent_at >= since,
                SendLog.status == SendStatus.FAILED
            )
            recent_failures = session.exec(query).first() or 0
            
            query = select(func.count(SendLog.id)).where(
                SendLog.account_id == account.id,
                SendLog.sent_at >= since
            )
            recent_total = session.exec(query).first() or 0
            
            if recent_total > 0:
                error_rate = (recent_failures / recent_total) * 100
                if error_rate > 20:
                    score -= 25
                    health_data["warnings"].append(f"High error rate: {error_rate:.1f}%")
                elif error_rate > 10:
                    score -= 10
        
        # Determine health status
        if score >= 90:
            health_data["health_status"] = HealthStatus.EXCELLENT.value
        elif score >= 75:
            health_data["health_status"] = HealthStatus.GOOD.value
        elif score >= 50:
            health_data["health_status"] = HealthStatus.WARNING.value
        else:
            health_data["health_status"] = HealthStatus.CRITICAL.value
        
        health_data["score"] = max(0.0, min(100.0, score))
        
        # Add recommendations
        if success_rate < 80:
            health_data["recommendations"].append("Consider reducing sending rate or checking message content")
        if account.warmup_enabled and not account.is_warmup_complete():
            health_data["recommendations"].append("Complete warmup phase before heavy usage")
        if recent_failures > 0 and recent_total > 0:
            error_rate = (recent_failures / recent_total) * 100
            if error_rate > 10:
                health_data["recommendations"].append("Review error logs and adjust sending strategy")
        
        # Store metrics
        health_data["metrics"] = {
            "success_rate": success_rate,
            "total_sent": account.total_messages_sent,
            "total_failed": account.total_messages_failed,
            "recent_failures": recent_failures,
            "recent_total": recent_total,
            "last_activity": account.last_activity.isoformat() if account.last_activity else None,
            "warmup_complete": account.is_warmup_complete()
        }
        
        return health_data
    
    def get_all_accounts_health(self) -> List[Dict[str, Any]]:
        """Get health status for all accounts."""
        with get_session() as session:
            query = select(Account).where(Account.is_deleted == False)
            accounts = session.exec(query).all()
            
            return [self.check_account_health(account) for account in accounts]
    
    def get_account_performance_metrics(self, account_id: int, days: int = 7) -> Dict[str, Any]:
        """Get performance metrics for an account over a period."""
        with get_session() as session:
            account = session.get(Account, account_id)
            if not account:
                return {}
            
            since = datetime.utcnow() - timedelta(days=days)
            
            # Get send logs
            query = select(SendLog).where(
                SendLog.account_id == account_id,
                SendLog.sent_at >= since
            )
            logs = session.exec(query).all()
            
            # Calculate metrics
            total_sent = sum(1 for log in logs if log.status == SendStatus.SENT)
            total_failed = sum(1 for log in logs if log.status == SendStatus.FAILED)
            total = len(logs)
            
            # Daily breakdown
            daily_stats = {}
            for log in logs:
                if log.sent_at:
                    day = log.sent_at.date().isoformat()
                    if day not in daily_stats:
                        daily_stats[day] = {"sent": 0, "failed": 0}
                    if log.status == SendStatus.SENT:
                        daily_stats[day]["sent"] += 1
                    else:
                        daily_stats[day]["failed"] += 1
            
            # Hourly breakdown
            hourly_stats = {}
            for log in logs:
                if log.sent_at:
                    hour = log.sent_at.hour
                    if hour not in hourly_stats:
                        hourly_stats[hour] = {"sent": 0, "failed": 0}
                    if log.status == SendStatus.SENT:
                        hourly_stats[hour]["sent"] += 1
                    else:
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
                "average_per_day": total / days if days > 0 else 0
            }

