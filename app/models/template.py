"""
Template models for managing message templates.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlmodel import Field, Relationship
from sqlalchemy import JSON

from .base import BaseModel, SoftDeleteMixin, JSONFieldMixin


class TemplateType(str, Enum):
    """Template type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    VOICE = "voice"
    STICKER = "sticker"
    ANIMATION = "animation"


class TemplateCategory(str, Enum):
    """Template category enumeration."""
    GENERAL = "general"
    MARKETING = "marketing"
    NOTIFICATION = "notification"
    WELCOME = "welcome"
    FOLLOW_UP = "follow_up"
    REMINDER = "reminder"
    PROMOTIONAL = "promotional"


class MessageTemplate(BaseModel, SoftDeleteMixin, JSONFieldMixin, table=True):
    """Message template model."""
    
    __tablename__ = "templates"
    
    # Basic info
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    template_type: TemplateType = Field(default=TemplateType.TEXT)
    category: TemplateCategory = Field(default=TemplateCategory.GENERAL)
    
    # Content
    subject: Optional[str] = Field(default=None)
    body: str
    media_path: Optional[str] = Field(default=None)
    caption: Optional[str] = Field(default=None)
    
    # Variables and personalization
    variables: Optional[str] = Field(default=None, sa_column=JSON)
    variable_descriptions: Optional[str] = Field(default=None, sa_column=JSON)
    use_spintax: bool = Field(default=False)
    spintax_text: Optional[str] = Field(default=None)
    
    # A/B Testing
    use_ab_testing: bool = Field(default=False)
    ab_variants: Optional[str] = Field(default=None, sa_column=JSON)
    
    # Organization
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    notes: Optional[str] = Field(default=None)
    
    # Usage statistics
    usage_count: int = Field(default=0)
    last_used: Optional[datetime] = Field(default=None)
    success_rate: float = Field(default=0.0)
    
    # Settings
    is_active: bool = Field(default=True)
    is_public: bool = Field(default=False)
    created_by: Optional[str] = Field(default=None)
    
    # Relationships
    # campaigns: List["Campaign"] = Relationship(back_populates="template")
    
    def get_available_variables(self) -> List[str]:
        """Get list of available variables in the template."""
        return self.variables.copy()
    
    def add_variable(self, variable: str, description: str = "") -> None:
        """Add a variable to the template."""
        if variable not in self.variables:
            self.variables.append(variable)
            if description:
                self.variable_descriptions[variable] = description
    
    def remove_variable(self, variable: str) -> None:
        """Remove a variable from the template."""
        if variable in self.variables:
            self.variables.remove(variable)
            self.variable_descriptions.pop(variable, None)
    
    def render_template(self, variables: Dict[str, str]) -> Dict[str, str]:
        """Render template with provided variables."""
        rendered = {
            "subject": self.subject,
            "body": self.body,
            "caption": self.caption,
        }
        
        # Replace variables in text fields
        for field in ["subject", "body", "caption"]:
            if rendered[field]:
                for var, value in variables.items():
                    placeholder = f"{{{{{var}}}}}"
                    rendered[field] = rendered[field].replace(placeholder, str(value))
        
        return rendered
    
    def validate_variables(self, variables: Dict[str, str]) -> List[str]:
        """Validate that all required variables are provided."""
        missing = []
        for var in self.variables:
            if var not in variables or not variables[var]:
                missing.append(var)
        return missing
    
    def get_preview_text(self, max_length: int = 100) -> str:
        """Get preview text for the template."""
        preview = self.body or ""
        if len(preview) > max_length:
            preview = preview[:max_length] + "..."
        return preview
    
    def increment_usage(self, success: bool = True) -> None:
        """Increment usage statistics."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        
        # Update success rate (simple moving average)
        if success:
            self.success_rate = (self.success_rate * (self.usage_count - 1) + 100) / self.usage_count
        else:
            self.success_rate = (self.success_rate * (self.usage_count - 1) + 0) / self.usage_count
    
    def get_tags_list(self) -> List[str]:
        """Get tags as a list."""
        if self.tags:
            import json
            if isinstance(self.tags, str):
                try:
                    return json.loads(self.tags)
                except (json.JSONDecodeError, TypeError):
                    return []
            return self.tags if isinstance(self.tags, list) else []
        return []
    
    def set_tags_list(self, tags: List[str]) -> None:
        """Set tags from a list."""
        import json
        self.tags = json.dumps(tags) if tags else None
    
    def get_ab_variant(self, recipient_id: int) -> Dict[str, Any]:
        """Get A/B test variant for a recipient."""
        if not self.use_ab_testing or not self.ab_variants:
            return {
                "subject": self.subject,
                "body": self.body,
                "media_path": self.media_path,
                "caption": self.caption,
            }
        
        # Simple round-robin assignment based on recipient_id
        variant_index = recipient_id % len(self.ab_variants)
        return self.ab_variants[variant_index]
    
    def is_usable(self) -> bool:
        """Check if template can be used."""
        return (
            self.is_active and
            not self.is_deleted and
            bool(self.body.strip())
        )
