
#!/usr/bin/env python3
"""
Database migration script to add multi-addon package tables
"""

import os
import sqlite3

def migrate_multiaddon():
    """Add multi-addon package tables"""
    db_path = os.path.join('instance', 'xl_packages.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create multi_addon_package table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS multi_addon_package (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                package_code VARCHAR(100) NOT NULL,
                api_code VARCHAR(100) NOT NULL,
                price_member FLOAT DEFAULT 1000,
                price_reseller FLOAT DEFAULT 500,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print('✓ Created multi_addon_package table')
        
        # Create multi_addon_transaction table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS multi_addon_transaction (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phone_number VARCHAR(20) NOT NULL,
                selected_packages TEXT NOT NULL,
                total_amount FLOAT NOT NULL,
                total_packages INTEGER NOT NULL,
                successful_packages INTEGER DEFAULT 0,
                failed_packages INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'processing',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES user (id)
            )
        ''')
        print('✓ Created multi_addon_transaction table')
        
        # Add multi-addon notification formats to telegram_settings
        cursor.execute("PRAGMA table_info(telegram_settings)")
        telegram_columns = [row[1] for row in cursor.fetchall()]
        
        if 'multiaddon_success_message_format' not in telegram_columns:
            cursor.execute('''
                ALTER TABLE telegram_settings 
                ADD COLUMN multiaddon_success_message_format TEXT DEFAULT 
                '✅ TRANSAKSI MULTI-ADDON SUKSES #{transaction_count}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📦 Paket: {package_name} BYPASS
💰 Harga: {amount}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
📱 Respon: {response}'
            ''')
            print('✓ Added multiaddon_success_message_format column')
        
        if 'multiaddon_failed_message_format' not in telegram_columns:
            cursor.execute('''
                ALTER TABLE telegram_settings 
                ADD COLUMN multiaddon_failed_message_format TEXT DEFAULT 
                '❌ TRANSAKSI MULTI-ADDON GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📦 Paket: {package_name} BYPASS
💰 Harga: {amount}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: Gagal
🔍 Error: {error_message}'
            ''')
            print('✓ Added multiaddon_failed_message_format column')
        
        # Insert default multi-addon packages
        default_packages = [
            ('Premium', 'PREMIUMXC', 'XLUNLITURBOPREMIUMXC_PULSA'),
            ('Super', 'SUPERXC', 'XLUNLITURBOSUPERXC_PULSA'),
            ('Standard', 'STANDARDXC', 'XLUNLITURBOSTANDARDXC_PULSA'),
            ('Basic', 'BASICXC', 'XLUNLITURBOBASICXC_PULSA'),
            ('Netflix', 'NETFLIXXC', 'XLUNLITURBONETFLIXXC_PULSA'),
            ('Viu', 'VIU', 'XLUNLITURBOVIU_PULSA'),
            ('Youtube', 'YOUTUBEXC', 'XLUNLITURBOYOUTUBEXC_PULSA'),
            ('TikTok', 'TIKTOK', 'XLUNLITURBOTIKTOK_PULSA'),
            ('Joox', 'JOOXXC', 'XLUNLITURBOJOOXXC_PULSA')
        ]
        
        for name, package_code, api_code in default_packages:
            cursor.execute('''
                INSERT OR IGNORE INTO multi_addon_package (name, package_code, api_code)
                VALUES (?, ?, ?)
            ''', (name, package_code, api_code))
        
        print('✓ Inserted default multi-addon packages')
        
        conn.commit()
        print('\n✅ Multi-addon migration completed successfully!')
        
    except Exception as e:
        print(f'❌ Migration failed: {str(e)}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_multiaddon()
