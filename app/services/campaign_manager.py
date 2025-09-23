"""
Campaign management service for handling campaign execution, scheduling, and status updates.
"""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from ..models import Campaign, CampaignStatus, Account, Recipient, SendLog, SendStatus
from ..services import get_logger, get_session
from ..core.engine import MessageEngine, CampaignRunner
from ..core.telethon_client import TelegramClientManager
from ..core.spintax import SpintaxProcessor


class CampaignManager(QObject):
    """Manages campaign execution, scheduling, and status updates."""
    
    # Signals for GUI updates
    campaign_started = pyqtSignal(int)  # campaign_id
    campaign_paused = pyqtSignal(int)  # campaign_id
    campaign_stopped = pyqtSignal(int)  # campaign_id
    campaign_completed = pyqtSignal(int)  # campaign_id
    campaign_progress_updated = pyqtSignal(int, dict)  # campaign_id, progress_data
    campaign_error = pyqtSignal(int, str)  # campaign_id, error_message
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.client_manager = TelegramClientManager()
        self.message_engine = MessageEngine(self.client_manager)
        self.campaign_runner = CampaignRunner(self.message_engine)
        self.spintax_processor = SpintaxProcessor()
        
        # Running campaigns tracking
        self._running_campaigns: Dict[int, asyncio.Task] = {}
        self._campaign_tasks: Dict[int, threading.Thread] = {}
        self._campaign_status: Dict[int, str] = {}
        
        # Track sent recipients per campaign to avoid resending
        self._sent_recipients: Dict[int, set] = {}  # campaign_id -> set of recipient_ids
        self._campaign_recipient_hashes: Dict[int, str] = {}  # campaign_id -> recipient_list_hash
        
        # Setup timer for status updates
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_campaign_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
        # Setup timer for scheduled campaigns
        self.scheduler_timer = QTimer()
        self.scheduler_timer.timeout.connect(self._check_scheduled_campaigns)
        self.scheduler_timer.start(60000)  # Check every minute
    
    def start_campaign(self, campaign_id: int) -> bool:
        """Start a campaign."""
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    self.logger.error(f"Campaign {campaign_id} not found")
                    return False
                
                if not campaign.can_start():
                    self.logger.warning(f"Campaign {campaign_id} cannot be started")
                    return False
                
                # Check if already running
                if campaign_id in self._running_campaigns:
                    self.logger.warning(f"Campaign {campaign_id} is already running")
                    return False
                
                # Double-check database status
                if campaign.status == CampaignStatus.RUNNING:
                    self.logger.warning(f"Campaign {campaign_id} is already running in database")
                    return False
                
                # Check if this is a retry and handle accordingly
                is_retry = campaign.status in [CampaignStatus.COMPLETED, CampaignStatus.STOPPED, CampaignStatus.ERROR]
                recipients_changed = False
                
                if is_retry:
                    # Check if recipients have changed
                    current_hash = self._calculate_recipient_hash(campaign)
                    stored_hash = self._campaign_recipient_hashes.get(campaign_id)
                    recipients_changed = current_hash != stored_hash
                    
                    if not recipients_changed and campaign.failed_count == 0:
                        self.logger.warning(f"Campaign {campaign_id} has no failed messages and recipients unchanged - no retry needed")
                        return False
                
                # Update campaign status
                if campaign.status == CampaignStatus.SCHEDULED:
                    campaign.status = CampaignStatus.RUNNING
                elif campaign.status == CampaignStatus.PAUSED:
                    campaign.status = CampaignStatus.RUNNING
                else:
                    campaign.status = CampaignStatus.RUNNING
                
                # Reset progress if this is a retry with changed recipients
                if is_retry and recipients_changed:
                    campaign.sent_count = 0
                    campaign.failed_count = 0
                    campaign.skipped_count = 0
                    campaign.progress_percentage = 0.0
                    # Clear sent recipients tracking for this campaign
                    self._sent_recipients[campaign_id] = set()
                
                campaign.start_time_actual = datetime.utcnow()
                campaign.last_activity = datetime.utcnow()
                session.commit()
                
                # Store recipient hash for change detection
                current_hash = self._calculate_recipient_hash(campaign)
                self._campaign_recipient_hashes[campaign_id] = current_hash
                
                # Mark as running BEFORE starting thread to prevent race conditions
                self._running_campaigns[campaign_id] = True
                self._campaign_status[campaign_id] = "running"
                
                # Start campaign in background thread
                thread = threading.Thread(
                    target=self._run_campaign_thread,
                    args=(campaign_id,),
                    daemon=True
                )
                thread.start()
                self._campaign_tasks[campaign_id] = thread
                
                self.logger.info(f"Started campaign {campaign_id}: {campaign.name}")
                self.logger.debug(f"Campaign {campaign_id} marked as running in tracking")
                self.campaign_started.emit(campaign_id)
                return True
                
        except Exception as e:
            self.logger.error(f"Error starting campaign {campaign_id}: {e}")
            self.campaign_error.emit(campaign_id, str(e))
            return False
    
    def pause_campaign(self, campaign_id: int) -> bool:
        """Pause a running campaign."""
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    self.logger.error(f"Campaign {campaign_id} not found")
                    return False
                
                if campaign.status != CampaignStatus.RUNNING:
                    self.logger.warning(f"Campaign {campaign_id} is not running")
                    return False
                
                # Update campaign status
                campaign.status = CampaignStatus.PAUSED
                campaign.last_activity = datetime.utcnow()
                session.commit()
                
                # Cancel running task
                if campaign_id in self._running_campaigns:
                    del self._running_campaigns[campaign_id]
                
                if campaign_id in self._campaign_tasks:
                    del self._campaign_tasks[campaign_id]
                
                self._campaign_status[campaign_id] = "paused"
                
                self.logger.info(f"Paused campaign {campaign_id}: {campaign.name}")
                self.campaign_paused.emit(campaign_id)
                return True
                
        except Exception as e:
            self.logger.error(f"Error pausing campaign {campaign_id}: {e}")
            self.campaign_error.emit(campaign_id, str(e))
            return False
    
    def stop_campaign(self, campaign_id: int) -> bool:
        """Stop a campaign."""
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    self.logger.error(f"Campaign {campaign_id} not found")
                    return False
                
                # Update campaign status
                campaign.status = CampaignStatus.STOPPED
                campaign.end_time_actual = datetime.utcnow()
                campaign.last_activity = datetime.utcnow()
                session.commit()
                
                # Cancel running task
                if campaign_id in self._running_campaigns:
                    del self._running_campaigns[campaign_id]
                
                if campaign_id in self._campaign_tasks:
                    del self._campaign_tasks[campaign_id]
                
                self._campaign_status[campaign_id] = "stopped"
                
                self.logger.info(f"Stopped campaign {campaign_id}: {campaign.name}")
                self.campaign_stopped.emit(campaign_id)
                return True
                
        except Exception as e:
            self.logger.error(f"Error stopping campaign {campaign_id}: {e}")
            self.campaign_error.emit(campaign_id, str(e))
            return False
    
    def resume_campaign(self, campaign_id: int) -> bool:
        """Resume a paused campaign."""
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    self.logger.error(f"Campaign {campaign_id} not found")
                    return False
                
                if campaign.status != CampaignStatus.PAUSED:
                    self.logger.warning(f"Cannot resume campaign {campaign_id} with status {campaign.status}")
                    return False
                
                # Update status to RUNNING
                campaign.status = CampaignStatus.RUNNING
                campaign.last_activity = datetime.now()
                session.commit()
                
                # Start the campaign thread
                self._running_campaigns[campaign_id] = True
                self._campaign_status[campaign_id] = "RUNNING"
                
                # Start campaign thread
                import threading
                thread = threading.Thread(target=self._run_campaign_thread, args=(campaign_id,))
                thread.daemon = True
                thread.start()
                
                self.logger.info(f"Resumed campaign {campaign_id}")
                self.campaign_started.emit(campaign_id)
                return True
                
        except Exception as e:
            self.logger.error(f"Error resuming campaign {campaign_id}: {e}")
            self.campaign_error.emit(campaign_id, str(e))
            return False
    
    def retry_campaign(self, campaign_id: int) -> bool:
        """Retry a failed campaign."""
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    self.logger.error(f"Campaign {campaign_id} not found")
                    return False
                
                if campaign.status not in [CampaignStatus.FAILED, CampaignStatus.INCOMPLETED, CampaignStatus.STOPPED, CampaignStatus.COMPLETED, CampaignStatus.ERROR]:
                    self.logger.warning(f"Cannot retry campaign {campaign_id} with status {campaign.status}")
                    return False
                
                # Reset campaign status and counters
                campaign.status = CampaignStatus.DRAFT
                campaign.sent_count = 0
                campaign.failed_count = 0
                campaign.skipped_count = 0
                campaign.progress_percentage = 0.0
                campaign.last_activity = datetime.now()
                session.commit()
                
                # Start the campaign
                return self.start_campaign(campaign_id)
                
        except Exception as e:
            self.logger.error(f"Error retrying campaign {campaign_id}: {e}")
            self.campaign_error.emit(campaign_id, str(e))
            return False
    
    def get_campaign_status(self, campaign_id: int) -> str:
        """Get current campaign status."""
        return self._campaign_status.get(campaign_id, "unknown")
    
    def is_campaign_running(self, campaign_id: int) -> bool:
        """Check if campaign is currently running."""
        return campaign_id in self._running_campaigns
    
    def can_retry_campaign(self, campaign_id: int) -> bool:
        """Check if campaign can be retried (has failed messages or recipients changed)."""
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    return False
                
                # Can retry if campaign status is FAILED or INCOMPLETED
                if campaign.status in [CampaignStatus.FAILED, CampaignStatus.INCOMPLETED]:
                    return True
                
                # Can retry if campaign is not running and has failed messages
                if campaign.failed_count > 0:
                    return True
                
                # Can retry if recipients have changed
                current_hash = self._calculate_recipient_hash(campaign)
                stored_hash = self._campaign_recipient_hashes.get(campaign_id)
                if current_hash != stored_hash:
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking retry eligibility: {e}")
            return False
    
    def duplicate_campaign(self, campaign_id: int) -> Optional[int]:
        """Duplicate a completed campaign as a new draft campaign."""
        try:
            with get_session() as session:
                # Get the original campaign
                original_campaign = session.get(Campaign, campaign_id)
                if not original_campaign:
                    self.logger.error(f"Campaign {campaign_id} not found")
                    return None
                
                # Allow duplicating any campaign (DRAFT, COMPLETED, etc.)
                # This is useful for creating variations of existing campaigns
                
                # Create new campaign with same settings but reset status and counts
                new_campaign = Campaign(
                    name=f"{original_campaign.name} (Copy)",
                    description=original_campaign.description,
                    campaign_type=original_campaign.campaign_type,
                    status=CampaignStatus.DRAFT,
                    message_text=original_campaign.message_text,
                    message_type=original_campaign.message_type,
                    media_path=original_campaign.media_path,
                    caption=original_campaign.caption,
                    use_spintax=original_campaign.use_spintax,
                    spintax_text=original_campaign.spintax_text,
                    use_ab_testing=original_campaign.use_ab_testing,
                    ab_variants=original_campaign.ab_variants,
                    ab_split_percentages=original_campaign.ab_split_percentages,
                    start_time=original_campaign.start_time,
                    end_time=original_campaign.end_time,
                    timezone=original_campaign.timezone,
                    messages_per_minute=original_campaign.messages_per_minute,
                    messages_per_hour=original_campaign.messages_per_hour,
                    messages_per_day=original_campaign.messages_per_day,
                    random_jitter_seconds=original_campaign.random_jitter_seconds,
                    account_selection_strategy=original_campaign.account_selection_strategy,
                    account_weights=original_campaign.account_weights,
                    max_concurrent_accounts=original_campaign.max_concurrent_accounts,
                    recipient_source=original_campaign.recipient_source,
                    recipient_list_id=original_campaign.recipient_list_id,
                    recipient_filters=original_campaign.recipient_filters,
                    dry_run=original_campaign.dry_run,
                    respect_rate_limits=original_campaign.respect_rate_limits,
                    stop_on_error=original_campaign.stop_on_error,
                    max_retries=original_campaign.max_retries,
                    # Reset progress fields
                    total_recipients=0,
                    sent_count=0,
                    failed_count=0,
                    skipped_count=0,
                    progress_percentage=0.0,
                    start_time_actual=None,
                    end_time_actual=None,
                    last_activity=None,
                    is_active=True,
                    tags=original_campaign.tags,
                    notes=f"Duplicated from campaign '{original_campaign.name}' (ID: {original_campaign.id})"
                )
                
                session.add(new_campaign)
                session.commit()
                session.refresh(new_campaign)
                
                self.logger.info(f"Duplicated campaign {campaign_id} as new campaign {new_campaign.id}")
                return new_campaign.id
                
        except Exception as e:
            self.logger.error(f"Error duplicating campaign {campaign_id}: {e}")
            return None
    
    def _calculate_recipient_hash(self, campaign: Campaign) -> str:
        """Calculate hash of current recipient list for a campaign."""
        try:
            import hashlib
            
            # Get current recipients
            recipients = self._get_campaign_recipients_sync(campaign)
            
            # Create hash from recipient IDs
            recipient_ids = sorted([r.id for r in recipients])
            hash_input = f"{campaign.id}_{len(recipient_ids)}_{'_'.join(map(str, recipient_ids))}"
            
            return hashlib.md5(hash_input.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating recipient hash: {e}")
            return ""
    
    def _get_campaign_recipients_sync(self, campaign: Campaign) -> List[Recipient]:
        """Get recipients for a campaign synchronously."""
        try:
            with get_session() as session:
                from sqlmodel import select
                
                # Get recipients based on campaign settings
                if campaign.recipient_source == "manual":
                    # Get all active recipients
                    query = select(Recipient).where(
                        Recipient.is_deleted == False,
                        Recipient.status == "active"
                    )
                else:
                    # For other sources, return empty for now
                    return []
                
                recipients = session.exec(query).all()
                return list(recipients)
                
        except Exception as e:
            self.logger.error(f"Error getting recipients: {e}")
            return []
    
    async def _get_sent_recipients(self, campaign_id: int) -> set:
        """Get recipients that have already been sent to successfully."""
        try:
            with get_session() as session:
                from sqlmodel import select
                from ..models import SendLog, SendStatus
                
                # Get all successful send logs for this campaign
                query = select(SendLog.recipient_id).where(
                    SendLog.campaign_id == campaign_id,
                    SendLog.status == SendStatus.SENT
                )
                
                sent_recipient_ids = session.exec(query).all()
                return set(sent_recipient_ids)
                
        except Exception as e:
            self.logger.error(f"Error getting sent recipients: {e}")
            return set()
    
    def _run_campaign_thread(self, campaign_id: int):
        """Run campaign in a separate thread."""
        try:
            # Use asyncio.run() to create a completely isolated event loop
            asyncio.run(self._run_campaign_async(campaign_id))
            
        except Exception as e:
            self.logger.error(f"Error in campaign thread {campaign_id}: {e}")
            self.campaign_error.emit(campaign_id, str(e))
        finally:
            # Clean up
            if campaign_id in self._running_campaigns:
                del self._running_campaigns[campaign_id]
            if campaign_id in self._campaign_tasks:
                del self._campaign_tasks[campaign_id]
            if campaign_id in self._campaign_status:
                del self._campaign_status[campaign_id]
    
    async def _run_campaign_async(self, campaign_id: int):
        """Run campaign asynchronously."""
        self.logger.info(f"Campaign {campaign_id} execution started")
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if not campaign:
                    return
                
                # Get recipients
                recipients = await self._get_campaign_recipients(campaign)
                if not recipients:
                    self.logger.warning(f"No recipients found for campaign {campaign_id}")
                    campaign.status = CampaignStatus.COMPLETED
                    campaign.end_time_actual = datetime.utcnow()
                    session.commit()
                    self.campaign_completed.emit(campaign_id)
                    return
                
                # Update total recipients
                campaign.total_recipients = len(recipients)
                session.commit()
                
                # Get available accounts
                accounts = await self._get_available_accounts()
                if not accounts:
                    self.logger.error(f"No available accounts for campaign {campaign_id}")
                    campaign.status = CampaignStatus.ERROR
                    session.commit()
                    self.campaign_error.emit(campaign_id, "No available accounts")
                    return
                
                # For campaign execution, we'll create new clients in the thread
                # This avoids the asyncio event loop conflict
                ready_accounts = []
                for account in accounts:
                    # Check if account is online (handle both string and enum)
                    account_status = str(account.status).split('.')[-1] if hasattr(account.status, 'value') else str(account.status)
                    if account_status == "ONLINE":
                        ready_accounts.append(account)
                    else:
                        self.logger.warning(f"Account {account.name} (ID: {account.id}) is not online (status: {account_status}) - skipping")
                
                if not ready_accounts:
                    self.logger.error(f"No ready accounts for campaign {campaign_id}")
                    campaign.status = CampaignStatus.ERROR
                    campaign.end_time_actual = datetime.utcnow()
                    session.commit()
                    self.campaign_error.emit(campaign_id, "No ready accounts")
                    
                    # Create error log
                    await self._create_error_log(campaign, "No ready accounts available")
                    return
                
                # Use only ready accounts
                accounts = ready_accounts
                
                # Initialize sent recipients tracking for this campaign
                if campaign_id not in self._sent_recipients:
                    self._sent_recipients[campaign_id] = set()
                
                # Get already sent recipients from database
                already_sent = await self._get_sent_recipients(campaign_id)
                self._sent_recipients[campaign_id].update(already_sent)
                
                # Process recipients
                sent_count = campaign.sent_count  # Start with existing count
                failed_count = campaign.failed_count  # Start with existing count
                skipped_count = campaign.skipped_count  # Start with existing count
                
                for i, recipient in enumerate(recipients):
                    # Check if campaign should continue
                    with get_session() as check_session:
                        check_campaign = check_session.get(Campaign, campaign_id)
                        if check_campaign.status != CampaignStatus.RUNNING:
                            break
                    
                    # Skip if already sent successfully
                    if recipient.id in self._sent_recipients[campaign_id]:
                        self.logger.debug(f"Skipping already sent recipient {recipient.get_display_name()}")
                        continue
                    
                    try:
                        # Select account
                        account = self._select_account(accounts, campaign)
                        if not account:
                            skipped_count += 1
                            continue
                        
                        # Prepare message
                        message_text = self._prepare_message(campaign, recipient)
                        media_path = campaign.get_effective_media_path(recipient.id)
                        
                        # Send message
                        result = await self._send_message(account, recipient, message_text, media_path)
                        
                        # Update counts and tracking
                        if result["success"]:
                            sent_count += 1
                            self._sent_recipients[campaign_id].add(recipient.id)
                            self.logger.info(f"Sent message to {recipient.get_display_name()}")
                        else:
                            failed_count += 1
                            self.logger.warning(f"Failed to send message to {recipient.get_display_name()}: {result.get('error', 'Unknown error')}")
                        
                        # Create send log
                        await self._create_send_log(campaign, account, recipient, result)
                        self.logger.debug(f"Created send log for campaign {campaign_id}, account {account.id}, recipient {recipient.id}")
                        
                        # Update campaign progress
                        progress = ((i + 1) / len(recipients)) * 100
                        await self._update_campaign_progress(campaign_id, sent_count, failed_count, skipped_count, progress)
                        
                        # Rate limiting
                        if i < len(recipients) - 1:  # Don't sleep after last message
                            await asyncio.sleep(60 / campaign.messages_per_minute)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing recipient {recipient.id}: {e}")
                        failed_count += 1
                
                # Mark campaign as completed
                with get_session() as final_session:
                    final_campaign = final_session.get(Campaign, campaign_id)
                    if final_campaign.status == CampaignStatus.RUNNING:
                        # Determine final status based on results
                        if failed_count > 0 and sent_count == 0:
                            # All messages failed
                            final_campaign.status = CampaignStatus.FAILED
                        elif failed_count > 0 and sent_count > 0:
                            # Some messages failed
                            final_campaign.status = CampaignStatus.INCOMPLETED
                        else:
                            # All messages sent successfully
                            final_campaign.status = CampaignStatus.COMPLETED
                        
                        final_campaign.end_time_actual = datetime.utcnow()
                        final_campaign.sent_count = sent_count
                        final_campaign.failed_count = failed_count
                        final_campaign.skipped_count = skipped_count
                        final_campaign.progress_percentage = 100.0
                        final_campaign.last_activity = datetime.utcnow()
                        final_session.commit()
                        
                        self.logger.info(f"Completed campaign {campaign_id}: {sent_count} sent, {failed_count} failed, {skipped_count} skipped")
                        self.campaign_completed.emit(campaign_id)
                
        except Exception as e:
            self.logger.error(f"Error running campaign {campaign_id}: {e}")
            self.campaign_error.emit(campaign_id, str(e))
    
    async def _get_campaign_recipients(self, campaign: Campaign) -> List[Recipient]:
        """Get recipients for a campaign."""
        try:
            with get_session() as session:
                from sqlmodel import select
                
                # Get recipients based on campaign settings
                if campaign.recipient_source == "manual":
                    # Get all active recipients
                    query = select(Recipient).where(
                        Recipient.is_deleted == False,
                        Recipient.status == "active"
                    )
                else:
                    # For other sources, return empty for now
                    return []
                
                recipients = session.exec(query).all()
                return list(recipients)
                
        except Exception as e:
            self.logger.error(f"Error getting recipients: {e}")
            return []
    
    async def _get_available_accounts(self) -> List[Account]:
        """Get available accounts for sending."""
        try:
            with get_session() as session:
                from sqlmodel import select
                
                query = select(Account).where(
                    Account.is_deleted == False,
                    Account.status == "ONLINE",
                    Account.is_active == True
                )
                
                accounts = session.exec(query).all()
                return list(accounts)
                
        except Exception as e:
            self.logger.error(f"Error getting accounts: {e}")
            return []
    
    def _select_account(self, accounts: List[Account], campaign: Campaign) -> Optional[Account]:
        """Select an account for sending."""
        if not accounts:
            return None
        
        # Simple round-robin selection for now
        # Could be enhanced with weighted selection, random selection, etc.
        return accounts[0]  # For now, just return the first available account
    
    def _prepare_message(self, campaign: Campaign, recipient: Recipient) -> str:
        """Prepare message text for sending."""
        message_text = campaign.get_effective_message_text(recipient.id)
        
        # Apply spintax if enabled
        if campaign.use_spintax and message_text:
            try:
                spintax_result = self.spintax_processor.process(message_text)
                message_text = spintax_result.text
                self.logger.debug(f"Spintax processed: '{message_text}'")
            except Exception as e:
                self.logger.warning(f"Error processing spintax: {e}")
        
        # Apply basic personalization
        message_text = message_text.replace("{name}", recipient.get_display_name())
        message_text = message_text.replace("{username}", recipient.username or "")
        
        return message_text
    
    async def _send_message(self, account: Account, recipient: Recipient, message_text: str, media_path: Optional[str]) -> Dict[str, Any]:
        """Send a message using a fresh client to avoid event loop conflicts."""
        try:
            self.logger.debug(f"Creating fresh client for account {account.id}")
            # Import here to avoid circular imports
            from telethon import TelegramClient
            from telethon.errors import SessionPasswordNeededError
            import os
            
            # Create a completely fresh Telegram client
            client = TelegramClient(
                account.session_path,
                account.api_id,
                account.api_hash
            )
            
            # Connect the client
            try:
                await client.start(
                    phone=account.phone_number,
                    password=account.session_password
                )
            except SessionPasswordNeededError:
                await client.disconnect()
                return {"success": False, "error": "Session password needed"}
            except Exception as e:
                await client.disconnect()
                return {"success": False, "error": f"Failed to start client: {e}"}
            
            if not client.is_connected():
                await client.disconnect()
                return {"success": False, "error": "Account not connected"}
            
            # Get entity
            try:
                entity = await client.get_entity(recipient.get_identifier())
            except Exception as e:
                await client.disconnect()
                return {"success": False, "error": f"Failed to get entity: {e}"}
            
            # Send message
            try:
                if media_path and os.path.exists(media_path):
                    # Send with media
                    sent_message = await client.send_file(
                        entity,
                        media_path,
                        caption=message_text
                    )
                elif media_path and (media_path.startswith('http://') or media_path.startswith('https://')):
                    # Send URL as media
                    sent_message = await client.send_file(
                        entity,
                        media_path,
                        caption=message_text
                    )
                else:
                    # Send text only
                    sent_message = await client.send_message(
                        entity,
                        message_text
                    )
                
                await client.disconnect()
                self.logger.debug(f"Successfully sent message to {recipient.get_display_name()}")
                return {"success": True, "message_id": sent_message.id}
                
            except Exception as e:
                await client.disconnect()
                return {"success": False, "error": f"Failed to send message: {e}"}
            
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_error_log(self, campaign: Campaign, error_message: str):
        """Create an error log entry for campaign failures."""
        try:
            with get_session() as session:
                send_log = SendLog(
                    campaign_id=campaign.id,
                    account_id=None,  # No specific account for general errors
                    recipient_id=None,  # No specific recipient for general errors
                    recipient_type="error",
                    recipient_identifier=f"campaign_{campaign.id}_error",
                    message_text=campaign.message_text or "",
                    message_type=campaign.message_type or "text",
                    status=SendStatus.FAILED,
                    error_message=error_message,
                    sent_at=datetime.utcnow(),
                    is_warmup=False
                )
                
                session.add(send_log)
                session.commit()
                
        except Exception as e:
            self.logger.error(f"Error creating error log: {e}")
    
    async def _create_send_log(self, campaign: Campaign, account: Account, recipient: Recipient, result: Dict[str, Any]):
        """Create a send log entry."""
        try:
            self.logger.debug(f"Creating send log for campaign {campaign.id}, account {account.id}, recipient {recipient.id}, success: {result['success']}")
            with get_session() as session:
                send_log = SendLog(
                    campaign_id=campaign.id,
                    account_id=account.id,
                    recipient_id=recipient.id,
                    message_text=result.get("message_text", ""),
                    status=SendStatus.SENT if result["success"] else SendStatus.FAILED,
                    error_message=result.get("error"),
                    sent_at=datetime.utcnow() if result["success"] else None,
                    duration_ms=int(result.get("duration", 0) * 1000) if result.get("duration") else None
                )
                session.add(send_log)
                session.commit()
        except Exception as e:
            self.logger.error(f"Error creating send log: {e}")
    
    async def _update_campaign_progress(self, campaign_id: int, sent: int, failed: int, skipped: int, progress: float):
        """Update campaign progress."""
        try:
            with get_session() as session:
                campaign = session.get(Campaign, campaign_id)
                if campaign:
                    campaign.sent_count = sent
                    campaign.failed_count = failed
                    campaign.skipped_count = skipped
                    campaign.progress_percentage = progress
                    campaign.last_activity = datetime.utcnow()
                    session.commit()
                    
                    # Emit progress update signal
                    progress_data = {
                        "sent": sent,
                        "failed": failed,
                        "skipped": skipped,
                        "progress": progress
                    }
                    self.campaign_progress_updated.emit(campaign_id, progress_data)
        except Exception as e:
            self.logger.error(f"Error updating campaign progress: {e}")
    
    def _update_campaign_status(self):
        """Update campaign status from database."""
        try:
            with get_session() as session:
                from sqlmodel import select
                
                # Get all running campaigns from database
                query = select(Campaign).where(
                    Campaign.status == CampaignStatus.RUNNING,
                    Campaign.is_deleted == False
                )
                running_campaigns = session.exec(query).all()
                
                # Check if any running campaigns are no longer in our tracking
                for campaign in running_campaigns:
                    if campaign.id not in self._running_campaigns:
                        # Campaign was started externally or restarted
                        self._campaign_status[campaign.id] = "running"
                        self.campaign_started.emit(campaign.id)
                
        except Exception as e:
            self.logger.error(f"Error updating campaign status: {e}")
    
    def _check_scheduled_campaigns(self):
        """Check for campaigns that should be started based on their start time."""
        try:
            with get_session() as session:
                from sqlmodel import select
                from datetime import datetime
                import pytz
                
                # Get campaigns that are scheduled and should start now
                now = datetime.utcnow()
                query = select(Campaign).where(
                    Campaign.status == CampaignStatus.SCHEDULED,
                    Campaign.is_deleted == False,
                    Campaign.start_time <= now,
                    Campaign.is_active == True
                )
                
                scheduled_campaigns = session.exec(query).all()
                
                if scheduled_campaigns:
                    self.logger.info(f"Found {len(scheduled_campaigns)} scheduled campaigns to start")
                
                for campaign in scheduled_campaigns:
                    self.logger.info(f"Starting scheduled campaign {campaign.id}: {campaign.name} (scheduled for {campaign.start_time})")
                    # Start the campaign
                    success = self.start_campaign(campaign.id)
                    if success:
                        self.logger.info(f"Successfully started scheduled campaign {campaign.id}")
                    else:
                        self.logger.warning(f"Failed to start scheduled campaign {campaign.id}")
                
        except Exception as e:
            self.logger.error(f"Error checking scheduled campaigns: {e}")


# Global campaign manager instance
_campaign_manager = None

def get_campaign_manager() -> CampaignManager:
    """Get the global campaign manager instance."""
    global _campaign_manager
    if _campaign_manager is None:
        _campaign_manager = CampaignManager()
    return _campaign_manager
