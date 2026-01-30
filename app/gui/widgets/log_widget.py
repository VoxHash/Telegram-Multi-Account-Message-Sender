"""
Log viewing widgets.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QDateTimeEdit, QProgressBar, QTabWidget,
    QSplitter, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime, QThread
from PyQt5.QtGui import QFont, QIcon, QTextCursor, QColor

from ...services import get_logger, get_settings
from ...services.translation import _, get_translation_manager
from ...models import SendLog, SendStatus
import os
from datetime import datetime, timedelta


class LogViewer(QWidget):
    """Real-time log viewer widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.settings = get_settings()
        self.translation_manager = get_translation_manager()
        self.filtered_logs = []  # Initialize filtered logs list
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        self.setup_ui()
        self.setup_log_monitoring()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(_("logs.title"))
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Log level filter
        header_layout.addWidget(QLabel(f"{_('logs.level')}:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems([_("logs.all"), _("logs.debug"), _("logs.info"), _("logs.warning"), _("logs.error"), _("logs.critical")])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        header_layout.addWidget(self.level_combo)
        
        # Auto-scroll toggle
        self.auto_scroll_check = QCheckBox(_("logs.auto_scroll"))
        self.auto_scroll_check.setChecked(True)
        header_layout.addWidget(self.auto_scroll_check)
        
        # Clear button
        self.clear_button = QPushButton(_("logs.clear_logs"))
        self.clear_button.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.clear_button)
        
        # Refresh button
        self.refresh_button = QPushButton(_("logs.refresh"))
        self.refresh_button.clicked.connect(self.refresh_logs)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # Status bar
        self.status_label = QLabel(_("app.ready"))
        layout.addWidget(self.status_label)
    
    def setup_log_monitoring(self):
        """Set up log file monitoring."""
        self.log_file_path = self.settings.get_log_file_path()
        self.last_position = 0
        
        # Setup timer for checking log file
        self.log_timer = QTimer()
        self.log_timer.timeout.connect(self.check_log_file)
        self.log_timer.start(1000)  # Check every second
        
        # Load existing logs
        self.load_existing_logs()
    
    def load_existing_logs(self):
        """Load existing log content."""
        try:
            if self.log_file_path.exists():
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.log_text.setPlainText(content)
                    self.last_position = len(content)
                    
                    # Scroll to bottom
                    cursor = self.log_text.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    self.log_text.setTextCursor(cursor)
        except Exception as e:
            self.logger.error(f"Error loading existing logs: {e}")
    
    def check_log_file(self):
        """Check for new log entries."""
        try:
            if not self.log_file_path.exists():
                return
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_content = f.read()
                
                if new_content:
                    # Filter by level if not "All"
                    level_filter = self.level_combo.currentText()
                    if level_filter != _("logs.all"):
                        filtered_lines = []
                        for line in new_content.split('\n'):
                            if level_filter in line:
                                filtered_lines.append(line)
                        new_content = '\n'.join(filtered_lines)
                    
                    if new_content.strip():
                        # Append new content
                        self.log_text.append(new_content)
                        self.last_position = f.tell()
                        
                        # Auto-scroll if enabled
                        if self.auto_scroll_check.isChecked():
                            self.scroll_to_bottom()
                        
                        # Update status
                        self.status_label.setText(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
        
        except Exception as e:
            self.logger.error(f"Error checking log file: {e}")
    
    def filter_logs(self):
        """Filter logs by level."""
        try:
            if not self.log_file_path.exists():
                return
            
            level = self.level_combo.currentText()
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if level == _("logs.all"):
                # Show all logs
                self.log_text.setPlainText(content)
            else:
                # Filter by level - map UI level names to log level names
                level_mapping = {
                    _("logs.debug"): "DEBUG",
                    _("logs.info"): "INFO", 
                    _("logs.warning"): "WARNING",
                    _("logs.error"): "ERROR",
                    _("logs.critical"): "CRITICAL"
                }
                
                log_level = level_mapping.get(level, level)
                filtered_lines = []
                for line in content.split('\n'):
                    if log_level in line:
                        filtered_lines.append(line)
                self.log_text.setPlainText('\n'.join(filtered_lines))
            
            # Auto-scroll to bottom if enabled
            if self.auto_scroll_check.isChecked():
                cursor = self.log_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.log_text.setTextCursor(cursor)
            
            # Update status
            self.status_label.setText(f"Filtered by level: {level}")
            
        except Exception as e:
            self.logger.error(f"Error filtering logs: {e}")
            self.status_label.setText(f"Error filtering logs: {e}")
    
    def scroll_to_bottom(self):
        """Scroll to bottom of log text."""
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_logs(self):
        """Clear the log display and file."""
        self.log_text.clear()
        
        # Clear the actual log file
        try:
            if self.log_file_path.exists():
                with open(self.log_file_path, 'w', encoding='utf-8') as f:
                    f.write("")  # Clear the file
                self.last_position = 0  # Reset position to beginning
        except Exception as e:
            self.logger.error(f"Error clearing log file: {e}")
        
        # Reset filter to "All" to show all new logs
        self.level_combo.setCurrentText(_("logs.all"))
        
        # Clear the filtered logs list to reset filtering
        self.filtered_logs = []
        
        self.status_label.setText("Logs cleared - file and display cleared")
    
    def refresh_logs(self):
        """Refresh logs from file."""
        self.load_existing_logs()
        self.status_label.setText("Logs refreshed")
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Update UI elements with new translations
        self.title_label.setText(_("logs.title"))
        self.level_combo.clear()
        self.level_combo.addItems([_("logs.all"), _("logs.debug"), _("logs.info"), _("logs.warning"), _("logs.error"), _("logs.critical")])
        self.auto_scroll_check.setText(_("logs.auto_scroll"))
        self.clear_button.setText(_("logs.clear_logs"))
        self.refresh_button.setText(_("logs.refresh"))
        self.status_label.setText(_("app.ready"))
        self.setup_log_monitoring()


class SendLogWidget(QWidget):
    """Widget for viewing send logs from database."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.translation_manager = get_translation_manager()
        self.campaigns_loaded = False  # Flag to prevent duplicate campaign loading
        self.updating_campaigns = False  # Flag to prevent signal loops
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        self.setup_ui()
        self.load_send_logs()
        
        # Setup refresh timer (optional - user can manually refresh)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_send_logs)
        # Don't start auto-refresh by default - let user control it
        # self.refresh_timer.start(30000)  # Refresh every 30 seconds if enabled
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Header section
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(6)
        
        # Title and description
        title_layout = QHBoxLayout()
        self.title_label = QLabel(f"📊 {_('logs.send_logs')}")
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.title_label.setStyleSheet("color: #ffffff; margin-bottom: 2px;")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("🟢 Ready")
        self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
        title_layout.addWidget(self.status_indicator)
        
        header_layout.addLayout(title_layout)
        
        # Description
        self.desc_label = QLabel(_("logs.send_logs_description"))
        self.desc_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        self.desc_label.setWordWrap(True)
        header_layout.addWidget(self.desc_label)
        
        layout.addWidget(header_widget)
        
        # Filters section
        filters_widget = QWidget()
        filters_widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(12, 6, 12, 6)
        filters_layout.setSpacing(10)
        
        # Status filter
        status_label = QLabel(f"{_('logs.status')}:")
        status_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        filters_layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems([_("logs.all"), _("logs.sent"), _("logs.failed"), _("logs.rate_limited"), _("logs.skipped"), _("logs.pending")])
        self.status_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
        """)
        self.status_combo.currentTextChanged.connect(self.filter_logs)
        filters_layout.addWidget(self.status_combo)
        
        # Campaign filter
        campaign_label = QLabel(f"{_('logs.campaign')}:")
        campaign_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        filters_layout.addWidget(campaign_label)
        
        self.campaign_combo = QComboBox()
        self.campaign_combo.addItems([_("logs.all")])
        self.campaign_combo.setStyleSheet(self.status_combo.styleSheet())
        self.campaign_combo.currentTextChanged.connect(self.filter_logs)
        filters_layout.addWidget(self.campaign_combo)
        
        # Date range
        date_label = QLabel(f"{_('logs.date_range')}:")
        date_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        filters_layout.addWidget(date_label)
        
        self.from_date_edit = QDateTimeEdit()
        self.from_date_edit.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setStyleSheet("""
            QDateTimeEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 150px;
            }
            QDateTimeEdit:hover {
                border-color: #2196F3;
            }
        """)
        filters_layout.addWidget(self.from_date_edit)
        
        self.to_date_edit = QDateTimeEdit()
        self.to_date_edit.setDateTime(QDateTime.currentDateTime())
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setStyleSheet(self.from_date_edit.styleSheet())
        filters_layout.addWidget(self.to_date_edit)
        
        filters_layout.addStretch()
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.refresh_button = QPushButton(f"🔄 {_('logs.refresh_logs')}")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.refresh_button.clicked.connect(self.refresh_send_logs)
        button_layout.addWidget(self.refresh_button)
        
        self.export_button = QPushButton(f"📊 {_('logs.export_logs')}")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.export_button.clicked.connect(self.export_logs)
        button_layout.addWidget(self.export_button)
        
        filters_layout.addLayout(button_layout)
        layout.addWidget(filters_widget)
        
        # Search section
        search_widget = QWidget()
        search_widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(12, 6, 12, 6)
        search_layout.setSpacing(10)
        
        search_label = QLabel(f"{_('common.search')}:")
        search_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(_("logs.search_placeholder"))
        self.search_edit.textChanged.connect(self.filter_logs)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px 12px;
                min-width: 200px;
            }
            QLineEdit:hover {
                border-color: #2196F3;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        search_layout.addWidget(self.search_edit)
        search_layout.addStretch()
        
        layout.addWidget(search_widget)
        
        # Send logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(8)
        self.logs_table.setHorizontalHeaderLabels([
            _("logs.timestamp"), _("logs.campaign"), _("logs.account"), _("logs.recipient"), _("logs.status"), 
            _("logs.error_message"), _("logs.duration"), _("logs.retry_count")
        ])
        
        # Enhanced table styling
        self.logs_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                alternate-background-color: #2d2d2d;
                gridline-color: #404040;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 6px;
                selection-background-color: #2196F3;
                selection-color: #ffffff;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #2196F3 !important;
                color: #ffffff !important;
            }
            QTableWidget::item:alternate:selected {
                background-color: #2196F3 !important;
                color: #ffffff !important;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 12px 8px;
                border: none;
                border-right: 1px solid #404040;
                font-weight: bold;
                font-size: 12px;
            }
            QHeaderView::section:first {
                border-top-left-radius: 6px;
            }
            QHeaderView::section:last {
                border-top-right-radius: 6px;
                border-right: none;
            }
        """)
        
        # Configure table
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Timestamp
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Campaign
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Account
        header.setSectionResizeMode(3, QHeaderView.Stretch)          # Recipient
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Status
        header.setSectionResizeMode(5, QHeaderView.Stretch)          # Error Message
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Duration
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # Retry Count
        
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionMode(QTableWidget.SingleSelection)
        self.logs_table.setSortingEnabled(True)
        
        layout.addWidget(self.logs_table)
        
        # Status bar
        status_widget = QWidget()
        status_widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(8, 3, 8, 3)
        
        self.status_label = QLabel(f"📋 {_('logs.ready_no_logs')}")
        self.status_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Log count
        self.log_count_label = QLabel(f"0 {_('logs.logs')}")
        self.log_count_label.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 11px;")
        status_layout.addWidget(self.log_count_label)
        
        layout.addWidget(status_widget)
    
    def load_send_logs(self):
        """Load send logs from database."""
        try:
            from ...services.db import get_session
            from ...models import SendLog, Campaign, Account
            from sqlmodel import select, and_
            
            session = get_session()
            try:
                # Build query with filters and eager loading
                from sqlalchemy.orm import selectinload
                
                query = select(SendLog).options(
                    selectinload(SendLog.campaign),
                    selectinload(SendLog.account),
                    selectinload(SendLog.recipient)
                )
                
                # Status filter
                status_filter = self.status_combo.currentText()
                if status_filter != _("logs.all"):
                    # Map UI status names to enum values
                    status_mapping = {
                        _("logs.sent"): "sent",
                        _("logs.failed"): "failed", 
                        _("logs.rate_limited"): "rate_limited",
                        _("logs.skipped"): "skipped",
                        _("logs.pending"): "pending"
                    }
                    if status_filter in status_mapping:
                        query = query.where(SendLog.status == status_mapping[status_filter])
                
                # Date range filter
                from_date = self.from_date_edit.dateTime().toPyDateTime()
                to_date = self.to_date_edit.dateTime().toPyDateTime()
                query = query.where(and_(SendLog.created_at >= from_date, SendLog.created_at <= to_date))
                
                # Campaign filter
                campaign_filter = self.campaign_combo.currentText()
                if campaign_filter != _("logs.all"):
                    query = query.join(Campaign).where(Campaign.name == campaign_filter)
                
                # Execute query and load all data within session
                logs = session.exec(query.order_by(SendLog.created_at.desc()).limit(1000)).all()
                
                # Update campaign combo with available campaigns (only if not already loaded)
                if not self.campaigns_loaded:
                    self.logger.debug("Updating campaign combo - not loaded yet")
                    self.update_campaign_combo(session)
                else:
                    self.logger.debug("Campaign combo already loaded, skipping update")
                
                # Process logs within session context
                self.logs_table.setRowCount(len(logs))
                
                for row, log in enumerate(logs):
                    # Timestamp
                    timestamp = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    timestamp_item = QTableWidgetItem(timestamp)
                    timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemIsEditable)
                    self.logs_table.setItem(row, 0, timestamp_item)
                    
                    # Campaign - access within session
                    campaign_name = "Unknown"
                    if log.campaign:
                        campaign_name = log.campaign.name
                    campaign_item = QTableWidgetItem(campaign_name)
                    campaign_item.setFlags(campaign_item.flags() & ~Qt.ItemIsEditable)
                    self.logs_table.setItem(row, 1, campaign_item)
                    
                    # Account - access within session
                    account_name = "Unknown"
                    if log.account:
                        account_name = log.account.name
                    account_item = QTableWidgetItem(account_name)
                    account_item.setFlags(account_item.flags() & ~Qt.ItemIsEditable)
                    self.logs_table.setItem(row, 2, account_item)
                    
                    # Recipient - access within session
                    recipient_info = f"ID: {log.recipient_id}"
                    if log.recipient:
                        recipient_info = log.recipient.get_display_name()
                    recipient_item = QTableWidgetItem(recipient_info)
                    recipient_item.setFlags(recipient_item.flags() & ~Qt.ItemIsEditable)
                    self.logs_table.setItem(row, 3, recipient_item)
                    
                    # Status with enhanced styling
                    status_text = log.status.value.title()
                    status_item = QTableWidgetItem(status_text)
                    status_item.setTextAlignment(Qt.AlignCenter)
                    status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                    
                    # Enhanced status styling
                    if log.status == SendStatus.SENT:
                        status_item.setBackground(QColor(76, 175, 80))  # Green
                        status_item.setForeground(QColor(255, 255, 255))  # White text
                        status_text = f"✅ {status_text}"
                    elif log.status == SendStatus.FAILED:
                        status_item.setBackground(QColor(244, 67, 54))  # Red
                        status_item.setForeground(QColor(255, 255, 255))  # White text
                        status_text = f"❌ {status_text}"
                    elif log.status == SendStatus.RATE_LIMITED:
                        status_item.setBackground(QColor(255, 152, 0))  # Orange
                        status_item.setForeground(QColor(255, 255, 255))  # White text
                        status_text = f"⏰ {status_text}"
                    elif log.status == SendStatus.SKIPPED:
                        status_item.setBackground(QColor(33, 150, 243))  # Blue
                        status_item.setForeground(QColor(255, 255, 255))  # White text
                        status_text = f"⏭️ {status_text}"
                    elif log.status == SendStatus.PENDING:
                        status_item.setBackground(QColor(158, 158, 158))  # Gray
                        status_item.setForeground(QColor(255, 255, 255))  # White text
                        status_text = f"⏳ {status_text}"
                    
                    status_item.setText(status_text)
                    self.logs_table.setItem(row, 4, status_item)
                    
                    # Error message
                    error_msg = log.get_error_summary() if log.error_message else ""
                    error_item = QTableWidgetItem(error_msg)
                    error_item.setFlags(error_item.flags() & ~Qt.ItemIsEditable)
                    self.logs_table.setItem(row, 5, error_item)
                    
                    # Duration
                    duration = str(log.duration_ms) if log.duration_ms else "N/A"
                    duration_item = QTableWidgetItem(duration)
                    duration_item.setFlags(duration_item.flags() & ~Qt.ItemIsEditable)
                    self.logs_table.setItem(row, 6, duration_item)
                    
                    # Retry count
                    retry_item = QTableWidgetItem(str(log.retry_count))
                    retry_item.setFlags(retry_item.flags() & ~Qt.ItemIsEditable)
                    self.logs_table.setItem(row, 7, retry_item)
                
            finally:
                session.close()
            
            # Update status and count
            log_count = len(logs)
            self.status_label.setText(f"📋 {_('logs.loaded_successfully').format(count=log_count)}")
            self.log_count_label.setText(f"{log_count} {_('logs.logs')}")
            
            # Update status indicator
            if log_count > 0:
                self.status_indicator.setText("🟢 Active")
                self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.status_indicator.setText("🟡 No Data")
                self.status_indicator.setStyleSheet("color: #FF9800; font-weight: bold;")
            
            # Apply search filter if there's search text
            self.filter_logs_by_search()
            
        except Exception as e:
            self.logger.error(f"Error loading send logs: {e}")
            self.status_label.setText(f"❌ {_('logs.error_loading').format(error=str(e)[:50])}")
            self.log_count_label.setText(f"0 {_('logs.logs')}")
            self.status_indicator.setText("🔴 Error")
            self.status_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
    
    def refresh_send_logs(self):
        """Refresh send logs."""
        self.load_send_logs()
    
    def filter_logs(self):
        """Apply filters to logs."""
        if not self.updating_campaigns:
            self.load_send_logs()
    
    def filter_logs_by_search(self):
        """Filter logs based on search text."""
        search_text = self.search_edit.text().lower().strip()
        
        if not search_text:
            # Show all logs
            for row in range(self.logs_table.rowCount()):
                self.logs_table.setRowHidden(row, False)
            return
        
        # Filter logs (exclude Actions column - column 7)
        for row in range(self.logs_table.rowCount()):
            should_show = False
            
            # Check all columns except Actions column for search text
            for col in range(self.logs_table.columnCount() - 1):  # Exclude last column (Actions)
                item = self.logs_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            
            self.logs_table.setRowHidden(row, not should_show)
    
    def refresh_campaigns(self):
        """Refresh campaign list from database."""
        self.campaigns_loaded = False
        self.load_send_logs()
    
    def update_campaign_combo(self, session):
        """Update campaign combo with available campaigns."""
        try:
            from sqlmodel import select
            from ...models import Campaign
            
            # Set flag to prevent signal loops
            self.updating_campaigns = True
            
            # Get all campaigns
            campaigns = session.exec(select(Campaign).order_by(Campaign.name)).all()
            
            # Store current selection
            current_selection = self.campaign_combo.currentText()
            
            # Get current items to avoid unnecessary updates
            current_items = [self.campaign_combo.itemText(i) for i in range(self.campaign_combo.count())]
            expected_items = [_("logs.all")] + [campaign.name for campaign in campaigns if campaign.name]
            
            # Only update if the items have changed
            if set(current_items) != set(expected_items):
                # Clear and repopulate
                self.campaign_combo.clear()
                self.campaign_combo.addItem(_("logs.all"))
                
                # Add unique campaigns only
                seen_campaigns = set()
                for campaign in campaigns:
                    if campaign.name and campaign.name not in seen_campaigns:
                        self.campaign_combo.addItem(campaign.name)
                        seen_campaigns.add(campaign.name)
                
                # Restore selection if it still exists
                if current_selection in [self.campaign_combo.itemText(i) for i in range(self.campaign_combo.count())]:
                    self.campaign_combo.setCurrentText(current_selection)
                else:
                    self.campaign_combo.setCurrentText(_("logs.all"))
                
                self.logger.debug(f"Campaign combo updated with {len(seen_campaigns)} unique campaigns")
            else:
                self.logger.debug("Campaign combo items unchanged, skipping update")
            
            # Mark as loaded
            self.campaigns_loaded = True
                
        except Exception as e:
            self.logger.error(f"Error updating campaign combo: {e}")
        finally:
            # Clear flag to allow normal filtering
            self.updating_campaigns = False

    def export_logs(self):
        """Export logs to CSV."""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Send Logs",
                f"send_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write header
                    writer.writerow([
                        "Timestamp", "Campaign", "Account", "Recipient", "Status",
                        "Error Message", "Duration (ms)", "Retry Count"
                    ])
                    
                    # Write data
                    for row in range(self.logs_table.rowCount()):
                        row_data = []
                        for col in range(self.logs_table.columnCount()):
                            item = self.logs_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                exported_count = self.logs_table.rowCount()
                self.logger.info(f"Send logs exported to: {file_path}")
                
                # Update status
                self.status_label.setText(f"📊 {_('logs.exported_successfully').format(count=exported_count)}")
                
                QMessageBox.information(
                    self, 
                    _("logs.export_successful"), 
                    _("logs.exported_successfully").format(count=exported_count)
                )
        
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            self.status_label.setText(f"❌ Export failed: {str(e)[:30]}...")
            QMessageBox.critical(self, _("logs.export_failed"), _("logs.export_failed").format(error=str(e)))
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Update UI elements with new translations
        self.title_label.setText(f"📊 {_('logs.send_logs')}")
        self.desc_label.setText(_("logs.send_logs_description"))
        self.refresh_button.setText(f"🔄 {_('logs.refresh_logs')}")
        self.export_button.setText(f"📊 {_('logs.export_logs')}")
        
        # Update table headers
        self.logs_table.setHorizontalHeaderLabels([
            _("logs.timestamp"), _("logs.campaign"), _("logs.account"), _("logs.recipient"), _("logs.status"), 
            _("logs.error_message"), _("logs.duration"), _("logs.retry_count")
        ])
        
        # Update status bar
        self.status_label.setText(f"📋 {_('logs.ready_no_logs')}")
        self.log_count_label.setText(f"0 {_('logs.logs')}")
        
        # Reload data to refresh status messages
        self.load_send_logs()


class LogWidget(QWidget):
    """Main log management widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.translation_manager = get_translation_manager()
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Application logs tab
        self.app_log_viewer = LogViewer()
        tab_widget.addTab(self.app_log_viewer, _("logs.application_logs"))
        
        # Send logs tab
        self.send_log_widget = SendLogWidget()
        tab_widget.addTab(self.send_log_widget, _("logs.send_logs"))
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Update tab names
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            tab_widget.setTabText(0, _("logs.application_logs"))
            tab_widget.setTabText(1, _("logs.send_logs"))
