
#!/usr/bin/env python3

import os
import sys
from app import create_app, db

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def migrate_website_settings():
    """Create WebsiteSettings table and add default settings"""
    app = create_app()
    
    with app.app_context():
        # Import models after app context is created
        from models import WebsiteSettings
        
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Check if WebsiteSettings already exists with data
            existing_settings = WebsiteSettings.query.first()
            if not existing_settings:
                # Create default website settings
                default_settings = WebsiteSettings(
                    site_title='XL Package Manager',
                    site_description='Manage your XL packages with ease. Purchase data packages, monitor usage, and track your transactions all in one place.',
                    logo_url='https://img.icons8.com/ios/100/ffffff/smartphone.png'
                )
                db.session.add(default_settings)
                db.session.commit()
                print("✅ Default website settings created successfully!")
            else:
                print("✅ Website settings already exist!")
                
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            db.session.rollback()
            return False
            
    return True

if __name__ == '__main__':
    success = migrate_website_settings()
    if success:
        print("🎉 Website settings migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
