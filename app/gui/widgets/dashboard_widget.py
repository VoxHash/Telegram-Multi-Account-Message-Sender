"""
Dashboard widget with analytics and overview.
"""

from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
    QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import QTimer, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QBrush

from ...models import Campaign, CampaignStatus, Account, AccountStatus, SendLog, SendStatus
from ...services import get_logger, get_session
from ...services.translation import _
from ...core.analytics import AnalyticsCollector, CampaignAnalytics
from ...services.account_health import AccountHealthMonitor, HealthStatus
from sqlmodel import select, func


# Health signal colors (readable on light and dark palettes)
_HEALTH_COLORS = {
    HealthStatus.EXCELLENT.value: QColor(22, 163, 74),  # green
    HealthStatus.GOOD.value: QColor(34, 197, 94),
    HealthStatus.WARNING.value: QColor(217, 119, 6),  # amber
    HealthStatus.CRITICAL.value: QColor(220, 38, 38),  # red
    HealthStatus.OFFLINE.value: QColor(107, 114, 128),  # gray
}


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

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("color: palette(mid); font-size: 12px;")
        layout.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("color: palette(text); font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)

        self.subtitle_label = QLabel(subtitle if subtitle else "")
        self.subtitle_label.setStyleSheet("color: palette(mid); font-size: 10px;")
        self.subtitle_label.setVisible(bool(subtitle))
        layout.addWidget(self.subtitle_label)

        layout.addStretch()

    def set_value(self, value: str):
        """Update the value displayed in the card."""
        self.value_label.setText(value)

    def set_subtitle(self, subtitle: str):
        """Update the subtitle under the value."""
        self.subtitle_label.setText(subtitle)
        self.subtitle_label.setVisible(bool(subtitle))

    def set_value_color(self, color: QColor):
        """Tint the primary value for status emphasis."""
        self.value_label.setStyleSheet(
            f"color: {color.name()}; font-size: 24px; font-weight: bold;"
        )


class DashboardWidget(QWidget):
    """Dashboard widget showing overview and analytics."""

    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.analytics_collector = AnalyticsCollector()
        self.campaign_analytics = CampaignAnalytics(self.analytics_collector)
        self.health_monitor = AccountHealthMonitor()
        self._health_rows: list = []

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

        self.campaigns_empty_label = QLabel(_("dashboard.no_campaigns"))
        self.campaigns_empty_label.setAlignment(Qt.AlignCenter)
        self.campaigns_empty_label.setStyleSheet("color: palette(mid); padding: 16px;")
        self.campaigns_empty_label.setVisible(False)
        campaigns_layout.addWidget(self.campaigns_empty_label)

        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(6)
        self.campaigns_table.setHorizontalHeaderLabels(
            [
                _("common.name"),
                _("common.status"),
                _("campaigns.progress"),
                _("campaigns.sent"),
                _("campaigns.failed"),
                _("campaigns.success_rate"),
            ]
        )
        campaigns_header = self.campaigns_table.horizontalHeader()
        campaigns_header.setSectionResizeMode(0, QHeaderView.Stretch)
        campaigns_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        campaigns_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        campaigns_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        campaigns_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        campaigns_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.campaigns_table.setAlternatingRowColors(True)
        self.campaigns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.campaigns_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.campaigns_table.setSelectionMode(QAbstractItemView.SingleSelection)
        campaigns_layout.addWidget(self.campaigns_table)

        layout.addWidget(campaigns_group)

        # Account health summary + table
        health_group = QGroupBox(_("dashboard.account_health"))
        health_layout = QVBoxLayout(health_group)

        health_summary_layout = QGridLayout()
        health_summary_layout.setSpacing(12)
        self.health_avg_card = StatCard(_("dashboard.avg_health_score"), "—")
        self.health_healthy_card = StatCard(_("dashboard.healthy_accounts"), "0")
        self.health_attention_card = StatCard(_("dashboard.needs_attention"), "0")
        self.health_critical_card = StatCard(_("dashboard.critical_accounts"), "0")
        health_summary_layout.addWidget(self.health_avg_card, 0, 0)
        health_summary_layout.addWidget(self.health_healthy_card, 0, 1)
        health_summary_layout.addWidget(self.health_attention_card, 0, 2)
        health_summary_layout.addWidget(self.health_critical_card, 0, 3)
        health_layout.addLayout(health_summary_layout)

        self.health_empty_label = QLabel(_("dashboard.no_accounts_health"))
        self.health_empty_label.setAlignment(Qt.AlignCenter)
        self.health_empty_label.setStyleSheet("color: palette(mid); padding: 16px;")
        self.health_empty_label.setWordWrap(True)
        self.health_empty_label.setVisible(False)
        health_layout.addWidget(self.health_empty_label)

        self.health_table = QTableWidget()
        self.health_table.setColumnCount(6)
        self.health_table.setHorizontalHeaderLabels(
            [
                _("common.name"),
                _("common.status"),
                _("dashboard.health_status"),
                _("dashboard.health_score"),
                _("dashboard.success_rate_col"),
                _("dashboard.warnings"),
            ]
        )
        health_header = self.health_table.horizontalHeader()
        health_header.setSectionResizeMode(0, QHeaderView.Stretch)
        health_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        health_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        health_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        health_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        health_header.setSectionResizeMode(5, QHeaderView.Stretch)
        self.health_table.setAlternatingRowColors(True)
        self.health_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.health_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.health_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.health_table.setSortingEnabled(True)
        self.health_table.itemSelectionChanged.connect(self._on_health_selection_changed)
        health_layout.addWidget(self.health_table)

        self.health_detail_label = QLabel(_("dashboard.health_detail_hint"))
        self.health_detail_label.setWordWrap(True)
        self.health_detail_label.setStyleSheet(
            "color: palette(text); background-color: palette(base); "
            "border: 1px solid palette(mid); border-radius: 6px; padding: 10px;"
        )
        self.health_detail_label.setMinimumHeight(64)
        health_layout.addWidget(self.health_detail_label)

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
                query = select(func.count(Campaign.id)).where(Campaign.is_deleted.is_(False))
                total_campaigns = session.exec(query).first() or 0

                query = select(func.count(Campaign.id)).where(
                    Campaign.is_deleted.is_(False), Campaign.status == CampaignStatus.RUNNING
                )
                running_campaigns = session.exec(query).first() or 0

                query = select(func.count(Account.id)).where(Account.is_deleted.is_(False))
                total_accounts = session.exec(query).first() or 0

                query = select(func.count(Account.id)).where(
                    Account.is_deleted.is_(False), Account.status == AccountStatus.ONLINE
                )
                online_accounts = session.exec(query).first() or 0

                since = datetime.utcnow() - timedelta(hours=24)
                query = select(func.count(SendLog.id)).where(
                    SendLog.sent_at >= since, SendLog.status == SendStatus.SENT
                )
                messages_sent = session.exec(query).first() or 0

                query = select(func.count(SendLog.id)).where(SendLog.sent_at >= since)
                total_messages = session.exec(query).first() or 0

                query = select(func.count(SendLog.id)).where(
                    SendLog.sent_at >= since, SendLog.status == SendStatus.SENT
                )
                successful_messages = session.exec(query).first() or 0

                success_rate = (
                    (successful_messages / total_messages * 100) if total_messages > 0 else 0.0
                )

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
                query = (
                    select(Campaign)
                    .where(Campaign.is_deleted.is_(False))
                    .order_by(Campaign.updated_at.desc())
                    .limit(10)
                )
                campaigns = session.exec(query).all()

                is_empty = len(campaigns) == 0
                self.campaigns_empty_label.setVisible(is_empty)
                self.campaigns_table.setVisible(not is_empty)
                if is_empty:
                    self.campaigns_table.setRowCount(0)
                    return

                self.campaigns_table.setRowCount(len(campaigns))

                for row, campaign in enumerate(campaigns):
                    self.campaigns_table.setItem(row, 0, QTableWidgetItem(campaign.name))

                    status_item = QTableWidgetItem(campaign.status.value.title())
                    if campaign.status == CampaignStatus.RUNNING:
                        status_item.setForeground(QColor(0, 128, 0))
                    elif campaign.status == CampaignStatus.COMPLETED:
                        status_item.setForeground(QColor(0, 0, 255))
                    elif campaign.status == CampaignStatus.FAILED:
                        status_item.setForeground(QColor(255, 0, 0))
                    self.campaigns_table.setItem(row, 1, status_item)

                    self.campaigns_table.setItem(
                        row, 2, QTableWidgetItem(f"{campaign.progress_percentage:.1f}%")
                    )
                    self.campaigns_table.setItem(row, 3, QTableWidgetItem(str(campaign.sent_count)))

                    failed_item = QTableWidgetItem(str(campaign.failed_count))
                    if campaign.failed_count > 0:
                        failed_item.setForeground(QColor(255, 0, 0))
                    self.campaigns_table.setItem(row, 4, failed_item)

                    success_rate = campaign.get_success_rate()
                    success_item = QTableWidgetItem(f"{success_rate:.1f}%")
                    if success_rate < 50:
                        success_item.setForeground(QColor(255, 0, 0))
                    elif success_rate < 80:
                        success_item.setForeground(QColor(255, 165, 0))
                    self.campaigns_table.setItem(row, 5, success_item)

        except Exception as e:
            self.logger.error(f"Error updating campaigns table: {e}")

    def update_health_table(self):
        """Update account health summary cards and table."""
        try:
            health_data = self.health_monitor.get_all_accounts_health()
            self._health_rows = health_data
            summary = self.health_monitor.get_health_summary(health_data)

            self._update_health_summary_cards(summary)

            is_empty = len(health_data) == 0
            self.health_empty_label.setVisible(is_empty)
            self.health_table.setVisible(not is_empty)
            if is_empty:
                self.health_table.setRowCount(0)
                self.health_detail_label.setText(_("dashboard.no_accounts_health"))
                return

            # Disable sorting while populating to avoid row shuffle mid-fill
            self.health_table.setSortingEnabled(False)
            self.health_table.setRowCount(len(health_data))

            for row, health in enumerate(health_data):
                name_item = QTableWidgetItem(health.get("account_name") or "")
                name_item.setData(Qt.UserRole, health.get("account_id"))
                self.health_table.setItem(row, 0, name_item)

                status = health.get("status")
                status_text = status.value.title() if hasattr(status, "value") else str(status)
                status_item = QTableWidgetItem(status_text)
                if status == AccountStatus.ONLINE:
                    status_item.setForeground(QColor(22, 163, 74))
                elif status == AccountStatus.ERROR:
                    status_item.setForeground(QColor(220, 38, 38))
                elif status == AccountStatus.SUSPENDED:
                    status_item.setForeground(QColor(220, 38, 38))
                elif status == AccountStatus.CONNECTING:
                    status_item.setForeground(QColor(217, 119, 6))
                else:
                    status_item.setForeground(QColor(107, 114, 128))
                self.health_table.setItem(row, 1, status_item)

                health_status = health.get("health_status", HealthStatus.OFFLINE.value)
                label_key = f"dashboard.health_{health_status}"
                localized = _(label_key)
                if localized == label_key:
                    localized = health_status.replace("_", " ").title()
                health_item = QTableWidgetItem(localized)
                color = _HEALTH_COLORS.get(health_status, _HEALTH_COLORS[HealthStatus.OFFLINE.value])
                health_item.setForeground(color)
                health_item.setBackground(QBrush(QColor(color.red(), color.green(), color.blue(), 28)))
                self.health_table.setItem(row, 2, health_item)

                score = float(health.get("score", 0.0))
                score_item = QTableWidgetItem()
                score_item.setData(Qt.DisplayRole, round(score, 1))
                score_item.setForeground(
                    _HEALTH_COLORS.get(
                        health_status, _HEALTH_COLORS[HealthStatus.OFFLINE.value]
                    )
                )
                score_item.setTextAlignment(Qt.AlignCenter)
                self.health_table.setItem(row, 3, score_item)

                metrics = health.get("metrics") or {}
                total_attempted = metrics.get("total_attempted", 0)
                if total_attempted == 0:
                    rate_text = _("dashboard.no_send_history")
                    rate_item = QTableWidgetItem(rate_text)
                    rate_item.setForeground(QColor(107, 114, 128))
                else:
                    rate = float(metrics.get("success_rate", 0.0))
                    rate_item = QTableWidgetItem(f"{rate:.1f}%")
                    if rate < 50:
                        rate_item.setForeground(_HEALTH_COLORS[HealthStatus.CRITICAL.value])
                    elif rate < 80:
                        rate_item.setForeground(_HEALTH_COLORS[HealthStatus.WARNING.value])
                    else:
                        rate_item.setForeground(_HEALTH_COLORS[HealthStatus.GOOD.value])
                rate_item.setTextAlignment(Qt.AlignCenter)
                self.health_table.setItem(row, 4, rate_item)

                warnings = health.get("warnings") or []
                recommendations = health.get("recommendations") or []
                if warnings:
                    warnings_text = "; ".join(warnings[:2])
                    if len(warnings) > 2:
                        warnings_text += f" (+{len(warnings) - 2})"
                else:
                    warnings_text = _("dashboard.no_warnings")
                warnings_item = QTableWidgetItem(warnings_text)

                tooltip_parts = []
                if warnings:
                    tooltip_parts.append(
                        _("dashboard.warnings") + ":\n• " + "\n• ".join(warnings)
                    )
                if recommendations:
                    tooltip_parts.append(
                        _("dashboard.recommendations") + ":\n• " + "\n• ".join(recommendations)
                    )
                if tooltip_parts:
                    tip = "\n\n".join(tooltip_parts)
                    warnings_item.setToolTip(tip)
                    name_item.setToolTip(tip)
                    health_item.setToolTip(tip)
                else:
                    warnings_item.setForeground(QColor(22, 163, 74))

                self.health_table.setItem(row, 5, warnings_item)

            self.health_table.setSortingEnabled(True)
            # Default: worst scores first (actionable)
            self.health_table.sortItems(3, Qt.AscendingOrder)

            if self.health_table.currentRow() < 0 and self.health_table.rowCount() > 0:
                self.health_table.selectRow(0)
            else:
                self._on_health_selection_changed()

        except Exception as e:
            self.logger.error(f"Error updating health table: {e}")
            self.health_detail_label.setText(_("dashboard.health_refresh_error").format(error=str(e)))

    def _update_health_summary_cards(self, summary: dict):
        """Refresh the four health summary StatCards."""
        total = summary.get("total", 0)
        if total == 0:
            self.health_avg_card.set_value("—")
            self.health_avg_card.set_subtitle("")
            self.health_avg_card.value_label.setStyleSheet(
                "color: palette(text); font-size: 24px; font-weight: bold;"
            )
            self.health_healthy_card.set_value("0")
            self.health_healthy_card.set_subtitle("")
            self.health_attention_card.set_value("0")
            self.health_attention_card.set_subtitle("")
            self.health_critical_card.set_value("0")
            self.health_critical_card.set_subtitle("")
            return

        avg = float(summary.get("average_score", 0.0))
        self.health_avg_card.set_value(f"{avg:.0f}")
        status = AccountHealthMonitor._score_to_status(avg)
        self.health_avg_card.set_subtitle(status.value.replace("_", " ").title())
        self.health_avg_card.set_value_color(
            _HEALTH_COLORS.get(status.value, _HEALTH_COLORS[HealthStatus.OFFLINE.value])
        )

        healthy = int(summary.get("healthy", 0))
        attention = int(summary.get("needs_attention", 0))
        critical = int(summary.get("critical", 0)) + int(summary.get("offline", 0))

        self.health_healthy_card.set_value(str(healthy))
        self.health_healthy_card.set_subtitle(
            _("dashboard.of_total").format(count=total)
        )
        self.health_healthy_card.set_value_color(_HEALTH_COLORS[HealthStatus.GOOD.value])

        self.health_attention_card.set_value(str(attention))
        self.health_attention_card.set_subtitle(
            _("dashboard.warning_and_worse")
        )
        color = (
            _HEALTH_COLORS[HealthStatus.WARNING.value]
            if attention > 0
            else _HEALTH_COLORS[HealthStatus.GOOD.value]
        )
        self.health_attention_card.set_value_color(color)

        self.health_critical_card.set_value(str(critical))
        self.health_critical_card.set_subtitle(_("dashboard.critical_or_offline"))
        self.health_critical_card.set_value_color(
            _HEALTH_COLORS[HealthStatus.CRITICAL.value]
            if critical > 0
            else _HEALTH_COLORS[HealthStatus.GOOD.value]
        )

    def _on_health_selection_changed(self):
        """Show actionable detail for the selected health row."""
        row = self.health_table.currentRow()
        if row < 0 or not self._health_rows:
            self.health_detail_label.setText(_("dashboard.health_detail_hint"))
            return

        name_item = self.health_table.item(row, 0)
        if name_item is None:
            self.health_detail_label.setText(_("dashboard.health_detail_hint"))
            return

        account_id = name_item.data(Qt.UserRole)
        health = next(
            (h for h in self._health_rows if h.get("account_id") == account_id),
            None,
        )
        if health is None and 0 <= row < len(self._health_rows):
            # Fallback if sorting moved rows: match by name
            name = name_item.text()
            health = next(
                (h for h in self._health_rows if h.get("account_name") == name),
                None,
            )
        if health is None:
            self.health_detail_label.setText(_("dashboard.health_detail_hint"))
            return

        warnings = health.get("warnings") or []
        recommendations = health.get("recommendations") or []
        metrics = health.get("metrics") or {}
        parts = [
            f"{health.get('account_name')} — "
            f"{(health.get('health_status') or '').replace('_', ' ').title()} "
            f"({float(health.get('score', 0)):.0f}/100)"
        ]
        if metrics.get("last_activity"):
            parts.append(_("dashboard.last_activity").format(when=metrics["last_activity"]))
        elif warnings or recommendations:
            pass
        else:
            parts.append(_("dashboard.no_warnings"))

        if warnings:
            parts.append(
                _("dashboard.warnings") + ": " + "; ".join(warnings)
            )
        if recommendations:
            parts.append(
                _("dashboard.recommendations") + ": " + "; ".join(recommendations)
            )

        self.health_detail_label.setText("\n".join(parts))
