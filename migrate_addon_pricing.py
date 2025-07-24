
#!/usr/bin/env python3
"""
Database migration script to add addon pricing columns to package table
"""

import os
import sqlite3

def migrate_addon_pricing():
    """Add addon pricing columns to package table"""
    db_path = os.path.join('instance', 'xl_packages.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns exist first
        cursor.execute("PRAGMA table_info(package)")
        package_columns = [row[1] for row in cursor.fetchall()]
        
        if 'addon_price_member' not in package_columns:
            cursor.execute('ALTER TABLE package ADD COLUMN addon_price_member REAL DEFAULT 6000')
            print('✓ Added addon_price_member column to package table')
        else:
            print('✓ addon_price_member column already exists in package table')
        
        if 'addon_price_reseller' not in package_columns:
            cursor.execute('ALTER TABLE package ADD COLUMN addon_price_reseller REAL DEFAULT 6000')
            print('✓ Added addon_price_reseller column to package table')
        else:
            print('✓ addon_price_reseller column already exists in package table')
        
        # Update existing packages with default addon prices
        cursor.execute('UPDATE package SET addon_price_member = 6000 WHERE addon_price_member IS NULL')
        cursor.execute('UPDATE package SET addon_price_reseller = 6000 WHERE addon_price_reseller IS NULL')
        
        conn.commit()
        print('✓ Addon pricing migration completed successfully')
        
    except Exception as e:
        print(f'❌ Migration error: {e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_addon_pricing()
