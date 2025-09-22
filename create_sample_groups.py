#!/usr/bin/env python3
"""
Create sample groups for testing the Recipients tab with group support.
"""

from app.services.db import initialize_database, get_session
from app.models.recipient import Recipient, RecipientType, RecipientSource, RecipientStatus

def create_sample_groups():
    """Create sample groups in the database."""
    print("Creating sample groups...")
    
    # Initialize database
    initialize_database()
    
    # Sample groups data
    sample_groups = [
        {
            "recipient_type": RecipientType.GROUP,
            "group_id": -1001234567890,
            "group_title": "Tech Enthusiasts",
            "group_username": "techenthusiasts",
            "group_type": "supergroup",
            "member_count": 1250,
            "source": RecipientSource.MANUAL,
            "status": RecipientStatus.ACTIVE,
            "notes": "Active tech discussion group"
        },
        {
            "recipient_type": RecipientType.CHANNEL,
            "group_id": -1001234567891,
            "group_title": "News Updates",
            "group_username": "news_updates",
            "group_type": "channel",
            "member_count": 5000,
            "source": RecipientSource.MANUAL,
            "status": RecipientStatus.ACTIVE,
            "notes": "Official news channel"
        },
        {
            "recipient_type": RecipientType.GROUP,
            "group_id": -1001234567892,
            "group_title": "Marketing Professionals",
            "group_username": "marketing_pros",
            "group_type": "supergroup",
            "member_count": 850,
            "source": RecipientSource.MANUAL,
            "status": RecipientStatus.ACTIVE,
            "notes": "Marketing and business discussion group"
        },
        {
            "recipient_type": RecipientType.CHANNEL,
            "group_id": -1001234567893,
            "group_title": "Daily Tips",
            "group_username": "daily_tips",
            "group_type": "channel",
            "member_count": 3200,
            "source": RecipientSource.MANUAL,
            "status": RecipientStatus.ACTIVE,
            "notes": "Daily productivity tips channel"
        },
        {
            "recipient_type": RecipientType.GROUP,
            "group_id": -1001234567894,
            "group_title": "Crypto Traders",
            "group_username": "crypto_traders",
            "group_type": "supergroup",
            "member_count": 2100,
            "source": RecipientSource.MANUAL,
            "status": RecipientStatus.ACTIVE,
            "notes": "Cryptocurrency trading discussion group"
        }
    ]
    
    session = get_session()
    try:
        for group_data in sample_groups:
            # Check if group already exists
            existing = session.query(Recipient).filter(
                Recipient.group_id == group_data["group_id"]
            ).first()
            
            if not existing:
                group = Recipient(**group_data)
                session.add(group)
                print(f"Created group: {group.get_display_name()}")
            else:
                print(f"Group already exists: {existing.get_display_name()}")
        
        session.commit()
        print(f"Successfully created {len(sample_groups)} sample groups!")
        
    except Exception as e:
        print(f"Error creating sample groups: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_sample_groups()
