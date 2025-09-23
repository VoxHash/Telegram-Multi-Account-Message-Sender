"""
Campaign management widgets.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QComboBox, QCheckBox, QSpinBox,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout,
    QTextEdit, QDateTimeEdit, QProgressBar, QTabWidget, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt5.QtGui import QFont, QIcon, QColor

from ...models import Campaign, CampaignStatus, CampaignType, MessageType
from ...services import get_logger, get_campaign_manager
from ...services.db import get_session
from ...services.translation import _, get_translation_manager
from ...core import SpintaxProcessor


class CampaignDialog(QDialog):
    """Dialog for creating/editing campaigns."""
    
    campaign_saved = pyqtSignal(int)
    
    def __init__(self, parent=None, campaign: Optional[Campaign] = None):
        super().__init__(parent)
        self.campaign = campaign
        self.logger = get_logger()
        self.spintax_processor = SpintaxProcessor()
        self.setup_ui()
        
        if campaign:
            self.load_campaign_data()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle(_("campaigns.create_campaign") if not self.campaign else _("campaigns.edit_campaign"))
        self.setModal(True)
        self.resize(700, 800)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Basic Information Tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        
        # Campaign Info
        info_group = QGroupBox(_("campaigns.campaign_information"))
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(_("campaigns.campaign_name_placeholder"))
        info_layout.addRow(_("common.name") + ":", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText(_("campaigns.campaign_description_placeholder"))
        info_layout.addRow(_("common.description") + ":", self.description_edit)
        
        self.campaign_type_combo = QComboBox()
        self.campaign_type_combo.addItems([ct.value.title() for ct in CampaignType])
        info_layout.addRow(_("common.type") + ":", self.campaign_type_combo)
        
        basic_layout.addWidget(info_group)
        
        # Message Content
        message_group = QGroupBox(_("campaigns.message_content"))
        message_layout = QVBoxLayout(message_group)
        
        # Message type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel(_("common.message_type") + ":"))
        self.message_type_combo = QComboBox()
        self.message_type_combo.addItems([mt.value.title() for mt in MessageType])
        type_layout.addWidget(self.message_type_combo)
        type_layout.addStretch()
        message_layout.addLayout(type_layout)
        
        # Message text
        message_layout.addWidget(QLabel(_("common.message_text") + ":"))
        self.message_text_edit = QTextEdit()
        self.message_text_edit.setMaximumHeight(120)
        self.message_text_edit.setPlaceholderText(_("campaigns.message_text_placeholder"))
        message_layout.addWidget(self.message_text_edit)
        
        # Spintax controls
        spintax_layout = QHBoxLayout()
        self.use_spintax_check = QCheckBox(_("templates.use_spintax"))
        self.use_spintax_check.toggled.connect(self.toggle_spintax)
        spintax_layout.addWidget(self.use_spintax_check)
        
        self.preview_spintax_button = QPushButton(_("templates.preview_spintax"))
        self.preview_spintax_button.clicked.connect(self.preview_spintax)
        spintax_layout.addWidget(self.preview_spintax_button)
        
        spintax_layout.addStretch()
        message_layout.addLayout(spintax_layout)
        
        # Media
        media_layout = QHBoxLayout()
        media_layout.addWidget(QLabel("Media File:"))
        self.media_path_edit = QLineEdit()
        self.media_path_edit.setPlaceholderText("Path to media file (optional)")
        media_layout.addWidget(self.media_path_edit)
        
        self.browse_media_button = QPushButton("Browse")
        self.browse_media_button.clicked.connect(self.browse_media)
        media_layout.addWidget(self.browse_media_button)
        message_layout.addLayout(media_layout)
        
        # Caption
        self.caption_edit = QLineEdit()
        self.caption_edit.setPlaceholderText("Media caption (optional)")
        message_layout.addWidget(QLabel("Caption:"))
        message_layout.addWidget(self.caption_edit)
        
        basic_layout.addWidget(message_group)
        
        # A/B Testing
        ab_group = QGroupBox("A/B Testing")
        ab_layout = QVBoxLayout(ab_group)
        
        self.use_ab_testing_check = QCheckBox("Enable A/B Testing")
        self.use_ab_testing_check.toggled.connect(self.toggle_ab_testing)
        ab_layout.addWidget(self.use_ab_testing_check)
        
        self.ab_variants_edit = QTextEdit()
        self.ab_variants_edit.setMaximumHeight(100)
        self.ab_variants_edit.setPlaceholderText("Enter A/B test variants (one per line)")
        ab_layout.addWidget(self.ab_variants_edit)
        
        basic_layout.addWidget(ab_group)
        
        tab_widget.addTab(basic_tab, "Basic")
        
        # Scheduling Tab
        schedule_tab = QWidget()
        schedule_layout = QVBoxLayout(schedule_tab)
        
        # Start time
        start_group = QGroupBox("Start Time")
        start_layout = QFormLayout(start_group)
        
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDateTime(QDateTime.currentDateTime())
        self.start_time_edit.setCalendarPopup(True)
        start_layout.addRow("Start Time:", self.start_time_edit)
        
        self.timezone_combo = QComboBox()
        self.timezone_combo.addItems(["UTC", "EST", "PST", "CET", "JST"])
        start_layout.addRow("Timezone:", self.timezone_combo)
        
        schedule_layout.addWidget(start_group)
        
        # Rate Limiting
        rate_group = QGroupBox("Rate Limiting")
        rate_layout = QFormLayout(rate_group)
        
        self.messages_per_minute_spin = QSpinBox()
        self.messages_per_minute_spin.setRange(1, 60)
        self.messages_per_minute_spin.setValue(1)
        rate_layout.addRow("Messages per Minute:", self.messages_per_minute_spin)
        
        self.messages_per_hour_spin = QSpinBox()
        self.messages_per_hour_spin.setRange(1, 1000)
        self.messages_per_hour_spin.setValue(30)
        rate_layout.addRow("Messages per Hour:", self.messages_per_hour_spin)
        
        self.messages_per_day_spin = QSpinBox()
        self.messages_per_day_spin.setRange(1, 10000)
        self.messages_per_day_spin.setValue(500)
        rate_layout.addRow("Messages per Day:", self.messages_per_day_spin)
        
        self.random_jitter_spin = QSpinBox()
        self.random_jitter_spin.setRange(0, 300)
        self.random_jitter_spin.setValue(5)
        rate_layout.addRow("Random Jitter (seconds):", self.random_jitter_spin)
        
        schedule_layout.addWidget(rate_group)
        
        # Safety Settings
        safety_group = QGroupBox("Safety Settings")
        safety_layout = QFormLayout(safety_group)
        
        self.dry_run_check = QCheckBox("Dry Run (log only, don't send)")
        safety_layout.addRow(self.dry_run_check)
        
        self.respect_rate_limits_check = QCheckBox("Respect Rate Limits")
        self.respect_rate_limits_check.setChecked(True)
        safety_layout.addRow(self.respect_rate_limits_check)
        
        self.stop_on_error_check = QCheckBox("Stop on Error")
        safety_layout.addRow(self.stop_on_error_check)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(3)
        safety_layout.addRow("Max Retries:", self.max_retries_spin)
        
        schedule_layout.addWidget(safety_group)
        
        tab_widget.addTab(schedule_tab, "Scheduling")
        
        # Recipients Tab
        recipients_tab = QWidget()
        recipients_layout = QVBoxLayout(recipients_tab)
        
        # Recipient source
        source_group = QGroupBox("Recipient Source")
        source_layout = QFormLayout(source_group)
        
        self.recipient_source_combo = QComboBox()
        self.recipient_source_combo.addItems(["Manual", "CSV Import"])
        self.recipient_source_combo.currentTextChanged.connect(self.on_recipient_source_changed)
        source_layout.addRow("Source:", self.recipient_source_combo)
        
        self.recipient_count_label = QLabel("0 recipients")
        source_layout.addRow("Total Recipients:", self.recipient_count_label)
        
        recipients_layout.addWidget(source_group)
        
        # Manual recipients
        self.manual_group = QGroupBox("Manual Recipients")
        manual_layout = QVBoxLayout(self.manual_group)
        
        self.manual_recipients_edit = QTextEdit()
        self.manual_recipients_edit.setMaximumHeight(150)
        self.manual_recipients_edit.setPlaceholderText("Enter recipients (one per line):\n@username1\n@username2\n+1234567890")
        manual_layout.addWidget(self.manual_recipients_edit)
        
        self.manual_recipients_edit.textChanged.connect(self.update_recipient_count)
        
        recipients_layout.addWidget(self.manual_group)
        
        # CSV Import section
        self.csv_group = QGroupBox("CSV Import")
        csv_layout = QVBoxLayout(self.csv_group)
        
        csv_import_layout = QHBoxLayout()
        self.csv_file_edit = QLineEdit()
        self.csv_file_edit.setPlaceholderText("Select CSV file to import recipients...")
        self.csv_file_edit.setReadOnly(True)
        csv_import_layout.addWidget(self.csv_file_edit)
        
        self.browse_csv_button = QPushButton("Browse")
        self.browse_csv_button.clicked.connect(self.browse_csv_file)
        csv_import_layout.addWidget(self.browse_csv_button)
        
        csv_layout.addLayout(csv_import_layout)
        
        # CSV format info
        csv_info = QLabel("CSV Format: username,phone_number,first_name,last_name (one per line)")
        csv_info.setStyleSheet("color: #888; font-size: 11px;")
        csv_layout.addWidget(csv_info)
        
        recipients_layout.addWidget(self.csv_group)
        
        
        tab_widget.addTab(recipients_tab, "Recipients")
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_campaign)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Add Help button to top right corner
        help_button = QPushButton("?")
        help_button.setFixedSize(25, 25)
        help_button.setToolTip("Show Help")
        help_button.clicked.connect(self.show_help)
        help_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        
        # Store help button reference for positioning
        self.help_button = help_button
        
        # Initialize
        self.toggle_spintax(False)
        self.toggle_ab_testing(False)
        self.update_recipient_count()
        self.on_recipient_source_changed("Manual")  # Set initial state
        
        # Position help button initially
        self.position_help_button()
        
        # Ensure help button is visible and on top
        self.help_button.raise_()
        self.help_button.show()
        
        # Use a timer to position the button after the dialog is fully rendered
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.position_help_button)
    
    def resizeEvent(self, event):
        """Handle dialog resize to reposition help button."""
        super().resizeEvent(event)
        self.position_help_button()
    
    def position_help_button(self):
        """Position the help button in the top right corner."""
        if hasattr(self, 'help_button'):
            self.help_button.move(self.width() - 35, 10)
    
    def toggle_spintax(self, enabled: bool):
        """Toggle spintax controls."""
        self.preview_spintax_button.setEnabled(enabled)
    
    def toggle_ab_testing(self, enabled: bool):
        """Toggle A/B testing controls."""
        self.ab_variants_edit.setEnabled(enabled)
    
    def preview_spintax(self):
        """Preview spintax processing."""
        text = self.message_text_edit.toPlainText()
        if not text:
            QMessageBox.information(self, _("campaigns.preview"), _("campaigns.no_message_text"))
            return
        
        try:
            samples = self.spintax_processor.get_preview_samples(text, 5)
            preview_text = "\n".join(samples)
            
            QMessageBox.information(
                self, 
                _("templates.spintax_preview"), 
                f"Here are 5 random samples:\n\n{preview_text}"
            )
        except Exception as e:
            QMessageBox.warning(self, _("templates.spintax_preview"), f"Error processing spintax: {e}")
    
    def browse_media(self):
        """Browse for media file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Media File",
            "",
            "All Files (*);;Images (*.jpg *.jpeg *.png *.gif);;Videos (*.mp4 *.avi *.mov);;Documents (*.pdf *.doc *.docx)"
        )
        
        if file_path:
            self.media_path_edit.setText(file_path)
    
    def update_recipient_count(self):
        """Update recipient count display."""
        text = self.manual_recipients_edit.toPlainText()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        self.recipient_count_label.setText(f"{len(lines)} recipients")
    
    def on_recipient_source_changed(self, source: str):
        """Handle recipient source selection change."""
        # Show/hide appropriate sections based on selection
        if source == "Manual":
            self.manual_group.setVisible(True)
            self.csv_group.setVisible(False)
        elif source == "CSV Import":
            self.manual_group.setVisible(False)
            self.csv_group.setVisible(True)
    
    def browse_csv_file(self):
        """Browse for CSV file to import recipients."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.csv_file_edit.setText(file_path)
            # Parse CSV and update recipient count
            self.parse_csv_recipients(file_path)
    
    def parse_csv_recipients(self, file_path: str):
        """Parse CSV file and update recipient count."""
        try:
            import csv
            recipient_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if row and any(cell.strip() for cell in row):  # Skip empty rows
                        recipient_count += 1
            
            self.recipient_count_label.setText(f"{recipient_count} recipients")
            
        except Exception as e:
            QMessageBox.warning(
                self, 
                "CSV Import Error", 
                f"Error reading CSV file: {e}"
            )
            self.recipient_count_label.setText("0 recipients")
    
    def show_help(self):
        """Show help information for the campaign dialog."""
        help_text = """
        <h2>Campaign Creation Help</h2>

