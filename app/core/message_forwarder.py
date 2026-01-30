"""
Message forwarding functionality for Telegram.
"""

from typing import Dict, Any, Optional
from telethon import TelegramClient
from telethon.errors import MessageIdInvalidError, ChannelPrivateError

from ..services import get_logger


class MessageForwarder:
    """Handles forwarding messages from Telegram chats/channels."""
    
    def __init__(self):
        """Initialize message forwarder."""
        self.logger = get_logger()
    
    async def forward_message(
        self,
        client: TelegramClient,
        from_chat: str,  # Chat identifier (username, ID, etc.)
        message_id: int,
        to_chat: str,  # Destination chat identifier
        thread_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Forward a message from one chat to another.
        
        Args:
            client: TelegramClient instance
            from_chat: Source chat identifier (username, ID, etc.)
            message_id: ID of the message to forward
            to_chat: Destination chat identifier
            thread_id: Optional thread ID for group threads
        
        Returns:
            Dict with success status and result/error
        """
        try:
            # Get source entity
            try:
                from_entity = await client.get_entity(from_chat)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Could not access source chat: {e}"
                }
            
            # Get destination entity
            try:
                to_entity = await client.get_entity(to_chat)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Could not access destination chat: {e}"
                }
            
            # Forward the message
            try:
                if thread_id:
                    # Forward to a specific thread
                    result = await client.forward_messages(
                        to_entity,
                        message_id,
                        from_entity,
                        silent=False
                    )
                    # Note: Telethon doesn't directly support thread_id in forward_messages
                    # We may need to send to the thread separately or use a workaround
                    self.logger.warning("Thread forwarding may require additional implementation")
                else:
                    # Forward to chat/channel
                    result = await client.forward_messages(
                        to_entity,
                        message_id,
                        from_entity,
                        silent=False
                    )
                
                return {
                    "success": True,
                    "message_id": result[0].id if isinstance(result, list) else result.id,
                    "forwarded_from": {
                        "chat_id": from_entity.id,
                        "message_id": message_id
                    }
                }
                
            except MessageIdInvalidError:
                return {
                    "success": False,
                    "error": "Message not found in source chat"
                }
            except ChannelPrivateError:
                return {
                    "success": False,
                    "error": "Cannot access private channel"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Forwarding failed: {e}"
                }
                
        except Exception as e:
            self.logger.error(f"Error forwarding message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_message_info(
        self,
        client: TelegramClient,
        chat: str,
        message_id: int
    ) -> Dict[str, Any]:
        """
        Get information about a message before forwarding.
        
        Args:
            client: TelegramClient instance
            chat: Chat identifier
            message_id: Message ID
        
        Returns:
            Dict with message information
        """
        try:
            entity = await client.get_entity(chat)
            message = await client.get_messages(entity, ids=message_id)
            
            if not message:
                return {
                    "success": False,
                    "error": "Message not found"
                }
            
            return {
                "success": True,
                "message_id": message.id,
                "text": message.text or "",
                "date": message.date.isoformat() if message.date else None,
                "from_id": message.from_id.user_id if message.from_id else None,
                "media": bool(message.media),
                "forward": bool(message.forward)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting message info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

