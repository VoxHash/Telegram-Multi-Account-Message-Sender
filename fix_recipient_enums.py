#!/usr/bin/env python3
"""
Script to fix recipient enum values in the database.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.db import initialize_database, get_session
from app.models import Recipient, RecipientType
from sqlmodel import select, text


def fix_recipient_enums():
    """Fix recipient enum values in the database."""
    
    # Initialize database
    initialize_database()
    
    # Get database session
    session = get_session()
    
    try:
        # Get all recipients
        recipients = session.exec(select(Recipient)).all()
        
        print(f"Found {len(recipients)} recipients to check...")
        
        fixed_count = 0
        for recipient in recipients:
            # Check if recipient_type is valid
            if recipient.recipient_type not in [e.value for e in RecipientType]:
                print(f"Fixing recipient {recipient.id}: '{recipient.recipient_type}' -> 'user'")
                
                # Update to valid enum value
                recipient.recipient_type = RecipientType.USER.value
                session.add(recipient)
                fixed_count += 1
        
        # Commit changes
        session.commit()
        print(f"Successfully fixed {fixed_count} recipients!")
        
        # Verify the fix
        print("\nVerifying fix...")
        recipients = session.exec(select(Recipient)).all()
        invalid_count = 0
        for recipient in recipients:
            if recipient.recipient_type not in [e.value for e in RecipientType]:
                invalid_count += 1
                print(f"Still invalid: {recipient.id} = '{recipient.recipient_type}'")
        
        if invalid_count == 0:
            print("✅ All recipient types are now valid!")
        else:
            print(f"❌ {invalid_count} recipients still have invalid types")
        
    except Exception as e:
        print(f"Error fixing recipient enums: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    fix_recipient_enums()
