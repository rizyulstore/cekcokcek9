
#!/usr/bin/env python3
"""
Script untuk menambahkan package XL Unlimited Turbo Vidio
Sesuai dengan kode bot yang diberikan
"""

from app import app, db
from models import Package

def add_xl_vidio_package():
    """Menambahkan package XL Unlimited Turbo Vidio"""
    
    with app.app_context():
        # Cek apakah package sudah ada
        existing_package = Package.query.filter_by(api_code='XLUNLITURBOVIDIO_PULSA').first()
        
        if existing_package:
            print("❌ Package XL Unlimited Turbo Vidio sudah ada!")
            print(f"   Name: {existing_package.name}")
            print(f"   Code: {existing_package.code}")
            print(f"   API Code: {existing_package.api_code}")
            return
        
        # Buat package baru
        xl_vidio_package = Package(
            name="XL Unlimited Turbo Vidio",
            code="XUT_VIDIO",
            price_member=5000.0,     # Harga untuk member: Rp 5,000
            price_reseller=3500.0,   # Harga untuk reseller: Rp 3,500
            api_code="XLUNLITURBOVIDIO_PULSA",  # API code sesuai bot
            is_active=True
        )
        
        # Simpan ke database
        db.session.add(xl_vidio_package)
        db.session.commit()
        
        print("✅ Package XL Unlimited Turbo Vidio berhasil ditambahkan!")
        print(f"   Name: {xl_vidio_package.name}")
        print(f"   Code: {xl_vidio_package.code}")
        print(f"   Member Price: Rp {xl_vidio_package.price_member:,.0f}")
        print(f"   Reseller Price: Rp {xl_vidio_package.price_reseller:,.0f}")
        print(f"   API Code: {xl_vidio_package.api_code}")
        print(f"   Status: {'Active' if xl_vidio_package.is_active else 'Inactive'}")
        
        # Tampilkan semua packages yang tersedia
        print("\n📦 Semua packages yang tersedia:")
        all_packages = Package.query.all()
        for i, pkg in enumerate(all_packages, 1):
            status = "✅ Active" if pkg.is_active else "❌ Inactive"
            print(f"   {i}. {pkg.name} ({pkg.code}) - {status}")

if __name__ == "__main__":
    add_xl_vidio_package()
