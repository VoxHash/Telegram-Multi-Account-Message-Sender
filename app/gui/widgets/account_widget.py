"""
Account management widgets.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QFileDialog, QProgressBar, QAbstractItemView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

from ...models import Account, AccountStatus, ProxyType
from ...models.base import SoftDeleteMixin
from ...services import get_logger, get_session
from ...services.translation import _, get_translation_manager
from ...services.warmup_manager import get_warmup_manager
from ...core import TelegramClientManager
from ...services.db import get_session as db_get_session


class ProgressDialog(QDialog):
    """Custom progress dialog for Telegram operations."""
    
    def __init__(self, parent=None, title="Operation", initial_text="Processing..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel(initial_text)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)
    
    def update_status(self, text):
        """Update the status text."""
        self.status_label.setText(text)
    
    def set_determinate(self, maximum):
        """Set progress bar to determinate mode."""
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(0)
    
    def set_progress(self, value):
        """Set progress bar value."""
        self.progress_bar.setValue(value)


class VerificationCodeDialog(QDialog):
    """Dialog for entering Telegram verification code."""
    
    def __init__(self, parent=None, phone_number=""):
        super().__init__(parent)
        self.phone_number = phone_number
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Enter Verification Code")
        self.setModal(True)
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(f"Please enter the verification code sent to {self.phone_number}")
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Code input
        code_layout = QHBoxLayout()
        code_layout.addWidget(QLabel("Code:"))
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Enter 5-digit code")
        self.code_edit.setMaxLength(5)
        self.code_edit.textChanged.connect(self.on_code_changed)
        code_layout.addWidget(self.code_edit)
        layout.addLayout(code_layout)
        
        # Password hint (if needed)
        self.password_hint = QLabel("If you have 2FA enabled, you'll be prompted for your password next.")
        self.password_hint.setStyleSheet("color: #888888; font-style: italic; margin-top: 10px;")
        self.password_hint.setWordWrap(True)
        layout.addWidget(self.password_hint)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.ok_button = buttons.button(QDialogButtonBox.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(buttons)
    
    def on_code_changed(self, text):
        """Handle code input changes."""
        self.ok_button.setEnabled(len(text) == 5 and text.isdigit())
    
    def get_code(self):
        """Get the entered verification code."""
        return self.code_edit.text().strip()
    
    def get_password(self):
        """Get password if needed (for 2FA)."""
        from PyQt5.QtWidgets import QInputDialog
        password, ok = QInputDialog.getText(
            self, 
            "Two-Factor Authentication", 
            "Please enter your 2FA password:",
            QLineEdit.Password
        )
        return password if ok else None


class TelegramWorker(QThread):
    """Worker thread for Telegram operations."""
    
    finished = pyqtSignal(str, bool)  # message, success
    progress = pyqtSignal(str)  # progress message
    code_required = pyqtSignal(str)  # phone_number - signal that code is needed
    
    def __init__(self, operation, account_id, account_name, api_id, api_hash, phone_number, session_path=None, proxy_config=None, verification_code=None, password=None, phone_code_hash=None):
        super().__init__()
        self.operation = operation
        self.account_id = account_id
        self.account_name = account_name
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.session_path = session_path
        self.proxy_config = proxy_config
        self.verification_code = verification_code
        self.password = password
        self.phone_code_hash = phone_code_hash
        self.logger = get_logger()
        self._should_stop = False
    
    def stop(self):
        """Stop the worker thread."""
        self._should_stop = True
        self.quit()
        self.wait(5000)  # Wait up to 5 seconds for thread to finish
    
    def run(self):
        """Run the Telegram operation."""
        try:
            if self._should_stop:
                return
                
            if self.operation == "authorize":
                self._authorize_account()
            elif self.operation == "test":
                self._test_account()
            elif self.operation == "connect":
                self._connect_account()
        except Exception as e:
            self.logger.error(f"Error in Telegram worker: {e}")
            self.finished.emit(f"Error: {str(e)}", False)
    
    def _authorize_account(self):
        """Authorize account with Telegram."""
        try:
            if self._should_stop:
                return
                
            self.progress.emit("Initializing Telegram client...")
            
            # Import here to avoid circular imports
            import asyncio
            from telethon import TelegramClient
            from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, ApiIdInvalidError
            
            # Validate API credentials
            if not self.api_id or not self.api_hash:
                self.finished.emit("❌ API credentials are not configured. Please set them in Settings first.", False)
                return
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Create client
                client = TelegramClient(
                    self.session_path or f"app_data/sessions/session_{self.phone_number}",
                    int(self.api_id),
                    self.api_hash
                )
                
                if self._should_stop:
                    return
                    
                self.progress.emit("Connecting to Telegram...")
                
                # Run the async operations
                loop.run_until_complete(self._async_authorize(client))
                
            finally:
                loop.close()
            
        except ApiIdInvalidError:
            self.finished.emit("❌ Invalid API ID or API Hash. Please check your credentials in Settings.", False)
        except Exception as e:
            self.logger.error(f"Authorization error: {e}")
            self.finished.emit(f"❌ Authorization failed: {str(e)}", False)
    
    async def _async_authorize(self, client):
        """Async authorization logic."""
        try:
            await client.connect()
            
            if self._should_stop:
                await client.disconnect()
                return
            
            if not await client.is_user_authorized():
                if not self.verification_code:
                    # First step: send verification code
                    self.progress.emit("Sending verification code...")
                    result = await client.send_code_request(self.phone_number)
                    
                    # Update account status to CONNECTING
                    self._update_account_status(AccountStatus.CONNECTING)
                    
                    # Emit signal that code is required with phone_code_hash
                    self.code_required.emit(f"{self.phone_number}|{result.phone_code_hash}")
                    return
                else:
                    # Second step: verify code
                    self.progress.emit("Verifying code...")
                    try:
                        if self.phone_code_hash:
                            await client.sign_in(self.phone_number, self.verification_code, phone_code_hash=self.phone_code_hash)
                        else:
                            await client.sign_in(self.phone_number, self.verification_code)
                        
                        # Check if 2FA is required
                        if not await client.is_user_authorized():
                            if not self.password:
                                # Need 2FA password
                                self.finished.emit("2FA_PASSWORD_REQUIRED", False)
                                return
                            else:
                                # Sign in with 2FA password
                                self.progress.emit("Verifying 2FA password...")
                                await client.sign_in(password=self.password)
                        
                        # Authorization successful
                        self._update_account_status(AccountStatus.ONLINE)
                        self.finished.emit(
                            f"✅ Account {self.account_name} successfully authorized!\n\n"
                            f"Account is now online and ready for messaging.",
                            True
                        )
                        
                    except Exception as e:
                        self.logger.error(f"Code verification error: {e}")
                        self._update_account_status(AccountStatus.ERROR)
                        self.finished.emit(f"❌ Code verification failed: {str(e)}", False)
            else:
                self._update_account_status(AccountStatus.ONLINE)
                self.finished.emit(f"✅ Account {self.account_name} is already authorized!", True)
            
            await client.disconnect()
            
        except Exception as e:
            self.logger.error(f"Async authorization error: {e}")
            self.finished.emit(f"❌ Authorization failed: {str(e)}", False)
    
    def _test_account(self):
        """Test account connection."""
        try:
            if self._should_stop:
                return
                
            self.progress.emit("Testing account connection...")
            
            import asyncio
            from telethon import TelegramClient
            from telethon.errors import ApiIdInvalidError
            
            # Validate API credentials
            if not self.api_id or not self.api_hash:
                self.finished.emit("❌ API credentials are not configured. Please set them in Settings first.", False)
                return
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Create client
                client = TelegramClient(
                    self.session_path or f"app_data/sessions/session_{self.phone_number}",
                    int(self.api_id),
                    self.api_hash
                )
                
                if self._should_stop:
                    return
                    
                self.progress.emit("Connecting to Telegram...")
                
                # Run the async operations
                loop.run_until_complete(self._async_test(client))
                
            finally:
                loop.close()
            
        except ApiIdInvalidError:
            self.finished.emit("❌ Invalid API ID or API Hash. Please check your credentials in Settings.", False)
        except Exception as e:
            self.logger.error(f"Test error: {e}")
            self._update_account_status(AccountStatus.ERROR)
            self.finished.emit(f"❌ Test failed: {str(e)}", False)
    
    async def _async_test(self, client):
        """Async test logic."""
        try:
            await client.connect()
            
            if self._should_stop:
                await client.disconnect()
                return
            
            if await client.is_user_authorized():
                # Get account info
                me = await client.get_me()
                self._update_account_status(AccountStatus.ONLINE)
                self.finished.emit(
                    f"✅ Account test successful!\n\n"
                    f"📱 Name: {me.first_name} {me.last_name or ''}\n"
                    f"👤 Username: @{me.username or 'N/A'}\n"
                    f"📞 Phone: {me.phone}\n"
                    f"🆔 ID: {me.id}\n\n"
                    f"Account is ready for messaging!",
                    True
                )
            else:
                self._update_account_status(AccountStatus.OFFLINE)
                self.finished.emit("❌ Account is not authorized. Please use 'Authorize' first to set up the account.", False)
            
            await client.disconnect()
            
        except Exception as e:
            self.logger.error(f"Async test error: {e}")
            self._update_account_status(AccountStatus.ERROR)
            self.finished.emit(f"❌ Test failed: {str(e)}", False)
    
    def _connect_account(self):
        """Connect to account (for already authorized accounts)."""
        try:
            if self._should_stop:
                return
                
            self.progress.emit("Connecting to account...")
            
            import asyncio
            from telethon import TelegramClient
            from telethon.errors import ApiIdInvalidError
            
            # Validate API credentials
            if not self.api_id or not self.api_hash:
                self.finished.emit("❌ API credentials are not configured. Please set them in Settings first.", False)
                return
            
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Create client
                client = TelegramClient(
                    self.session_path or f"app_data/sessions/session_{self.phone_number}",
                    int(self.api_id),
                    self.api_hash
                )
                
                if self._should_stop:
                    return
                    
                self.progress.emit("Connecting to Telegram...")
                
                # Run the async operations
                loop.run_until_complete(self._async_connect(client))
                
            finally:
                loop.close()
            
        except ApiIdInvalidError:
            self.finished.emit("❌ Invalid API ID or API Hash. Please check your credentials in Settings.", False)
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self._update_account_status(AccountStatus.ERROR)
            self.finished.emit(f"❌ Connection failed: {str(e)}", False)
    
    async def _async_connect(self, client):
        """Async connect logic."""
        try:
            await client.connect()
            
            if self._should_stop:
                await client.disconnect()
                return
            
            if await client.is_user_authorized():
                # Update account status in database
                self._update_account_status(AccountStatus.ONLINE)
                self.finished.emit(f"✅ Successfully connected to {self.account_name}!\n\nAccount is now online and ready for messaging.", True)
            else:
                self._update_account_status(AccountStatus.OFFLINE)
                self.finished.emit("❌ Account is not authorized. Please use 'Authorize' first to set up the account.", False)
            
            await client.disconnect()
            
        except Exception as e:
            self.logger.error(f"Async connection error: {e}")
            self._update_account_status(AccountStatus.ERROR)
            self.finished.emit(f"❌ Connection failed: {str(e)}", False)
    
    def _update_account_status(self, status):
        """Update account status in database."""
        try:
            session = db_get_session()
            try:
                from ...models import Account
                from sqlmodel import select
                account = session.exec(select(Account).where(Account.id == self.account_id)).first()
                if account:
                    account.status = status
                    session.commit()
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"Error updating account status: {e}")


class AccountDialog(QDialog):
    """Dialog for adding/editing accounts."""
    
    account_saved = pyqtSignal(int)
    
    def __init__(self, parent=None, account: Optional[Account] = None):
        super().__init__(parent)
        self.account = account
        self.logger = get_logger()
        self.setup_ui()
        
        if account:
            self.load_account_data()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Add Account" if not self.account else "Edit Account")
        self.setModal(True)
        self.resize(500, 600)
        
        # Add help button to title bar
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Account name (e.g., 'My Business Account')")
        basic_layout.addRow("Name:", self.name_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+1234567890")
        basic_layout.addRow("Phone Number:", self.phone_edit)
        
        # Note about API credentials
        api_note = QLabel("Note: API ID and API Hash are configured globally in Settings.")
        api_note.setStyleSheet("color: #888888; font-style: italic;")
        basic_layout.addRow("", api_note)
        
        layout.addWidget(basic_group)
        
        # Proxy Settings
        proxy_group = QGroupBox("Proxy Settings (Optional)")
        proxy_layout = QFormLayout(proxy_group)
        
        self.use_proxy_check = QCheckBox("Use Proxy")
        self.use_proxy_check.toggled.connect(self.toggle_proxy_settings)
        proxy_layout.addRow(self.use_proxy_check)
        
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems([pt.value for pt in ProxyType])
        proxy_layout.addRow("Proxy Type:", self.proxy_type_combo)
        
        self.proxy_host_edit = QLineEdit()
        self.proxy_host_edit.setPlaceholderText("proxy.example.com")
        proxy_layout.addRow("Host:", self.proxy_host_edit)
        
        self.proxy_port_spin = QSpinBox()
        self.proxy_port_spin.setRange(1, 65535)
        self.proxy_port_spin.setValue(8080)
        proxy_layout.addRow("Port:", self.proxy_port_spin)
        
        self.proxy_username_edit = QLineEdit()
        self.proxy_username_edit.setPlaceholderText("Username (optional)")
        proxy_layout.addRow("Username:", self.proxy_username_edit)
        
        self.proxy_password_edit = QLineEdit()
        self.proxy_password_edit.setEchoMode(QLineEdit.Password)
        self.proxy_password_edit.setPlaceholderText("Password (optional)")
        proxy_layout.addRow("Password:", self.proxy_password_edit)
        
        layout.addWidget(proxy_group)
        
        # Rate Limiting
        rate_group = QGroupBox("Rate Limiting")
        rate_layout = QFormLayout(rate_group)
        
        self.rate_per_minute_spin = QSpinBox()
        self.rate_per_minute_spin.setRange(1, 60)
        self.rate_per_minute_spin.setValue(30)
        rate_layout.addRow("Messages per Minute:", self.rate_per_minute_spin)
        
        self.rate_per_hour_spin = QSpinBox()
        self.rate_per_hour_spin.setRange(1, 1000)
        self.rate_per_hour_spin.setValue(100)
        rate_layout.addRow("Messages per Hour:", self.rate_per_hour_spin)
        
        self.rate_per_day_spin = QSpinBox()
        self.rate_per_day_spin.setRange(1, 10000)
        self.rate_per_day_spin.setValue(1000)
        rate_layout.addRow("Messages per Day:", self.rate_per_day_spin)
        
        layout.addWidget(rate_group)
        
        # Warmup Settings
        warmup_group = QGroupBox("Warmup Settings")
        warmup_layout = QFormLayout(warmup_group)
        
        self.warmup_enabled_check = QCheckBox("Enable Warmup")
        self.warmup_enabled_check.setChecked(True)
        warmup_layout.addRow(self.warmup_enabled_check)
        
        self.warmup_messages_spin = QSpinBox()
        self.warmup_messages_spin.setRange(1, 50)
        self.warmup_messages_spin.setValue(5)
        warmup_layout.addRow("Warmup Messages:", self.warmup_messages_spin)
        
        self.warmup_interval_spin = QSpinBox()
        self.warmup_interval_spin.setRange(10, 1440)
        self.warmup_interval_spin.setValue(60)
        warmup_layout.addRow("Interval (minutes):", self.warmup_interval_spin)
        
        layout.addWidget(warmup_group)
        
        # Notes
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes about this account...")
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_account)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initialize proxy settings as disabled
        self.toggle_proxy_settings(False)
    
    def show_help(self):
        """Show help information for adding accounts."""
        help_text = """
