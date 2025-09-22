"""
Account model for managing Telegram accounts.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from sqlmodel import Field, Relationship
from sqlalchemy import JSON

from .base import BaseModel, SoftDeleteMixin, JSONFieldMixin


class AccountStatus(str, Enum):
    """Account status enumeration."""
    OFFLINE = "offline"
    ONLINE = "online"
    CONNECTING = "connecting"
    ERROR = "error"
    SUSPENDED = "suspended"


class ProxyType(str, Enum):
    """Proxy type enumeration."""
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class Account(BaseModel, SoftDeleteMixin, JSONFieldMixin, table=True):
    """Telegram account model."""
    
    __tablename__ = "accounts"
    
    # Basic account info
    name: str = Field(index=True)
    phone_number: str = Field(unique=True, index=True)
    api_id: int
    api_hash: str
    
    # Session management
    session_path: str = Field(unique=True)
    session_password: Optional[str] = Field(default=None)
    
    # Status and health
    status: AccountStatus = Field(default=AccountStatus.OFFLINE)
    last_login: Optional[datetime] = Field(default=None)
    last_activity: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    
    # Proxy configuration
    proxy_type: Optional[ProxyType] = Field(default=None)
    proxy_host: Optional[str] = Field(default=None)
    proxy_port: Optional[int] = Field(default=None)
    proxy_username: Optional[str] = Field(default=None)
    proxy_password: Optional[str] = Field(default=None)
    
    # Rate limiting and safety
    rate_limit_per_minute: int = Field(default=30)
    rate_limit_per_hour: int = Field(default=100)
    rate_limit_per_day: int = Field(default=1000)
    
    # Warmup settings
    warmup_enabled: bool = Field(default=True)
    warmup_messages_sent: int = Field(default=0)
    warmup_target_messages: int = Field(default=5)
    warmup_interval_minutes: int = Field(default=60)
    
    # Additional settings
    is_active: bool = Field(default=True)
    notes: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None, sa_column=JSON)
    
    # Statistics
    total_messages_sent: int = Field(default=0)
    total_messages_failed: int = Field(default=0)
    last_send_time: Optional[datetime] = Field(default=None)
    
    # Relationships
    send_logs: List["SendLog"] = Relationship(back_populates="account")
    
    def get_proxy_url(self) -> Optional[str]:
        """Get formatted proxy URL."""
        if not self.proxy_host or not self.proxy_port:
            return None
        
        auth = ""
        if self.proxy_username and self.proxy_password:
            auth = f"{self.proxy_username}:{self.proxy_password}@"
        
        return f"{self.proxy_type}://{auth}{self.proxy_host}:{self.proxy_port}"
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get rate limits as dictionary."""
        return {
            "per_minute": self.rate_limit_per_minute,
            "per_hour": self.rate_limit_per_hour,
            "per_day": self.rate_limit_per_day,
        }
    
    def set_rate_limits(self, limits: Dict[str, int]) -> None:
        """Set rate limits from dictionary."""
        self.rate_limit_per_minute = limits.get("per_minute", 30)
        self.rate_limit_per_hour = limits.get("per_hour", 100)
        self.rate_limit_per_day = limits.get("per_day", 1000)
    
    def is_warmup_complete(self) -> bool:
        """Check if warmup is complete."""
        if not self.warmup_enabled:
            return True
        return self.warmup_messages_sent >= self.warmup_target_messages
    
    def can_send_message(self) -> bool:
        """Check if account can send messages."""
        return (
            self.is_active and
            not self.is_deleted and
            self.status in [AccountStatus.ONLINE, AccountStatus.CONNECTING] and
            self.is_warmup_complete()
        )
    
    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def increment_message_count(self, success: bool = True) -> None:
        """Increment message counters."""
        if success:
            self.total_messages_sent += 1
        else:
            self.total_messages_failed += 1
        self.last_send_time = datetime.utcnow()
        self.update_activity()
    
    def get_success_rate(self) -> float:
        """Get success rate percentage."""
        total_attempted = self.total_messages_sent + self.total_messages_failed
        if total_attempted == 0:
            return 0.0
        return (self.total_messages_sent / total_attempted) * 100
    
    def get_tags(self) -> List[str]:
        """Get tags as a list."""
        if self.tags is None:
            return []
        try:
            import json
            return json.loads(self.tags) if isinstance(self.tags, str) else self.tags
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_tags(self, tags: List[str]) -> None:
        """Set tags from a list."""
        if not tags:
            self.tags = None
        else:
            import json
            self.tags = json.dumps(tags)
