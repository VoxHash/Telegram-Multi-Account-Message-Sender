"""
Send log model for tracking message sending activities.
"""

from datetime import datetime
from typing import Dict, Optional, Any
from enum import Enum

from sqlmodel import Field, Relationship
from sqlalchemy import JSON

from .base import BaseModel, JSONFieldMixin


class SendStatus(str, Enum):
    """Send status enumeration."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class SendLog(BaseModel, JSONFieldMixin, table=True):
    """Send log model for tracking message sending activities."""
    
    __tablename__ = "send_logs"
    
    # Campaign and account info
    campaign_id: Optional[int] = Field(foreign_key="campaigns.id", index=True, default=None)
    account_id: int = Field(foreign_key="accounts.id", index=True)
    recipient_id: Optional[int] = Field(foreign_key="recipients.id", index=True, default=None)
    
    # Warmup support
    is_warmup: bool = Field(default=False)
    recipient_type: Optional[str] = Field(default=None)
    recipient_identifier: Optional[str] = Field(default=None)
    sent_at: Optional[datetime] = Field(default=None)
    
    # Message details
    message_text: str
    message_type: str = Field(default="text")
    media_path: Optional[str] = Field(default=None)
    caption: Optional[str] = Field(default=None)
    
    # Status and timing
    status: SendStatus = Field(default=SendStatus.PENDING)
    error_message: Optional[str] = Field(default=None)
    error_code: Optional[str] = Field(default=None)
    
    # Timing
    scheduled_at: Optional[datetime] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    duration_ms: Optional[int] = Field(default=None)
    
    # Retry information
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    next_retry_at: Optional[datetime] = Field(default=None)
    
    # Telegram specific
    telegram_message_id: Optional[int] = Field(default=None)
    telegram_chat_id: Optional[int] = Field(default=None)
    telegram_error_code: Optional[str] = Field(default=None)
    
    # Additional metadata
    log_metadata: Optional[str] = Field(default=None, sa_column=JSON)
    user_agent: Optional[str] = Field(default=None)
    ip_address: Optional[str] = Field(default=None)
    
    # Relationships
    campaign: Optional["Campaign"] = Relationship(back_populates="send_logs")
    account: "Account" = Relationship(back_populates="send_logs")
    recipient: Optional["Recipient"] = Relationship(back_populates="send_logs")
    
    def start_sending(self) -> None:
        """Mark the send as started."""
        self.status = SendStatus.SENDING
        self.started_at = datetime.utcnow()
    
    def mark_sent(self, telegram_message_id: Optional[int] = None, telegram_chat_id: Optional[int] = None) -> None:
        """Mark the send as successful."""
        self.status = SendStatus.SENT
        self.completed_at = datetime.utcnow()
        self.telegram_message_id = telegram_message_id
        self.telegram_chat_id = telegram_chat_id
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_ms = int(duration.total_seconds() * 1000)
    
    def mark_failed(self, error_message: str, error_code: Optional[str] = None, telegram_error_code: Optional[str] = None) -> None:
        """Mark the send as failed."""
        self.status = SendStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.error_code = error_code
        self.telegram_error_code = telegram_error_code
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_ms = int(duration.total_seconds() * 1000)
    
    def mark_rate_limited(self, retry_after_seconds: int) -> None:
        """Mark the send as rate limited."""
        self.status = SendStatus.RATE_LIMITED
        self.completed_at = datetime.utcnow()
        self.next_retry_at = datetime.utcnow().timestamp() + retry_after_seconds
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_ms = int(duration.total_seconds() * 1000)
    
    def mark_skipped(self, reason: str) -> None:
        """Mark the send as skipped."""
        self.status = SendStatus.SKIPPED
        self.completed_at = datetime.utcnow()
        self.error_message = reason
    
    def mark_cancelled(self, reason: str) -> None:
        """Mark the send as cancelled."""
        self.status = SendStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.error_message = reason
    
    def can_retry(self) -> bool:
        """Check if the send can be retried."""
        return (
            self.status in [SendStatus.FAILED, SendStatus.RATE_LIMITED] and
            self.retry_count < self.max_retries
        )
    
    def increment_retry(self) -> None:
        """Increment retry count."""
        self.retry_count += 1
        self.status = SendStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.duration_ms = None
    
    def is_completed(self) -> bool:
        """Check if the send is completed."""
        return self.status in [SendStatus.SENT, SendStatus.FAILED, SendStatus.SKIPPED, SendStatus.CANCELLED]
    
    def is_successful(self) -> bool:
        """Check if the send was successful."""
        return self.status == SendStatus.SENT
    
    def get_duration_seconds(self) -> Optional[float]:
        """Get duration in seconds."""
        if self.duration_ms is not None:
            return self.duration_ms / 1000.0
        return None
    
    def get_error_summary(self) -> str:
        """Get a summary of the error."""
        if not self.error_message:
            return ""
        
        summary = self.error_message
        if self.error_code:
            summary += f" (Code: {self.error_code})"
        if self.telegram_error_code:
            summary += f" (Telegram: {self.telegram_error_code})"
        
        return summary
