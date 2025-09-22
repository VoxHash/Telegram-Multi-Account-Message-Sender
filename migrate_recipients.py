#!/usr/bin/env python3
"""
Migrate recipients table to add group support fields.
"""

import sqlite3
from pathlib import Path

def migrate_recipients_table():
    """Add new columns to recipients table for group support."""
    db_path = Path("app_data/app.db")
    
    if not db_path.exists():
        print("Database not found. Please run the application first to create the database.")
        return
    
    print("Migrating recipients table to add group support...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        # Add new columns for group support
        new_columns = [
            "ALTER TABLE recipients ADD COLUMN recipient_type TEXT DEFAULT 'user'",
            "ALTER TABLE recipients ADD COLUMN group_id INTEGER",
            "ALTER TABLE recipients ADD COLUMN group_title TEXT",
            "ALTER TABLE recipients ADD COLUMN group_username TEXT",
            "ALTER TABLE recipients ADD COLUMN group_type TEXT",
            "ALTER TABLE recipients ADD COLUMN member_count INTEGER"
        ]
        
        for column_sql in new_columns:
            try:
                cursor.execute(column_sql)
                print(f"Added column: {column_sql.split()[-1]}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"Column already exists: {column_sql.split()[-1]}")
                else:
                    print(f"Error adding column: {e}")
        
        # Create indexes for new columns
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_recipients_recipient_type ON recipients(recipient_type)",
            "CREATE INDEX IF NOT EXISTS idx_recipients_group_id ON recipients(group_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipients_group_username ON recipients(group_username)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"Created index: {index_sql.split()[-1]}")
            except sqlite3.Error as e:
                print(f"Error creating index: {e}")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_recipients_table()
