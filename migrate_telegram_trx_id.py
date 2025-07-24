
import sqlite3
import os

def migrate_telegram_formats():
    """Update Telegram message formats to include TRX ID"""
    
    db_path = os.path.join('instance', 'xl_packages.db')
    
    if not os.path.exists(db_path):
        print("Database not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # New formats with TRX ID
        success_format = """⚡️ Transaksi Portal Ke-{transaction_count}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔢 TRX ID: {trx_id}
📆 Tanggal: {expired_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
💰 Harga: {amount}"""

        failed_format = """❌ Transaksi Portal Ke-{transaction_count} GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔢 TRX ID: {trx_id}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: Gagal
💰 Harga: {amount}
🔍 Error: {error_message}"""
        
        # Update existing telegram settings
        cursor.execute("""
            UPDATE telegram_settings 
            SET success_message_format = ?, 
                failed_message_format = ?
            WHERE id = 1
        """, (success_format, failed_format))
        
        conn.commit()
        print("Telegram message formats updated successfully!")
        return True
        
    except Exception as e:
        print(f"Migration error: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_telegram_formats()
