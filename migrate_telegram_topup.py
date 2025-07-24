
#!/usr/bin/env python3
"""
Migration script to add top-up notification formats to TelegramSettings table
"""

import sqlite3
import os

def migrate_telegram_topup():
    db_path = os.path.join('instance', 'xl_packages.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(telegram_settings)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add missing columns
        if 'topup_pending_message_format' not in columns:
            cursor.execute('''ALTER TABLE telegram_settings 
                             ADD COLUMN topup_pending_message_format TEXT DEFAULT "💰 Top-Up Portal Ke-{topup_count} PENDING
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

⏳ Status: Menunggu Konfirmasi
💰 Jumlah: {amount}"''')
            print("Added topup_pending_message_format column")
        
        if 'topup_success_message_format' not in columns:
            cursor.execute('''ALTER TABLE telegram_settings 
                             ADD COLUMN topup_success_message_format TEXT DEFAULT "✅ Top-Up Portal Ke-{topup_count} BERHASIL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
💰 Jumlah: {amount}"''')
            print("Added topup_success_message_format column")
        
        if 'topup_failed_message_format' not in columns:
            cursor.execute('''ALTER TABLE telegram_settings 
                             ADD COLUMN topup_failed_message_format TEXT DEFAULT "❌ Top-Up Portal Ke-{topup_count} GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: Gagal
💰 Jumlah: {amount}"''')
            print("Added topup_failed_message_format column")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_telegram_topup()
