"""
Base model classes and common functionality.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """Base model with common fields."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TimestampMixin:
    """Mixin for timestamp fields."""
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UUIDMixin:
    """Mixin for UUID fields."""
    
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True, index=True)


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""
    
    deleted_at: Optional[datetime] = Field(default=None)
    is_deleted: bool = Field(default=False)
    
    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None


class JSONFieldMixin:
    """Mixin for JSON field handling."""
    
    def get_json_field(self, field_name: str, default: Any = None) -> Any:
        """Get a JSON field value with default."""
        value = getattr(self, field_name, None)
        return value if value is not None else default
    
    def set_json_field(self, field_name: str, value: Any) -> None:
        """Set a JSON field value."""
        setattr(self, field_name, value)
