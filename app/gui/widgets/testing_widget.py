"""
Testing widget for sending test messages.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QGroupBox, QListWidget, QListWidgetItem, QMessageBox,
    QSplitter, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from ...services import get_logger, get_session
from ...models import Account, Recipient, MessageTemplate
from ...core.telethon_client import TelegramClientManager
from ...core.spintax import SpintaxProcessor


class TestMessageWorker(QThread):
    """Worker thread for sending test messages."""
    
    finished = pyqtSignal(dict)  # result dict with success, message, details
    progress = pyqtSignal(str)   # progress message
    
    def __init__(self, account_id: int, recipient_identifier: str, message_text: str, media_path: Optional[str] = None):
        super().__init__()
        self.account_id = account_id
        self.recipient_identifier = recipient_identifier
        self.message_text = message_text
        self.media_path = media_path
        self.logger = get_logger()
        self.client_manager = TelegramClientManager()
    
    def run(self):
        """Send test message."""
        import asyncio
        
        async def async_send():
            try:
                self.progress.emit("Connecting to Telegram...")
                
                # Get account from database
                with get_session() as session:
                    account = session.get(Account, self.account_id)
                    if not account:
                        self.finished.emit({
                            'success': False,
                            'message': 'Account not found',
                            'details': f'Account ID {self.account_id} not found in database'
                        })
                        return
                    
                    # Add account to client manager if not already added
                    if not self.client_manager.get_client(self.account_id):
                        self.progress.emit("Adding account to client manager...")
                        await self.client_manager.add_account(account)
                    
                    # Send message
                    self.progress.emit("Sending message...")
                    result = await self.client_manager.send_message(
                        account_id=self.account_id,
                        peer=self.recipient_identifier,
                        text=self.message_text,
                        media_path=self.media_path
                    )
                    
                    if result.get('success', False):
                        self.finished.emit({
                            'success': True,
                            'message': 'Message sent successfully',
                            'details': f"Sent to {self.recipient_identifier} at {datetime.now().strftime('%H:%M:%S')}"
                        })
                    else:
                        self.finished.emit({
                            'success': False,
                            'message': 'Failed to send message',
                            'details': result.get('error', 'Unknown error')
                        })
                    
            except Exception as e:
                self.logger.error(f"Error sending test message: {e}")
                self.finished.emit({
                    'success': False,
                    'message': 'Error sending message',
                    'details': str(e)
                })
            finally:
                # Clean up
                try:
                    if self.client_manager.get_client(self.account_id):
                        await self.client_manager.remove_account(self.account_id)
                except:
                    pass
        
        # Run the async function
        asyncio.run(async_send())


class TestingWidget(QWidget):
    """Widget for testing message sending."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.spintax_processor = SpintaxProcessor()
        self.recent_tests = []  # Store recent tests in memory
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Create splitter for form and results
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left side - Test Form
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        
        # Test Form Group
        form_group = QGroupBox("Send Test Message")
        form_group_layout = QFormLayout(form_group)
        
        # Account selection
        self.account_combo = QComboBox()
        self.account_combo.setPlaceholderText("Select account...")
        form_group_layout.addRow("Account:", self.account_combo)
        
        # Recipient selection
        self.recipient_combo = QComboBox()
        self.recipient_combo.setPlaceholderText("Select recipient...")
        form_group_layout.addRow("Recipient:", self.recipient_combo)
        
        # Message template selection
        self.template_combo = QComboBox()
        self.template_combo.setPlaceholderText("Select template (optional)...")
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        form_group_layout.addRow("Template:", self.template_combo)
        
        # Message text
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Enter message text or select a template...")
        self.message_edit.setMaximumHeight(100)
        form_group_layout.addRow("Message:", self.message_edit)
        
        # Media path (optional)
        self.media_edit = QLineEdit()
        self.media_edit.setPlaceholderText("Media file path (optional)...")
        form_group_layout.addRow("Media:", self.media_edit)
        
        form_layout.addWidget(form_group)
        
        # Send button
        self.send_button = QPushButton("Send Test Message")
        self.send_button.clicked.connect(self.send_test_message)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        form_layout.addWidget(self.send_button)
        
        form_layout.addStretch()
        splitter.addWidget(form_widget)
        
        # Right side - Recent Tests
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        # Recent Tests Group
        tests_group = QGroupBox("Recent Tests")
        tests_layout = QVBoxLayout(tests_group)
        
        # Clear button
        clear_layout = QHBoxLayout()
        self.clear_button = QPushButton("Clear Tests")
        self.clear_button.clicked.connect(self.clear_tests)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        clear_layout.addWidget(self.clear_button)
        clear_layout.addStretch()
        tests_layout.addLayout(clear_layout)
        
        # Tests list
        self.tests_list = QListWidget()
        self.tests_list.setStyleSheet("""
            QListWidget {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #404040;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
        """)
        tests_layout.addWidget(self.tests_list)
        
        results_layout.addWidget(tests_group)
        splitter.addWidget(results_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 300])
    
    def load_data(self):
        """Load accounts, recipients, and templates."""
        try:
            with get_session() as session:
                # Load accounts
                accounts = session.query(Account).filter(Account.deleted_at.is_(None)).all()
                self.account_combo.clear()
                for account in accounts:
                    status_icon = "🟢" if account.status == "ONLINE" else "🔴"
                    self.account_combo.addItem(f"{status_icon} {account.phone_number}", account.id)
                
                # Load recipients
                recipients = session.query(Recipient).filter(Recipient.deleted_at.is_(None)).all()
                self.recipient_combo.clear()
                for recipient in recipients:
                    if recipient.recipient_type == "USER":
                        icon = "👤"
                        name = recipient.username or recipient.first_name or recipient.phone_number or f"User {recipient.id}"
                    elif recipient.recipient_type == "GROUP":
                        icon = "👥"
                        name = recipient.group_title or recipient.group_username or f"Group {recipient.id}"
                    else:  # CHANNEL
                        icon = "📢"
                        name = recipient.group_title or recipient.group_username or f"Channel {recipient.id}"
                    
                    identifier = recipient.get_identifier()
                    self.recipient_combo.addItem(f"{icon} {name} ({identifier})", identifier)
                
                # Load templates
                templates = session.query(MessageTemplate).filter(MessageTemplate.deleted_at.is_(None)).all()
                self.template_combo.clear()
                self.template_combo.addItem("None", None)
                for template in templates:
                    self.template_combo.addItem(template.name, template.id)
                
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load data: {e}")
    
    def on_template_changed(self, template_name):
        """Handle template selection change."""
        if template_name == "None":
            return
        
        try:
            template_id = self.template_combo.currentData()
            if not template_id:
                return
            
            with get_session() as session:
                template = session.get(MessageTemplate, template_id)
                if template:
                    # Use spintax text if available, otherwise use body
                    message_text = template.spintax_text or template.body
                    self.message_edit.setPlainText(message_text)
                    
                    # Show template info
                    self.logger.info(f"Loaded template: {template.name}")
                    
        except Exception as e:
            self.logger.error(f"Error loading template: {e}")
    
    def send_test_message(self):
        """Send test message."""
        try:
            # Validate inputs
            account_id = self.account_combo.currentData()
            recipient_identifier = self.recipient_combo.currentData()
            message_text = self.message_edit.toPlainText().strip()
            
            if not account_id:
                QMessageBox.warning(self, "Validation Error", "Please select an account.")
                return
            
            if not recipient_identifier:
                QMessageBox.warning(self, "Validation Error", "Please select a recipient.")
                return
            
            if not message_text:
                QMessageBox.warning(self, "Validation Error", "Please enter a message.")
                return
            
            # Disable send button
            self.send_button.setEnabled(False)
            self.send_button.setText("Sending...")
            
            # Get media path
            media_path = self.media_edit.text().strip() or None
            
            # Create and start worker
            self.worker = TestMessageWorker(account_id, recipient_identifier, message_text, media_path)
            self.worker.finished.connect(self.on_test_finished)
            self.worker.progress.connect(self.on_test_progress)
            self.worker.start()
            
        except Exception as e:
            self.logger.error(f"Error sending test message: {e}")
            QMessageBox.critical(self, "Error", f"Failed to send test message: {e}")
            self.send_button.setEnabled(True)
            self.send_button.setText("Send Test Message")
    
    @pyqtSlot(str)
    def on_test_progress(self, message):
        """Handle test progress updates."""
        self.logger.info(f"Test progress: {message}")
    
    @pyqtSlot(dict)
    def on_test_finished(self, result):
        """Handle test completion."""
        try:
            # Re-enable send button
            self.send_button.setEnabled(True)
            self.send_button.setText("Send Test Message")
            
            # Add to recent tests
            test_entry = {
                'timestamp': datetime.now(),
                'account': self.account_combo.currentText(),
                'recipient': self.recipient_combo.currentText(),
                'message': self.message_edit.toPlainText()[:50] + "..." if len(self.message_edit.toPlainText()) > 50 else self.message_edit.toPlainText(),
                'success': result['success'],
                'details': result['details']
            }
            
            self.recent_tests.insert(0, test_entry)  # Add to beginning
            self.update_tests_list()
            
            # Show result message
            if result['success']:
                QMessageBox.information(self, "Success", f"Test message sent successfully!\n\n{result['details']}")
            else:
                QMessageBox.warning(self, "Failed", f"Test message failed!\n\n{result['message']}\n{result['details']}")
            
        except Exception as e:
            self.logger.error(f"Error handling test completion: {e}")
        finally:
            # Clean up worker
            if hasattr(self, 'worker'):
                self.worker.deleteLater()
    
    def update_tests_list(self):
        """Update the recent tests list."""
        self.tests_list.clear()
        
        for test in self.recent_tests[:20]:  # Show last 20 tests
            status_icon = "✅" if test['success'] else "❌"
            timestamp = test['timestamp'].strftime("%H:%M:%S")
            
            item_text = f"{status_icon} [{timestamp}] {test['account']} → {test['recipient']}"
            if not test['success']:
                item_text += f" - {test['details']}"
            
            item = QListWidgetItem(item_text)
            item.setToolTip(f"Message: {test['message']}\nDetails: {test['details']}")
            
            # Color code based on success
            if test['success']:
                item.setBackground(Qt.green)
            else:
                item.setBackground(Qt.red)
            
            self.tests_list.addItem(item)
    
    def clear_tests(self):
        """Clear recent tests."""
        reply = QMessageBox.question(
            self,
            "Clear Tests",
            "Are you sure you want to clear all recent tests?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.recent_tests.clear()
            self.update_tests_list()
            self.logger.info("Recent tests cleared")
