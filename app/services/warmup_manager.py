"""
Account warmup management service.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from ..models import Account, SendLog, SendStatus
from ..services import get_logger, get_session
from ..core.telethon_client import TelegramClientManager


class WarmupManager(QObject):
    """Manages account warmup process."""
    
    # Signals
    warmup_started = pyqtSignal(int)  # account_id
    warmup_completed = pyqtSignal(int)  # account_id
    warmup_progress = pyqtSignal(int, int, int)  # account_id, sent, target
    warmup_error = pyqtSignal(int, str)  # account_id, error_message
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger()
        self.client_manager = TelegramClientManager()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_warmup_accounts)
        self.timer.start(60000)  # Check every minute
        
        # Track warmup progress
        self.warmup_in_progress: Dict[int, bool] = {}
        self.active_workers: List[WarmupWorker] = []
    
    def start_warmup(self, account_id: int) -> bool:
        """Start warmup process for an account."""
        try:
            with get_session() as session:
                account = session.get(Account, account_id)
                if not account:
                    self.logger.error(f"Account {account_id} not found for warmup")
                    return False
                
                if not account.warmup_enabled:
                    self.logger.info(f"Warmup disabled for account {account.name}")
                    return False
                
                # Check if account is online (handle both string and enum status)
                account_status = str(account.status).split('.')[-1] if '.' in str(account.status) else str(account.status)
                if account_status != "ONLINE":
                    self.logger.warning(f"Account {account.name} is not online (status: {account_status}), cannot start warmup")
                    self.warmup_error.emit(account_id, f"Account is not online (status: {account_status})")
                    return False
                
                if account.is_warmup_complete():
                    self.logger.info(f"Warmup already complete for account {account.name}")
                    return True
                
                if self.warmup_in_progress.get(account_id, False):
                    self.logger.info(f"Warmup already in progress for account {account.name}")
                    return True
                
                self.warmup_in_progress[account_id] = True
                self.warmup_started.emit(account_id)
                
                # Start warmup process in background using QThread
                from PyQt5.QtCore import QThread
                
                class WarmupWorker(QThread):
                    def __init__(self, warmup_manager, account_id):
                        super().__init__()
                        self.warmup_manager = warmup_manager
                        self.account_id = account_id
                    
                    def run(self):
                        # Create new event loop for this thread
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self.warmup_manager._warmup_account(self.account_id))
                        finally:
                            loop.close()
                
                worker = WarmupWorker(self, account_id)
                worker.finished.connect(lambda: self.cleanup_worker(worker))
                worker.finished.connect(lambda: self._reset_warmup_progress(account_id))
                worker.start()
                
                # Store worker reference to prevent garbage collection
                self.active_workers.append(worker)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error starting warmup for account {account_id}: {e}")
            self.warmup_error.emit(account_id, str(e))
            return False
    
    def cleanup_worker(self, worker):
        """Clean up finished worker thread."""
        try:
            if worker in self.active_workers:
                self.active_workers.remove(worker)
            worker.deleteLater()
        except Exception as e:
            self.logger.error(f"Error cleaning up worker: {e}")
    
    def _reset_warmup_progress(self, account_id: int):
        """Reset warmup progress flag when worker finishes."""
        try:
            self.warmup_in_progress[account_id] = False
            self.logger.debug(f"Reset warmup progress flag for account {account_id}")
        except Exception as e:
            self.logger.error(f"Error resetting warmup progress: {e}")
    
    async def _warmup_account(self, account_id: int):
        """Warmup an account by sending test messages."""
        try:
            with get_session() as session:
                account = session.get(Account, account_id)
                if not account:
                    return
                
                self.logger.info(f"Starting warmup for account {account.name}")
                
                # Get warmup settings
                target_messages = account.warmup_target_messages
                interval_minutes = account.warmup_interval_minutes
                sent_messages = account.warmup_messages_sent
                
                # Calculate how many messages to send
                messages_to_send = target_messages - sent_messages
                
                if messages_to_send <= 0:
                    self.logger.info(f"Warmup complete for account {account.name}")
                    self.warmup_completed.emit(account_id)
                    return
                
                # Send warmup messages
                for i in range(messages_to_send):
                    try:
                        # Create a test recipient (self)
                        test_recipient = {
                            "user_id": account.phone_number,  # Use phone number as test recipient
                            "username": f"test_{account.name}",
                            "first_name": "Test",
                            "last_name": "User"
                        }
                        
                        # Create warmup message
                        warmup_message = self._create_warmup_message(i + 1, target_messages)
                        
                        # Send message
                        result = await self._send_warmup_message(account, test_recipient, warmup_message)
                        
                        if result["success"]:
                            # Update warmup progress
                            account.warmup_messages_sent += 1
                            account.total_messages_sent += 1
                            account.last_activity = datetime.utcnow()
                            
                            session.commit()
                            
                            # Emit progress signal
                            self.warmup_progress.emit(account_id, account.warmup_messages_sent, target_messages)
                            
                            self.logger.info(f"Warmup message {account.warmup_messages_sent}/{target_messages} sent for account {account.name}")
                            
                            # Check if warmup is complete
                            if account.is_warmup_complete():
                                self.logger.info(f"Warmup completed for account {account.name}")
                                self.warmup_completed.emit(account_id)
                                break
                            
                            # Wait for interval before next message
                            if i < messages_to_send - 1:  # Don't wait after last message
                                await asyncio.sleep(interval_minutes * 60)
                        else:
                            self.logger.warning(f"Failed to send warmup message for account {account.name}: {result.get('error', 'Unknown error')}")
                            self.warmup_error.emit(account_id, result.get('error', 'Unknown error'))
                            break
                            
                    except Exception as e:
                        self.logger.error(f"Error sending warmup message {i+1} for account {account.name}: {e}")
                        self.warmup_error.emit(account_id, str(e))
                        break
                
        except Exception as e:
            self.logger.error(f"Error in warmup process for account {account_id}: {e}")
            self.warmup_error.emit(account_id, str(e))
        finally:
            self.warmup_in_progress[account_id] = False
    
    def _create_warmup_message(self, message_number: int, total_messages: int) -> str:
        """Create a warmup message."""
        messages = [
            f"Warmup message {message_number}/{total_messages} - Testing account functionality.",
            f"Account warmup in progress: {message_number}/{total_messages}",
            f"System test message {message_number}/{total_messages}",
            f"Warmup verification {message_number}/{total_messages}",
            f"Account testing message {message_number}/{total_messages}"
        ]
        
        # Use modulo to cycle through messages
        return messages[(message_number - 1) % len(messages)]
    
    async def _send_warmup_message(self, account: Account, recipient: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Send a warmup message."""
        try:
            # Get Telegram client
            self.logger.debug(f"Getting client for account {account.name} (ID: {account.id})")
            client = self.client_manager.get_client(account.id)
            if not client:
                # Try to add the account to client manager first
                self.logger.debug(f"Client not found, adding account {account.name} to client manager")
                try:
                    success = await self.client_manager.add_account(account)
                    if not success:
                        return {"success": False, "error": "Failed to add account to client manager"}
                    
                    client = self.client_manager.get_client(account.id)
                    if not client:
                        return {"success": False, "error": "Failed to initialize Telegram client after adding account"}
                except Exception as e:
                    self.logger.error(f"Error adding account to client manager: {e}")
                    return {"success": False, "error": f"Failed to add account to client manager: {e}"}
            
            # Check if client is ready
            self.logger.debug(f"Checking if client is ready for account {account.name}")
            if not client.is_ready():
                self.logger.warning(f"Client not ready for account {account.name}")
                return {"success": False, "error": "Telegram client is not ready"}
            
            # Send message to self (saved messages)
            try:
                # Send to "Saved Messages" (self)
                await client.send_message("me", message)
                
                # Create send log
                await self._create_warmup_log(account, recipient, message, True, None)
                
                return {"success": True}
                
            except Exception as e:
                # Create send log for failed message
                await self._create_warmup_log(account, recipient, message, False, str(e))
                return {"success": False, "error": str(e)}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _create_warmup_log(self, account: Account, recipient: Dict[str, Any], message: str, success: bool, error: Optional[str]):
        """Create a send log for warmup message."""
        try:
            with get_session() as session:
                send_log = SendLog(
                    account_id=account.id,
                    recipient_id=None,  # No specific recipient for warmup
                    recipient_type="warmup",
                    recipient_identifier=f"warmup_{account.id}",
                    message_text=message,
                    message_type="text",
                    status=SendStatus.SENT if success else SendStatus.FAILED,
                    error_message=error,
                    sent_at=datetime.utcnow(),
                    campaign_id=0,  # Use 0 for warmup (no real campaign)
                    is_warmup=True
                )
                
                session.add(send_log)
                session.commit()
                
        except Exception as e:
            self.logger.error(f"Error creating warmup log: {e}")
    
    def check_warmup_accounts(self):
        """Check for accounts that need warmup."""
        try:
            with get_session() as session:
                # Find accounts that need warmup
                accounts = session.query(Account).filter(
                    Account.warmup_enabled == True,
                    Account.is_active == True,
                    Account.is_deleted == False,
                    Account.status == "ONLINE"
                ).all()
                
                for account in accounts:
                    if not account.is_warmup_complete() and not self.warmup_in_progress.get(account.id, False):
                        # Check if it's time for next warmup message
                        if self._should_send_warmup_message(account):
                            self.start_warmup(account.id)
                            
        except Exception as e:
            self.logger.error(f"Error checking warmup accounts: {e}")
    
    def _should_send_warmup_message(self, account: Account) -> bool:
        """Check if it's time to send the next warmup message."""
        if account.warmup_messages_sent >= account.warmup_target_messages:
            return False
        
        # Check if enough time has passed since last warmup message
        if account.last_activity:
            time_since_last = datetime.utcnow() - account.last_activity
            return time_since_last >= timedelta(minutes=account.warmup_interval_minutes)
        
        # If no last activity, start warmup
        return True
    
    def get_warmup_status(self, account_id: int) -> Dict[str, Any]:
        """Get warmup status for an account."""
        try:
            with get_session() as session:
                account = session.get(Account, account_id)
                if not account:
                    return {"error": "Account not found"}
                
                return {
                    "enabled": account.warmup_enabled,
                    "sent": account.warmup_messages_sent,
                    "target": account.warmup_target_messages,
                    "complete": account.is_warmup_complete(),
                    "in_progress": self.warmup_in_progress.get(account_id, False),
                    "interval_minutes": account.warmup_interval_minutes
                }
                
        except Exception as e:
            self.logger.error(f"Error getting warmup status for account {account_id}: {e}")
            return {"error": str(e)}
    
    def reset_warmup(self, account_id: int) -> bool:
        """Reset warmup progress for an account."""
        try:
            with get_session() as session:
                account = session.get(Account, account_id)
                if not account:
                    return False
                
                account.warmup_messages_sent = 0
                session.commit()
                
                self.logger.info(f"Warmup reset for account {account.name}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error resetting warmup for account {account_id}: {e}")
            return False


# Global warmup manager instance
_warmup_manager: Optional[WarmupManager] = None


def get_warmup_manager() -> WarmupManager:
    """Get the global warmup manager instance."""
    global _warmup_manager
    if _warmup_manager is None:
        _warmup_manager = WarmupManager()
    return _warmup_manager
