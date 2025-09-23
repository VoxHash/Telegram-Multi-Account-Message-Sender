"""
Reusable GUI widgets for the application.
"""

from .account_widget import AccountWidget, AccountListWidget
from .campaign_widget import CampaignWidget, CampaignListWidget
from .template_widget import TemplateWidget, TemplateListWidget
from .recipient_widget import RecipientWidget, RecipientListWidget
from .testing_widget import TestingWidget
from .log_widget import LogWidget, LogViewer
from .settings_widget import SettingsWidget

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
]
