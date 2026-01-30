"""
Campaign template and preset models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlmodel import Field, Relationship
from sqlalchemy import JSON

from .base import BaseModel, SoftDeleteMixin, JSONFieldMixin
from .campaign import CampaignType, MessageType


class TemplateCategory(str, Enum):
    """Template category enumeration."""
    MARKETING = "marketing"
    NOTIFICATION = "notification"
    PROMOTIONAL = "promotional"
    INFORMATIONAL = "informational"
    CUSTOM = "custom"


class CampaignTemplate(BaseModel, SoftDeleteMixin, JSONFieldMixin, table=True):
    """Campaign template/preset model."""
    
    __tablename__ = "campaign_templates"
    
    # Basic info
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    category: TemplateCategory = Field(default=TemplateCategory.CUSTOM)
    
    # Template settings (stored as JSON to match Campaign structure)
    campaign_type: CampaignType = Field(default=CampaignType.IMMEDIATE)
    message_text: str
    message_type: MessageType = Field(default=MessageType.TEXT)
    media_path: Optional[str] = Field(default=None)
    caption: Optional[str] = Field(default=None)
    
    # Spintax and A/B testing
    use_spintax: bool = Field(default=False)
    spintax_text: Optional[str] = Field(default=None)
    use_ab_testing: bool = Field(default=False)
    ab_variants: Optional[str] = Field(default=None, sa_column=JSON)
    ab_split_percentages: Optional[str] = Field(default=None, sa_column=JSON)
    
    # Scheduling defaults
    messages_per_minute: int = Field(default=1)
    messages_per_hour: int = Field(default=30)
    messages_per_day: int = Field(default=500)
    random_jitter_seconds: int = Field(default=5)
    
    # Account selection defaults
    account_selection_strategy: str = Field(default="round_robin")
    account_weights: Optional[str] = Field(default=None, sa_column=JSON)
    max_concurrent_accounts: int = Field(default=3)
    
    # Safety defaults
    dry_run: bool = Field(default=False)
    respect_rate_limits: bool = Field(default=True)
    stop_on_error: bool = Field(default=False)
    max_retries: int = Field(default=3)
    
    # Metadata
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    usage_count: int = Field(default=0)
    is_public: bool = Field(default=False)  # For sharing templates
    created_by: Optional[str] = Field(default=None)
    
    # Relationships
    campaigns: List["Campaign"] = Relationship(back_populates="template")
    
    def create_campaign_from_template(self, name: str, **overrides) -> Dict[str, Any]:
        """Create campaign data from template with optional overrides."""
        campaign_data = {
            "name": name,
            "description": self.description,
            "campaign_type": self.campaign_type,
            "message_text": self.message_text,
            "message_type": self.message_type,
            "media_path": self.media_path,
            "caption": self.caption,
            "use_spintax": self.use_spintax,
            "spintax_text": self.spintax_text,
            "use_ab_testing": self.use_ab_testing,
            "ab_variants": self.ab_variants,
            "ab_split_percentages": self.ab_split_percentages,
            "messages_per_minute": self.messages_per_minute,
            "messages_per_hour": self.messages_per_hour,
            "messages_per_day": self.messages_per_day,
            "random_jitter_seconds": self.random_jitter_seconds,
            "account_selection_strategy": self.account_selection_strategy,
            "account_weights": self.account_weights,
            "max_concurrent_accounts": self.max_concurrent_accounts,
            "dry_run": self.dry_run,
            "respect_rate_limits": self.respect_rate_limits,
            "stop_on_error": self.stop_on_error,
            "max_retries": self.max_retries,
            "tags": self.tags,
        }
        
        # Apply overrides
        campaign_data.update(overrides)
        
        # Increment usage count
        self.usage_count += 1
        
        return campaign_data
    
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

