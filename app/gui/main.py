"""
Main window for the Telegram Multi-Account Message Sender.
"""

import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QStatusBar, QMenuBar,
    QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon

from ..services import get_settings, get_logger
from .theme import ThemeManager
from .widgets import AccountWidget, CampaignWidget, LogWidget, RecipientWidget, SettingsWidget
from .widgets.about_widget import AboutWidget


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        self.settings = get_settings()
        self.logger = get_logger()
        self.theme_manager = ThemeManager()
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Setup timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds
        
        # Initial status update
        self.update_status()
        
        self.logger.info("Main window initialized")
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Telegram Multi-Account Message Sender")
        self.setGeometry(100, 100, self.settings.window_width, self.settings.window_height)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_accounts_tab()
        self.create_campaigns_tab()
        self.create_templates_tab()
        self.create_recipients_tab()
        self.create_logs_tab()
        self.create_settings_tab()
        self.create_about_tab()
    
    def create_dashboard_tab(self):
        """Create dashboard tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Welcome message
        welcome_label = QLabel("Welcome to Telegram Multi-Account Message Sender")
        welcome_label.setStyleSheet("font-size: 16px; margin: 20px;")
        layout.addWidget(welcome_label)
        
        # Status overview
        status_label = QLabel("Status: Ready")
        status_label.setStyleSheet("font-size: 14px; margin: 10px;")
        layout.addWidget(status_label)
        
        # Quick actions
        actions_layout = QHBoxLayout()
        
        add_account_btn = QPushButton("Add Account")
        add_account_btn.clicked.connect(self.add_account)
        actions_layout.addWidget(add_account_btn)
        
        create_campaign_btn = QPushButton("Create Campaign")
        create_campaign_btn.clicked.connect(self.create_campaign)
        actions_layout.addWidget(create_campaign_btn)
        
        layout.addLayout(actions_layout)
        layout.addStretch()
        
        self.tab_widget.addTab(dashboard_widget, "Dashboard")
    
    def create_accounts_tab(self):
        """Create accounts management tab."""
        self.accounts_widget = AccountWidget()
        self.tab_widget.addTab(self.accounts_widget, "Accounts")
    
    def create_campaigns_tab(self):
        """Create campaigns management tab."""
        self.campaigns_widget = CampaignWidget()
        self.tab_widget.addTab(self.campaigns_widget, "Campaigns")
    
    def create_templates_tab(self):
        """Create templates management tab."""
        from .widgets.template_widget import TemplateWidget
        self.templates_widget = TemplateWidget()
        self.tab_widget.addTab(self.templates_widget, "Templates")
    
    def create_recipients_tab(self):
        """Create recipients management tab."""
        self.recipients_widget = RecipientWidget()
        self.tab_widget.addTab(self.recipients_widget, "Recipients")
    
    def create_logs_tab(self):
        """Create logs viewer tab."""
        self.logs_widget = LogWidget()
        self.tab_widget.addTab(self.logs_widget, "Logs")
    
    def create_settings_tab(self):
        """Create settings tab."""
        self.settings_widget = SettingsWidget()
        # Connect settings update signal to update status bar
        self.settings_widget.settings_updated.connect(self.on_settings_updated)
        self.tab_widget.addTab(self.settings_widget, "Settings")
    
    def create_about_tab(self):
        """Create about tab."""
        self.about_widget = AboutWidget()
        self.tab_widget.addTab(self.about_widget, "About")
    
    def setup_menu(self):
        """Set up menu bar."""
        # Menu bar removed as requested
        pass
    
    def setup_status_bar(self):
        """Set up status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("background-color: transparent;")
        self.status_bar.addWidget(self.status_label)
        
        # Theme label
        self.theme_label = QLabel(f"Theme: {self.theme_manager.get_current_theme()}")
        self.theme_label.setStyleSheet("background-color: transparent;")
        self.status_bar.addPermanentWidget(self.theme_label)
    
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        current = self.theme_manager.get_current_theme()
        if current == "light":
            self.set_theme("dark")
        else:
            self.set_theme("light")
    
    def set_theme(self, theme: str):
        """Set application theme."""
        self.theme_manager.apply_theme(theme)
        self.theme_label.setText(f"Theme: {self.theme_manager.get_current_theme()}")
    
    def add_account(self):
        """Add new account."""
        QMessageBox.information(self, "Add Account", "Account management coming soon!")
    
    def create_campaign(self):
        """Create new campaign."""
        QMessageBox.information(self, "Create Campaign", "Campaign management coming soon!")
    
    
    def on_settings_updated(self):
        """Handle settings update."""
        # Update theme label when settings change
        self.theme_label.setText(f"Theme: {self.theme_manager.get_current_theme()}")
        self.logger.info("Settings updated, status bar refreshed")
    
    def update_status(self):
        """Update status bar with current application status."""
        try:
            # Get current status information
            status_info = self.get_application_status()
            self.status_label.setText(status_info)
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
            self.status_label.setText("Error updating status")
    
    def get_application_status(self):
        """Get current application status information."""
        try:
            from ..services import get_session
            from ..models import Account, Campaign, Recipient
            
            session = get_session()
            try:
                # Count accounts
                from sqlmodel import select, func
                account_count = session.exec(select(func.count(Account.id)).where(Account.is_deleted == False)).first() or 0
                
                # Count campaigns
                campaign_count = session.exec(select(func.count(Campaign.id)).where(Campaign.is_deleted == False)).first() or 0
                
                # Count recipients
                recipient_count = session.exec(select(func.count(Recipient.id)).where(Recipient.is_deleted == False)).first() or 0
                
                # Get online accounts
                online_accounts = session.exec(
                    select(func.count(Account.id))
                    .where(Account.is_deleted == False)
                    .where(Account.status == "online")
                ).first() or 0
                
                # Build status message
                status_parts = []
                if account_count > 0:
                    status_parts.append(f"{account_count} account{'s' if account_count != 1 else ''}")
                    if online_accounts > 0:
                        status_parts.append(f"({online_accounts} online)")
                
                if campaign_count > 0:
                    status_parts.append(f"{campaign_count} campaign{'s' if campaign_count != 1 else ''}")
                
                if recipient_count > 0:
                    status_parts.append(f"{recipient_count} recipient{'s' if recipient_count != 1 else ''}")
                
                if status_parts:
                    return " | ".join(status_parts)
                else:
                    return "Ready - No data loaded"
                    
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error getting application status: {e}")
            return "Ready"
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Application closing")
        event.accept()
