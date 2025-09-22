#!/usr/bin/env python3
"""
Script to fix recipient enum values in the database using direct SQL.
"""

import sys
import os
import sqlite3

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.db import initialize_database


def fix_recipient_enums_direct():
    """Fix recipient enum values in the database using direct SQL."""
    
    # Initialize database
    initialize_database()
    
    # Connect directly to SQLite database
    db_path = "app_data/app.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current values
        cursor.execute("SELECT DISTINCT recipient_type FROM recipients")
        current_types = [row[0] for row in cursor.fetchall()]
        print(f"Current recipient types: {current_types}")
        
        # Update lowercase to uppercase
        updates = [
            ("user", "USER"),
            ("group", "GROUP"), 
            ("channel", "CHANNEL")
        ]
        
        for old_val, new_val in updates:
            cursor.execute("UPDATE recipients SET recipient_type = ? WHERE recipient_type = ?", (new_val, old_val))
            affected = cursor.rowcount
            if affected > 0:
                print(f"Updated {affected} recipients from '{old_val}' to '{new_val}'")
        
        # Commit changes
        conn.commit()
        
        # Verify the fix
        cursor.execute("SELECT DISTINCT recipient_type FROM recipients")
        new_types = [row[0] for row in cursor.fetchall()]
        print(f"New recipient types: {new_types}")
        
        # Check for any remaining invalid types
        valid_types = ["USER", "GROUP", "CHANNEL"]
        invalid_types = [t for t in new_types if t not in valid_types]
        
        if not invalid_types:
            print("✅ All recipient types are now valid!")
        else:
            print(f"❌ Invalid types still exist: {invalid_types}")
        
    except Exception as e:
        print(f"Error fixing recipient enums: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    fix_recipient_enums_direct()
