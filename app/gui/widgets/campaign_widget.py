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
from PyQt5.QtGui import QFont, QIcon

from ...models import Campaign, CampaignStatus, CampaignType, MessageType
from ...services import get_logger, get_session
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
        self.setWindowTitle("Create Campaign" if not self.campaign else "Edit Campaign")
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
        info_group = QGroupBox("Campaign Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Campaign name")
        info_layout.addRow("Name:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Campaign description (optional)")
        info_layout.addRow("Description:", self.description_edit)
        
        self.campaign_type_combo = QComboBox()
        self.campaign_type_combo.addItems([ct.value.title() for ct in CampaignType])
        info_layout.addRow("Type:", self.campaign_type_combo)
        
        basic_layout.addWidget(info_group)
        
        # Message Content
        message_group = QGroupBox("Message Content")
        message_layout = QVBoxLayout(message_group)
        
        # Message type
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Message Type:"))
        self.message_type_combo = QComboBox()
        self.message_type_combo.addItems([mt.value.title() for mt in MessageType])
        type_layout.addWidget(self.message_type_combo)
        type_layout.addStretch()
        message_layout.addLayout(type_layout)
        
        # Message text
        message_layout.addWidget(QLabel("Message Text:"))
        self.message_text_edit = QTextEdit()
        self.message_text_edit.setMaximumHeight(120)
        self.message_text_edit.setPlaceholderText("Enter your message text here...\nUse {{first_name}} for personalization\nUse {option1|option2|option3} for spintax")
        message_layout.addWidget(self.message_text_edit)
        
        # Spintax controls
        spintax_layout = QHBoxLayout()
        self.use_spintax_check = QCheckBox("Use Spintax")
        self.use_spintax_check.toggled.connect(self.toggle_spintax)
        spintax_layout.addWidget(self.use_spintax_check)
        
        self.preview_spintax_button = QPushButton("Preview Spintax")
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
        self.recipient_source_combo.addItems(["Manual", "CSV Import", "Channel Scrape"])
        source_layout.addRow("Source:", self.recipient_source_combo)
        
        self.recipient_count_label = QLabel("0 recipients")
        source_layout.addRow("Total Recipients:", self.recipient_count_label)
        
        recipients_layout.addWidget(source_group)
        
        # Manual recipients
        manual_group = QGroupBox("Manual Recipients")
        manual_layout = QVBoxLayout(manual_group)
        
        self.manual_recipients_edit = QTextEdit()
        self.manual_recipients_edit.setMaximumHeight(150)
        self.manual_recipients_edit.setPlaceholderText("Enter recipients (one per line):\n@username1\n@username2\n+1234567890")
        manual_layout.addWidget(self.manual_recipients_edit)
        
        self.manual_recipients_edit.textChanged.connect(self.update_recipient_count)
        
        recipients_layout.addWidget(manual_group)
        
        tab_widget.addTab(recipients_tab, "Recipients")
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_campaign)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Initialize
        self.toggle_spintax(False)
        self.toggle_ab_testing(False)
        self.update_recipient_count()
    
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
            QMessageBox.information(self, "Preview", "No message text to preview")
            return
        
        try:
            samples = self.spintax_processor.get_preview_samples(text, 5)
            preview_text = "\n".join(samples)
            
            QMessageBox.information(
                self, 
                "Spintax Preview", 
                f"Here are 5 random samples:\n\n{preview_text}"
            )
        except Exception as e:
            QMessageBox.warning(self, "Preview Error", f"Error processing spintax: {e}")
    
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
                QMessageBox.warning(self, "Validation Error", "Campaign name is required")
                return
            
            if not self.message_text_edit.toPlainText().strip():
                QMessageBox.warning(self, "Validation Error", "Message text is required")
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
            
            # Update recipients count
            manual_recipients = self.manual_recipients_edit.toPlainText().strip()
            if manual_recipients:
                lines = [line.strip() for line in manual_recipients.split('\n') if line.strip()]
                self.campaign.total_recipients = len(lines)
            
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
            QMessageBox.critical(self, "Error", f"Failed to save campaign: {e}")


