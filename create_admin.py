#!/usr/bin/env python3
"""
Script to create default admin user for XL Package Manager
Run this script to create the initial admin account
"""

import os
import sys
from app import app, db
from models import User, UserRole

def create_admin_user():
    """Create default admin user"""
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin user already exists!")
            print(f"Username: admin")
            print(f"Email: {admin.email}")
            return
        
        # Create admin user
        admin = User(
            username='admin',
            email='admin@xlpackage.com',
            phone='081234567890',
            role=UserRole.ADMIN,
            balance=1000000.0,  # 1 million rupiah starting balance
            is_active=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        
        print("✓ Admin user created successfully!")
        print(f"Username: admin")
        print(f"Password: admin123")
        print(f"Email: admin@xlpackage.com")
        print(f"Phone: 081234567890")
        print(f"Role: Admin")
        print(f"Starting Balance: Rp 1.000.000")
        print("\nPlease change the password after first login!")

if __name__ == '__main__':
    create_admin_user()