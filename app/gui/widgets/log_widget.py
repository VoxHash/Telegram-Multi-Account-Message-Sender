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
from PyQt5.QtGui import QFont, QIcon, QTextCursor

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
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_send_logs)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Send Logs")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Filters
        header_layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["All", "Sent", "Failed", "Rate Limited", "Skipped", "Pending"])
        self.status_combo.currentTextChanged.connect(self.filter_logs)
        header_layout.addWidget(self.status_combo)
        
        header_layout.addWidget(QLabel("Campaign:"))
        self.campaign_combo = QComboBox()
        self.campaign_combo.addItems(["All"])
        self.campaign_combo.currentTextChanged.connect(self.filter_logs)
        header_layout.addWidget(self.campaign_combo)
        
        # Date range
        header_layout.addWidget(QLabel("From:"))
        self.from_date_edit = QDateTimeEdit()
        self.from_date_edit.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.from_date_edit.setCalendarPopup(True)
        header_layout.addWidget(self.from_date_edit)
        
        header_layout.addWidget(QLabel("To:"))
        self.to_date_edit = QDateTimeEdit()
        self.to_date_edit.setDateTime(QDateTime.currentDateTime())
        self.to_date_edit.setCalendarPopup(True)
        header_layout.addWidget(self.to_date_edit)
        
        # Refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_send_logs)
        header_layout.addWidget(self.refresh_button)
        
        # Export button
        self.export_button = QPushButton("Export CSV")
        self.export_button.clicked.connect(self.export_logs)
        header_layout.addWidget(self.export_button)
        
        layout.addLayout(header_layout)
        
        # Send logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(8)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "Campaign", "Account", "Recipient", "Status", 
            "Error Message", "Duration (ms)", "Retry Count"
        ])
        
        # Configure table
        header = self.logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.logs_table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def load_send_logs(self):
        """Load send logs from database."""
        try:
            from ...services import get_session
            from ...models import SendLog, Campaign, Account
            
            session = get_session()
            try:
                from ...models import SendLog, Campaign, Account
                from sqlmodel import select, and_
                
                # Build query with filters
                query = select(SendLog)
                
                # Status filter
                status_filter = self.status_combo.currentText()
                if status_filter != "All":
                    query = query.where(SendLog.status == status_filter.lower())
                
                # Date range filter
                from_date = self.from_date_edit.dateTime().toPyDateTime()
                to_date = self.to_date_edit.dateTime().toPyDateTime()
                query = query.where(and_(SendLog.created_at >= from_date, SendLog.created_at <= to_date))
                
                # Campaign filter
                campaign_filter = self.campaign_combo.currentText()
                if campaign_filter != "All":
                    query = query.join(Campaign).where(Campaign.name == campaign_filter)
                
                logs = session.exec(query.order_by(SendLog.created_at.desc()).limit(1000)).all()
            finally:
                session.close()
            
            self.logs_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                # Timestamp
                timestamp = log.created_at.strftime("%Y-%m-%d %H:%M:%S")
                self.logs_table.setItem(row, 0, QTableWidgetItem(timestamp))
                
                # Campaign
                campaign_name = log.campaign.name if log.campaign else "Unknown"
                self.logs_table.setItem(row, 1, QTableWidgetItem(campaign_name))
                
                # Account
                account_name = log.account.name if log.account else "Unknown"
                self.logs_table.setItem(row, 2, QTableWidgetItem(account_name))
                
                # Recipient
                recipient_info = f"ID: {log.recipient_id}"
                if log.recipient:
                    recipient_info = log.recipient.get_display_name()
                self.logs_table.setItem(row, 3, QTableWidgetItem(recipient_info))
                
                # Status
                status_item = QTableWidgetItem(log.status.value.title())
                if log.status == SendStatus.SENT:
                    status_item.setBackground(Qt.green)
                elif log.status == SendStatus.FAILED:
                    status_item.setBackground(Qt.red)
                elif log.status == SendStatus.RATE_LIMITED:
                    status_item.setBackground(Qt.yellow)
                elif log.status == SendStatus.SKIPPED:
                    status_item.setBackground(Qt.blue)
                self.logs_table.setItem(row, 4, status_item)
                
                # Error message
                error_msg = log.get_error_summary() if log.error_message else ""
                self.logs_table.setItem(row, 5, QTableWidgetItem(error_msg))
                
                # Duration
                duration = str(log.duration_ms) if log.duration_ms else "N/A"
                self.logs_table.setItem(row, 6, QTableWidgetItem(duration))
                
                # Retry count
                self.logs_table.setItem(row, 7, QTableWidgetItem(str(log.retry_count)))
            
            self.status_label.setText(f"Loaded {len(logs)} send logs")
            
        except Exception as e:
            self.logger.error(f"Error loading send logs: {e}")
            self.status_label.setText(f"Error loading send logs: {e}")
    
    def refresh_send_logs(self):
        """Refresh send logs."""
        self.load_send_logs()
    
    def filter_logs(self):
        """Apply filters to logs."""
        self.load_send_logs()
    
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
                
                self.logger.info(f"Send logs exported to: {file_path}")
                QMessageBox.information(self, "Export Complete", f"Logs exported to:\n{file_path}")
        
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            QMessageBox.critical(self, "Export Error", f"Failed to export logs: {e}")


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
