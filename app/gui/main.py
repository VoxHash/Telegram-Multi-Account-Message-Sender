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
from ..services.translation import get_translation_manager, _
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
        self.translation_manager = get_translation_manager()
        
        # Connect language change signal
        self.translation_manager.language_changed.connect(self.on_language_changed)
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
        # Setup timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(30000)  # Update every 30 seconds
        
        # Initial status update
        self.update_status()
        
        self.logger.info("Main window initialized")
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(_("app.title"))
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
        self.create_accounts_tab()
        self.create_campaigns_tab()
        self.create_templates_tab()
        self.create_recipients_tab()
        self.create_testing_tab()
        self.create_logs_tab()
        self.create_settings_tab()
        self.create_about_tab()
        
        # Set Accounts as the default tab
        self.tab_widget.setCurrentIndex(0)
    
    def create_accounts_tab(self):
        """Create accounts management tab."""
        self.accounts_widget = AccountWidget()
        self.tab_widget.addTab(self.accounts_widget, _("tabs.accounts"))
    
    def create_campaigns_tab(self):
        """Create campaigns management tab."""
        self.campaigns_widget = CampaignWidget()
        self.tab_widget.addTab(self.campaigns_widget, _("tabs.campaigns"))
    
    def create_templates_tab(self):
        """Create templates management tab."""
        from .widgets.template_widget import TemplateWidget
        self.templates_widget = TemplateWidget()
        self.tab_widget.addTab(self.templates_widget, _("tabs.templates"))
    
    def create_recipients_tab(self):
        """Create recipients management tab."""
        self.recipients_widget = RecipientWidget()
        self.tab_widget.addTab(self.recipients_widget, _("tabs.recipients"))
    
    def create_testing_tab(self):
        """Create testing tab."""
        from .widgets.testing_widget import TestingWidget
        self.testing_widget = TestingWidget()
        self.tab_widget.addTab(self.testing_widget, _("tabs.testing"))
    
    def create_logs_tab(self):
        """Create logs viewer tab."""
        self.logs_widget = LogWidget()
        self.tab_widget.addTab(self.logs_widget, _("tabs.logs"))
    
    def create_settings_tab(self):
        """Create settings tab."""
        self.settings_widget = SettingsWidget()
        # Connect settings update signal to update status bar
        self.settings_widget.settings_updated.connect(self.on_settings_updated)
        self.tab_widget.addTab(self.settings_widget, _("tabs.settings"))
    
    def create_about_tab(self):
        """Create about tab."""
        self.about_widget = AboutWidget()
        self.tab_widget.addTab(self.about_widget, _("tabs.about"))
    
    def setup_menu(self):
        """Set up menu bar."""
        # Menu bar removed as requested
        pass
    
    def setup_status_bar(self):
        """Set up status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status label
        self.status_label = QLabel(_("app.ready"))
        self.status_label.setStyleSheet("background-color: transparent;")
        self.status_bar.addWidget(self.status_label)
        
        # Language label
        current_language = self.translation_manager.get_language_display_name(self.translation_manager.current_language)
        self.language_label = QLabel(f"{_('app.language')}: {current_language}")
        self.language_label.setStyleSheet("background-color: transparent;")
        self.status_bar.addPermanentWidget(self.language_label)
        
        # Theme label
        initial_theme = self.theme_manager.get_current_theme()
        formatted_theme = self.format_theme_name(initial_theme)
        self.theme_label = QLabel(f"{_('app.theme')}: {formatted_theme}")
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
        actual_theme = self.theme_manager.get_current_theme()
        formatted_theme = self.format_theme_name(actual_theme)
        self.theme_label.setText(f"{_('app.theme')}: {formatted_theme}")
    
    
    def on_settings_updated(self):
        """Handle settings update."""
        # Reload settings to get updated values
        from ..services import reload_settings
        reload_settings()
        self.settings = get_settings()
        
        # Update theme manager with new settings
        self.theme_manager.settings = self.settings
        
        # Convert enum to string value for theme application
        theme_value = self.settings.theme.value if hasattr(self.settings.theme, 'value') else str(self.settings.theme)
        
        # Apply the current theme from settings
        self.theme_manager.apply_theme(theme_value)
        
        # Force refresh the status bar theme display
        self.refresh_status_bar_theme()
        
        self.logger.info(f"Settings updated, theme changed to: {self.theme_manager.get_current_theme()}")
    
    def refresh_status_bar_theme(self):
        """Refresh the theme display in the status bar."""
        actual_theme = self.theme_manager.get_current_theme()
        formatted_theme = self.format_theme_name(actual_theme)
        self.theme_label.setText(f"{_('app.theme')}: {formatted_theme}")
        self.logger.debug(f"Status bar theme updated to: {formatted_theme}")
    
    def format_theme_name(self, theme: str) -> str:
        """Format theme name for display."""
        theme_formats = {
            "light": _("settings.light"),
            "dark": _("settings.dark"), 
            "dracula": _("settings.dracula"),
            "auto": _("settings.auto")
        }
        return theme_formats.get(theme, theme.title())
    
    def update_status(self):
        """Update status bar with current application status."""
        try:
            # Get current status information
            status_info = self.get_application_status()
            self.status_label.setText(status_info)
        except Exception as e:
            self.logger.error(f"Error updating status: {e}")
            self.status_label.setText(_("common.error"))
    
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
                
                # Get online accounts (only if we have accounts)
                online_accounts = 0
                if account_count > 0:
                    online_accounts = session.exec(
                        select(func.count(Account.id))
                        .where(Account.is_deleted == False)
                        .where(Account.status == "ONLINE")
                    ).first() or 0
                
                # Build status message
                status_parts = []
                if account_count > 0:
                    status_parts.append(_("app.accounts_count").format(count=account_count))
                    if online_accounts > 0:
                        status_parts.append(_("app.online_count").format(online=online_accounts))
                
                if campaign_count > 0:
                    status_parts.append(_("app.campaigns_count").format(count=campaign_count))
                
                if recipient_count > 0:
                    status_parts.append(_("app.recipients_count").format(count=recipient_count))
                
                if status_parts:
                    return " | ".join(status_parts)
                else:
                    return _("app.ready")
                    
            finally:
                session.close()
                
        except Exception as e:
            self.logger.error(f"Error getting application status: {e}")
            return _("app.ready")
    
    def on_language_changed(self, language: str):
        """Handle language change."""
        self.logger.info(f"Language changed to: {language}")
        # Update UI text
        self.setWindowTitle(_("app.title"))
        self.status_label.setText(_("app.ready"))
        
        # Update tab names
        self.tab_widget.setTabText(0, _("tabs.accounts"))
        self.tab_widget.setTabText(1, _("tabs.campaigns"))
        self.tab_widget.setTabText(2, _("tabs.templates"))
        self.tab_widget.setTabText(3, _("tabs.recipients"))
        self.tab_widget.setTabText(4, _("tabs.testing"))
        self.tab_widget.setTabText(5, _("tabs.logs"))
        self.tab_widget.setTabText(6, _("tabs.settings"))
        self.tab_widget.setTabText(7, _("tabs.about"))
        
        # Update language label
        current_language = self.translation_manager.get_language_display_name(language)
        self.language_label.setText(f"{_('app.language')}: {current_language}")
        
        # Update theme label
        current_theme = self.theme_manager.get_current_theme()
        formatted_theme = self.format_theme_name(current_theme)
        self.theme_label.setText(f"{_('app.theme')}: {formatted_theme}")
        
        # Update status bar
        self.update_status()
        
        # Force refresh all widgets
        self.refresh_all_widgets()
    
    def refresh_all_widgets(self):
        """Refresh all widgets to apply language changes."""
        try:
            # Refresh each widget if it has a refresh method
            if hasattr(self, 'accounts_widget') and hasattr(self.accounts_widget, 'refresh_accounts'):
                self.accounts_widget.refresh_accounts()
            if hasattr(self, 'campaigns_widget') and hasattr(self.campaigns_widget, 'refresh_campaigns'):
                self.campaigns_widget.refresh_campaigns()
            if hasattr(self, 'templates_widget') and hasattr(self.templates_widget, 'refresh_templates'):
                self.templates_widget.refresh_templates()
            if hasattr(self, 'recipients_widget') and hasattr(self.recipients_widget, 'refresh_recipients'):
                self.recipients_widget.refresh_recipients()
            if hasattr(self, 'logs_widget') and hasattr(self.logs_widget, 'refresh_logs'):
                self.logs_widget.refresh_logs()
            if hasattr(self, 'settings_widget') and hasattr(self.settings_widget, 'load_settings'):
                self.settings_widget.load_settings()
            if hasattr(self, 'about_widget') and hasattr(self.about_widget, 'refresh_content'):
                self.about_widget.refresh_content()
        except Exception as e:
            self.logger.error(f"Error refreshing widgets: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.logger.info("Application closing")
        event.accept()