<h3>Basic Tab</h3>
<p><b>Campaign Information:</b></p>
<ul>
<li><b>Name:</b> A unique name for your campaign</li>
<li><b>Description:</b> Optional description of the campaign purpose</li>
<li><b>Type:</b> Choose between Immediate (starts right away) or Scheduled (starts at specific time)</li>
</ul>

<p><b>Message Content:</b></p>
<ul>
<li><b>Message Type:</b> Select the type of message (Text, Image, Video, Document, etc.)</li>
<li><b>Message Text:</b> The main message content to send</li>
<li><b>Use Spintax:</b> Enable to use {option1|option2|option3} syntax for message variations</li>
<li><b>Media File:</b> Path to media file (for non-text messages)</li>
<li><b>Caption:</b> Caption for media messages</li>
</ul>

<p><b>A/B Testing:</b></p>
<ul>
<li><b>Enable A/B Testing:</b> Test different message variants</li>
<li><b>Variants:</b> Enter different message versions (one per line)</li>
</ul>

<h3>Scheduling Tab</h3>
<p><b>Start Time:</b> When the campaign should begin (for scheduled campaigns)</p>
<p><b>Timezone:</b> Timezone for the start time</p>

<p><b>Rate Limiting:</b></p>
<ul>
<li><b>Messages per Minute:</b> Maximum messages to send per minute</li>
<li><b>Messages per Hour:</b> Maximum messages to send per hour</li>
<li><b>Messages per Day:</b> Maximum messages to send per day</li>
<li><b>Random Jitter:</b> Random delay between messages (in seconds)</li>
</ul>

