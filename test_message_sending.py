#!/usr/bin/env python3
"""
Test script to send a message from voxhash account to @jomadev
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.services.db import initialize_database, get_session
from app.models import Account, Recipient
from app.core.telethon_client import TelegramClientManager
from sqlmodel import select

async def test_message_sending():
    """Test sending a message from voxhash account to @jomadev"""
    print("🚀 Testing message sending functionality...")
    
    # Initialize database
    initialize_database()
    
    # Get database session
    session = get_session()
    try:
        # Find voxhash account
        voxhash_account = session.exec(
            select(Account).where(Account.phone_number == "+1234567890")
        ).first()
        
        if not voxhash_account:
            print("❌ VoxHash account not found!")
            return
        
        print(f"✅ Found account: {voxhash_account.phone_number}")
        
        # Find @jomadev recipient
        jomadev_recipient = session.exec(
            select(Recipient).where(Recipient.username == "jomadev")
        ).first()
        
        if not jomadev_recipient:
            print("❌ @jomadev recipient not found!")
            return
        
        print(f"✅ Found recipient: @{jomadev_recipient.username}")
        
        # Create Telegram client manager
        client_manager = TelegramClientManager()
        
        # Get client for voxhash account
        client = await client_manager.get_client(voxhash_account.id)
        
        if not client:
            print("❌ Failed to get Telegram client for voxhash account")
            return
        
        print("✅ Telegram client created")
        
        # Send test message
        message_text = "Hello @jomadev! This is a test message from the Telegram Multi-Account Message Sender app. 🚀"
        
        try:
            await client.send_message("jomadev", message_text)
            print("✅ Message sent successfully!")
            print(f"📤 Message: {message_text}")
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
        
        # Close client
        await client_manager.close_client(voxhash_account.id)
        print("✅ Client closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(test_message_sending())
