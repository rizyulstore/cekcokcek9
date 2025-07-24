
#!/usr/bin/env python3
"""
Migration script to add XUT notification format columns to TelegramSettings table
"""

import os
import sqlite3

def migrate_xut_telegram():
    """Add XUT notification format columns to telegram_settings table"""
    db_path = os.path.join('instance', 'xl_packages.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Skipping migration.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(telegram_settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add XUT success message format column
        if 'xut_success_message_format' not in columns:
            cursor.execute('''ALTER TABLE telegram_settings 
                             ADD COLUMN xut_success_message_format TEXT DEFAULT "⚡️ Transaksi Portal Ke-{transaction_count}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔢 TRX ID: {trx_id}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
💰 Harga: {amount}
📱 Respon: {response}"''')
            print("✓ Added xut_success_message_format column")
        else:
            print("✓ xut_success_message_format column already exists")
        
        # Add XUT failed message format column
        if 'xut_failed_message_format' not in columns:
            cursor.execute('''ALTER TABLE telegram_settings 
                             ADD COLUMN xut_failed_message_format TEXT DEFAULT "❌ Transaksi Portal Ke-{transaction_count} - {addon_name} GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔢 TRX ID: {trx_id}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: {addon_name} Gagal
💰 Harga: {amount}
🔍 Error: {error_message}"''')
            print("✓ Added xut_failed_message_format column")
        else:
            print("✓ xut_failed_message_format column already exists")
        
        conn.commit()
        conn.close()
        
        print("✅ XUT Telegram migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    migrate_xut_telegram()
