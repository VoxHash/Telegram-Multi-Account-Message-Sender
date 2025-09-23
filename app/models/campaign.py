"""
Campaign model for managing message campaigns.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlmodel import Field, Relationship
from sqlalchemy import JSON

from .base import BaseModel, SoftDeleteMixin, JSONFieldMixin


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"
    FAILED = "failed"
    INCOMPLETED = "incompleted"


class CampaignType(str, Enum):
    """Campaign type enumeration."""
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    STICKER = "sticker"
    ANIMATION = "animation"


class Campaign(BaseModel, SoftDeleteMixin, JSONFieldMixin, table=True):
    """Campaign model for managing message campaigns."""
    
    __tablename__ = "campaigns"
    
    # Basic campaign info
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    campaign_type: CampaignType = Field(default=CampaignType.IMMEDIATE)
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT)
    
    # Message content
    message_text: str
    message_type: MessageType = Field(default=MessageType.TEXT)
    media_path: Optional[str] = Field(default=None)
    caption: Optional[str] = Field(default=None)
    
    # Spintax support
    use_spintax: bool = Field(default=False)
    spintax_text: Optional[str] = Field(default=None)
    
    # A/B Testing
    use_ab_testing: bool = Field(default=False)
    ab_variants: Optional[str] = Field(default=None, sa_column=JSON)
    ab_split_percentages: Optional[str] = Field(default=None, sa_column=JSON)
    
    # Scheduling
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    timezone: str = Field(default="UTC")
    
    # Rate limiting
    messages_per_minute: int = Field(default=1)
    messages_per_hour: int = Field(default=30)
    messages_per_day: int = Field(default=500)
    random_jitter_seconds: int = Field(default=5)
    
    # Account selection
    account_selection_strategy: str = Field(default="round_robin")  # round_robin, random, weighted
    account_weights: Optional[str] = Field(default=None, sa_column=JSON)
    max_concurrent_accounts: int = Field(default=3)
    
    # Recipients
    recipient_source: str = Field(default="manual")  # manual, csv, channel, group
    recipient_list_id: Optional[int] = Field(default=None, foreign_key="recipientlists.id")
    recipient_filters: Optional[str] = Field(default=None, sa_column=JSON)
    
    # Safety and compliance
    dry_run: bool = Field(default=False)
    respect_rate_limits: bool = Field(default=True)
    stop_on_error: bool = Field(default=False)
    max_retries: int = Field(default=3)
    
    # Progress tracking
    total_recipients: int = Field(default=0)
    sent_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    skipped_count: int = Field(default=0)
    progress_percentage: float = Field(default=0.0)
    
    # Statistics
    start_time_actual: Optional[datetime] = Field(default=None)
    end_time_actual: Optional[datetime] = Field(default=None)
    last_activity: Optional[datetime] = Field(default=None)
    
    # Additional settings
    is_active: bool = Field(default=True)
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    notes: Optional[str] = Field(default=None)
    
    # Relationships
    send_logs: List["SendLog"] = Relationship(back_populates="campaign")
    recipient_list: Optional["RecipientList"] = Relationship(back_populates="campaigns")
    
    def get_ab_variant(self, recipient_id: int) -> Dict[str, Any]:
        """Get A/B test variant for a recipient."""
        if not self.use_ab_testing or not self.ab_variants:
            return {"text": self.message_text, "media_path": self.media_path}
        
        # Get variants list
        variants_list = self.get_ab_variants_list()
        if not variants_list:
            return {"text": self.message_text, "media_path": self.media_path}
        
        # Simple round-robin assignment based on recipient_id
        variant_index = recipient_id % len(variants_list)
        return variants_list[variant_index]
    
    def get_effective_message_text(self, recipient_id: int) -> str:
        """Get the effective message text for a recipient."""
        if self.use_ab_testing:
            variant = self.get_ab_variant(recipient_id)
            return variant.get("text", self.message_text)
        return self.message_text
    
    def get_effective_media_path(self, recipient_id: int) -> Optional[str]:
        """Get the effective media path for a recipient."""
        if self.use_ab_testing:
            variant = self.get_ab_variant(recipient_id)
            return variant.get("media_path", self.media_path)
        return self.media_path
    
    def can_start(self) -> bool:
        """Check if campaign can be started."""
        return (
            self.status in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED] and
            self.is_active and
            not self.is_deleted and
            self.total_recipients > 0
        )
    
    def can_pause(self) -> bool:
        """Check if campaign can be paused."""
        return self.status == CampaignStatus.RUNNING
    
    def can_resume(self) -> bool:
        """Check if campaign can be resumed."""
        return self.status == CampaignStatus.PAUSED
    
    def can_stop(self) -> bool:
        """Check if campaign can be stopped."""
        return self.status in [CampaignStatus.RUNNING, CampaignStatus.PAUSED]
    
    def update_progress(self) -> None:
        """Update progress percentage."""
        if self.total_recipients > 0:
            self.progress_percentage = (self.sent_count + self.failed_count + self.skipped_count) / self.total_recipients * 100
        else:
            self.progress_percentage = 0.0
    
    def is_completed(self) -> bool:
        """Check if campaign is completed."""
        return (
            self.status == CampaignStatus.COMPLETED or
            (self.total_recipients > 0 and 
             self.sent_count + self.failed_count + self.skipped_count >= self.total_recipients)
        )
    
    def get_remaining_recipients(self) -> int:
        """Get number of remaining recipients."""
        return max(0, self.total_recipients - (self.sent_count + self.failed_count + self.skipped_count))
    
    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        total_attempted = self.sent_count + self.failed_count
        if total_attempted == 0:
            return 0.0
        return (self.sent_count / total_attempted) * 100
    
    def get_ab_variants_list(self) -> List[Dict[str, Any]]:
        """Get A/B variants as a list."""
        if self.ab_variants is None:
            return []
        try:
            import json
            return json.loads(self.ab_variants) if isinstance(self.ab_variants, str) else self.ab_variants
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_ab_variants_list(self, variants: List[Dict[str, Any]]) -> None:
        """Set A/B variants from a list."""
        if not variants:
            self.ab_variants = None
        else:
            import json
            self.ab_variants = json.dumps(variants)
    
    def get_ab_split_percentages_list(self) -> List[float]:
        """Get A/B split percentages as a list."""
        if self.ab_split_percentages is None:
            return []
        try:
            import json
            return json.loads(self.ab_split_percentages) if isinstance(self.ab_split_percentages, str) else self.ab_split_percentages
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_ab_split_percentages_list(self, percentages: List[float]) -> None:
        """Set A/B split percentages from a list."""
        if not percentages:
            self.ab_split_percentages = None
        else:
            import json
            self.ab_split_percentages = json.dumps(percentages)
    
    def get_account_weights_dict(self) -> Dict[int, float]:
        """Get account weights as a dictionary."""
        if self.account_weights is None:
            return {}
        try:
            import json
            return json.loads(self.account_weights) if isinstance(self.account_weights, str) else self.account_weights
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_account_weights_dict(self, weights: Dict[int, float]) -> None:
        """Set account weights from a dictionary."""
        if not weights:
            self.account_weights = None
        else:
            import json
            self.account_weights = json.dumps(weights)
    
    def get_recipient_filters_dict(self) -> Dict[str, Any]:
        """Get recipient filters as a dictionary."""
        if self.recipient_filters is None:
            return {}
        try:
            import json
            return json.loads(self.recipient_filters) if isinstance(self.recipient_filters, str) else self.recipient_filters
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_recipient_filters_dict(self, filters: Dict[str, Any]) -> None:
        """Set recipient filters from a dictionary."""
        if not filters:
            self.recipient_filters = None
        else:
            import json
            self.recipient_filters = json.dumps(filters)
    
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
