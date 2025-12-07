"""
Dashboard widget with analytics and overview.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette

from ...models import Campaign, CampaignStatus, Account, AccountStatus, SendLog, SendStatus
from ...services import get_logger, get_session
from ...services.translation import _, get_translation_manager
from ...core.analytics import AnalyticsCollector, CampaignAnalytics
from ...services.account_health import AccountHealthMonitor, HealthStatus
from sqlmodel import select, func


class StatCard(QFrame):
    """Stat card widget for displaying metrics."""
    
    def __init__(self, title: str, value: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: palette(base);
                border: 1px solid palette(mid);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: palette(mid); font-size: 12px;")
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet("color: palette(text); font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)
        
        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: palette(mid); font-size: 10px;")
            layout.addWidget(subtitle_label)
        
        layout.addStretch()


class DashboardWidget(QWidget):
    """Dashboard widget showing overview and analytics."""
    
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.analytics_collector = AnalyticsCollector()
        self.campaign_analytics = CampaignAnalytics(self.analytics_collector)
        self.health_monitor = AccountHealthMonitor()
        
        self.setup_ui()
        self.setup_timer()
        self.refresh_data()
    
    def setup_ui(self):
        """Set up the dashboard UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel(_("dashboard.title"))
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        refresh_btn = QPushButton(_("common.refresh"))
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Stats cards
        stats_group = QGroupBox(_("dashboard.overview"))
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(12)
        
        self.campaigns_total_card = StatCard(_("dashboard.total_campaigns"), "0")
        self.campaigns_running_card = StatCard(_("dashboard.running_campaigns"), "0")
        self.accounts_total_card = StatCard(_("dashboard.total_accounts"), "0")
        self.accounts_online_card = StatCard(_("dashboard.online_accounts"), "0")
        self.messages_sent_card = StatCard(_("dashboard.messages_sent"), "0")
        self.success_rate_card = StatCard(_("dashboard.success_rate"), "0%")
        
        stats_layout.addWidget(self.campaigns_total_card, 0, 0)
        stats_layout.addWidget(self.campaigns_running_card, 0, 1)
        stats_layout.addWidget(self.accounts_total_card, 0, 2)
        stats_layout.addWidget(self.accounts_online_card, 1, 0)
        stats_layout.addWidget(self.messages_sent_card, 1, 1)
        stats_layout.addWidget(self.success_rate_card, 1, 2)
        
        layout.addWidget(stats_group)
        
        # Recent campaigns
        campaigns_group = QGroupBox(_("dashboard.recent_campaigns"))
        campaigns_layout = QVBoxLayout(campaigns_group)
        
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(6)
        self.campaigns_table.setHorizontalHeaderLabels([
            _("common.name"),
            _("common.status"),
            _("campaigns.progress"),
            _("campaigns.sent"),
            _("campaigns.failed"),
            _("campaigns.success_rate")
        ])
        self.campaigns_table.horizontalHeader().setStretchLastSection(True)
        self.campaigns_table.setAlternatingRowColors(True)
        self.campaigns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.campaigns_table.setEditTriggers(QTableWidget.NoEditTriggers)
        campaigns_layout.addWidget(self.campaigns_table)
        
        layout.addWidget(campaigns_group)
        
        # Account health
        health_group = QGroupBox(_("dashboard.account_health"))
        health_layout = QVBoxLayout(health_group)
        
        self.health_table = QTableWidget()
        self.health_table.setColumnCount(5)
        self.health_table.setHorizontalHeaderLabels([
            _("common.name"),
            _("common.status"),
            _("dashboard.health_status"),
            _("dashboard.health_score"),
            _("dashboard.warnings")
        ])
        self.health_table.horizontalHeader().setStretchLastSection(True)
        self.health_table.setAlternatingRowColors(True)
        self.health_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.health_table.setEditTriggers(QTableWidget.NoEditTriggers)
        health_layout.addWidget(self.health_table)
        
        layout.addWidget(health_group)
        
        layout.addStretch()
    
    def setup_timer(self):
        """Set up auto-refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_data(self):
        """Refresh dashboard data."""
        try:
            self.update_stats_cards()
            self.update_campaigns_table()
            self.update_health_table()
        except Exception as e:
            self.logger.error(f"Error refreshing dashboard: {e}")
    
    def update_stats_cards(self):
        """Update statistics cards."""
        try:
            with get_session() as session:
                # Campaigns
                query = select(func.count(Campaign.id)).where(Campaign.is_deleted == False)
                total_campaigns = session.exec(query).first() or 0
                
                query = select(func.count(Campaign.id)).where(
                    Campaign.is_deleted == False,
                    Campaign.status == CampaignStatus.RUNNING
                )
                running_campaigns = session.exec(query).first() or 0
                
                # Accounts
                query = select(func.count(Account.id)).where(Account.is_deleted == False)
                total_accounts = session.exec(query).first() or 0
                
                query = select(func.count(Account.id)).where(
                    Account.is_deleted == False,
                    Account.status == AccountStatus.ONLINE
                )
                online_accounts = session.exec(query).first() or 0
                
                # Messages (last 24 hours)
                since = datetime.utcnow() - timedelta(hours=24)
                query = select(func.count(SendLog.id)).where(
                    SendLog.sent_at >= since,
                    SendLog.status == SendStatus.SENT
                )
                messages_sent = session.exec(query).first() or 0
                
                # Success rate (last 24 hours)
                query = select(func.count(SendLog.id)).where(SendLog.sent_at >= since)
                total_messages = session.exec(query).first() or 0
                
                query = select(func.count(SendLog.id)).where(
                    SendLog.sent_at >= since,
                    SendLog.status == SendStatus.SENT
                )
                successful_messages = session.exec(query).first() or 0
                
                success_rate = (successful_messages / total_messages * 100) if total_messages > 0 else 0.0
                
                # Update cards
                self.campaigns_total_card.set_value(str(total_campaigns))
                self.campaigns_running_card.set_value(str(running_campaigns))
                self.accounts_total_card.set_value(str(total_accounts))
                self.accounts_online_card.set_value(str(online_accounts))
                self.messages_sent_card.set_value(str(messages_sent))
                self.success_rate_card.set_value(f"{success_rate:.1f}%")
                
        except Exception as e:
            self.logger.error(f"Error updating stats cards: {e}")
    
    def update_campaigns_table(self):
        """Update campaigns table."""
        try:
            with get_session() as session:
                # Get recent campaigns (last 10)
                query = select(Campaign).where(
                    Campaign.is_deleted == False
                ).order_by(Campaign.updated_at.desc()).limit(10)
                campaigns = session.exec(query).all()
                
                self.campaigns_table.setRowCount(len(campaigns))
                
                for row, campaign in enumerate(campaigns):
                    # Name
                    self.campaigns_table.setItem(row, 0, QTableWidgetItem(campaign.name))
                    
                    # Status
                    status_item = QTableWidgetItem(campaign.status.value.title())
                    if campaign.status == CampaignStatus.RUNNING:
                        status_item.setForeground(QColor(0, 128, 0))
                    elif campaign.status == CampaignStatus.COMPLETED:
                        status_item.setForeground(QColor(0, 0, 255))
                    elif campaign.status == CampaignStatus.FAILED:
                        status_item.setForeground(QColor(255, 0, 0))
                    self.campaigns_table.setItem(row, 1, status_item)
                    
                    # Progress
                    progress_item = QTableWidgetItem(f"{campaign.progress_percentage:.1f}%")
                    self.campaigns_table.setItem(row, 2, progress_item)
                    
                    # Sent
                    self.campaigns_table.setItem(row, 3, QTableWidgetItem(str(campaign.sent_count)))
                    
                    # Failed
                    failed_item = QTableWidgetItem(str(campaign.failed_count))
                    if campaign.failed_count > 0:
                        failed_item.setForeground(QColor(255, 0, 0))
                    self.campaigns_table.setItem(row, 4, failed_item)
                    
                    # Success rate
                    success_rate = campaign.get_success_rate()
                    success_item = QTableWidgetItem(f"{success_rate:.1f}%")
                    if success_rate < 80:
                        success_item.setForeground(QColor(255, 165, 0))
                    elif success_rate < 50:
                        success_item.setForeground(QColor(255, 0, 0))
                    self.campaigns_table.setItem(row, 5, success_item)
                
                self.campaigns_table.resizeColumnsToContents()
                
        except Exception as e:
            self.logger.error(f"Error updating campaigns table: {e}")
    
    def update_health_table(self):
        """Update account health table."""
        try:
            health_data = self.health_monitor.get_all_accounts_health()
            
            self.health_table.setRowCount(len(health_data))
            
            for row, health in enumerate(health_data):
                # Name
                self.health_table.setItem(row, 0, QTableWidgetItem(health["account_name"]))
                
                # Status
                status_item = QTableWidgetItem(health["status"].value.title() if hasattr(health["status"], "value") else str(health["status"]))
                if health["status"] == AccountStatus.ONLINE:
                    status_item.setForeground(QColor(0, 128, 0))
                else:
                    status_item.setForeground(QColor(128, 128, 128))
                self.health_table.setItem(row, 1, status_item)
                
                # Health status
                health_status = health["health_status"]
                health_item = QTableWidgetItem(health_status.title())
                if health_status == HealthStatus.EXCELLENT.value:
                    health_item.setForeground(QColor(0, 128, 0))
                elif health_status == HealthStatus.GOOD.value:
                    health_item.setForeground(QColor(0, 200, 0))
                elif health_status == HealthStatus.WARNING.value:
                    health_item.setForeground(QColor(255, 165, 0))
                elif health_status == HealthStatus.CRITICAL.value:
                    health_item.setForeground(QColor(255, 0, 0))
                self.health_table.setItem(row, 2, health_item)
                
                # Health score
                score = health["score"]
                score_item = QTableWidgetItem(f"{score:.1f}")
                if score >= 90:
                    score_item.setForeground(QColor(0, 128, 0))
                elif score >= 75:
                    score_item.setForeground(QColor(0, 200, 0))
                elif score >= 50:
                    score_item.setForeground(QColor(255, 165, 0))
                else:
                    score_item.setForeground(QColor(255, 0, 0))
                self.health_table.setItem(row, 3, score_item)
                
                # Warnings
                warnings = health.get("warnings", [])
                warnings_text = "; ".join(warnings[:2]) if warnings else _("dashboard.no_warnings")
                if len(warnings) > 2:
                    warnings_text += f" (+{len(warnings) - 2})"
                self.health_table.setItem(row, 4, QTableWidgetItem(warnings_text))
            
            self.health_table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Error updating health table: {e}")

