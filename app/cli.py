"""
Command-line interface for the Telegram Multi-Account Message Sender.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

from .services import initialize_database, get_settings, get_logger
from .core import TelegramClientManager, MessageEngine


async def main():
    """Main CLI entry point."""
    # Initialize services
    initialize_database()
    settings = get_settings()
    logger = get_logger()
    
    logger.info("Telegram Multi-Account Message Sender CLI")
    
    # Check if Telegram API is configured
    if not settings.is_telegram_configured():
        logger.error("Telegram API not configured. Please set TELEGRAM_API_ID and TELEGRAM_API_HASH")
        sys.exit(1)
    
    # Initialize components
    client_manager = TelegramClientManager()
    message_engine = MessageEngine(client_manager)
    
    try:
        # CLI logic would go here
        logger.info("CLI mode not yet implemented. Use GUI mode for now.")
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        await client_manager.disconnect_all()


if __name__ == "__main__":
    asyncio.run(main())
