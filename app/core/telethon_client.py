"""
Telegram client management using Telethon.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError, 
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    ApiIdInvalidError,
    HashInvalidError
)

from ..services.logger import get_logger
from ..models import Account, AccountStatus


class TelegramClientWrapper:
    """Wrapper for Telethon TelegramClient with additional functionality."""
    
    def __init__(self, account: Account, proxy: Optional[Dict[str, str]] = None):
        """Initialize client wrapper."""
        self.account = account
        self.proxy = proxy
        self.client: Optional[TelegramClient] = None
        self.logger = get_logger()
        self._connected = False
        self._authorized = False
    
    async def connect(self) -> bool:
        """Connect to Telegram."""
        try:
            if self.client and self._connected:
                return True
            
            # Create client
            self.client = TelegramClient(
                self.account.session_path,
                self.account.api_id,
                self.account.api_hash,
                proxy=self.proxy
            )
            
            # Connect
            await self.client.connect()
            self._connected = True
            
            # Check authorization
            self._authorized = await self.client.is_user_authorized()
            
            self.logger.log_telegram_event(
                "connect", 
                self.account.id, 
                f"Connected successfully. Authorized: {self._authorized}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect account {self.account.id}: {e}")
            self.account.status = AccountStatus.ERROR
            self.account.error_message = str(e)
            return False
    
    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client and self._connected:
            try:
                await self.client.disconnect()
                self._connected = False
                self._authorized = False
                self.logger.log_telegram_event("disconnect", self.account.id, "Disconnected")
            except Exception as e:
                self.logger.error(f"Error disconnecting account {self.account.id}: {e}")
    
    async def authorize(self, phone_code: str, password: Optional[str] = None) -> bool:
        """Authorize the client."""
        if not self.client or not self._connected:
            await self.connect()
        
        if not self.client:
            return False
        
        try:
            if not self._authorized:
                # Send code request
                await self.client.send_code_request(self.account.phone_number)
                
                # Sign in with code
                await self.client.sign_in(self.account.phone_number, phone_code)
                
                # Check if password is needed
                if not await self.client.is_user_authorized():
                    if password:
                        await self.client.sign_in(password=password)
                    else:
                        raise SessionPasswordNeededError("Two-step verification password required")
                
                self._authorized = True
                self.account.status = AccountStatus.ONLINE
                self.account.last_login = datetime.utcnow()
                self.account.error_message = None
                
                self.logger.log_telegram_event("authorize", self.account.id, "Authorization successful")
                return True
            
            return True
            
        except PhoneCodeInvalidError:
            self.logger.error(f"Invalid phone code for account {self.account.id}")
            self.account.status = AccountStatus.ERROR
            self.account.error_message = "Invalid phone code"
            return False
        except SessionPasswordNeededError:
            self.logger.error(f"Password required for account {self.account.id}")
            self.account.status = AccountStatus.ERROR
            self.account.error_message = "Two-step verification password required"
            return False
        except Exception as e:
            self.logger.error(f"Authorization failed for account {self.account.id}: {e}")
            self.account.status = AccountStatus.ERROR
            self.account.error_message = str(e)
            return False
    
    async def send_message(self, peer: str, text: str, media_path: Optional[str] = None) -> Dict[str, Any]:
        """Send a message."""
        if not self.client or not self._connected or not self._authorized:
            return {"success": False, "error": "Client not ready"}
        
        try:
            # Get entity
            entity = await self.client.get_entity(peer)
            
            # Send message
            if media_path and os.path.exists(media_path):
                message = await self.client.send_file(
                    entity, 
                    media_path, 
                    caption=text
                )
            else:
                message = await self.client.send_message(entity, text)
            
            self.logger.log_telegram_event(
                "send_message", 
                self.account.id, 
                f"Message sent to {peer}"
            )
            
            return {
                "success": True,
                "message_id": message.id,
                "chat_id": entity.id,
                "timestamp": datetime.utcnow()
            }
            
        except FloodWaitError as e:
            self.logger.warning(f"Rate limited for account {self.account.id}: {e.seconds} seconds")
            return {
                "success": False,
                "error": "Rate limited",
                "retry_after": e.seconds
            }
        except Exception as e:
            self.logger.error(f"Failed to send message from account {self.account.id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_me(self) -> Optional[Dict[str, Any]]:
        """Get current user info."""
        if not self.client or not self._connected or not self._authorized:
            return None
        
        try:
            me = await self.client.get_me()
            return {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "phone": me.phone
            }
        except Exception as e:
            self.logger.error(f"Failed to get user info for account {self.account.id}: {e}")
            return None
    
    def is_ready(self) -> bool:
        """Check if client is ready for sending."""
        return self._connected and self._authorized and self.client is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status."""
        return {
            "connected": self._connected,
            "authorized": self._authorized,
            "ready": self.is_ready(),
            "account_id": self.account.id,
            "phone": self.account.phone_number
        }


