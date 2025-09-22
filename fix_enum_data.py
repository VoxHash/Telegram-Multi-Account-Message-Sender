#!/usr/bin/env python3
"""
Fix enum data in the database after adding RecipientType.
"""

import sqlite3
from pathlib import Path

def fix_enum_data():
    """Fix enum values in the database."""
    db_path = Path("app_data/app.db")
    
    if not db_path.exists():
        print("Database not found.")
        return
    
    print("Fixing enum data in database...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Check if recipient_type column exists and has data
        cursor.execute("SELECT COUNT(*) FROM recipients WHERE recipient_type IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"Found {count} recipients with recipient_type data")
        
        # Update any NULL recipient_type values to 'user' (default)
        cursor.execute("UPDATE recipients SET recipient_type = 'user' WHERE recipient_type IS NULL")
        updated = cursor.rowcount
        print(f"Updated {updated} NULL recipient_type values to 'user'")
        
        # Check for any invalid enum values
        cursor.execute("SELECT DISTINCT recipient_type FROM recipients")
        types = [row[0] for row in cursor.fetchall()]
        print(f"Current recipient_type values: {types}")
        
        # Update any invalid values to 'user'
        valid_types = ['user', 'group', 'channel']
        for invalid_type in types:
            if invalid_type not in valid_types:
                print(f"Found invalid recipient_type: '{invalid_type}', updating to 'user'")
                cursor.execute("UPDATE recipients SET recipient_type = 'user' WHERE recipient_type = ?", (invalid_type,))
        
        conn.commit()
        print("Enum data fix completed successfully!")
        
    except Exception as e:
        print(f"Error fixing enum data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_enum_data()
