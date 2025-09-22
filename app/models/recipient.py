"""
Recipient models for managing message recipients.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlmodel import Field, Relationship
from sqlalchemy import JSON

from .base import BaseModel, SoftDeleteMixin, JSONFieldMixin


class RecipientType(str, Enum):
    """Recipient type enumeration."""
    USER = "USER"
    GROUP = "GROUP"
    CHANNEL = "CHANNEL"

class RecipientSource(str, Enum):
    """Recipient source enumeration."""
    MANUAL = "manual"
    CSV_IMPORT = "csv_import"
    CHANNEL_SCRAPE = "channel_scrape"
    GROUP_SCRAPE = "group_scrape"
    USER_SCRAPE = "user_scrape"


class RecipientStatus(str, Enum):
    """Recipient status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class Recipient(BaseModel, SoftDeleteMixin, JSONFieldMixin, table=True):
    """Individual recipient model."""
    
    __tablename__ = "recipients"
    
    # Basic info
    recipient_type: RecipientType = Field(default=RecipientType.USER)
    username: Optional[str] = Field(default=None, index=True)
    user_id: Optional[int] = Field(default=None, index=True)
    phone_number: Optional[str] = Field(default=None, index=True)
    first_name: Optional[str] = Field(default=None)
    last_name: Optional[str] = Field(default=None)
    display_name: Optional[str] = Field(default=None)
    
    # Group/Channel specific fields
    group_id: Optional[int] = Field(default=None, index=True)
    group_title: Optional[str] = Field(default=None)
    group_username: Optional[str] = Field(default=None, index=True)
    group_type: Optional[str] = Field(default=None)  # "group", "supergroup", "channel"
    member_count: Optional[int] = Field(default=None)
    
    # Contact info
    email: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None)
    profile_photo_url: Optional[str] = Field(default=None)
    
    # Status and metadata
    status: RecipientStatus = Field(default=RecipientStatus.ACTIVE)
    source: RecipientSource = Field(default=RecipientSource.MANUAL)
    source_metadata: Optional[str] = Field(default=None, sa_column=JSON)
    
    # Organization
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    notes: Optional[str] = Field(default=None)
    custom_fields: Optional[str] = Field(default=None, sa_column=JSON)
    
    # Statistics
    total_messages_sent: int = Field(default=0)
    total_messages_failed: int = Field(default=0)
    last_message_sent: Optional[datetime] = Field(default=None)
    last_message_failed: Optional[datetime] = Field(default=None)
    
    # Relationships
    send_logs: List["SendLog"] = Relationship(back_populates="recipient")
    recipient_lists: List["RecipientListRecipient"] = Relationship(back_populates="recipient")
    
    def get_display_name(self) -> str:
        """Get display name for the recipient."""
        if self.recipient_type == RecipientType.GROUP or self.recipient_type == RecipientType.CHANNEL:
            if self.group_title:
                return self.group_title
            elif self.group_username:
                return f"@{self.group_username}"
            elif self.group_id:
                return f"Group {self.group_id}"
            else:
                return "Unknown Group"
        else:
            # User type
            if self.display_name:
                return self.display_name
            
            if self.first_name and self.last_name:
                return f"{self.first_name} {self.last_name}"
            elif self.first_name:
                return self.first_name
            elif self.username:
                return f"@{self.username}"
            elif self.user_id:
                return f"User {self.user_id}"
            else:
                return "Unknown"
    
    def get_identifier(self) -> str:
        """Get unique identifier for the recipient."""
        if self.recipient_type == RecipientType.GROUP or self.recipient_type == RecipientType.CHANNEL:
            if self.group_username:
                return f"@{self.group_username}"
            elif self.group_id:
                return str(self.group_id)
            else:
                return f"group_{self.id}"
        else:
            # User type
            if self.username:
                return f"@{self.username}"
            elif self.user_id:
                return str(self.user_id)
            elif self.phone_number:
                return self.phone_number
            else:
                return f"recipient_{self.id}"
    
    def is_contactable(self) -> bool:
        """Check if recipient can be contacted."""
        return (
            self.status == RecipientStatus.ACTIVE and
            not self.is_deleted and
            (self.username or self.user_id or self.phone_number)
        )
    
    def increment_message_count(self, success: bool = True) -> None:
        """Increment message counters."""
        if success:
            self.total_messages_sent += 1
            self.last_message_sent = datetime.utcnow()
        else:
            self.total_messages_failed += 1
            self.last_message_failed = datetime.utcnow()
    
    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        total_attempted = self.total_messages_sent + self.total_messages_failed
        if total_attempted == 0:
            return 0.0
        return (self.total_messages_sent / total_attempted) * 100
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        if self.tags is None:
            return []
        try:
            import json
            return json.loads(self.tags) if isinstance(self.tags, str) else self.tags
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_tags_list(self, tags: List[str]) -> None:
        """Set tags from a list."""
        if not tags:
            self.tags = None
        else:
            import json
            self.tags = json.dumps(tags)
    
    def get_source_metadata_dict(self) -> Dict[str, Any]:
        """Get source metadata as a dictionary."""
        if self.source_metadata is None:
            return {}
        try:
            import json
            return json.loads(self.source_metadata) if isinstance(self.source_metadata, str) else self.source_metadata
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_source_metadata_dict(self, metadata: Dict[str, Any]) -> None:
        """Set source metadata from a dictionary."""
        if not metadata:
            self.source_metadata = None
        else:
            import json
            self.source_metadata = json.dumps(metadata)
    
    def get_custom_fields_dict(self) -> Dict[str, Any]:
        """Get custom fields as a dictionary."""
        if self.custom_fields is None:
            return {}
        try:
            import json
            return json.loads(self.custom_fields) if isinstance(self.custom_fields, str) else self.custom_fields
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_custom_fields_dict(self, fields: Dict[str, Any]) -> None:
        """Set custom fields from a dictionary."""
        if not fields:
            self.custom_fields = None
        else:
            import json
            self.custom_fields = json.dumps(fields)


