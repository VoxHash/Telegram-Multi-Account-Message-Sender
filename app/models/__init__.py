"""
Database models for the Telegram Multi-Account Message Sender.
"""

from .base import BaseModel, TimestampMixin, UUIDMixin, SoftDeleteMixin, JSONFieldMixin
from .account import Account, AccountStatus, ProxyType
from .campaign import Campaign, CampaignStatus, CampaignType, MessageType, RecurrencePattern
from .campaign_template import CampaignTemplate, TemplateCategory as CampaignTemplateCategory
from .recipient import (
    Recipient,
    RecipientList,
    RecipientListRecipient,
    RecipientSource,
    RecipientStatus,
    RecipientType,
)
from .recipient_group import RecipientGroup, RecipientGroupMember, GroupType
from .template import MessageTemplate, TemplateType, TemplateCategory
from .send_log import SendLog, SendStatus

__all__ = [
    # Base classes
    "BaseModel",
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    "JSONFieldMixin",
    # Account models
    "Account",
    "AccountStatus",
    "ProxyType",
    # Campaign models
    "Campaign",
    "CampaignStatus",
    "CampaignType",
    "MessageType",
    "RecurrencePattern",
    "CampaignTemplate",
    "CampaignTemplateCategory",
    # Recipient models
    "Recipient",
    "RecipientList",
    "RecipientListRecipient",
    "RecipientSource",
    "RecipientStatus",
    "RecipientType",
    "RecipientGroup",
    "RecipientGroupMember",
    "GroupType",
    # Template models
    "MessageTemplate",
    "TemplateType",
    "TemplateCategory",
    # Send log models
    "SendLog",
    "SendStatus",
]
