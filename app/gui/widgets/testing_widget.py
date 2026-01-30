"""
Testing widget for sending test messages.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit,
    QGroupBox, QListWidget, QListWidgetItem, QMessageBox,
    QSplitter, QFrame, QFileDialog, QTabWidget, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from ...services import get_logger
from ...services.db import get_session
from ...services.translation import _, get_translation_manager
from ...models import Account, Recipient, MessageTemplate
from ...core.telethon_client import TelegramClientManager
from ...core.spintax import SpintaxProcessor


class TestMessageWorker(QThread):
    """Worker thread for sending test messages."""
    
    finished = pyqtSignal(dict)  # result dict with success, message, details
    progress = pyqtSignal(str)   # progress message
    
    def __init__(self, account_id: int, recipient_identifier: str, message_text: str, media_path: Optional[str] = None, use_spintax: bool = False):
        super().__init__()
        self.account_id = account_id
        self.recipient_identifier = recipient_identifier
        self.message_text = message_text
        self.media_path = media_path
        self.use_spintax = use_spintax
        self.logger = get_logger()
        self.client_manager = TelegramClientManager()
        self.spintax_processor = SpintaxProcessor()
    
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
                    
                    # Process spintax if enabled
                    processed_message = self.message_text
                    if self.use_spintax and self.message_text:
                        try:
                            spintax_result = self.spintax_processor.process(self.message_text)
                            processed_message = spintax_result.text
                            self.logger.debug(f"Spintax processed: '{processed_message}'")
                        except Exception as e:
                            self.logger.warning(f"Error processing spintax: {e}")
                    
                    # Send message
                    self.progress.emit("Sending message...")
                    result = await self.client_manager.send_message(
                        account_id=self.account_id,
                        peer=self.recipient_identifier,
                        text=processed_message,
                        media_path=self.media_path
                    )
                    
                    if result.get('success', False):
                        self.finished.emit({
                            'success': True,
                            'message': 'Message sent successfully',
                            'details': f"Sent to {self.recipient_identifier} at {datetime.now().strftime('%H:%M:%S')}",
                            'media_path': self.media_path
                        })
                    else:
                        self.finished.emit({
                            'success': False,
                            'message': 'Failed to send message',
                            'details': result.get('error', 'Unknown error'),
                            'media_path': self.media_path
                        })
                    
            except Exception as e:
                self.logger.error(f"Error sending test message: {e}")
                self.finished.emit({
                    'success': False,
                    'message': 'Error sending message',
                    'details': str(e),
                    'media_path': self.media_path
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
        self.translation_manager = get_translation_manager()
        self.recent_tests = []  # Store recent tests in memory
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        self.setup_ui()
        self.load_data()
        # Ensure translations are applied after UI setup
        self.update_ui_translations()
    
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
        self.form_group = QGroupBox(_("testing.send_test_message"))
        form_group_layout = QFormLayout(self.form_group)
        
        # Account selection
        self.account_combo = QComboBox()
        self.account_combo.setPlaceholderText(_("testing.select_account"))
        form_group_layout.addRow(_("common.account") + ":", self.account_combo)
        
        # Recipient selection
        self.recipient_combo = QComboBox()
        self.recipient_combo.setPlaceholderText(_("testing.select_recipient"))
        form_group_layout.addRow(_("testing.recipient") + ":", self.recipient_combo)
        
        # Message template selection
        self.template_combo = QComboBox()
        self.template_combo.setPlaceholderText(_("testing.select_template_optional"))
        self.template_combo.currentTextChanged.connect(self.on_template_changed)
        form_group_layout.addRow(_("common.template") + ":", self.template_combo)
        
        # Message text
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText(_("testing.enter_message_text"))
        self.message_edit.setMaximumHeight(100)
        form_group_layout.addRow(_("common.message") + ":", self.message_edit)
        
        # Media section with tabs for file and URL
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        media_layout.setContentsMargins(0, 0, 0, 0)
        
        # Media tabs
        self.media_tabs = QTabWidget()
        self.media_tabs.setMaximumHeight(80)
        
        # File tab
        file_tab = QWidget()
        file_layout = QHBoxLayout(file_tab)
        file_layout.setContentsMargins(5, 5, 5, 5)
        
        self.media_file_edit = QLineEdit()
        self.media_file_edit.setPlaceholderText(_("testing.no_file_selected"))
        self.media_file_edit.setReadOnly(True)
        file_layout.addWidget(self.media_file_edit)
        
        self.choose_file_button = QPushButton(_("testing.choose_file"))
        self.choose_file_button.clicked.connect(self.choose_media_file)
        self.choose_file_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 12px;
                font-size: 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        file_layout.addWidget(self.choose_file_button)
        
        self.media_tabs.addTab(file_tab, _("testing.file"))
        
        # URL tab
        url_tab = QWidget()
        url_layout = QHBoxLayout(url_tab)
        url_layout.setContentsMargins(5, 5, 5, 5)
        
        self.media_url_edit = QLineEdit()
        self.media_url_edit.setPlaceholderText(_("testing.paste_media_url"))
        url_layout.addWidget(self.media_url_edit)
        
        self.media_tabs.addTab(url_tab, _("testing.url"))
        
        media_layout.addWidget(self.media_tabs)
        form_group_layout.addRow(_("testing.media") + ":", media_widget)
        
        form_layout.addWidget(self.form_group)
        
        # Spintax checkbox
        self.spintax_checkbox = QCheckBox(_("testing.enable_spintax"))
        self.spintax_checkbox.setToolTip(_("testing.spintax_tooltip"))
        form_layout.addWidget(self.spintax_checkbox)
        
        # Send button
        self.send_button = QPushButton(_("testing.send_test_message"))
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
        self.tests_group = QGroupBox(_("testing.recent_tests"))
        tests_layout = QVBoxLayout(self.tests_group)
        
        # Clear button
        clear_layout = QHBoxLayout()
        self.clear_button = QPushButton(_("testing.clear_tests"))
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
        
        results_layout.addWidget(self.tests_group)
        splitter.addWidget(results_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 300])
    
    def choose_media_file(self):
        """Open file dialog to choose media file."""
        # Telegram supported media file extensions
        supported_extensions = [
            "Images (*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff *.ico)",
            "Videos (*.mp4 *.avi *.mov *.wmv *.flv *.webm *.mkv *.3gp *.m4v)",
            "Audio (*.mp3 *.wav *.ogg *.m4a *.aac *.flac *.wma)",
            "Documents (*.pdf *.doc *.docx *.txt *.rtf *.odt)",
            "All Files (*)"
        ]
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            _("testing.choose_media_file"),
            "",
            ";;".join(supported_extensions)
        )
        
        if file_path:
            self.media_file_edit.setText(file_path)
            # Switch to file tab if not already there
            self.media_tabs.setCurrentIndex(0)
            self.logger.info(f"Selected media file: {file_path}")
    
    def validate_media_url(self, url: str) -> bool:
        """Validate if URL is a supported media URL."""
        if not url:
            return True  # Empty URL is valid (no media)
        
        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            return False
        
        # Check for common media file extensions in URL
        media_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.ico',
            '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.3gp', '.m4v',
            '.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.wma',
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'
        ]
        
        url_lower = url.lower()
        return any(ext in url_lower for ext in media_extensions)
    
    def load_data(self):
        """Load accounts, recipients, and templates."""
        try:
            with get_session() as session:
                # Load accounts
                accounts = session.query(Account).filter(Account.deleted_at.is_(None)).all()
                self.account_combo.clear()
                self.logger.info(f"Loading {len(accounts)} accounts for testing")
                for account in accounts:
                    status_icon = "🟢" if account.status == "ONLINE" else "🔴"
                    self.account_combo.addItem(f"{status_icon} {account.phone_number}", account.id)
                    self.logger.debug(f"Added account: {account.phone_number} (ID: {account.id})")
                
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
            
            self.logger.debug(f"Account ID: {account_id}, Recipient: {recipient_identifier}, Message: {message_text[:50]}...")
            self.logger.debug(f"Account combo current index: {self.account_combo.currentIndex()}")
            self.logger.debug(f"Account combo count: {self.account_combo.count()}")
            
            # Check if account is selected by index instead of data
            if not account_id and self.account_combo.currentIndex() >= 0:
                # Try to get account ID from the current index
                account_id = self.account_combo.itemData(self.account_combo.currentIndex())
                self.logger.debug(f"Retrieved account ID from index: {account_id}")
            
            if not account_id:
                self.logger.warning("No account selected")
                QMessageBox.warning(self, _("testing.validation_error"), _("testing.please_select_account"))
                return
            
            # Check if recipient is selected by index instead of data
            if not recipient_identifier and self.recipient_combo.currentIndex() >= 0:
                # Try to get recipient identifier from the current index
                recipient_identifier = self.recipient_combo.itemData(self.recipient_combo.currentIndex())
                self.logger.debug(f"Retrieved recipient identifier from index: {recipient_identifier}")
            
            if not recipient_identifier:
                QMessageBox.warning(self, _("testing.validation_error"), _("testing.please_select_recipient"))
                return
            
            if not message_text:
                QMessageBox.warning(self, _("testing.validation_error"), _("testing.please_enter_message"))
                return
            
            # Disable send button
            self.send_button.setEnabled(False)
            self.send_button.setText(_("testing.sending"))
            
            # Get media path from selected tab
            media_path = None
            if self.media_tabs.currentIndex() == 0:  # File tab
                media_path = self.media_file_edit.text().strip() or None
            else:  # URL tab
                media_url = self.media_url_edit.text().strip()
                if media_url:
                    if not self.validate_media_url(media_url):
                        QMessageBox.warning(
                            self,
                            "Invalid Media URL",
                            "Please enter a valid URL for a supported media file.\n\n"
                            "Supported formats:\n"
                            "• Images: JPG, PNG, GIF, WebP, etc.\n"
                            "• Videos: MP4, AVI, MOV, WebM, etc.\n"
                            "• Audio: MP3, WAV, OGG, M4A, etc.\n"
                            "• Documents: PDF, DOC, TXT, etc."
                        )
                        return
                    media_path = media_url
            
            # Create and start worker
            use_spintax = self.spintax_checkbox.isChecked()
            self.worker = TestMessageWorker(account_id, recipient_identifier, message_text, media_path, use_spintax)
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
                'details': result['details'],
                'media_path': result.get('media_path', '')
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
            
            # Add media info if present
            if test.get('media_path'):
                if test['media_path'].startswith(('http://', 'https://')):
                    item_text += " [URL]"
                else:
                    item_text += " [File]"
            
            if not test['success']:
                item_text += f" - {test['details']}"
            
            item = QListWidgetItem(item_text)
            
            # Enhanced tooltip with media info
            tooltip = f"Message: {test['message']}\nDetails: {test['details']}"
            if test.get('media_path'):
                tooltip += f"\nMedia: {test['media_path']}"
            item.setToolTip(tooltip)
            
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
            _("testing.clear_tests"),
            _("testing.clear_tests_confirm"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.recent_tests.clear()
            self.update_tests_list()
            self.logger.info("Recent tests cleared")
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Update UI elements with new translations
        self.update_ui_translations()
    
    def update_ui_translations(self):
        """Update UI elements with current translations."""
        try:
            # Update form group title
            if hasattr(self, 'form_group'):
                self.form_group.setTitle(_("testing.send_test_message"))
            
            # Update labels
            if hasattr(self, 'account_combo'):
                self.account_combo.setPlaceholderText(_("testing.select_account"))
            
            if hasattr(self, 'recipient_combo'):
                self.recipient_combo.setPlaceholderText(_("testing.select_recipient"))
            
            if hasattr(self, 'template_combo'):
                self.template_combo.setPlaceholderText(_("testing.select_template_optional"))
            
            if hasattr(self, 'message_edit'):
                self.message_edit.setPlaceholderText(_("testing.enter_message_text"))
            
            if hasattr(self, 'media_file_edit'):
                self.media_file_edit.setPlaceholderText(_("testing.no_file_selected"))
            
            if hasattr(self, 'choose_file_button'):
                self.choose_file_button.setText(_("testing.choose_file"))
            
            if hasattr(self, 'media_url_edit'):
                self.media_url_edit.setPlaceholderText(_("testing.paste_media_url"))
            
            if hasattr(self, 'send_button'):
                self.send_button.setText(_("testing.send_test_message"))
            
            if hasattr(self, 'tests_group'):
                self.tests_group.setTitle(_("testing.recent_tests"))
            
            if hasattr(self, 'clear_button'):
                self.clear_button.setText(_("testing.clear_tests"))
            
            # Update media tabs
            if hasattr(self, 'media_tabs'):
                try:
                    self.media_tabs.setTabText(0, _("testing.file"))
                    self.media_tabs.setTabText(1, _("testing.url"))
                except Exception as e:
                    self.logger.warning(f"Error updating media tabs: {e}")
            
            self.logger.info("UI translations updated successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating UI translations: {e}")
