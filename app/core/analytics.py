"""
Analytics and reporting for campaigns and accounts.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

from ..services import get_logger
from ..models import Campaign, Account, SendLog, SendStatus


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


class AnalyticsCollector:
    """Collects and processes analytics data."""
    
    def __init__(self):
        """Initialize analytics collector."""
        self.logger = get_logger()
    
    def collect_campaign_analytics(self, campaign: Campaign) -> CampaignStats:
        """Collect analytics for a campaign."""
        total_attempted = campaign.sent_count + campaign.failed_count
        success_rate = (campaign.sent_count / total_attempted * 100) if total_attempted > 0 else 0.0
        
        duration_minutes = None
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
            duration_minutes=duration_minutes
        )
    
    def collect_account_analytics(self, account: Account) -> AccountStats:
        """Collect analytics for an account."""
        total_attempted = account.total_messages_sent + account.total_messages_failed
        success_rate = (account.total_messages_sent / total_attempted * 100) if total_attempted > 0 else 0.0
        
        return AccountStats(
            account_id=account.id,
            account_name=account.name,
            total_messages_sent=account.total_messages_sent,
            total_messages_failed=account.total_messages_failed,
            success_rate=success_rate,
            last_activity=account.last_activity,
            status=account.status
        )
    
    def collect_send_log_analytics(self, send_logs: List[SendLog]) -> Dict[str, Any]:
        """Collect analytics from send logs."""
        if not send_logs:
            return {
                "total_logs": 0,
                "status_counts": {},
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "error_summary": {}
            }
        
        status_counts = defaultdict(int)
        durations = []
        errors = defaultdict(int)
        
        for log in send_logs:
            status_counts[log.status] += 1
            
            if log.duration_ms:
                durations.append(log.duration_ms)
            
            if log.status == "failed" and log.error_message:
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
            "error_summary": dict(errors)
        }


class CampaignAnalytics:
    """Campaign-specific analytics and reporting."""
    
    def __init__(self, analytics_collector: AnalyticsCollector):
        """Initialize campaign analytics."""
        self.analytics_collector = analytics_collector
        self.logger = get_logger()
    
    def generate_campaign_report(self, campaign: Campaign, send_logs: List[SendLog]) -> Dict[str, Any]:
        """Generate comprehensive campaign report."""
        campaign_stats = self.analytics_collector.collect_campaign_analytics(campaign)
        log_analytics = self.analytics_collector.collect_send_log_analytics(send_logs)
        
        # Calculate additional metrics
        completion_rate = (campaign_stats.sent_count + campaign_stats.failed_count) / campaign_stats.total_recipients * 100 if campaign_stats.total_recipients > 0 else 0.0
        
        # Group by account
        account_stats = defaultdict(lambda: {"sent": 0, "failed": 0, "skipped": 0})
        for log in send_logs:
            account_stats[log.account_id][log.status] += 1
        
        # Group by hour for timeline analysis
        hourly_stats = defaultdict(lambda: {"sent": 0, "failed": 0, "skipped": 0})
        for log in send_logs:
            if log.completed_at:
                hour = log.completed_at.hour
                hourly_stats[hour][log.status] += 1
        
        return {
            "campaign": {
                "id": campaign_stats.campaign_id,
                "name": campaign_stats.campaign_name,
                "status": campaign.status,
                "total_recipients": campaign_stats.total_recipients,
                "completion_rate": completion_rate
            },
            "performance": {
                "sent_count": campaign_stats.sent_count,
                "failed_count": campaign_stats.failed_count,
                "skipped_count": campaign_stats.skipped_count,
                "success_rate": campaign_stats.success_rate,
                "duration_minutes": campaign_stats.duration_minutes
            },
            "timing": {
                "start_time": campaign_stats.start_time,
                "end_time": campaign_stats.end_time,
                "hourly_breakdown": dict(hourly_stats)
            },
            "accounts": dict(account_stats),
            "logs": log_analytics,
            "generated_at": datetime.utcnow()
        }
    
    def generate_account_report(self, account: Account, send_logs: List[SendLog]) -> Dict[str, Any]:
        """Generate account performance report."""
        account_stats = self.analytics_collector.collect_account_analytics(account)
        log_analytics = self.analytics_collector.collect_send_log_analytics(send_logs)
        
        # Calculate daily performance
        daily_stats = defaultdict(lambda: {"sent": 0, "failed": 0, "skipped": 0})
        for log in send_logs:
            if log.completed_at:
                day = log.completed_at.date()
                daily_stats[day][log.status] += 1
        
        # Calculate hourly performance
        hourly_stats = defaultdict(lambda: {"sent": 0, "failed": 0, "skipped": 0})
        for log in send_logs:
            if log.completed_at:
                hour = log.completed_at.hour
                hourly_stats[hour][log.status] += 1
        
        return {
            "account": {
                "id": account_stats.account_id,
                "name": account_stats.account_name,
                "status": account_stats.status,
                "last_activity": account_stats.last_activity
            },
            "performance": {
                "total_sent": account_stats.total_messages_sent,
                "total_failed": account_stats.total_messages_failed,
                "success_rate": account_stats.success_rate
            },
            "daily_breakdown": {str(day): stats for day, stats in daily_stats.items()},
            "hourly_breakdown": dict(hourly_stats),
            "logs": log_analytics,
            "generated_at": datetime.utcnow()
        }
    
    def export_analytics_csv(self, data: Dict[str, Any], filename: str) -> bool:
        """Export analytics data to CSV."""
        try:
            import csv
            import json
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(['Metric', 'Value'])
                
                # Write basic metrics
                if 'campaign' in data:
                    writer.writerow(['Campaign ID', data['campaign']['id']])
                    writer.writerow(['Campaign Name', data['campaign']['name']])
                    writer.writerow(['Total Recipients', data['campaign']['total_recipients']])
                
                if 'performance' in data:
                    writer.writerow(['Sent Count', data['performance']['sent_count']])
                    writer.writerow(['Failed Count', data['performance']['failed_count']])
                    writer.writerow(['Success Rate', f"{data['performance']['success_rate']:.2f}%"])
                
                # Write detailed breakdowns
                if 'hourly_breakdown' in data:
                    writer.writerow([])
                    writer.writerow(['Hour', 'Sent', 'Failed', 'Skipped'])
                    for hour, stats in data['hourly_breakdown'].items():
                        writer.writerow([hour, stats['sent'], stats['failed'], stats['skipped']])
            
            self.logger.info(f"Analytics exported to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export analytics: {e}")
            return False