class CampaignListWidget(QWidget):
    """Widget for displaying and managing campaigns."""
    
    campaign_selected = pyqtSignal(int)
    campaign_updated = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_logger()
        self.setup_ui()
        self.load_campaigns()
        
        # Setup refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_campaigns)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds
    
    def setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Campaigns")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.create_button = QPushButton("Create Campaign")
        self.create_button.clicked.connect(self.create_campaign)
        header_layout.addWidget(self.create_button)
        
        self.edit_button = QPushButton("Edit Campaign")
        self.edit_button.clicked.connect(self.edit_campaign)
        self.edit_button.setEnabled(False)
        header_layout.addWidget(self.edit_button)
        
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_campaign)
        self.start_button.setEnabled(False)
        header_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_campaign)
        self.pause_button.setEnabled(False)
        header_layout.addWidget(self.pause_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_campaign)
        self.stop_button.setEnabled(False)
        header_layout.addWidget(self.stop_button)
        
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.delete_campaign)
        self.delete_button.setEnabled(False)
        header_layout.addWidget(self.delete_button)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_campaigns)
        header_layout.addWidget(self.refresh_button)
        
        layout.addLayout(header_layout)
        
        # Campaigns table
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(9)
        self.campaigns_table.setHorizontalHeaderLabels([
            "Name", "Status", "Recipients", "Sent", "Failed", "Progress", 
            "Start Time", "Last Activity", "Actions"
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
        self.campaigns_table.setAlternatingRowColors(True)
        self.campaigns_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.campaigns_table)
        
        # Status bar
        self.status_label = QLabel("Ready")
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
                # Name
                self.campaigns_table.setItem(row, 0, QTableWidgetItem(campaign.name))
                
                # Status
                status_item = QTableWidgetItem(campaign.status.value.title())
                if campaign.status == CampaignStatus.RUNNING:
                    status_item.setBackground(Qt.green)
                elif campaign.status == CampaignStatus.PAUSED:
                    status_item.setBackground(Qt.yellow)
                elif campaign.status == CampaignStatus.COMPLETED:
                    status_item.setBackground(Qt.blue)
                elif campaign.status == CampaignStatus.ERROR:
                    status_item.setBackground(Qt.red)
                self.campaigns_table.setItem(row, 1, status_item)
                
                # Recipients
                self.campaigns_table.setItem(row, 2, QTableWidgetItem(str(campaign.total_recipients)))
                
                # Sent
                self.campaigns_table.setItem(row, 3, QTableWidgetItem(str(campaign.sent_count)))
                
                # Failed
                self.campaigns_table.setItem(row, 4, QTableWidgetItem(str(campaign.failed_count)))
                
                # Progress
                progress = f"{campaign.progress_percentage:.1f}%"
                self.campaigns_table.setItem(row, 5, QTableWidgetItem(progress))
                
                # Start time
                start_time = campaign.start_time.strftime("%Y-%m-%d %H:%M") if campaign.start_time else "Not scheduled"
                self.campaigns_table.setItem(row, 6, QTableWidgetItem(start_time))
                
                # Last activity
                last_activity = campaign.last_activity.strftime("%Y-%m-%d %H:%M") if campaign.last_activity else "Never"
                self.campaigns_table.setItem(row, 7, QTableWidgetItem(last_activity))
                
                # Actions
                actions = []
                if campaign.can_start():
                    actions.append("Start")
                if campaign.can_pause():
                    actions.append("Pause")
                if campaign.can_resume():
                    actions.append("Resume")
                if campaign.can_stop():
                    actions.append("Stop")
                
                actions_item = QTableWidgetItem(" | ".join(actions))
                self.campaigns_table.setItem(row, 8, actions_item)
                
                # Store campaign ID in the first column for reference
                self.campaigns_table.item(row, 0).setData(Qt.UserRole, campaign.id)
            
            self.status_label.setText(f"Loaded {len(campaigns)} campaigns")
            
        except Exception as e:
            self.logger.error(f"Error loading campaigns: {e}")
            self.status_label.setText(f"Error loading campaigns: {e}")
    
    def refresh_campaigns(self):
        """Refresh campaigns data."""
        self.load_campaigns()
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_rows = self.campaigns_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        
        if has_selection:
            row = selected_rows[0].row()
            campaign_id = self.campaigns_table.item(row, 0).data(Qt.UserRole)
            
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
                
                self.campaign_selected.emit(campaign.id)
    
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
        """Start selected campaign."""
        # This would implement campaign starting logic
        QMessageBox.information(self, "Start Campaign", "Campaign starting functionality coming soon!")
    
    def pause_campaign(self):
        """Pause selected campaign."""
        # This would implement campaign pausing logic
        QMessageBox.information(self, "Pause Campaign", "Campaign pausing functionality coming soon!")
    
    def stop_campaign(self):
        """Stop selected campaign."""
        # This would implement campaign stopping logic
        QMessageBox.information(self, "Stop Campaign", "Campaign stopping functionality coming soon!")
    
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


class CampaignWidget(QWidget):
    """Main campaign management widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
