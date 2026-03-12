"""
Reusable GUI widgets for the application.
"""

# Import telegram_selector FIRST using absolute import to ensure PyInstaller includes it
# This MUST be at the top level, not in a try-except, so PyInstaller can detect it
from app.gui.widgets.telegram_selector import TelegramSelectorDialog

from .account_widget import AccountWidget, AccountListWidget
from .campaign_widget import CampaignWidget, CampaignListWidget
from .template_widget import TemplateWidget, TemplateListWidget
from .recipient_widget import RecipientWidget, RecipientListWidget
from .testing_widget import TestingWidget
from .log_widget import LogWidget, LogViewer
from .settings_widget import SettingsWidget
from .dashboard_widget import DashboardWidget
from .plugin_widget import PluginWidget, PluginListWidget

__all__ = [
    "AccountWidget",
    "AccountListWidget",
    "CampaignWidget",
    "CampaignListWidget",
    "TemplateWidget",
    "TemplateListWidget",
    "RecipientWidget",
    "RecipientListWidget",
    "TestingWidget",
    "LogWidget",
    "LogViewer",
    "SettingsWidget",
    "DashboardWidget",
    "TelegramSelectorDialog",
    "PluginWidget",
    "PluginListWidget",
]
