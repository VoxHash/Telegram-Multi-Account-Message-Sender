"""
Message engine for handling campaign execution.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..services import get_logger
from ..models import Campaign, Account, Recipient, SendLog, SendStatus
from .telethon_client import TelegramClientManager
from .throttler import Throttler
from .spintax import SpintaxProcessor


class MessageEngine:
    """Core message sending engine."""
    
    def __init__(self, client_manager: TelegramClientManager):
        """Initialize message engine."""
        self.client_manager = client_manager
        self.throttler = Throttler()
        self.spintax_processor = SpintaxProcessor()
        self.logger = get_logger()
        self._running_campaigns: Dict[int, asyncio.Task] = {}
    
    async def send_message(
        self, 
        account_id: int, 
        recipient: Recipient, 
        message_text: str,
        media_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a single message."""
        try:
            # Check if account is ready
            client = self.client_manager.get_client(account_id)
            if not client or not client.is_ready():
                return {"success": False, "error": "Account not ready"}
            
            # Apply spintax if needed
            if "{" in message_text and "}" in message_text:
                spintax_result = self.spintax_processor.process(message_text)
                message_text = spintax_result.text
            
            # Send message
            result = await self.client_manager.send_message(
                account_id, 
                recipient.get_identifier(), 
                message_text, 
                media_path
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return {"success": False, "error": str(e)}


class CampaignRunner:
    """Runs campaigns and manages message sending."""
    
    def __init__(self, message_engine: MessageEngine):
        """Initialize campaign runner."""
        self.message_engine = message_engine
        self.logger = get_logger()
    
    async def run_campaign(self, campaign: Campaign) -> bool:
        """Run a campaign."""
        try:
            self.logger.log_campaign_event("start", campaign.id, f"Starting campaign: {campaign.name}")
            
            # Update campaign status
            campaign.status = "running"
            campaign.start_time_actual = datetime.utcnow()
            
            # Get recipients
            recipients = await self._get_campaign_recipients(campaign)
            
            # Process recipients
            for recipient in recipients:
                if campaign.status != "running":
                    break
                
                # Select account
                account = await self._select_account(campaign)
                if not account:
                    self.logger.warning(f"No available account for campaign {campaign.id}")
                    continue
                
                # Send message
                await self._send_campaign_message(campaign, account, recipient)
                
                # Rate limiting
                await asyncio.sleep(campaign.messages_per_minute / 60)
            
            # Mark campaign as completed
            campaign.status = "completed"
            campaign.end_time_actual = datetime.utcnow()
            
            self.logger.log_campaign_event("complete", campaign.id, "Campaign completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error running campaign {campaign.id}: {e}")
            campaign.status = "error"
            return False
    
    async def _get_campaign_recipients(self, campaign: Campaign) -> List[Recipient]:
        """Get recipients for a campaign."""
        # This would query the database for recipients
        # For now, return empty list
        return []
    
    async def _select_account(self, campaign: Campaign) -> Optional[Account]:
        """Select an account for sending."""
        # This would implement account selection logic
        # For now, return None
        return None
    
    async def _send_campaign_message(
        self, 
        campaign: Campaign, 
        account: Account, 
        recipient: Recipient
    ):
        """Send a campaign message."""
        try:
            # Get message content
            message_text = campaign.get_effective_message_text(recipient.id)
            media_path = campaign.get_effective_media_path(recipient.id)
            
            # Send message
            result = await self.message_engine.send_message(
                account.id,
                recipient,
                message_text,
                media_path
            )
            
            # Log result
            if result["success"]:
                self.logger.log_send_event("sent", account.id, recipient.id, "Message sent")
                campaign.sent_count += 1
            else:
                self.logger.log_send_event("failed", account.id, recipient.id, result["error"])
                campaign.failed_count += 1
            
        except Exception as e:
            self.logger.error(f"Error sending campaign message: {e}")
            campaign.failed_count += 1