<h3>Adding a Telegram Account</h3>

<p><b>Basic Information:</b></p>
<ul>
<li><b>Name:</b> A friendly name to identify this account (e.g., "My Business Account")</li>
<li><b>Phone Number:</b> The phone number associated with your Telegram account (e.g., +1234567890)</li>
</ul>

<p><b>API Credentials:</b></p>
<p>API ID and API Hash are configured globally in Settings. Make sure to set them up before adding accounts.</p>

<p><b>Proxy Settings (Optional):</b></p>
<ul>
<li>Enable if you need to use a proxy server for this account</li>
<li>Choose the appropriate proxy type (HTTP, HTTPS, SOCKS4, SOCKS5)</li>
<li>Enter proxy server details if required</li>
</ul>

<p><b>Rate Limiting:</b></p>
<ul>
<li>Set how many messages this account can send per minute, hour, and day</li>
<li>These limits help prevent your account from being banned</li>
</ul>

<p><b>Warmup Settings:</b></p>
<ul>
<li>Enable warmup to gradually increase message sending activity</li>
<li>Start with a small number of messages and increase over time</li>
<li>This helps establish your account as legitimate</li>
</ul>

<p><b>Notes:</b></p>
<p>Add any additional information about this account for your reference.</p>

<p><b>Getting Started:</b></p>
<ol>
<li>First, configure your Telegram API credentials in Settings</li>
<li>Add your account details in this dialog</li>
<li>Click "Save" to add the account</li>
<li>Use the "Connect" action in the accounts table to authorize the account</li>
</ol>
        """
        
        QMessageBox.information(self, "Help - Adding Account", help_text)
    
    def event(self, event):
        """Override event handling for help button."""
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.EnterWhatsThisMode:
            self.show_help()
            return True
        return super().event(event)
    
    def toggle_proxy_settings(self, enabled: bool):
        """Toggle proxy settings visibility."""
        self.proxy_type_combo.setEnabled(enabled)
        self.proxy_host_edit.setEnabled(enabled)
        self.proxy_port_spin.setEnabled(enabled)
        self.proxy_username_edit.setEnabled(enabled)
        self.proxy_password_edit.setEnabled(enabled)
    
    def load_account_data(self):
        """Load account data into the form."""
        if not self.account:
            return
        
        self.name_edit.setText(self.account.name)
        self.phone_edit.setText(self.account.phone_number)
        
        # Proxy settings
        if self.account.proxy_type:
            self.use_proxy_check.setChecked(True)
            self.proxy_type_combo.setCurrentText(self.account.proxy_type.value)
            self.proxy_host_edit.setText(self.account.proxy_host or "")
            self.proxy_port_spin.setValue(self.account.proxy_port or 8080)
            self.proxy_username_edit.setText(self.account.proxy_username or "")
            self.proxy_password_edit.setText(self.account.proxy_password or "")
        
        # Rate limiting
        self.rate_per_minute_spin.setValue(self.account.rate_limit_per_minute)
        self.rate_per_hour_spin.setValue(self.account.rate_limit_per_hour)
        self.rate_per_day_spin.setValue(self.account.rate_limit_per_day)
        
        # Warmup settings
        self.warmup_enabled_check.setChecked(self.account.warmup_enabled)
        self.warmup_messages_spin.setValue(self.account.warmup_target_messages)
        self.warmup_interval_spin.setValue(self.account.warmup_interval_minutes)
        
        # Notes
        self.notes_edit.setText(self.account.notes or "")
    
    def save_account(self):
        """Save account data."""
        try:
            # Validate required fields
            if not self.name_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Name is required")
                return
            
            if not self.phone_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "Phone number is required")
                return
            
            # Get global API credentials from settings
            from ...services import get_settings
            settings = get_settings()
            
            if not settings.telegram_api_id or not settings.telegram_api_hash:
                QMessageBox.warning(
                    self, 
                    "API Credentials Required", 
                    "Please configure your Telegram API ID and API Hash in Settings before adding accounts."
                )
                return
            
            # Create or update account
            if self.account:
                # Update existing account
                self.account.name = self.name_edit.text().strip()
                self.account.phone_number = self.phone_edit.text().strip()
                self.account.api_id = settings.telegram_api_id
                self.account.api_hash = settings.telegram_api_hash
            else:
                # Create new account
                self.account = Account(
                    name=self.name_edit.text().strip(),
                    phone_number=self.phone_edit.text().strip(),
                    api_id=settings.telegram_api_id,
                    api_hash=settings.telegram_api_hash,
                    session_path=f"app_data/sessions/session_{self.phone_edit.text().strip()}"
                )
            
            # Update proxy settings
            if self.use_proxy_check.isChecked():
                self.account.proxy_type = ProxyType(self.proxy_type_combo.currentText())
                self.account.proxy_host = self.proxy_host_edit.text().strip() or None
                self.account.proxy_port = self.proxy_port_spin.value()
                self.account.proxy_username = self.proxy_username_edit.text().strip() or None
                self.account.proxy_password = self.proxy_password_edit.text().strip() or None
            else:
                self.account.proxy_type = None
                self.account.proxy_host = None
                self.account.proxy_port = None
                self.account.proxy_username = None
                self.account.proxy_password = None
            
            # Update rate limiting
            self.account.rate_limit_per_minute = self.rate_per_minute_spin.value()
            self.account.rate_limit_per_hour = self.rate_per_hour_spin.value()
            self.account.rate_limit_per_day = self.rate_per_day_spin.value()
            
            # Update warmup settings
            self.account.warmup_enabled = self.warmup_enabled_check.isChecked()
            self.account.warmup_target_messages = self.warmup_messages_spin.value()
            self.account.warmup_interval_minutes = self.warmup_interval_spin.value()
            
            # Update notes
            self.account.notes = self.notes_edit.toPlainText().strip() or None
            
            # Save to database
            session = db_get_session()
            try:
                if self.account.id is None:
                    session.add(self.account)
                else:
                    session.merge(self.account)
                session.commit()
                
                # Get the saved account ID before closing session
                account_id = self.account.id
                account_name = self.account.name
            finally:
                session.close()
            
            self.logger.info(f"Account saved: {account_name}")
            self.account_saved.emit(account_id)
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Error saving account: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save account: {e}")


class AccountListWidget(QWidget):
    """Widget for displaying and managing accounts."""
    
    account_selected = pyqtSignal(int)
    account_updated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.client_manager = TelegramClientManager()
        self.translation_manager = get_translation_manager()
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        # Connect warmup manager signals for real-time updates
        self.warmup_manager = get_warmup_manager()
        self.warmup_manager.warmup_started.connect(self.on_warmup_started)
        self.warmup_manager.warmup_progress.connect(self.on_warmup_progress)
        self.warmup_manager.warmup_completed.connect(self.on_warmup_completed)
        self.warmup_manager.warmup_error.connect(self.on_warmup_error)
        
        self.setup_ui()
        self.load_accounts()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_accounts)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Telegram Accounts")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.add_button = QPushButton("Add Account")
        self.add_button.clicked.connect(self.add_account)
        header_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton("Edit Account")
        self.edit_button.clicked.connect(self.edit_account)
        self.edit_button.setEnabled(False)
        header_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete Account")
        self.delete_button.clicked.connect(self.delete_account)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_accounts)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Search field
        search_layout = QHBoxLayout()
        search_label = QLabel(_("common.search") + ":")
        search_label.setStyleSheet("color: white; font-weight: bold;")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(_("accounts.search_placeholder"))
        self.search_edit.textChanged.connect(self.filter_accounts)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #404040;
                border-radius: 4px;
                background-color: #2d2d2d;
                color: white;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
        """)
        search_layout.addWidget(self.search_edit)
        search_layout.addStretch()
        
        layout.addLayout(search_layout)
        
        # Accounts table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(8)
        self.accounts_table.setHorizontalHeaderLabels([
            "Name", "Phone", "Status", "Messages Sent", "Success Rate", 
            "Last Activity", "Warmup", "Actions"
        ])
        
        # Configure table
        header = self.accounts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Set custom styling for black and gray alternating rows
        self.accounts_table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #2d2d2d;
                background-color: #1a1a1a;
                gridline-color: #404040;
                color: white;
                selection-background-color: #0078d4;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4 !important;
                color: white !important;
            }
            QTableWidget::item:alternate {
                background-color: #2d2d2d;
            }
            QTableWidget::item:alternate:selected {
                background-color: #0078d4 !important;
                color: white !important;
            }
        """)
        
        # Connect cell clicked signal for actions
        self.accounts_table.cellClicked.connect(self.on_cell_clicked)
        
        layout.addWidget(self.accounts_table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def load_accounts(self):
        """Load accounts from database."""
        try:
            session = db_get_session()
            try:
                from ...models import Account
                from sqlmodel import select
                accounts = session.exec(select(Account).where(Account.is_deleted == False)).all()
            finally:
                session.close()
            
            self.accounts_table.setRowCount(len(accounts))
            
            for row, account in enumerate(accounts):
                # Name - Disabled text field
                name_item = QTableWidgetItem(account.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                # Store account ID in the name item for selection handling
                name_item.setData(Qt.UserRole, account.id)
                self.accounts_table.setItem(row, 0, name_item)
                
                # Phone - Disabled text field
                phone_item = QTableWidgetItem(account.phone_number)
                phone_item.setFlags(phone_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                self.accounts_table.setItem(row, 1, phone_item)
                
                # Status - Enhanced button-like appearance
                status_item = QTableWidgetItem(account.status.value.title())
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                
                # Set status-specific styling with button-like appearance
                if account.status == AccountStatus.ONLINE:
                    status_item.setBackground(QColor(34, 197, 94))  # Green
                    status_item.setForeground(Qt.white)
                elif account.status == AccountStatus.ERROR:
                    status_item.setBackground(QColor(239, 68, 68))  # Red
                    status_item.setForeground(Qt.white)
                elif account.status == AccountStatus.OFFLINE:
                    status_item.setBackground(QColor(107, 114, 128))  # Gray
                    status_item.setForeground(Qt.white)
                elif account.status == AccountStatus.CONNECTING:
                    status_item.setBackground(QColor(245, 158, 11))  # Orange
                    status_item.setForeground(Qt.white)
                elif account.status == AccountStatus.SUSPENDED:
                    status_item.setBackground(QColor(156, 163, 175))  # Light gray
                    status_item.setForeground(Qt.white)
                
                # Center align status text
                status_item.setTextAlignment(Qt.AlignCenter)
                self.accounts_table.setItem(row, 2, status_item)
                
                # Messages sent - Disabled text field
                messages_item = QTableWidgetItem(str(account.total_messages_sent))
                messages_item.setFlags(messages_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                messages_item.setTextAlignment(Qt.AlignCenter)
                self.accounts_table.setItem(row, 3, messages_item)
                
                # Success rate - Disabled text field
                success_rate = account.get_success_rate()
                success_item = QTableWidgetItem(f"{success_rate:.1f}%")
                success_item.setFlags(success_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                success_item.setTextAlignment(Qt.AlignCenter)
                self.accounts_table.setItem(row, 4, success_item)
                
                # Last activity - Disabled text field
                last_activity = account.last_activity.strftime("%Y-%m-%d %H:%M") if account.last_activity else "Never"
                activity_item = QTableWidgetItem(last_activity)
                activity_item.setFlags(activity_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                activity_item.setTextAlignment(Qt.AlignCenter)
                self.accounts_table.setItem(row, 5, activity_item)
                
                # Warmup status - Disabled text field
                warmup_status = "Complete" if account.is_warmup_complete() else f"{account.warmup_messages_sent}/{account.warmup_target_messages}"
                warmup_item = QTableWidgetItem(warmup_status)
                warmup_item.setFlags(warmup_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                warmup_item.setTextAlignment(Qt.AlignCenter)
                self.accounts_table.setItem(row, 6, warmup_item)
                
                # Actions - Create action buttons
                actions_item = QTableWidgetItem("Connect | Test | Authorize")
                actions_item.setFlags(actions_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                actions_item.setTextAlignment(Qt.AlignCenter)
                actions_item.setData(Qt.UserRole, account.id)  # Store account ID for actions
                self.accounts_table.setItem(row, 7, actions_item)
            
            self.status_label.setText(f"Loaded {len(accounts)} accounts")
            
            # Apply search filter if there's search text
            self.filter_accounts()
            
        except Exception as e:
            self.logger.error(f"Error loading accounts: {e}")
            self.status_label.setText(f"Error loading accounts: {e}")
    
    def refresh_accounts(self):
        """Refresh accounts data."""
        self.load_accounts()
    
    def filter_accounts(self):
        """Filter accounts based on search text."""
        search_text = self.search_edit.text().lower().strip()
        
        if not search_text:
            # Show all accounts
            for row in range(self.accounts_table.rowCount()):
                self.accounts_table.setRowHidden(row, False)
            return
        
        # Filter accounts (exclude Actions column - column 7)
        for row in range(self.accounts_table.rowCount()):
            should_show = False
            
            # Check all columns except Actions column for search text
            for col in range(self.accounts_table.columnCount() - 1):  # Exclude last column (Actions)
                item = self.accounts_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            
            self.accounts_table.setRowHidden(row, not should_show)
    
    def on_cell_clicked(self, row, column):
        """Handle cell click events."""
        if column == 7:  # Actions column
            account_id = self.accounts_table.item(row, 0).data(Qt.UserRole)
            if account_id is not None:
                self.show_action_menu(row, column, account_id)
        else:
            # For other columns, ensure the row is selected
            self.accounts_table.selectRow(row)
            # Also trigger selection changed manually
            self.on_selection_changed()
    
    def show_action_menu(self, row, column, account_id):
        """Show action menu for account actions."""
        from PyQt5.QtWidgets import QMenu
        
        # Get account name for display
        account_name = self.accounts_table.item(row, 0).text()
        
        # Create context menu
        menu = QMenu(self)
        
        # Connect action
        connect_action = menu.addAction("🔗 Connect")
        connect_action.triggered.connect(lambda: self.connect_account(account_id, account_name))
        
        # Test action
        test_action = menu.addAction("🧪 Test")
        test_action.triggered.connect(lambda: self.test_account(account_id, account_name))
        
        # Authorize action
        authorize_action = menu.addAction("🔐 Authorize")
        authorize_action.triggered.connect(lambda: self.authorize_account(account_id, account_name))
        
        # Show menu at cursor position
        menu.exec_(self.accounts_table.mapToGlobal(
            self.accounts_table.visualItemRect(self.accounts_table.item(row, column)).bottomLeft()
        ))
    
    def connect_account(self, account_id, account_name):
        """Connect to account."""
        self._start_telegram_operation("connect", account_id, account_name)
    
    def test_account(self, account_id, account_name):
        """Test account connection."""
        self._start_telegram_operation("test", account_id, account_name)
    
    def authorize_account(self, account_id, account_name):
        """Authorize account."""
        self._start_telegram_operation("authorize", account_id, account_name)
    
    def _start_telegram_operation(self, operation, account_id, account_name):
        """Start a Telegram operation in a worker thread."""
        try:
            # Get account details from database
            session = db_get_session()
            try:
                from ...models import Account
                from sqlmodel import select
                account = session.exec(select(Account).where(Account.id == account_id)).first()
                if not account:
                    QMessageBox.warning(self, "Error", "Account not found!")
                    return
                
                # Get API credentials from settings
                from ...services import get_settings
                settings = get_settings()
                
                if not settings.telegram_api_id or not settings.telegram_api_hash:
                    QMessageBox.warning(
                        self, 
                        "API Credentials Required", 
                        "Please configure your Telegram API ID and API Hash in Settings first."
                    )
                    return
                
                # Create progress dialog
                progress_dialog = ProgressDialog(
                    self, 
                    f"{operation.title()} Account",
                    f"{operation.title()}ing {account_name}..."
                )
                
                # Create worker thread
                self.worker = TelegramWorker(
                    operation=operation,
                    account_id=account_id,
                    account_name=account_name,
                    api_id=settings.telegram_api_id,
                    api_hash=settings.telegram_api_hash,
                    phone_number=account.phone_number,
                    session_path=account.session_path,
                    proxy_config=None  # TODO: Add proxy support
                )
                
                # Connect signals
                self.worker.finished.connect(
                    lambda msg, success: self._on_operation_finished(progress_dialog, msg, success, account_id, account_name)
                )
                self.worker.progress.connect(
                    lambda msg: progress_dialog.update_status(f"{operation.title()}ing {account_name}...\n{msg}")
                )
                
                # Connect code required signal for authorization
                if operation == "authorize":
                    self.worker.code_required.connect(
                        lambda phone: self._handle_code_required(progress_dialog, account_id, account_name, phone)
                    )
                
                # Show progress dialog
                progress_dialog.show()
                
                # Connect cancel button to stop worker
                progress_dialog.cancel_button.clicked.connect(self.worker.stop)
                
                # Start worker
                self.worker.start()
                
                # Set up timeout timer (30 seconds)
                timeout_timer = QTimer()
                timeout_timer.setSingleShot(True)
                timeout_timer.timeout.connect(lambda: self._handle_timeout(progress_dialog, operation, account_name))
                timeout_timer.start(30000)  # 30 seconds timeout
                
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error starting {operation} operation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start {operation}: {e}")
    
    def _handle_timeout(self, progress_dialog, operation, account_name):
        """Handle operation timeout."""
        progress_dialog.close()
        self.worker.stop()
        QMessageBox.warning(
            self, 
            "Operation Timeout", 
            f"The {operation} operation for {account_name} timed out after 30 seconds. Please try again."
        )
    
    def _handle_code_required(self, progress_dialog, account_id, account_name, phone_data):
        """Handle when verification code is required."""
        progress_dialog.close()
        
        # Parse phone_number and phone_code_hash from the signal data
        if "|" in phone_data:
            phone_number, phone_code_hash = phone_data.split("|", 1)
        else:
            phone_number = phone_data
            phone_code_hash = None
        
        # Show verification code dialog
        code_dialog = VerificationCodeDialog(self, phone_number)
        if code_dialog.exec_() == QDialog.Accepted:
            code = code_dialog.get_code()
            if code:
                # Start second phase of authorization with code and phone_code_hash
                self._start_telegram_operation_with_code("authorize", account_id, account_name, code, phone_code_hash=phone_code_hash)
        else:
            # User cancelled, update status
            self._update_account_status(account_id, AccountStatus.OFFLINE)
    
    def _start_telegram_operation_with_code(self, operation, account_id, account_name, verification_code, password=None, phone_code_hash=None):
        """Start a Telegram operation with verification code."""
        try:
            # Get account details from database
            session = db_get_session()
            try:
                from ...models import Account
                from sqlmodel import select
                account = session.exec(select(Account).where(Account.id == account_id)).first()
                if not account:
                    QMessageBox.warning(self, "Error", "Account not found!")
                    return
                
                # Get API credentials from settings
                from ...services import get_settings
                settings = get_settings()
                
                # Create progress dialog
                progress_dialog = ProgressDialog(
                    self, 
                    f"{operation.title()} Account",
                    f"Verifying code for {account_name}..."
                )
                
                # Create worker thread with code
                self.worker = TelegramWorker(
                    operation=operation,
                    account_id=account_id,
                    account_name=account_name,
                    api_id=settings.telegram_api_id,
                    api_hash=settings.telegram_api_hash,
                    phone_number=account.phone_number,
                    session_path=account.session_path,
                    proxy_config=None,
                    verification_code=verification_code,
                    password=password,
                    phone_code_hash=phone_code_hash
                )
                
                # Connect signals
                self.worker.finished.connect(
                    lambda msg, success: self._on_operation_finished(progress_dialog, msg, success, account_id, account_name)
                )
                self.worker.progress.connect(
                    lambda msg: progress_dialog.update_status(f"Verifying code for {account_name}...\n{msg}")
                )
                
                # Show progress dialog
                progress_dialog.show()
                
                # Connect cancel button to stop worker
                progress_dialog.cancel_button.clicked.connect(self.worker.stop)
                
                # Start worker
                self.worker.start()
                
                # Set up timeout timer (30 seconds)
                timeout_timer = QTimer()
                timeout_timer.setSingleShot(True)
                timeout_timer.timeout.connect(lambda: self._handle_timeout(progress_dialog, operation, account_name))
                timeout_timer.start(30000)  # 30 seconds timeout
                
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error starting {operation} operation with code: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start {operation}: {e}")
    
    def _update_account_status(self, account_id, status):
        """Update account status in database."""
        try:
            session = db_get_session()
            try:
                from ...models import Account
                from sqlmodel import select
                account = session.exec(select(Account).where(Account.id == account_id)).first()
                if account:
                    account.status = status
                    session.commit()
            finally:
                session.close()
        except Exception as e:
            self.logger.error(f"Error updating account status: {e}")
    
    def _on_operation_finished(self, progress_dialog, message, success, account_id=None, account_name=None):
        """Handle operation completion."""
        progress_dialog.close()
        
        if success:
            QMessageBox.information(self, "Success", message)
            # Refresh accounts to update status
            self.refresh_accounts()
        elif message == "2FA_PASSWORD_REQUIRED":
            # Handle 2FA password requirement
            if account_id and account_name:
                from PyQt5.QtWidgets import QInputDialog
                password, ok = QInputDialog.getText(
                    self, 
                    "Two-Factor Authentication", 
                    f"Please enter your 2FA password for {account_name}:",
                    QLineEdit.Password
                )
                if ok and password:
                    # Restart authorization with password (need to get phone_code_hash from worker)
                    if hasattr(self, 'worker') and hasattr(self.worker, 'phone_code_hash'):
                        self._start_telegram_operation_with_code("authorize", account_id, account_name, None, password, self.worker.phone_code_hash)
                    else:
                        self._start_telegram_operation_with_code("authorize", account_id, account_name, None, password)
                else:
                    self._update_account_status(account_id, AccountStatus.OFFLINE)
        else:
            QMessageBox.critical(self, "Error", message)

    def on_selection_changed(self):
        """Handle selection change."""
        selected_rows = self.accounts_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.logger.debug(f"Selection changed: {len(selected_rows)} rows selected")
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            self.logger.debug(f"Selected row: {row}")
            # Try to get account ID from the first column (Name column)
            name_item = self.accounts_table.item(row, 0)
            if name_item:
                account_id = name_item.data(Qt.UserRole)
                self.logger.debug(f"Account ID for row {row}: {account_id}")
                if account_id is not None:
                    # Emit signal with account ID for further processing
                    self.account_selected.emit(account_id)
                else:
                    self.logger.warning(f"No account ID found for row {row}")
            else:
                self.logger.warning(f"No name item found for row {row}")
    
    def add_account(self):
        """Add new account."""
        dialog = AccountDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_accounts()
    
    def edit_account(self):
        """Edit selected account."""
        selected_rows = self.accounts_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        account_id = self.accounts_table.item(row, 0).data(Qt.UserRole)
        
        # Load account from database
        session = db_get_session()
        try:
            from ...models import Account
            from sqlmodel import select
            account = session.exec(select(Account).where(Account.id == account_id)).first()
        finally:
            session.close()
        
        if account:
            dialog = AccountDialog(self, account)
            if dialog.exec_() == QDialog.Accepted:
                self.load_accounts()
    
    def delete_account(self):
        """Delete selected account."""
        selected_rows = self.accounts_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        account_name = self.accounts_table.item(row, 0).text()
        account_id = self.accounts_table.item(row, 0).data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Delete Account", 
            f"Are you sure you want to delete account '{account_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                session = db_get_session()
                try:
                    from ...models import Account
                    from sqlmodel import select
                    account = session.exec(select(Account).where(Account.id == account_id)).first()
                    if account:
                        account.soft_delete()
                        session.commit()
                finally:
                    session.close()
                
                self.logger.info(f"Account deleted: {account_name}")
                self.load_accounts()
                
            except Exception as e:
                self.logger.error(f"Error deleting account: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete account: {e}")
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Recreate the UI with new translations
        self.setup_ui()
        self.load_accounts()
    
    @pyqtSlot(int)
    def on_warmup_started(self, account_id: int):
        """Handle warmup started signal."""
        self.logger.info(f"Warmup started for account {account_id}")
        # Refresh the accounts table to show updated status
        self.refresh_accounts()
    
    @pyqtSlot(int, int, int)
    def on_warmup_progress(self, account_id: int, sent: int, total: int):
        """Handle warmup progress signal."""
        self.logger.debug(f"Warmup progress for account {account_id}: {sent}/{total}")
        # Refresh the accounts table to show updated progress
        self.refresh_accounts()
    
    @pyqtSlot(int)
    def on_warmup_completed(self, account_id: int):
        """Handle warmup completed signal."""
        self.logger.info(f"Warmup completed for account {account_id}")
        # Refresh the accounts table to show completed status
        self.refresh_accounts()
    
    @pyqtSlot(int, str)
    def on_warmup_error(self, account_id: int, error: str):
        """Handle warmup error signal."""
        self.logger.error(f"Warmup error for account {account_id}: {error}")
        # Refresh the accounts table to show error status
        self.refresh_accounts()


class AccountWidget(QWidget):
    """Main account management widget."""
    
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
        
        # Account list
        self.account_list = AccountListWidget()
        layout.addWidget(self.account_list)
        
        # Connect signals
        self.account_list.account_selected.connect(self.on_account_selected)
        self.account_list.account_updated.connect(self.on_account_updated)
    
    def on_account_selected(self, account_id):
        """Handle account selection."""
        # This could show account details in a side panel
        pass
    
    def on_account_updated(self, account_id):
        """Handle account update."""
        # Refresh the list
        self.account_list.refresh_accounts()
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # The account_list widget will handle its own language change
        # No need to recreate the UI since it only contains the account_list
