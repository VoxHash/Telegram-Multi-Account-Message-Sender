"""
Recipient management widgets.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QFileDialog, QProgressBar, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor

from ...models import Recipient, RecipientList, RecipientSource, RecipientStatus, RecipientType
from ...services import get_logger, get_session
import csv
import pandas as pd


class RecipientDialog(QDialog):
    """Dialog for adding/editing recipients."""
    
    recipient_saved = pyqtSignal(int)
    
    def __init__(self, parent=None, recipient: Optional[Recipient] = None):
        super().__init__(parent)
        self.recipient = recipient
        self.logger = get_logger()
        self.setup_ui()
        
        if recipient:
            self.load_recipient_data()
        
        # Initialize form based on type
        self.on_type_changed()
    
    def on_type_changed(self):
        """Handle recipient type change."""
        recipient_type = self.type_combo.currentText().lower()
        
        # Show/hide fields based on type
        is_user = recipient_type == "user"
        is_group = recipient_type in ["group", "channel"]
        
        # User fields
        self.user_id_edit.setVisible(is_user)
        self.phone_edit.setVisible(is_user)
        self.first_name_edit.setVisible(is_user)
        self.last_name_edit.setVisible(is_user)
        
        # Group fields
        self.group_id_edit.setVisible(is_group)
        self.group_title_edit.setVisible(is_group)
        self.group_username_edit.setVisible(is_group)
        self.group_type_edit.setVisible(is_group)
        self.member_count_edit.setVisible(is_group)
        
        # Update labels
        if is_group:
            self.username_edit.setPlaceholderText("@group_username")
        else:
            self.username_edit.setPlaceholderText("@username")
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Add Recipient" if not self.recipient else "Edit Recipient")
        self.setModal(True)
        self.resize(500, 400)
        
        # Enable help button
        self.setWindowFlags(self.windowFlags() | Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        
        # Basic Information
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # Recipient Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["User", "Group", "Channel"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        basic_layout.addRow("Type:", self.type_combo)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("@username")
        basic_layout.addRow("Username:", self.username_edit)
        
        self.user_id_edit = QLineEdit()
        self.user_id_edit.setPlaceholderText("123456789")
        basic_layout.addRow("User ID:", self.user_id_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+1234567890")
        basic_layout.addRow("Phone Number:", self.phone_edit)
        
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText("John")
        basic_layout.addRow("First Name:", self.first_name_edit)
        
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText("Doe")
        basic_layout.addRow("Last Name:", self.last_name_edit)
        
        # Group/Channel fields
        self.group_id_edit = QLineEdit()
        self.group_id_edit.setPlaceholderText("-1001234567890")
        basic_layout.addRow("Group ID:", self.group_id_edit)
        
        self.group_title_edit = QLineEdit()
        self.group_title_edit.setPlaceholderText("My Group Name")
        basic_layout.addRow("Group Title:", self.group_title_edit)
        
        self.group_username_edit = QLineEdit()
        self.group_username_edit.setPlaceholderText("@mygroup")
        basic_layout.addRow("Group Username:", self.group_username_edit)
        
        self.group_type_edit = QLineEdit()
        self.group_type_edit.setPlaceholderText("supergroup")
        basic_layout.addRow("Group Type:", self.group_type_edit)
        
        self.member_count_edit = QLineEdit()
        self.member_count_edit.setPlaceholderText("150")
        basic_layout.addRow("Member Count:", self.member_count_edit)
        
        layout.addWidget(basic_group)
        
        # Additional Information
        additional_group = QGroupBox("Additional Information")
        additional_layout = QFormLayout(additional_group)
        
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("john@example.com")
        additional_layout.addRow("Email:", self.email_edit)
        
        self.bio_edit = QTextEdit()
        self.bio_edit.setMaximumHeight(60)
        self.bio_edit.setPlaceholderText("Bio or description...")
        additional_layout.addRow("Bio:", self.bio_edit)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("tag1, tag2, tag3")
        additional_layout.addRow("Tags:", self.tags_edit)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        self.notes_edit.setPlaceholderText("Notes about this recipient...")
        additional_layout.addRow("Notes:", self.notes_edit)
        
        layout.addWidget(additional_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_recipient)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_recipient_data(self):
        """Load recipient data into the form."""
        if not self.recipient:
            return
        
        # Set recipient type
        type_mapping = {
            RecipientType.USER: "User",
            RecipientType.GROUP: "Group", 
            RecipientType.CHANNEL: "Channel"
        }
        self.type_combo.setCurrentText(type_mapping.get(self.recipient.recipient_type, "User"))
        
        # Load common fields
        self.username_edit.setText(self.recipient.username or "")
        self.email_edit.setText(self.recipient.email or "")
        self.bio_edit.setText(self.recipient.bio or "")
        self.tags_edit.setText(", ".join(self.recipient.get_tags_list()))
        self.notes_edit.setText(self.recipient.notes or "")
        
        # Load user-specific fields
        if self.recipient.recipient_type == RecipientType.USER:
            self.user_id_edit.setText(str(self.recipient.user_id) if self.recipient.user_id else "")
            self.phone_edit.setText(self.recipient.phone_number or "")
            self.first_name_edit.setText(self.recipient.first_name or "")
            self.last_name_edit.setText(self.recipient.last_name or "")
        else:
            # Load group/channel fields
            self.group_id_edit.setText(str(self.recipient.group_id) if self.recipient.group_id else "")
            self.group_title_edit.setText(self.recipient.group_title or "")
            self.group_username_edit.setText(self.recipient.group_username or "")
            self.group_type_edit.setText(self.recipient.group_type or "")
            self.member_count_edit.setText(str(self.recipient.member_count) if self.recipient.member_count else "")
    
    def save_recipient(self):
        """Save recipient data."""
        try:
            # Get recipient type
            recipient_type_text = self.type_combo.currentText().lower()
            recipient_type = RecipientType.USER
            if recipient_type_text == "group":
                recipient_type = RecipientType.GROUP
            elif recipient_type_text == "channel":
                recipient_type = RecipientType.CHANNEL
            
            # Validate required fields based on type
            if recipient_type == RecipientType.USER:
                if not any([
                    self.username_edit.text().strip(),
                    self.user_id_edit.text().strip(),
                    self.phone_edit.text().strip()
                ]):
                    QMessageBox.warning(self, "Validation Error", "At least one identifier (username, user ID, or phone) is required for users")
                    return
            else:
                if not any([
                    self.group_id_edit.text().strip(),
                    self.group_title_edit.text().strip(),
                    self.group_username_edit.text().strip()
                ]):
                    QMessageBox.warning(self, "Validation Error", "At least one identifier (group ID, title, or username) is required for groups/channels")
                    return
            
            # Create or update recipient
            if self.recipient:
                # Update existing recipient
                self.recipient.recipient_type = recipient_type
                self.recipient.username = self.username_edit.text().strip() or None
                self.recipient.email = self.email_edit.text().strip() or None
                self.recipient.bio = self.bio_edit.toPlainText().strip() or None
                self.recipient.notes = self.notes_edit.toPlainText().strip() or None
                
                if recipient_type == RecipientType.USER:
                    self.recipient.user_id = int(self.user_id_edit.text().strip()) if self.user_id_edit.text().strip() else None
                    self.recipient.phone_number = self.phone_edit.text().strip() or None
                    self.recipient.first_name = self.first_name_edit.text().strip() or None
                    self.recipient.last_name = self.last_name_edit.text().strip() or None
                else:
                    self.recipient.group_id = int(self.group_id_edit.text().strip()) if self.group_id_edit.text().strip() else None
                    self.recipient.group_title = self.group_title_edit.text().strip() or None
                    self.recipient.group_username = self.group_username_edit.text().strip() or None
                    self.recipient.group_type = self.group_type_edit.text().strip() or None
                    self.recipient.member_count = int(self.member_count_edit.text().strip()) if self.member_count_edit.text().strip() else None
            else:
                # Create new recipient
                recipient_data = {
                    "recipient_type": recipient_type,
                    "username": self.username_edit.text().strip() or None,
                    "email": self.email_edit.text().strip() or None,
                    "bio": self.bio_edit.toPlainText().strip() or None,
                    "notes": self.notes_edit.toPlainText().strip() or None,
                    "source": RecipientSource.MANUAL
                }
                
                if recipient_type == RecipientType.USER:
                    recipient_data.update({
                        "user_id": int(self.user_id_edit.text().strip()) if self.user_id_edit.text().strip() else None,
                        "phone_number": self.phone_edit.text().strip() or None,
                        "first_name": self.first_name_edit.text().strip() or None,
                        "last_name": self.last_name_edit.text().strip() or None,
                    })
                else:
                    recipient_data.update({
                        "group_id": int(self.group_id_edit.text().strip()) if self.group_id_edit.text().strip() else None,
                        "group_title": self.group_title_edit.text().strip() or None,
                        "group_username": self.group_username_edit.text().strip() or None,
                        "group_type": self.group_type_edit.text().strip() or None,
                        "member_count": int(self.member_count_edit.text().strip()) if self.member_count_edit.text().strip() else None,
                    })
                
                self.recipient = Recipient(**recipient_data)
            
            # Update tags
            tags_text = self.tags_edit.text().strip()
            if tags_text:
                tags_list = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                self.recipient.set_tags_list(tags_list)
            else:
                self.recipient.set_tags_list([])
            
            # Save to database
            session = get_session()
            try:
                if self.recipient.id is None:
                    session.add(self.recipient)
                    session.flush()  # Flush to get the ID
                    recipient_id = self.recipient.id
                else:
                    session.merge(self.recipient)
                    recipient_id = self.recipient.id
                session.commit()
                
                self.logger.info(f"Recipient saved: {self.recipient.get_display_name()}")
                self.recipient_saved.emit(recipient_id)
                self.accept()
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
            
        except Exception as e:
            self.logger.error(f"Error saving recipient: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save recipient: {e}")
    
    def event(self, event):
        """Handle events including help button clicks."""
        if event.type() == event.EnterWhatsThisMode:
            self.show_help()
            return True
        return super().event(event)
    
    def show_help(self):
        """Show help dialog."""
        help_text = """
        <h3>Add/Edit Recipient Help</h3>
        
        <h4>Recipient Types:</h4>
        <ul>
        <li><b>User:</b> Individual Telegram users (personal accounts)</li>
        <li><b>Group:</b> Telegram groups (up to 200,000 members)</li>
        <li><b>Channel:</b> Telegram channels (unlimited subscribers)</li>
        </ul>
        
        <h4>Required Fields by Type:</h4>
        <p><b>For Users:</b> At least one identifier required:</p>
        <ul>
        <li>Username (e.g., @username)</li>
        <li>User ID (numeric ID)</li>
        <li>Phone Number (e.g., +1234567890)</li>
        </ul>
        
        <p><b>For Groups/Channels:</b> At least one identifier required:</p>
        <ul>
        <li>Group ID (numeric ID)</li>
        <li>Group Title (display name)</li>
        <li>Group Username (e.g., @groupname)</li>
        </ul>
        
        <h4>Optional Fields:</h4>
        <ul>
        <li><b>Email:</b> Contact email address</li>
        <li><b>Bio:</b> Description or bio text</li>
        <li><b>Tags:</b> Comma-separated tags for organization</li>
        <li><b>Notes:</b> Internal notes about this recipient</li>
        </ul>
        
        <h4>Tips:</h4>
        <ul>
        <li>Use tags to organize recipients (e.g., "vip, customer, newsletter")</li>
        <li>Phone numbers should include country code (e.g., +1234567890)</li>
        <li>Usernames should not include the @ symbol</li>
        <li>Group types can be: "group", "supergroup", "channel"</li>
        </ul>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Recipient Help")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()