class TelegramClientManager:
    """Manages multiple Telegram clients."""
    
    def __init__(self):
        """Initialize client manager."""
        self.clients: Dict[int, TelegramClientWrapper] = {}
        self.logger = get_logger()
    
    async def add_account(self, account: Account) -> bool:
        """Add an account to the manager."""
        try:
            # Create proxy config if needed
            proxy = None
            if account.proxy_type and account.proxy_host and account.proxy_port:
                proxy = {
                    "proxy_type": account.proxy_type,
                    "addr": account.proxy_host,
                    "port": account.proxy_port,
                    "username": account.proxy_username,
                    "password": account.proxy_password
                }
            
            # Create client wrapper
            client = TelegramClientWrapper(account, proxy)
            
            # Connect
            if await client.connect():
                self.clients[account.id] = client
                self.logger.log_telegram_event("add_account", account.id, "Account added successfully")
                return True
            else:
                self.logger.error(f"Failed to add account {account.id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error adding account {account.id}: {e}")
            return False
    
    async def remove_account(self, account_id: int):
        """Remove an account from the manager."""
        if account_id in self.clients:
            await self.clients[account_id].disconnect()
            del self.clients[account_id]
            self.logger.log_telegram_event("remove_account", account_id, "Account removed")
    
    async def authorize_account(self, account_id: int, phone_code: str, password: Optional[str] = None) -> bool:
        """Authorize an account."""
        if account_id not in self.clients:
            return False
        
        return await self.clients[account_id].authorize(phone_code, password)
    
    async def send_message(self, account_id: int, peer: str, text: str, media_path: Optional[str] = None) -> Dict[str, Any]:
        """Send a message using an account."""
        if account_id not in self.clients:
            return {"success": False, "error": "Account not found"}
        
        return await self.clients[account_id].send_message(peer, text, media_path)
    
    def get_client(self, account_id: int) -> Optional[TelegramClientWrapper]:
        """Get a client by account ID."""
        return self.clients.get(account_id)
    
    def get_ready_clients(self) -> List[TelegramClientWrapper]:
        """Get all ready clients."""
        return [client for client in self.clients.values() if client.is_ready()]
    
    def get_client_status(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get client status."""
        if account_id in self.clients:
            return self.clients[account_id].get_status()
        return None
    
    def get_all_statuses(self) -> Dict[int, Dict[str, Any]]:
        """Get status of all clients."""
        return {account_id: client.get_status() for account_id, client in self.clients.items()}
    
    async def disconnect_all(self):
        """Disconnect all clients."""
        for client in self.clients.values():
            await client.disconnect()
        self.clients.clear()
        self.logger.info("All clients disconnected")
    
    def get_account_count(self) -> int:
        """Get number of managed accounts."""
        return len(self.clients)
    
    def get_ready_count(self) -> int:
        """Get number of ready accounts."""
        return len(self.get_ready_clients())
