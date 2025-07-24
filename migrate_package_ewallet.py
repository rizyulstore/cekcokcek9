#!/usr/bin/env python3

import os
import sys
import sqlite3

def migrate_package_ewallet():
    """Add package_ewallet column to package table"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'xl_packages.db')

    try:
        # Connect directly to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if column exists first
        cursor.execute("PRAGMA table_info(package)")
        package_columns = [row[1] for row in cursor.fetchall()]

        if 'package_ewallet' not in package_columns:
            cursor.execute('ALTER TABLE package ADD COLUMN package_ewallet VARCHAR(100)')
            print('✓ Added package_ewallet column to package table')
            conn.commit()
        else:
            print('✓ package_ewallet column already exists in package table')

        conn.close()
        print('✓ Package ewallet migration completed successfully')

    except Exception as e:
        print(f'❌ Migration error: {e}')

if __name__ == '__main__':
    migrate_package_ewallet()