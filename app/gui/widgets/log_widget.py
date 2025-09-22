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
from ...models import SendLog, SendStatus
import os
from datetime import datetime, timedelta


class LogViewer(QWidget):
    """Real-time log viewer widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.settings = get_settings()
        self.setup_ui()
        self.setup_log_monitoring()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Log Viewer")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Log level filter
        header_layout.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self.filter_logs)
        header_layout.addWidget(self.level_combo)
        
        # Auto-scroll toggle
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        header_layout.addWidget(self.auto_scroll_check)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_logs)
        header_layout.addWidget(self.clear_button)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_logs)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Log display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # Status bar
        self.status_label = QLabel("Ready")
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
                    if level_filter != "All":
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
    
    def filter_logs(self, level: str):
        """Filter logs by level."""
        try:
            if not self.log_file_path.exists():
                return
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if level == "All":
                # Show all logs
                self.log_text.setPlainText(content)
            else:
                # Filter by level
                filtered_lines = []
                for line in content.split('\n'):
                    if level in line:
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
        """Clear the log display."""
        self.log_text.clear()
        
        # Reset the log file position to current end to avoid re-adding cleared content
        try:
            if self.log_file_path.exists():
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    f.seek(0, 2)  # Seek to end of file
                    self.last_position = f.tell()
        except Exception as e:
            self.logger.error(f"Error resetting log position: {e}")
        
        # Reset filter to "All" to show all new logs
        self.level_combo.setCurrentText("All")
        
        self.status_label.setText("Logs cleared - monitoring from current position")
    
    def refresh_logs(self):
        """Refresh logs from file."""
        self.load_existing_logs()
        self.status_label.setText("Logs refreshed")


class SendLogWidget(QWidget):
    """Widget for viewing send logs from database."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
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
        layout.setSpacing(15)
        
        # Header section
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 15, 15, 15)
        header_layout.setSpacing(15)
        
        # Title and description
        title_layout = QHBoxLayout()
        title_label = QLabel("📊 Send Logs")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 5px;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Status indicator
        self.status_indicator = QLabel("🟢 Ready")
        self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
        title_layout.addWidget(self.status_indicator)
        
        header_layout.addLayout(title_layout)
        
        # Description
        desc_label = QLabel("Monitor and analyze message delivery status, errors, and performance metrics.")
        desc_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        desc_label.setWordWrap(True)
        header_layout.addWidget(desc_label)
        
        layout.addWidget(header_widget)
        
        # Filters section
        filters_widget = QWidget()
        filters_widget.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(15, 10, 15, 10)
        filters_layout.setSpacing(15)
        
        # Status filter
        status_label = QLabel("Status:")
        status_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        filters_layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Sent", "Failed", "Rate Limited", "Skipped", "Pending"])
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
        campaign_label = QLabel("Campaign:")
        campaign_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        filters_layout.addWidget(campaign_label)
        
        self.campaign_combo = QComboBox()
        self.campaign_combo.addItems(["All"])
        self.campaign_combo.setStyleSheet(self.status_combo.styleSheet())
        self.campaign_combo.currentTextChanged.connect(self.filter_logs)
        filters_layout.addWidget(self.campaign_combo)
        
        # Date range
        date_label = QLabel("Date Range:")
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
        
        self.refresh_button = QPushButton("🔄 Refresh")
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
        
        self.export_button = QPushButton("📊 Export CSV")
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
        
        # Send logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(8)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "Campaign", "Account", "Recipient", "Status", 
            "Error Message", "Duration (ms)", "Retry Count"
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
                padding: 8px;
            }
        """)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_label = QLabel("📋 Ready - No logs loaded")
        self.status_label.setStyleSheet("color: #cccccc; font-size: 11px;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Log count
        self.log_count_label = QLabel("0 logs")
        self.log_count_label.setStyleSheet("color: #2196F3; font-weight: bold; font-size: 11px;")
        status_layout.addWidget(self.log_count_label)
        
        layout.addWidget(status_widget)
    
    def load_send_logs(self):
        """Load send logs from database."""
        try:
            from ...services import get_session
            from ...models import SendLog, Campaign, Account
            from sqlmodel import select, and_
            
            session = get_session()
            try:
                # Build query with filters and eager loading
                from sqlmodel import selectinload
                
                query = select(SendLog).options(
                    selectinload(SendLog.campaign),
                    selectinload(SendLog.account),
                    selectinload(SendLog.recipient)
                )
                
                # Status filter
                status_filter = self.status_combo.currentText()
                if status_filter != "All":
                    # Map UI status names to enum values
                    status_mapping = {
                        "Sent": "sent",
                        "Failed": "failed", 
                        "Rate Limited": "rate_limited",
                        "Skipped": "skipped",
                        "Pending": "pending"
                    }
                    if status_filter in status_mapping:
                        query = query.where(SendLog.status == status_mapping[status_filter])
                
                # Date range filter
                from_date = self.from_date_edit.dateTime().toPyDateTime()
                to_date = self.to_date_edit.dateTime().toPyDateTime()
                query = query.where(and_(SendLog.created_at >= from_date, SendLog.created_at <= to_date))
                
                # Campaign filter
                campaign_filter = self.campaign_combo.currentText()
                if campaign_filter != "All":
                    query = query.join(Campaign).where(Campaign.name == campaign_filter)
                
                # Execute query and load all data within session
                logs = session.exec(query.order_by(SendLog.created_at.desc()).limit(1000)).all()
                
                # Update campaign combo with available campaigns
                self.update_campaign_combo(session)
                
                # Process logs within session context
                self.logs_table.setRowCount(len(logs))
                
                for row, log in enumerate(logs):
                    # Timestamp
                    timestamp = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    self.logs_table.setItem(row, 0, QTableWidgetItem(timestamp))
                    
                    # Campaign - access within session
                    campaign_name = "Unknown"
                    if log.campaign:
                        campaign_name = log.campaign.name
                    self.logs_table.setItem(row, 1, QTableWidgetItem(campaign_name))
                    
                    # Account - access within session
                    account_name = "Unknown"
                    if log.account:
                        account_name = log.account.name
                    self.logs_table.setItem(row, 2, QTableWidgetItem(account_name))
                    
                    # Recipient - access within session
                    recipient_info = f"ID: {log.recipient_id}"
                    if log.recipient:
                        recipient_info = log.recipient.get_display_name()
                    self.logs_table.setItem(row, 3, QTableWidgetItem(recipient_info))
                    
                    # Status with enhanced styling
                    status_text = log.status.value.title()
                    status_item = QTableWidgetItem(status_text)
                    status_item.setTextAlignment(Qt.AlignCenter)
                    
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
                    self.logs_table.setItem(row, 5, QTableWidgetItem(error_msg))
                    
                    # Duration
                    duration = str(log.duration_ms) if log.duration_ms else "N/A"
                    self.logs_table.setItem(row, 6, QTableWidgetItem(duration))
                    
                    # Retry count
                    self.logs_table.setItem(row, 7, QTableWidgetItem(str(log.retry_count)))
                
            finally:
                session.close()
            
            # Update status and count
            log_count = len(logs)
            self.status_label.setText(f"📋 Loaded {log_count} send logs successfully")
            self.log_count_label.setText(f"{log_count} logs")
            
            # Update status indicator
            if log_count > 0:
                self.status_indicator.setText("🟢 Active")
                self.status_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
            else:
                self.status_indicator.setText("🟡 No Data")
                self.status_indicator.setStyleSheet("color: #FF9800; font-weight: bold;")
            
        except Exception as e:
            self.logger.error(f"Error loading send logs: {e}")
            self.status_label.setText(f"❌ Error loading send logs: {str(e)[:50]}...")
            self.log_count_label.setText("0 logs")
            self.status_indicator.setText("🔴 Error")
            self.status_indicator.setStyleSheet("color: #F44336; font-weight: bold;")
    
    def refresh_send_logs(self):
        """Refresh send logs."""
        self.load_send_logs()
    
    def filter_logs(self):
        """Apply filters to logs."""
        self.load_send_logs()
    
    def update_campaign_combo(self, session):
        """Update campaign combo with available campaigns."""
        try:
            from sqlmodel import select
            
            # Get all campaigns
            campaigns = session.exec(select(Campaign).order_by(Campaign.name)).all()
            
            # Store current selection
            current_selection = self.campaign_combo.currentText()
            
            # Clear and repopulate
            self.campaign_combo.clear()
            self.campaign_combo.addItem("All")
            
            for campaign in campaigns:
                self.campaign_combo.addItem(campaign.name)
            
            # Restore selection if it still exists
            if current_selection in [self.campaign_combo.itemText(i) for i in range(self.campaign_combo.count())]:
                self.campaign_combo.setCurrentText(current_selection)
            else:
                self.campaign_combo.setCurrentText("All")
                
        except Exception as e:
            self.logger.error(f"Error updating campaign combo: {e}")

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
                self.status_label.setText(f"📊 Exported {exported_count} logs successfully")
                
                QMessageBox.information(
                    self, 
                    "Export Complete", 
                    f"Successfully exported {exported_count} logs to:\n{file_path}"
                )
        
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            self.status_label.setText(f"❌ Export failed: {str(e)[:30]}...")
            QMessageBox.critical(self, "Export Error", f"Failed to export logs:\n{str(e)}")


class LogWidget(QWidget):
    """Main log management widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Application logs tab
        self.app_log_viewer = LogViewer()
        tab_widget.addTab(self.app_log_viewer, "Application Logs")
        
        # Send logs tab
        self.send_log_widget = SendLogWidget()
        tab_widget.addTab(self.send_log_widget, "Send Logs")