class RecipientList(BaseModel, SoftDeleteMixin, JSONFieldMixin, table=True):
    """Recipient list model for organizing recipients."""
    
    __tablename__ = "recipientlists"
    
    # Basic info
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    
    # Metadata
    source: RecipientSource = Field(default=RecipientSource.MANUAL)
    source_file_path: Optional[str] = Field(default=None)
    import_metadata: Optional[str] = Field(default=None, sa_column=JSON)
    
    # Organization
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    notes: Optional[str] = Field(default=None)
    
    # Statistics
    total_recipients: int = Field(default=0)
    active_recipients: int = Field(default=0)
    last_updated: Optional[datetime] = Field(default=None)
    
    # Settings
    is_active: bool = Field(default=True)
    auto_update: bool = Field(default=False)
    update_frequency_hours: int = Field(default=24)
    
    # Relationships
    recipients: List["RecipientListRecipient"] = Relationship(back_populates="recipient_list")
    campaigns: List["Campaign"] = Relationship(back_populates="recipient_list")
    
    def update_statistics(self) -> None:
        """Update recipient statistics."""
        self.total_recipients = len(self.recipients)
        self.active_recipients = sum(1 for r in self.recipients if r.recipient.is_contactable())
        self.last_updated = datetime.utcnow()
    
    def get_recipient_count(self) -> int:
        """Get total recipient count."""
        return len(self.recipients)
    
    def get_active_recipient_count(self) -> int:
        """Get active recipient count."""
        return sum(1 for r in self.recipients if r.recipient.is_contactable())
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        if self.tags is None:
            return []
        try:
            import json
            return json.loads(self.tags) if isinstance(self.tags, str) else self.tags
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_tags_list(self, tags: List[str]) -> None:
        """Set tags from a list."""
        if not tags:
            self.tags = None
        else:
            import json
            self.tags = json.dumps(tags)
    
    def get_import_metadata_dict(self) -> Dict[str, Any]:
        """Get import metadata as a dictionary."""
        if self.import_metadata is None:
            return {}
        try:
            import json
            return json.loads(self.import_metadata) if isinstance(self.import_metadata, str) else self.import_metadata
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_import_metadata_dict(self, metadata: Dict[str, Any]) -> None:
        """Set import metadata from a dictionary."""
        if not metadata:
            self.import_metadata = None
        else:
            import json
            self.import_metadata = json.dumps(metadata)


class RecipientListRecipient(BaseModel, table=True):
    """Association table for recipient lists and recipients."""
    
    __tablename__ = "recipientlist_recipients"
    
    recipient_list_id: int = Field(foreign_key="recipientlists.id", primary_key=True)
    recipient_id: int = Field(foreign_key="recipients.id", primary_key=True)
    
    # Additional metadata
    added_at: datetime = Field(default_factory=datetime.utcnow)
    added_by: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    
    # Relationships
    recipient_list: RecipientList = Relationship(back_populates="recipients")
    recipient: Recipient = Relationship(back_populates="recipient_lists")
