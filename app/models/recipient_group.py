"""
Recipient grouping models for smart recipient management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlmodel import Field, Relationship
from sqlalchemy import Column, JSON

from .base import BaseModel, SoftDeleteMixin, JSONFieldMixin
from .recipient import Recipient


class GroupType(str, Enum):
    """Group type enumeration."""

    STATIC = "static"  # Manually assigned
    DYNAMIC = "dynamic"  # Based on rules/filters
    SMART = "smart"  # AI/ML based grouping


class RecipientGroup(BaseModel, SoftDeleteMixin, JSONFieldMixin, table=True):
    """Recipient group model for smart grouping."""

    __tablename__ = "recipient_groups"

    # Basic info
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    group_type: GroupType = Field(default=GroupType.STATIC)

    # Dynamic grouping rules (for dynamic/smart groups)
    grouping_rules: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))  # Filter criteria
    auto_update: bool = Field(default=False)  # Auto-update group members

    # Metadata
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    notes: Optional[str] = Field(default=None)

    # Statistics
    total_recipients: int = Field(default=0)
    active_recipients: int = Field(default=0)
    last_updated: Optional[datetime] = Field(default=None)

    # Settings
    is_active: bool = Field(default=True)

    # Relationships
    members: List["RecipientGroupMember"] = Relationship(back_populates="group")

    def update_statistics(self) -> None:
        """Update recipient statistics."""
        active_count = len(
            [m for m in self.members if m.recipient is not None and m.recipient.is_contactable()]
        )
        self.total_recipients = len(self.members)
        self.active_recipients = active_count
        self.last_updated = datetime.utcnow()

    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        return list(self.tags) if self.tags else []

    def set_tags_list(self, tags: List[str]) -> None:
        """Set tags from a list."""
        if not tags:
            self.tags = None
        else:
            import json

            self.tags = tags

    def get_grouping_rules_dict(self) -> Dict[str, Any]:
        """Get grouping rules as a dictionary."""
        return dict(self.grouping_rules) if self.grouping_rules else {}

    def set_grouping_rules_dict(self, rules: Dict[str, Any]) -> None:
        """Set grouping rules from a dictionary."""
        if not rules:
            self.grouping_rules = None
        else:
            import json

            self.grouping_rules = rules


class RecipientGroupMember(BaseModel, table=True):
    """Association table for recipient groups and recipients."""

    __tablename__ = "recipient_group_members"

    group_id: int = Field(foreign_key="recipient_groups.id", primary_key=True)
    recipient_id: int = Field(foreign_key="recipients.id", primary_key=True)

    # Additional metadata
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    score: Optional[float] = Field(default=None)  # For smart grouping

    # Relationships
    group: RecipientGroup = Relationship(back_populates="members")
    recipient: Recipient = Relationship()
