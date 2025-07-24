
#!/usr/bin/env python3
"""
Database migration script to add missing columns
"""

from app import app, db
from sqlalchemy import text

def migrate_database():
    """Add missing columns to database tables"""
    with app.app_context():
        try:
            # Check if columns exist first
            result = db.session.execute(text("PRAGMA table_info(transaction)"))
            transaction_columns = [row[1] for row in result.fetchall()]
            
            if 'payment_method' not in transaction_columns:
                db.session.execute(text('ALTER TABLE "transaction" ADD COLUMN payment_method VARCHAR(20) DEFAULT "PULSA"'))
                print('✓ Added payment_method column to transaction table')
            else:
                print('✓ payment_method column already exists in transaction table')
            
            # Check package table
            result = db.session.execute(text("PRAGMA table_info(package)"))
            package_columns = [row[1] for row in result.fetchall()]
            
            if 'payment_methods' not in package_columns:
                db.session.execute(text('ALTER TABLE package ADD COLUMN payment_methods VARCHAR(100) DEFAULT "PULSA,DANA,QRIS"'))
                print('✓ Added payment_methods column to package table')
            else:
                print('✓ payment_methods column already exists in package table')
            
            db.session.commit()
            print('✓ Database migration completed successfully')
            
        except Exception as e:
            print(f'❌ Migration error: {e}')
            db.session.rollback()

if __name__ == '__main__':
    migrate_database()
