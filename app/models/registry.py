"""
Model registry to ensure all models are properly registered with SQLModel.
"""

from . import (
    Account, Campaign, Recipient, SendLog, MessageTemplate,
    RecipientList, RecipientListRecipient
)

# This module ensures all models are imported and registered
# The imports above will register the models with SQLModel.metadata

__all__ = [
    "Account", "Campaign", "Recipient", "SendLog", "MessageTemplate",
    "RecipientList", "RecipientListRecipient"
]
