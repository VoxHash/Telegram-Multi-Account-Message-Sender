"""
Account management widgets.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from ...models import Account, AccountStatus, ProxyType
from ...models.base import SoftDeleteMixin
from ...services import get_logger, get_session
from ...core import TelegramClientManager


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
        
        self.api_id_edit = QLineEdit()
        self.api_id_edit.setPlaceholderText("Your Telegram API ID")
        basic_layout.addRow("API ID:", self.api_id_edit)
        
        self.api_hash_edit = QLineEdit()
        self.api_hash_edit.setEchoMode(QLineEdit.Password)
        self.api_hash_edit.setPlaceholderText("Your Telegram API Hash")
        basic_layout.addRow("API Hash:", self.api_hash_edit)
        
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
        self.api_id_edit.setText(str(self.account.api_id))
        self.api_hash_edit.setText(self.account.api_hash)
        
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
            
            if not self.api_id_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "API ID is required")
                return
            
            if not self.api_hash_edit.text().strip():
                QMessageBox.warning(self, "Validation Error", "API Hash is required")
                return
            
            # Create or update account
            if self.account:
                # Update existing account
                self.account.name = self.name_edit.text().strip()
                self.account.phone_number = self.phone_edit.text().strip()
                self.account.api_id = int(self.api_id_edit.text().strip())
                self.account.api_hash = self.api_hash_edit.text().strip()
            else:
                # Create new account
                self.account = Account(
                    name=self.name_edit.text().strip(),
                    phone_number=self.phone_edit.text().strip(),
                    api_id=int(self.api_id_edit.text().strip()),
                    api_hash=self.api_hash_edit.text().strip(),
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
            session = get_session()
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
        self.accounts_table.setAlternatingRowColors(True)
        self.accounts_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.accounts_table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def load_accounts(self):
        """Load accounts from database."""
        try:
            session = get_session()
            try:
                from ...models import Account
                from sqlmodel import select
                accounts = session.exec(select(Account).where(Account.is_deleted == False)).all()
            finally:
                session.close()
            
            self.accounts_table.setRowCount(len(accounts))
            
            for row, account in enumerate(accounts):
                # Name
                self.accounts_table.setItem(row, 0, QTableWidgetItem(account.name))
                
                # Phone
                self.accounts_table.setItem(row, 1, QTableWidgetItem(account.phone_number))
                
                # Status
                status_item = QTableWidgetItem(account.status.value.title())
                if account.status == AccountStatus.ONLINE:
                    status_item.setBackground(Qt.green)
                elif account.status == AccountStatus.ERROR:
                    status_item.setBackground(Qt.red)
                elif account.status == AccountStatus.OFFLINE:
                    status_item.setBackground(Qt.gray)
                self.accounts_table.setItem(row, 2, status_item)
                
                # Messages sent
                self.accounts_table.setItem(row, 3, QTableWidgetItem(str(account.total_messages_sent)))
                
                # Success rate
                success_rate = account.get_success_rate()
                self.accounts_table.setItem(row, 4, QTableWidgetItem(f"{success_rate:.1f}%"))
                
                # Last activity
                last_activity = account.last_activity.strftime("%Y-%m-%d %H:%M") if account.last_activity else "Never"
                self.accounts_table.setItem(row, 5, QTableWidgetItem(last_activity))
                
                # Warmup status
                warmup_status = "Complete" if account.is_warmup_complete() else f"{account.warmup_messages_sent}/{account.warmup_target_messages}"
                self.accounts_table.setItem(row, 6, QTableWidgetItem(warmup_status))
                
                # Actions
                actions_item = QTableWidgetItem("Connect | Test | Authorize")
                self.accounts_table.setItem(row, 7, actions_item)
                
                # Store account ID in the first column for reference
                self.accounts_table.item(row, 0).setData(Qt.UserRole, account.id)
            
            self.status_label.setText(f"Loaded {len(accounts)} accounts")
            
        except Exception as e:
            self.logger.error(f"Error loading accounts: {e}")
            self.status_label.setText(f"Error loading accounts: {e}")
    
    def refresh_accounts(self):
        """Refresh accounts data."""
        self.load_accounts()
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_rows = self.accounts_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            account_id = self.accounts_table.item(row, 0).data(Qt.UserRole)
            # Emit signal with account ID for further processing
            self.account_selected.emit(account_id)
    
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
        session = get_session()
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
                session = get_session()
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


class AccountWidget(QWidget):
    """Main account management widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