class CSVImportDialog(QDialog):
    """Dialog for importing recipients from CSV."""
    
    recipients_imported = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Import Recipients from CSV")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # File selection
        file_group = QGroupBox("Select CSV File")
        file_layout = QHBoxLayout(file_group)
        
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select a CSV file...")
        file_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(self.browse_button)
        
        layout.addWidget(file_group)
        
        # Column mapping
        mapping_group = QGroupBox("Column Mapping")
        mapping_layout = QGridLayout(mapping_group)
        
        # Create column mapping controls
        self.column_mappings = {}
        csv_columns = ["username", "user_id", "phone_number", "first_name", "last_name", "email", "bio", "tags"]
        
        for i, column in enumerate(csv_columns):
            mapping_layout.addWidget(QLabel(f"{column.replace('_', ' ').title()}:"), i, 0)
            combo = QComboBox()
            combo.addItem("-- Select Column --")
            self.column_mappings[column] = combo
            mapping_layout.addWidget(combo, i, 1)
        
        layout.addWidget(mapping_group)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        preview_layout.addWidget(self.preview_table)
        
        self.load_preview_button = QPushButton("Load Preview")
        self.load_preview_button.clicked.connect(self.load_preview)
        preview_layout.addWidget(self.load_preview_button)
        
        layout.addWidget(preview_group)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Import | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Import).setText("Import")
        buttons.accepted.connect(self.import_recipients)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def browse_file(self):
        """Browse for CSV file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.load_csv_columns()
    
    def load_csv_columns(self):
        """Load CSV columns into mapping combos."""
        try:
            file_path = self.file_path_edit.text()
            if not file_path:
                return
            
            # Read CSV header
            df = pd.read_csv(file_path, nrows=0)
            columns = list(df.columns)
            
            # Update all combo boxes
            for combo in self.column_mappings.values():
                combo.clear()
                combo.addItem("-- Select Column --")
                combo.addItems(columns)
        
        except Exception as e:
            self.logger.error(f"Error loading CSV columns: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load CSV file: {e}")
    
    def load_preview(self):
        """Load preview of CSV data."""
        try:
            file_path = self.file_path_edit.text()
            if not file_path:
                QMessageBox.warning(self, "No File", "Please select a CSV file first")
                return
            
            # Read first 10 rows
            df = pd.read_csv(file_path, nrows=10)
            
            # Setup preview table
            self.preview_table.setRowCount(len(df))
            self.preview_table.setColumnCount(len(df.columns))
            self.preview_table.setHorizontalHeaderLabels(df.columns.tolist())
            
            # Fill preview table
            for i, row in df.iterrows():
                for j, value in enumerate(row):
                    self.preview_table.setItem(i, j, QTableWidgetItem(str(value)))
            
            # Resize columns
            self.preview_table.resizeColumnsToContents()
        
        except Exception as e:
            self.logger.error(f"Error loading preview: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load preview: {e}")
    
    def import_recipients(self):
        """Import recipients from CSV."""
        try:
            file_path = self.file_path_edit.text()
            if not file_path:
                QMessageBox.warning(self, "No File", "Please select a CSV file first")
                return
            
            # Check if all required mappings are set
            required_columns = ["username", "user_id", "phone_number"]
            has_identifier = False
            
            for col in required_columns:
                if self.column_mappings[col].currentText() != "-- Select Column --":
                    has_identifier = True
                    break
            
            if not has_identifier:
                QMessageBox.warning(self, "Mapping Error", "Please map at least one identifier column (username, user_id, or phone_number)")
                return
            
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Create recipients
            recipients = []
            for _, row in df.iterrows():
                recipient_data = {}
                
                # Map columns
                for field, combo in self.column_mappings.items():
                    if combo.currentText() != "-- Select Column --":
                        value = row[combo.currentText()]
                        if pd.notna(value) and str(value).strip():
                            recipient_data[field] = str(value).strip()
                
                # Create recipient if has at least one identifier
                if any(recipient_data.get(field) for field in required_columns):
                    recipient = Recipient(
                        username=recipient_data.get("username"),
                        user_id=int(recipient_data["user_id"]) if recipient_data.get("user_id") and recipient_data["user_id"].isdigit() else None,
                        phone_number=recipient_data.get("phone_number"),
                        first_name=recipient_data.get("first_name"),
                        last_name=recipient_data.get("last_name"),
                        email=recipient_data.get("email"),
                        bio=recipient_data.get("bio"),
                        source=RecipientSource.CSV_IMPORT
                    )
                    
                    # Set tags using proper JSON serialization
                    if recipient_data.get("tags"):
                        tags_list = [tag.strip() for tag in recipient_data["tags"].split(",") if tag.strip()]
                        recipient.set_tags_list(tags_list)
                    else:
                        recipient.set_tags_list([])
                    recipients.append(recipient)
            
            # Save to database
            session = get_session()
            try:
                session.add_all(recipients)
                session.commit()
            finally:
                session.close()
            
            self.logger.info(f"Imported {len(recipients)} recipients from CSV")
            self.recipients_imported.emit(recipients)
            QMessageBox.information(self, "Import Complete", f"Successfully imported {len(recipients)} recipients")
            self.accept()
        
        except Exception as e:
            self.logger.error(f"Error importing recipients: {e}")
            QMessageBox.critical(self, "Import Error", f"Failed to import recipients: {e}")


class RecipientListWidget(QWidget):
    """Widget for displaying and managing recipients."""
    
    recipient_selected = pyqtSignal(int)
    recipient_updated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.setup_ui()
        self.load_recipients()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_recipients)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Recipients")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.add_button = QPushButton("Add Recipient")
        self.add_button.clicked.connect(self.add_recipient)
        header_layout.addWidget(self.add_button)
        
        self.import_button = QPushButton("Import CSV")
        self.import_button.clicked.connect(self.import_csv)
        header_layout.addWidget(self.import_button)
        
        self.edit_button = QPushButton("Edit Recipient")
        self.edit_button.clicked.connect(self.edit_recipient)
        self.edit_button.setEnabled(False)
        header_layout.addWidget(self.edit_button)
        
        self.delete_button = QPushButton("Delete Recipient")
        self.delete_button.clicked.connect(self.delete_recipient)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_recipients)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Recipients table
        self.recipients_table = QTableWidget()
        self.recipients_table.setColumnCount(8)
        self.recipients_table.setHorizontalHeaderLabels([
            "Type", "Display Name", "Username/Group", "ID", "Phone", "Source", "Status", "Messages"
        ])
        
        # Configure table
        header = self.recipients_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Display Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Username/Group
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Phone
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Source
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Messages
        
        self.recipients_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.recipients_table.setSelectionMode(QTableWidget.SingleSelection)
        self.recipients_table.setAlternatingRowColors(True)
        self.recipients_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Set custom styling for black and gray alternating rows
        self.recipients_table.setStyleSheet("""
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
        self.recipients_table.cellClicked.connect(self.on_cell_clicked)
        
        layout.addWidget(self.recipients_table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
    
    def load_recipients(self):
        """Load recipients from database."""
        try:
            session = get_session()
            try:
                from ...models import Recipient
                from sqlmodel import select
                recipients = session.exec(select(Recipient).where(Recipient.is_deleted == False)).all()
            finally:
                session.close()
            
            self.recipients_table.setRowCount(len(recipients))
            
            for row, recipient in enumerate(recipients):
                # Type - Disabled text field
                type_text = recipient.recipient_type.value.title()
                if recipient.recipient_type.value == "group":
                    type_text = "👥 Group"
                elif recipient.recipient_type.value == "channel":
                    type_text = "📢 Channel"
                else:
                    type_text = "👤 User"
                
                type_item = QTableWidgetItem(type_text)
                type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                type_item.setTextAlignment(Qt.AlignCenter)
                self.recipients_table.setItem(row, 0, type_item)
                
                # Display name - Disabled text field
                display_name_item = QTableWidgetItem(recipient.get_display_name())
                display_name_item.setFlags(display_name_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                # Store recipient ID in the display name item for selection handling
                display_name_item.setData(Qt.UserRole, recipient.id)
                self.recipients_table.setItem(row, 1, display_name_item)
                
                # Username/Group - Disabled text field
                if recipient.recipient_type.value in ["group", "channel"]:
                    username = f"@{recipient.group_username}" if recipient.group_username else ""
                else:
                    username = f"@{recipient.username}" if recipient.username else ""
                username_item = QTableWidgetItem(username)
                username_item.setFlags(username_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                self.recipients_table.setItem(row, 2, username_item)
                
                # ID - Disabled text field
                if recipient.recipient_type.value in ["group", "channel"]:
                    id_text = str(recipient.group_id) if recipient.group_id else ""
                else:
                    id_text = str(recipient.user_id) if recipient.user_id else ""
                id_item = QTableWidgetItem(id_text)
                id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                id_item.setTextAlignment(Qt.AlignCenter)
                self.recipients_table.setItem(row, 3, id_item)
                
                # Phone - Disabled text field (only for users)
                phone_text = recipient.phone_number if recipient.recipient_type.value == "user" else ""
                phone_item = QTableWidgetItem(phone_text or "")
                phone_item.setFlags(phone_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                phone_item.setTextAlignment(Qt.AlignCenter)
                self.recipients_table.setItem(row, 4, phone_item)
                
                # Source - Disabled text field
                source_item = QTableWidgetItem(recipient.source.value.title())
                source_item.setFlags(source_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                source_item.setTextAlignment(Qt.AlignCenter)
                self.recipients_table.setItem(row, 5, source_item)
                
                # Status - Enhanced button-like appearance
                status_item = QTableWidgetItem(recipient.status.value.title())
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                
                # Set status-specific styling with button-like appearance
                if recipient.status == RecipientStatus.ACTIVE:
                    status_item.setBackground(QColor(34, 197, 94))  # Green
                    status_item.setForeground(Qt.white)
                elif recipient.status == RecipientStatus.BLOCKED:
                    status_item.setBackground(QColor(239, 68, 68))  # Red
                    status_item.setForeground(Qt.white)
                elif recipient.status == RecipientStatus.INACTIVE:
                    status_item.setBackground(QColor(107, 114, 128))  # Gray
                    status_item.setForeground(Qt.white)
                
                # Center align status text
                status_item.setTextAlignment(Qt.AlignCenter)
                self.recipients_table.setItem(row, 6, status_item)
                
                # Messages - Disabled text field
                messages = f"{recipient.total_messages_sent}/{recipient.total_messages_sent + recipient.total_messages_failed}"
                messages_item = QTableWidgetItem(messages)
                messages_item.setFlags(messages_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                messages_item.setTextAlignment(Qt.AlignCenter)
                self.recipients_table.setItem(row, 7, messages_item)
            
            self.status_label.setText(f"Loaded {len(recipients)} recipients")
            
        except Exception as e:
            self.logger.error(f"Error loading recipients: {e}")
            self.status_label.setText(f"Error loading recipients: {e}")
    
    def refresh_recipients(self):
        """Refresh recipients data."""
        self.load_recipients()
    
    def on_cell_clicked(self, row, column):
        """Handle cell click events."""
        # For all columns, ensure the row is selected
        self.recipients_table.selectRow(row)
        # Also trigger selection changed manually
        self.on_selection_changed()
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_rows = self.recipients_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            # Try to get recipient ID from the first column (Display Name column)
            display_name_item = self.recipients_table.item(row, 0)
            if display_name_item:
                recipient_id = display_name_item.data(Qt.UserRole)
                if recipient_id is not None:
                    # Emit signal with recipient ID for further processing
                    self.recipient_selected.emit(recipient_id)
                else:
                    self.logger.warning(f"No recipient ID found for row {row}")
            else:
                self.logger.warning(f"No display name item found for row {row}")
    
    def add_recipient(self):
        """Add new recipient."""
        dialog = RecipientDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_recipients()
    
    def edit_recipient(self):
        """Edit selected recipient."""
        selected_rows = self.recipients_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        recipient_id = self.recipients_table.item(row, 0).data(Qt.UserRole)
        
        # Load recipient from database
        session = get_session()
        try:
            from ...models import Recipient
            from sqlmodel import select
            recipient = session.exec(select(Recipient).where(Recipient.id == recipient_id)).first()
        finally:
            session.close()
        
        if recipient:
            dialog = RecipientDialog(self, recipient)
            if dialog.exec_() == QDialog.Accepted:
                self.load_recipients()
    
    def import_csv(self):
        """Import recipients from CSV."""
        dialog = CSVImportDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_recipients()
    
    def delete_recipient(self):
        """Delete selected recipient."""
        selected_rows = self.recipients_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        recipient_name = self.recipients_table.item(row, 0).text()
        recipient_id = self.recipients_table.item(row, 0).data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Delete Recipient", 
            f"Are you sure you want to delete recipient '{recipient_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                session = get_session()
                try:
                    from ...models import Recipient
                    from sqlmodel import select
                    recipient = session.exec(select(Recipient).where(Recipient.id == recipient_id)).first()
                    if recipient:
                        recipient.soft_delete()
                        session.commit()
                finally:
                    session.close()
                
                self.logger.info(f"Recipient deleted: {recipient_name}")
                self.load_recipients()
                
            except Exception as e:
                self.logger.error(f"Error deleting recipient: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete recipient: {e}")


class RecipientWidget(QWidget):
    """Main recipient management widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Recipient list
        self.recipient_list = RecipientListWidget()
        layout.addWidget(self.recipient_list)
        
        # Connect signals
        self.recipient_list.recipient_selected.connect(self.on_recipient_selected)
        self.recipient_list.recipient_updated.connect(self.on_recipient_updated)
    
    def on_recipient_selected(self, recipient_id):
        """Handle recipient selection."""
        # This could show recipient details in a side panel
        pass
    
    def on_recipient_updated(self, recipient_id):
        """Handle recipient update."""
        # Refresh the list
        self.recipient_list.refresh_recipients()