<p><b>Safety Settings:</b></p>
<ul>
<li><b>Dry Run:</b> Test mode - logs messages without actually sending them</li>
<li><b>Respect Rate Limits:</b> Follow the rate limiting settings</li>
<li><b>Stop on Error:</b> Stop campaign if errors occur</li>
<li><b>Max Retries:</b> Number of retry attempts for failed messages</li>
</ul>

<h3>Recipients Tab</h3>
<p><b>Recipient Source:</b></p>
<ul>
<li><b>Manual:</b> Enter recipients manually (one per line)</li>
<li><b>CSV Import:</b> Import recipients from a CSV file</li>
</ul>

<p><b>Recipient Formats:</b></p>
<ul>
<li>Usernames: @username</li>
<li>Phone numbers: +1234567890</li>
<li>User IDs: 123456789</li>
</ul>

<p><b>CSV Format:</b></p>
<p>username,phone_number,first_name,last_name</p>
<p>Example: john_doe,+1234567890,John,Doe</p>

<h3>Tips</h3>
<ul>
<li>Use Dry Run mode to test campaigns before sending</li>
<li>Start with low rate limits to avoid being flagged as spam</li>
<li>Use Spintax to create message variations and avoid repetition</li>
<li>A/B testing helps optimize message performance</li>
<li>Always respect Telegram's terms of service and rate limits</li>
</ul>
        """
        
        # Create a custom message box with HTML support
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Campaign Help")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(help_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        
        # Center the message box on the dialog
        msg_box.setGeometry(
            self.x() + (self.width() - 600) // 2,
            self.y() + (self.height() - 400) // 2,
            600, 400
        )
        
        msg_box.exec_()
    
    def load_campaign_data(self):
        """Load campaign data into the form."""
        if not self.campaign:
            return
        
        self.name_edit.setText(self.campaign.name)
        self.description_edit.setText(self.campaign.description or "")
        self.campaign_type_combo.setCurrentText(self.campaign.campaign_type.value.title())
        
        # Message content
        self.message_type_combo.setCurrentText(self.campaign.message_type.value.title())
        self.message_text_edit.setText(self.campaign.message_text)
        self.use_spintax_check.setChecked(self.campaign.use_spintax)
        self.media_path_edit.setText(self.campaign.media_path or "")
        self.caption_edit.setText(self.campaign.caption or "")
        
        # A/B testing
        self.use_ab_testing_check.setChecked(self.campaign.use_ab_testing)
        variants = self.campaign.get_ab_variants_list()
        if variants:
            variants_text = "\n".join([v.get("text", "") for v in variants])
            self.ab_variants_edit.setText(variants_text)
        
        # Scheduling
        if self.campaign.start_time:
            self.start_time_edit.setDateTime(self.campaign.start_time)
        self.timezone_combo.setCurrentText(self.campaign.timezone)
        
        # Rate limiting
        self.messages_per_minute_spin.setValue(self.campaign.messages_per_minute)
        self.messages_per_hour_spin.setValue(self.campaign.messages_per_hour)
        self.messages_per_day_spin.setValue(self.campaign.messages_per_day)
        self.random_jitter_spin.setValue(self.campaign.random_jitter_seconds)
        
        # Safety settings
        self.dry_run_check.setChecked(self.campaign.dry_run)
        self.respect_rate_limits_check.setChecked(self.campaign.respect_rate_limits)
        self.stop_on_error_check.setChecked(self.campaign.stop_on_error)
        self.max_retries_spin.setValue(self.campaign.max_retries)
        
        # Recipients
        self.recipient_count_label.setText(f"{self.campaign.total_recipients} recipients")
    
    def save_campaign(self):
        """Save campaign data."""
        try:
            # Validate required fields
            if not self.name_edit.text().strip():
                QMessageBox.warning(self, _("common.error"), _("campaigns.name_required"))
                return
            
            if not self.message_text_edit.toPlainText().strip():
                QMessageBox.warning(self, _("common.error"), _("campaigns.message_required"))
                return
            
            # Create or update campaign
            if self.campaign:
                # Update existing campaign
                self.campaign.name = self.name_edit.text().strip()
                self.campaign.description = self.description_edit.toPlainText().strip() or None
                self.campaign.campaign_type = CampaignType(self.campaign_type_combo.currentText().lower())
            else:
                # Create new campaign
                self.campaign = Campaign(
                    name=self.name_edit.text().strip(),
                    description=self.description_edit.toPlainText().strip() or None,
                    campaign_type=CampaignType(self.campaign_type_combo.currentText().lower()),
                    message_text=self.message_text_edit.toPlainText().strip(),
                    total_recipients=0  # Will be updated when recipients are added
                )
            
            # Update message content
            self.campaign.message_type = MessageType(self.message_type_combo.currentText().lower())
            self.campaign.message_text = self.message_text_edit.toPlainText().strip()
            self.campaign.use_spintax = self.use_spintax_check.isChecked()
            self.campaign.media_path = self.media_path_edit.text().strip() or None
            self.campaign.caption = self.caption_edit.text().strip() or None
            
            # Update A/B testing
            self.campaign.use_ab_testing = self.use_ab_testing_check.isChecked()
            if self.campaign.use_ab_testing:
                variants_text = self.ab_variants_edit.toPlainText().strip()
                if variants_text:
                    variants = [{"text": line.strip()} for line in variants_text.split('\n') if line.strip()]
                    self.campaign.set_ab_variants_list(variants)
            
            # Update scheduling
            self.campaign.start_time = self.start_time_edit.dateTime().toPyDateTime()
            self.campaign.timezone = self.timezone_combo.currentText()
            
            # Update rate limiting
            self.campaign.messages_per_minute = self.messages_per_minute_spin.value()
            self.campaign.messages_per_hour = self.messages_per_hour_spin.value()
            self.campaign.messages_per_day = self.messages_per_day_spin.value()
            self.campaign.random_jitter_seconds = self.random_jitter_spin.value()
            
            # Update safety settings
            self.campaign.dry_run = self.dry_run_check.isChecked()
            self.campaign.respect_rate_limits = self.respect_rate_limits_check.isChecked()
            self.campaign.stop_on_error = self.stop_on_error_check.isChecked()
            self.campaign.max_retries = self.max_retries_spin.value()
            
            # Update recipients count based on source
            self.campaign.recipient_source = self.recipient_source_combo.currentText().lower().replace(" ", "_")
            
            if self.recipient_source_combo.currentText() == "Manual":
                manual_recipients = self.manual_recipients_edit.toPlainText().strip()
                if manual_recipients:
                    lines = [line.strip() for line in manual_recipients.split('\n') if line.strip()]
                    self.campaign.total_recipients = len(lines)
                else:
                    self.campaign.total_recipients = 0
            elif self.recipient_source_combo.currentText() == "CSV Import":
                csv_file = self.csv_file_edit.text().strip()
                if csv_file:
                    try:
                        import csv
                        recipient_count = 0
                        with open(csv_file, 'r', encoding='utf-8') as file:
                            csv_reader = csv.reader(file)
                            for row in csv_reader:
                                if row and any(cell.strip() for cell in row):
                                    recipient_count += 1
                        self.campaign.total_recipients = recipient_count
                    except Exception as e:
                        QMessageBox.warning(self, "CSV Import Error", f"Error reading CSV file: {e}")
                        self.campaign.total_recipients = 0
                else:
                    self.campaign.total_recipients = 0
            
            # Save to database
            session = get_session()
            try:
                if self.campaign.id is None:
                    session.add(self.campaign)
                else:
                    session.merge(self.campaign)
                session.commit()
                
                # Get the saved campaign ID before closing session
                campaign_id = self.campaign.id
                campaign_name = self.campaign.name
            finally:
                session.close()
            
            self.logger.info(f"Campaign saved: {campaign_name}")
            self.campaign_saved.emit(campaign_id)
            self.accept()
            
        except Exception as e:
            self.logger.error(f"Error saving campaign: {e}")
            QMessageBox.critical(self, _("common.error"), _("campaigns.save_failed").format(error=str(e)))


class CampaignListWidget(QWidget):
    """Widget for displaying and managing campaigns."""
    
    campaign_selected = pyqtSignal(int)
    campaign_updated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.campaign_manager = get_campaign_manager()
        self.translation_manager = get_translation_manager()
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        self.setup_ui()
        self.load_campaigns()
        
        # Connect campaign manager signals
        self.campaign_manager.campaign_started.connect(self.on_campaign_started)
        self.campaign_manager.campaign_paused.connect(self.on_campaign_paused)
        self.campaign_manager.campaign_stopped.connect(self.on_campaign_stopped)
        self.campaign_manager.campaign_completed.connect(self.on_campaign_completed)
        self.campaign_manager.campaign_progress_updated.connect(self.on_campaign_progress_updated)
        self.campaign_manager.campaign_error.connect(self.on_campaign_error)
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_campaigns)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Campaigns")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.create_button = QPushButton(_("campaigns.create_campaign"))
        self.create_button.clicked.connect(self.create_campaign)
        header_layout.addWidget(self.create_button)
        
        self.edit_button = QPushButton(_("campaigns.edit_campaign"))
        self.edit_button.clicked.connect(self.edit_campaign)
        self.edit_button.setEnabled(False)
        header_layout.addWidget(self.edit_button)
        
        self.start_button = QPushButton(_("common.start"))
        self.start_button.clicked.connect(self.start_campaign)
        self.start_button.setEnabled(False)
        header_layout.addWidget(self.start_button)
        
        self.retry_button = QPushButton(_("common.retry"))
        self.retry_button.clicked.connect(self.retry_campaign)
        self.retry_button.setEnabled(False)
        self.retry_button.setStyleSheet("QPushButton { background-color: #f59e0b; color: white; }")
        header_layout.addWidget(self.retry_button)
        
        self.duplicate_button = QPushButton(_("campaigns.duplicate_campaign"))
        self.duplicate_button.clicked.connect(self.duplicate_campaign)
        self.duplicate_button.setEnabled(False)
        self.duplicate_button.setStyleSheet("QPushButton { background-color: #8b5cf6; color: white; }")
        header_layout.addWidget(self.duplicate_button)
        
        self.pause_button = QPushButton(_("common.pause"))
        self.pause_button.clicked.connect(self.pause_campaign)
        self.pause_button.setEnabled(False)
        header_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton(_("common.stop"))
        self.stop_button.clicked.connect(self.stop_campaign)
        self.stop_button.setEnabled(False)
        header_layout.addWidget(self.stop_button)
        
        self.delete_button = QPushButton(_("common.delete"))
        self.delete_button.clicked.connect(self.delete_campaign)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)
        
        self.refresh_button = QPushButton(_("common.refresh"))
        self.refresh_button.clicked.connect(self.refresh_campaigns)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Search field
        search_layout = QHBoxLayout()
        search_label = QLabel(_("common.search") + ":")
        search_label.setStyleSheet("color: white; font-weight: bold;")
        search_layout.addWidget(search_label)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(_("campaigns.search_placeholder"))
        self.search_edit.textChanged.connect(self.filter_campaigns)
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
        
        # Campaigns table
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(9)
        self.campaigns_table.setHorizontalHeaderLabels([
            _("common.name"), _("common.status"), _("campaigns.recipients"), _("common.sent"), _("common.failed"), _("common.progress"), 
            _("campaigns.start_time"), _("campaigns.last_activity"), _("common.actions")
        ])
        
        # Configure table
        header = self.campaigns_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)
        
        self.campaigns_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.campaigns_table.setSelectionMode(QTableWidget.SingleSelection)
        self.campaigns_table.setAlternatingRowColors(True)
        self.campaigns_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Set custom styling for black and gray alternating rows
        self.campaigns_table.setStyleSheet("""
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
        self.campaigns_table.cellClicked.connect(self.on_cell_clicked)
        
        layout.addWidget(self.campaigns_table)
        
        # Status bar
        self.status_label = QLabel(_("campaigns.ready"))
        layout.addWidget(self.status_label)
    
    def load_campaigns(self):
        """Load campaigns from database."""
        try:
            session = get_session()
            try:
                from ...models import Campaign
                from sqlmodel import select
                campaigns = session.exec(select(Campaign).where(Campaign.is_deleted == False)).all()
            finally:
                session.close()
            
            self.campaigns_table.setRowCount(len(campaigns))
            
            for row, campaign in enumerate(campaigns):
                # Name - Disabled text field
                name_item = QTableWidgetItem(campaign.name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                # Store campaign ID in the name item for selection handling
                name_item.setData(Qt.UserRole, campaign.id)
                self.campaigns_table.setItem(row, 0, name_item)
                
                # Status - Enhanced button-like appearance
                status_item = QTableWidgetItem(campaign.status.value.title())
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                
                # Set status-specific styling with button-like appearance
                if campaign.status == CampaignStatus.RUNNING:
                    status_item.setBackground(QColor(34, 197, 94))  # Green
                    status_item.setForeground(Qt.white)
                elif campaign.status == CampaignStatus.PAUSED:
                    status_item.setBackground(QColor(245, 158, 11))  # Orange
                    status_item.setForeground(Qt.white)
                elif campaign.status == CampaignStatus.COMPLETED:
                    status_item.setBackground(QColor(59, 130, 246))  # Blue
                    status_item.setForeground(Qt.white)
                elif campaign.status == CampaignStatus.ERROR:
                    status_item.setBackground(QColor(239, 68, 68))  # Red
                    status_item.setForeground(Qt.white)
                elif campaign.status == CampaignStatus.DRAFT:
                    status_item.setBackground(QColor(107, 114, 128))  # Gray
                    status_item.setForeground(Qt.white)
                
                # Center align status text
                status_item.setTextAlignment(Qt.AlignCenter)
                self.campaigns_table.setItem(row, 1, status_item)
                
                # Recipients - Disabled text field
                recipients_item = QTableWidgetItem(str(campaign.total_recipients))
                recipients_item.setFlags(recipients_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                recipients_item.setTextAlignment(Qt.AlignCenter)
                self.campaigns_table.setItem(row, 2, recipients_item)
                
                # Sent - Disabled text field
                sent_item = QTableWidgetItem(str(campaign.sent_count))
                sent_item.setFlags(sent_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                sent_item.setTextAlignment(Qt.AlignCenter)
                self.campaigns_table.setItem(row, 3, sent_item)
                
                # Failed - Disabled text field
                failed_item = QTableWidgetItem(str(campaign.failed_count))
                failed_item.setFlags(failed_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                failed_item.setTextAlignment(Qt.AlignCenter)
                self.campaigns_table.setItem(row, 4, failed_item)
                
                # Progress - Disabled text field
                progress = f"{campaign.progress_percentage:.1f}%"
                progress_item = QTableWidgetItem(progress)
                progress_item.setFlags(progress_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                progress_item.setTextAlignment(Qt.AlignCenter)
                self.campaigns_table.setItem(row, 5, progress_item)
                
                # Start time - Disabled text field
                start_time = campaign.start_time.strftime("%Y-%m-%d %H:%M") if campaign.start_time else _("campaigns.not_scheduled")
                start_item = QTableWidgetItem(start_time)
                start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                start_item.setTextAlignment(Qt.AlignCenter)
                self.campaigns_table.setItem(row, 6, start_item)
                
                # Last activity - Disabled text field
                last_activity = campaign.last_activity.strftime("%Y-%m-%d %H:%M") if campaign.last_activity else _("campaigns.never")
                activity_item = QTableWidgetItem(last_activity)
                activity_item.setFlags(activity_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                activity_item.setTextAlignment(Qt.AlignCenter)
                self.campaigns_table.setItem(row, 7, activity_item)
                
                # Actions - Create action buttons based on status
                actions = []
                is_running = self.campaign_manager.is_campaign_running(campaign.id)
                
                # Status-based action logic according to specifications
                if campaign.status == CampaignStatus.COMPLETED:
                    actions.append(_("campaigns.duplicate_campaign"))
                elif campaign.status in [CampaignStatus.FAILED, CampaignStatus.INCOMPLETED]:
                    actions.append(_("common.retry"))
                elif campaign.status == CampaignStatus.ERROR:
                    actions.append(_("common.retry"))
                elif campaign.status == CampaignStatus.DRAFT:
                    if campaign.total_recipients > 0:
                        actions.append(_("common.start"))  # Only for DRAFT with recipients
                    else:
                        actions.append(_("campaigns.assign_recipients"))  # For DRAFT without recipients
                elif campaign.status == CampaignStatus.SCHEDULED:
                    # No actions for SCHEDULED (will start automatically)
                    pass
                elif campaign.status == CampaignStatus.RUNNING:
                    actions.append(_("common.pause"))  # Only for RUNNING
                    actions.append(_("common.stop"))   # Only for RUNNING
                elif campaign.status == CampaignStatus.PAUSED:
                    actions.append(_("common.start"))  # Only for PAUSED
                    actions.append(_("common.resume")) # Only for PAUSED
                elif campaign.status == CampaignStatus.STOPPED:
                    actions.append(_("common.retry"))  # Only for STOPPED
                
                actions_text = " | ".join(actions) if actions else _("campaigns.no_actions")
                actions_item = QTableWidgetItem(actions_text)
                actions_item.setFlags(actions_item.flags() & ~Qt.ItemIsEditable | Qt.ItemIsSelectable)
                actions_item.setTextAlignment(Qt.AlignCenter)
                actions_item.setData(Qt.UserRole, campaign.id)  # Store campaign ID for actions
                self.campaigns_table.setItem(row, 8, actions_item)
            
            self.status_label.setText(_("campaigns.loaded_campaigns").format(count=len(campaigns)))
            
            # Apply search filter if there's search text
            self.filter_campaigns()
            
        except Exception as e:
            self.logger.error(f"Error loading campaigns: {e}")
            self.status_label.setText(_("campaigns.error_loading_campaigns").format(error=str(e)))
    
    def update_button_states(self):
        """Update button states based on selected campaign."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        if not selected_rows:
            # No selection - disable all action buttons
            self.start_button.setEnabled(False)
            self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.retry_button.setEnabled(False)
            self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.duplicate_button.setEnabled(False)
            self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.pause_button.setEnabled(False)
            self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            return
        
        row = selected_rows[0].row()
        campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
        
        if not campaign_id:
            self.start_button.setEnabled(False)
            self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.retry_button.setEnabled(False)
            self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.duplicate_button.setEnabled(False)
            self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.pause_button.setEnabled(False)
            self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            return
        
        # Get campaign from database
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    self.start_button.setEnabled(False)
                    self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(False)
                    self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(False)
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.stop_button.setEnabled(False)
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    return
                
                # Update button states based on campaign status
                is_running = self.campaign_manager.is_campaign_running(campaign_id)
                can_retry = self.campaign_manager.can_retry_campaign(campaign_id)
                
                # Status-based button enabling according to specifications
                if campaign.status == CampaignStatus.COMPLETED:
                    self.start_button.setEnabled(False)
                    self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(False)
                    self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.duplicate_button.setEnabled(True)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #8b5cf6; color: white; }")  # Purple
                    self.pause_button.setEnabled(False)
                    self.pause_button.setText(_("common.pause"))  # Reset text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.stop_button.setEnabled(False)
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                elif campaign.status in [CampaignStatus.FAILED, CampaignStatus.INCOMPLETED]:
                    self.start_button.setEnabled(False)
                    self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(True)
                    self.retry_button.setStyleSheet("QPushButton { background-color: #f59e0b; color: white; }")  # Yellow/Orange
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(False)
                    self.pause_button.setText(_("common.pause"))  # Reset text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.stop_button.setEnabled(False)
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                elif campaign.status == CampaignStatus.ERROR:
                    self.start_button.setEnabled(False)
                    self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(True)
                    self.retry_button.setStyleSheet("QPushButton { background-color: #f59e0b; color: white; }")  # Yellow/Orange
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(False)
                    self.pause_button.setText(_("common.pause"))  # Reset text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.stop_button.setEnabled(False)
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                elif campaign.status == CampaignStatus.DRAFT:
                    if campaign.total_recipients > 0:
                        self.start_button.setEnabled(True)  # Only for DRAFT with recipients
                        self.start_button.setStyleSheet("QPushButton { background-color: #3b82f6; color: white; }")  # Blue
                    else:
                        self.start_button.setEnabled(False)  # Disabled for DRAFT without recipients
                        self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(False)  # Never for DRAFT
                    self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(False)
                    self.pause_button.setText(_("common.pause"))  # Reset text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.stop_button.setEnabled(False)
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                elif campaign.status == CampaignStatus.SCHEDULED:
                    self.start_button.setEnabled(False)  # Not for SCHEDULED
                    self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(False)  # Not for SCHEDULED
                    self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(False)
                    self.pause_button.setText(_("common.pause"))  # Reset text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.stop_button.setEnabled(False)
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                elif campaign.status == CampaignStatus.RUNNING:
                    self.start_button.setEnabled(False)  # Not for RUNNING
                    self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(False)  # Not for RUNNING
                    self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(True)  # Only for RUNNING
                    self.pause_button.setText(_("common.pause"))  # Pause text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: white; }")  # Gray
                    self.stop_button.setEnabled(True)  # Only for RUNNING
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: white; }")  # Gray
                elif campaign.status == CampaignStatus.PAUSED:
                    self.start_button.setEnabled(True)  # Only for PAUSED
                    self.start_button.setStyleSheet("QPushButton { background-color: #3b82f6; color: white; }")  # Blue
                    self.retry_button.setEnabled(False)  # Not for PAUSED
                    self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(True)  # Only for PAUSED
                    self.pause_button.setText(_("common.resume"))  # Resume text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #10b981; color: white; }")  # Green
                    self.stop_button.setEnabled(False)  # Not for PAUSED
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                elif campaign.status == CampaignStatus.STOPPED:
                    self.start_button.setEnabled(False)  # Not for STOPPED
                    self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(True)  # Only for STOPPED
                    self.retry_button.setStyleSheet("QPushButton { background-color: #f59e0b; color: white; }")  # Yellow/Orange
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(False)
                    self.pause_button.setText(_("common.pause"))  # Reset text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.stop_button.setEnabled(False)  # Not for STOPPED
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                else:
                    # For any other statuses, disable all action buttons
                    self.start_button.setEnabled(False)
                    self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.retry_button.setEnabled(False)
                    self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.duplicate_button.setEnabled(False)
                    self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.pause_button.setEnabled(False)
                    self.pause_button.setText(_("common.pause"))  # Reset text
                    self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                    self.stop_button.setEnabled(False)
                    self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
                
        except Exception as e:
            self.logger.error(f"Error updating button states: {e}")
            self.start_button.setEnabled(False)
            self.start_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.retry_button.setEnabled(False)
            self.retry_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.duplicate_button.setEnabled(False)
            self.duplicate_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.pause_button.setEnabled(False)
            self.pause_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
            self.stop_button.setEnabled(False)
            self.stop_button.setStyleSheet("QPushButton { background-color: #6b7280; color: #9ca3af; }")  # Gray
    
    def refresh_campaigns(self):
        """Refresh campaigns data."""
        self.load_campaigns()
    
    def filter_campaigns(self):
        """Filter campaigns based on search text."""
        search_text = self.search_edit.text().lower().strip()
        
        if not search_text:
            # Show all campaigns
            for row in range(self.campaigns_table.rowCount()):
                self.campaigns_table.setRowHidden(row, False)
            return
        
        # Filter campaigns (exclude Actions column - column 8)
        for row in range(self.campaigns_table.rowCount()):
            should_show = False
            
            # Check all columns except Actions column for search text
            for col in range(self.campaigns_table.columnCount() - 1):  # Exclude last column (Actions)
                item = self.campaigns_table.item(row, col)
                if item and search_text in item.text().lower():
                    should_show = True
                    break
            
            self.campaigns_table.setRowHidden(row, not should_show)
    
    def on_cell_clicked(self, row, column):
        """Handle cell click events."""
        if column == 8:  # Actions column
            campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
            if campaign_id is not None:
                self.show_action_menu(row, column, campaign_id)
        else:
            # For other columns, ensure the row is selected
            self.campaigns_table.selectRow(row)
            # Also trigger selection changed manually
            self.on_selection_changed()
    
    def show_action_menu(self, row, column, campaign_id):
        """Show action menu for campaign actions."""
        from PyQt5.QtWidgets import QMenu
        
        # Get campaign name for display
        campaign_name = self.campaigns_table.item(row, 0).text()
        
        # Create context menu
        menu = QMenu(self)
        
        # Get available actions
        session = get_session()
        try:
            from ...models import Campaign
            from sqlmodel import select
            campaign = session.exec(select(Campaign).where(Campaign.id == campaign_id)).first()
        finally:
            session.close()
        
        if campaign:
            # Status-based action menu logic (matching the table actions)
            if campaign.status == CampaignStatus.COMPLETED:
                duplicate_action = menu.addAction("📋 Duplicate Campaign")
                duplicate_action.triggered.connect(lambda: self.duplicate_campaign_by_id(campaign_id))
            elif campaign.status in [CampaignStatus.FAILED, CampaignStatus.INCOMPLETED, CampaignStatus.ERROR]:
                retry_action = menu.addAction("🔄 Retry")
                retry_action.triggered.connect(lambda: self.retry_campaign_by_id(campaign_id))
            elif campaign.status == CampaignStatus.DRAFT:
                if campaign.total_recipients > 0:
                    start_action = menu.addAction("▶️ Start")
                    start_action.triggered.connect(lambda: self.start_campaign_by_id(campaign_id))
                else:
                    assign_action = menu.addAction("👥 Assign Recipients")
                    assign_action.triggered.connect(lambda: self.edit_campaign())
            elif campaign.status == CampaignStatus.SCHEDULED:
                # No actions for SCHEDULED (will start automatically)
                pass
            elif campaign.status == CampaignStatus.RUNNING:
                pause_action = menu.addAction("⏸️ Pause")
                pause_action.triggered.connect(lambda: self.pause_campaign_by_id(campaign_id))
                stop_action = menu.addAction("⏹️ Stop")
                stop_action.triggered.connect(lambda: self.stop_campaign_by_id(campaign_id))
            elif campaign.status == CampaignStatus.PAUSED:
                start_action = menu.addAction("▶️ Start")
                start_action.triggered.connect(lambda: self.start_campaign_by_id(campaign_id))
                resume_action = menu.addAction("▶️ Resume")
                resume_action.triggered.connect(lambda: self.resume_campaign_by_id(campaign_id))
            elif campaign.status == CampaignStatus.STOPPED:
                retry_action = menu.addAction("🔄 Retry")
                retry_action.triggered.connect(lambda: self.retry_campaign_by_id(campaign_id))
        
        # Show menu at cursor position
        menu.exec_(self.campaigns_table.mapToGlobal(
            self.campaigns_table.visualItemRect(self.campaigns_table.item(row, column)).bottomLeft()
        ))
    
    def start_campaign_by_id(self, campaign_id):
        """Start campaign by ID."""
        try:
            # Check if campaign is already running
            if self.campaign_manager.is_campaign_running(campaign_id):
                QMessageBox.warning(self, _("campaigns.already_running"), _("campaigns.already_running_message"))
                return
            
            # Start the campaign
            success = self.campaign_manager.start_campaign(campaign_id)
            if success:
                QMessageBox.information(self, _("campaigns.start_campaign"), _("campaigns.campaign_started_successfully"))
                self.load_campaigns()  # Refresh the campaigns list
            else:
                QMessageBox.warning(self, _("campaigns.start_failed"), _("campaigns.campaign_start_failed"))
        except Exception as e:
            QMessageBox.critical(self, _("campaigns.error"), f"Error starting campaign: {str(e)}")
    
    def retry_campaign_by_id(self, campaign_id):
        """Retry campaign by ID."""
        try:
            # Check if campaign can be retried
            if not self.campaign_manager.can_retry_campaign(campaign_id):
                QMessageBox.information(
                    self, 
                    _("campaigns.no_retry_needed"), 
                    _("campaigns.no_retry_needed_message")
                )
                return
            
            # Retry the campaign
            success = self.campaign_manager.retry_campaign(campaign_id)
            if success:
                QMessageBox.information(self, _("campaigns.retry_campaign"), _("campaigns.campaign_retry_successful"))
                self.load_campaigns()  # Refresh the campaigns list
            else:
                QMessageBox.warning(self, _("campaigns.retry_failed"), _("campaigns.campaign_retry_failed"))
        except Exception as e:
            QMessageBox.critical(self, _("campaigns.error"), f"Error retrying campaign: {str(e)}")
    
    def duplicate_campaign_by_id(self, campaign_id):
        """Duplicate campaign by ID."""
        # Check if campaign is completed
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    QMessageBox.warning(self, _("campaigns.campaign_not_found"), _("campaigns.campaign_not_found_message"))
                    return
                
                if campaign.status != CampaignStatus.COMPLETED:
                    QMessageBox.warning(
                        self, 
                        _("campaigns.cannot_duplicate"), 
                        _("campaigns.cannot_duplicate_message").format(status=campaign.status.value.title())
                    )
                    return
        
        except Exception as e:
            self.logger.error(f"Error checking campaign status: {e}")
            QMessageBox.warning(self, _("campaigns.error_checking_status"), _("campaigns.error_checking_status_message"))
            return
        
        # Confirm duplication
        reply = QMessageBox.question(
            self, 
            _("campaigns.duplicate_campaign"), 
            _("campaigns.duplicate_campaign_message").format(name=campaign.name),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Duplicate the campaign
            new_campaign_id = self.campaign_manager.duplicate_campaign(campaign_id)
            if new_campaign_id:
                QMessageBox.information(
                    self, 
                    _("campaigns.campaign_duplicated"), 
                    _("campaigns.campaign_duplicated_message").format(id=new_campaign_id)
                )
                self.refresh_campaigns()
            else:
                QMessageBox.warning(self, _("campaigns.duplication_failed"), _("campaigns.duplication_failed_message"))
    
    def pause_campaign_by_id(self, campaign_id):
        """Pause campaign by ID."""
        try:
            success = self.campaign_manager.pause_campaign(campaign_id)
            if success:
                QMessageBox.information(self, _("campaigns.pause_campaign"), _("campaigns.campaign_paused_successfully"))
                self.load_campaigns()  # Refresh the campaigns list
            else:
                QMessageBox.warning(self, _("campaigns.pause_failed"), _("campaigns.campaign_pause_failed"))
        except Exception as e:
            QMessageBox.critical(self, _("campaigns.error"), f"Error pausing campaign: {str(e)}")
    
    def resume_campaign_by_id(self, campaign_id):
        """Resume campaign by ID."""
        try:
            success = self.campaign_manager.resume_campaign(campaign_id)
            if success:
                QMessageBox.information(self, _("campaigns.resume_campaign"), _("campaigns.campaign_resumed_successfully"))
                self.load_campaigns()  # Refresh the campaigns list
            else:
                QMessageBox.warning(self, _("campaigns.resume_failed"), _("campaigns.campaign_resume_failed"))
        except Exception as e:
            QMessageBox.critical(self, _("campaigns.error"), f"Error resuming campaign: {str(e)}")
    
    def stop_campaign_by_id(self, campaign_id):
        """Stop campaign by ID."""
        try:
            success = self.campaign_manager.stop_campaign(campaign_id)
            if success:
                QMessageBox.information(self, _("campaigns.stop_campaign"), _("campaigns.campaign_stopped_successfully"))
                self.load_campaigns()  # Refresh the campaigns list
            else:
                QMessageBox.warning(self, _("campaigns.stop_failed"), _("campaigns.campaign_stop_failed"))
        except Exception as e:
            QMessageBox.critical(self, _("campaigns.error"), f"Error stopping campaign: {str(e)}")
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        # Update action button states
        self.update_button_states()
        
        if has_selection:
            row = selected_rows[0].row()
            # Try to get campaign ID from the first column (Name column)
            name_item = self.campaigns_table.item(row, 0)
            if name_item:
                campaign_id = name_item.data(Qt.UserRole)
                if campaign_id is not None:
                    # Emit signal with campaign ID for further processing
                    self.campaign_selected.emit(campaign_id)
                    
                    # Load campaign to check available actions
                    session = get_session()
                    try:
                        from ...models import Campaign
                        from sqlmodel import select
                        campaign = session.exec(select(Campaign).where(Campaign.id == campaign_id)).first()
                    finally:
                        session.close()
                    
                    if campaign:
                        self.start_button.setEnabled(campaign.can_start())
                        self.pause_button.setEnabled(campaign.can_pause())
                        self.stop_button.setEnabled(campaign.can_stop())
                else:
                    self.logger.warning(f"No campaign ID found for row {row}")
            else:
                self.logger.warning(f"No name item found for row {row}")
    
    def create_campaign(self):
        """Create new campaign."""
        dialog = CampaignDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_campaigns()
    
    def edit_campaign(self):
        """Edit selected campaign."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
        
        # Load campaign from database
        session = get_session()
        try:
            from ...models import Campaign
            from sqlmodel import select
            campaign = session.exec(select(Campaign).where(Campaign.id == campaign_id)).first()
        finally:
            session.close()
        
        if campaign:
            dialog = CampaignDialog(self, campaign)
            if dialog.exec_() == QDialog.Accepted:
                self.load_campaigns()
    
    def start_campaign(self):
        """Start selected campaign (or resume if paused)."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, _("campaigns.no_selection"), _("campaigns.no_selection_start"))
            return
        
        row = selected_rows[0].row()
        campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
        
        if not campaign_id:
            QMessageBox.warning(self, _("campaigns.invalid_campaign"), _("campaigns.invalid_campaign_message"))
            return
        
        # Get campaign status to determine action
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    QMessageBox.warning(self, _("campaigns.invalid_campaign"), _("campaigns.invalid_campaign_message"))
                    return
                
                if campaign.status == CampaignStatus.DRAFT:
                    if campaign.total_recipients > 0:
                        # Start the campaign
                        success = self.campaign_manager.start_campaign(campaign_id)
                        if success:
                            QMessageBox.information(self, _("campaigns.campaign_started"), _("campaigns.campaign_started_message"))
                            self.refresh_campaigns()
                        else:
                            QMessageBox.warning(self, _("campaigns.start_failed"), _("campaigns.start_failed_message"))
                    else:
                        # No recipients assigned - open edit dialog
                        QMessageBox.information(
                            self, 
                            _("campaigns.assign_recipients"), 
                            _("campaigns.assign_recipients_message")
                        )
                        self.edit_campaign()  # Open edit dialog to assign recipients
                elif campaign.status == CampaignStatus.PAUSED:
                    # Resume the campaign
                    success = self.campaign_manager.resume_campaign(campaign_id)
                    if success:
                        QMessageBox.information(self, _("campaigns.campaign_resumed"), _("campaigns.campaign_resumed_message"))
                        self.refresh_campaigns()
                    else:
                        QMessageBox.warning(self, _("campaigns.resume_failed"), _("campaigns.resume_failed_message"))
                else:
                    QMessageBox.warning(self, _("campaigns.invalid_action"), _("campaigns.invalid_action_message"))
                    
        except Exception as e:
            QMessageBox.critical(self, _("campaigns.error"), f"Error: {str(e)}")
    
    def retry_campaign(self):
        """Retry selected campaign (only failed messages or when recipients changed)."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, _("campaigns.no_selection"), _("campaigns.no_selection_retry"))
            return
        
        row = selected_rows[0].row()
        campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
        
        if not campaign_id:
            QMessageBox.warning(self, _("campaigns.invalid_campaign"), _("campaigns.invalid_campaign_message"))
            return
        
        # Check if campaign can be retried
        if not self.campaign_manager.can_retry_campaign(campaign_id):
            QMessageBox.information(
                self, 
                _("campaigns.no_retry_needed"), 
                _("campaigns.no_retry_needed_message")
            )
            return
        
        # Check if campaign is already running
        if self.campaign_manager.is_campaign_running(campaign_id):
            QMessageBox.information(self, _("campaigns.campaign_running"), _("campaigns.campaign_running_message"))
            return
        
        # Confirm retry action
        reply = QMessageBox.question(
            self, 
            _("campaigns.retry_campaign"), 
            _("campaigns.retry_campaign_message"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Start the campaign (retry logic is handled in start_campaign)
            success = self.campaign_manager.start_campaign(campaign_id)
            if success:
                QMessageBox.information(self, _("campaigns.campaign_retry_started"), _("campaigns.campaign_retry_started_message"))
                self.refresh_campaigns()
            else:
                QMessageBox.warning(self, _("campaigns.retry_failed"), _("campaigns.retry_failed_message"))
    
    def duplicate_campaign(self):
        """Duplicate selected completed campaign as a new draft campaign."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, _("campaigns.no_selection"), _("campaigns.no_selection_duplicate"))
            return
        
        row = selected_rows[0].row()
        campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
        
        if not campaign_id:
            QMessageBox.warning(self, _("campaigns.invalid_campaign"), _("campaigns.invalid_campaign_message"))
            return
        
        # Check if campaign is completed
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    QMessageBox.warning(self, _("campaigns.campaign_not_found"), _("campaigns.campaign_not_found_message"))
                    return
                
                if campaign.status != CampaignStatus.COMPLETED:
                    QMessageBox.warning(
                        self, 
                        _("campaigns.cannot_duplicate"), 
                        _("campaigns.cannot_duplicate_message").format(status=campaign.status.value.title())
                    )
                    return
        
        except Exception as e:
            self.logger.error(f"Error checking campaign status: {e}")
            QMessageBox.warning(self, _("campaigns.error_checking_status"), _("campaigns.error_checking_status_message"))
            return
        
        # Confirm duplication
        reply = QMessageBox.question(
            self, 
            _("campaigns.duplicate_campaign"), 
            _("campaigns.duplicate_campaign_message").format(name=campaign.name),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Duplicate the campaign
            new_campaign_id = self.campaign_manager.duplicate_campaign(campaign_id)
            if new_campaign_id:
                QMessageBox.information(
                    self, 
                    _("campaigns.campaign_duplicated"), 
                    _("campaigns.campaign_duplicated_message").format(id=new_campaign_id)
                )
                self.refresh_campaigns()
            else:
                QMessageBox.warning(self, _("campaigns.duplication_failed"), _("campaigns.duplication_failed_message"))
    
    def pause_campaign(self):
        """Pause or resume selected campaign based on current status."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, _("campaigns.no_selection"), _("campaigns.no_selection_pause"))
            return
        
        row = selected_rows[0].row()
        campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
        
        if not campaign_id:
            QMessageBox.warning(self, _("campaigns.invalid_campaign"), _("campaigns.invalid_campaign_message"))
            return
        
        # Get campaign status to determine action
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    QMessageBox.warning(self, _("campaigns.invalid_campaign"), _("campaigns.invalid_campaign_message"))
                    return
                
                if campaign.status == CampaignStatus.RUNNING:
                    # Pause the campaign
                    success = self.campaign_manager.pause_campaign(campaign_id)
                    if success:
                        QMessageBox.information(self, _("campaigns.campaign_paused"), _("campaigns.campaign_paused_message"))
                        self.refresh_campaigns()
                    else:
                        QMessageBox.warning(self, _("campaigns.pause_failed"), _("campaigns.pause_failed_message"))
                elif campaign.status == CampaignStatus.PAUSED:
                    # Resume the campaign
                    success = self.campaign_manager.resume_campaign(campaign_id)
                    if success:
                        QMessageBox.information(self, _("campaigns.campaign_resumed"), _("campaigns.campaign_resumed_message"))
                        self.refresh_campaigns()
                    else:
                        QMessageBox.warning(self, _("campaigns.resume_failed"), _("campaigns.resume_failed_message"))
                else:
                    QMessageBox.warning(self, _("campaigns.invalid_action"), _("campaigns.invalid_action_message"))
                    
        except Exception as e:
            QMessageBox.critical(self, _("campaigns.error"), f"Error: {str(e)}")
    
    def stop_campaign(self):
        """Stop selected campaign."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, _("campaigns.no_selection"), _("campaigns.no_selection_stop"))
            return
        
        row = selected_rows[0].row()
        campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
        
        if not campaign_id:
            QMessageBox.warning(self, _("campaigns.invalid_campaign"), _("campaigns.invalid_campaign_message"))
            return
        
        # Confirm stop action
        reply = QMessageBox.question(
            self, 
            "Stop Campaign", 
            "Are you sure you want to stop this campaign? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop the campaign
            success = self.campaign_manager.stop_campaign(campaign_id)
            if success:
                QMessageBox.information(self, _("campaigns.campaign_stopped"), _("campaigns.campaign_stopped_message"))
                self.refresh_campaigns()
            else:
                QMessageBox.warning(self, _("campaigns.stop_failed"), _("campaigns.stop_failed_message"))
    
    def on_campaign_started(self, campaign_id: int):
        """Handle campaign started signal."""
        self.logger.info(f"Campaign {campaign_id} started")
        self.refresh_campaigns()
    
    def on_campaign_paused(self, campaign_id: int):
        """Handle campaign paused signal."""
        self.logger.info(f"Campaign {campaign_id} paused")
        self.refresh_campaigns()
    
    def on_campaign_stopped(self, campaign_id: int):
        """Handle campaign stopped signal."""
        self.logger.info(f"Campaign {campaign_id} stopped")
        self.refresh_campaigns()
    
    def on_campaign_completed(self, campaign_id: int):
        """Handle campaign completed signal."""
        self.logger.info(f"Campaign {campaign_id} completed")
        self.refresh_campaigns()
    
    def on_campaign_progress_updated(self, campaign_id: int, progress_data: dict):
        """Handle campaign progress updated signal."""
        self.logger.debug(f"Campaign {campaign_id} progress: {progress_data}")
        self.refresh_campaigns()
    
    def on_campaign_error(self, campaign_id: int, error_message: str):
        """Handle campaign error signal."""
        self.logger.error(f"Campaign {campaign_id} error: {error_message}")
        QMessageBox.warning(self, "Campaign Error", f"Campaign {campaign_id} encountered an error:\n{error_message}")
        self.refresh_campaigns()
    
    def delete_campaign(self):
        """Delete selected campaign."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        campaign_name = self.campaigns_table.item(row, 0).text()
        campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, 
            "Delete Campaign", 
            f"Are you sure you want to delete campaign '{campaign_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                session = get_session()
                try:
                    from ...models import Campaign
                    from sqlmodel import select
                    campaign = session.exec(select(Campaign).where(Campaign.id == campaign_id)).first()
                    if campaign:
                        campaign.soft_delete()
                        session.commit()
                finally:
                    session.close()
                
                self.logger.info(f"Campaign deleted: {campaign_name}")
                self.load_campaigns()
                
            except Exception as e:
                self.logger.error(f"Error deleting campaign: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete campaign: {e}")
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Recreate the UI with new translations
        self.setup_ui()
        self.load_campaigns()


class CampaignWidget(QWidget):
    """Main campaign management widget."""
    
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
        
        # Campaign list
        self.campaign_list = CampaignListWidget()
        layout.addWidget(self.campaign_list)
        
        # Connect signals
        self.campaign_list.campaign_selected.connect(self.on_campaign_selected)
        self.campaign_list.campaign_updated.connect(self.on_campaign_updated)
    
    def on_campaign_selected(self, campaign_id):
        """Handle campaign selection."""
        # This could show campaign details in a side panel
        pass
    
    def on_campaign_updated(self, campaign_id):
        """Handle campaign update."""
        # Refresh the list
        self.campaign_list.refresh_campaigns()
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # The campaign_list widget will handle its own language change
        # No need to recreate the UI since it only contains the campaign_list
