
#!/usr/bin/env python3
"""
Script untuk menambahkan paket XUT (XUTP dan XUTS) ke database
"""

from app import create_app, db
from models import Package

def add_xut_packages():
    """Menambahkan paket XUTP dan XUTS yang diperlukan"""
    
    app = create_app()
    
    # Data paket XUT
    xut_packages = [
        {
            "name": "XUT Premium",
            "code": "XUTP", 
            "price_member": 25000.0,
            "price_reseller": 23000.0,
            "api_code": "XLUNLITURBOPREMIUMXC_PULSA",
            "package_ewallet": "PREMIUMXC",
            "payment_methods": "PULSA"
        },
        {
            "name": "XUT Super",
            "code": "XUTS",
            "price_member": 12500.0,
            "price_reseller": 11000.0,
            "api_code": "XLUNLITURBOSUPERXC_PULSA", 
            "package_ewallet": "SUPERXC",
            "payment_methods": "PULSA"
        },
        {
            "name": "XCS Bonus (Premium Add-on)",
            "code": "XCS_PREMIUM",
            "price_member": 6000.0,
            "price_reseller": 5500.0,
            "api_code": "bdb392a7aa12b21851960b7e7d54af2c",
            "package_ewallet": None,
            "payment_methods": "PULSA"
        },
        {
            "name": "XC 1+1 GB (Super Add-on)",
            "code": "XC1PLUS1",
            "price_member": 6000.0,
            "price_reseller": 5500.0,
            "api_code": "XL_XC1PLUS1DISC_PULSA",
            "package_ewallet": None,
            "payment_methods": "PULSA"
        }
    ]
    
    with app.app_context():
        added_count = 0
        updated_count = 0
        
        for pkg_data in xut_packages:
            # Cek apakah package sudah ada berdasarkan api_code
            existing = Package.query.filter_by(api_code=pkg_data["api_code"]).first()
            
            if existing:
                # Update paket yang sudah ada
                existing.name = pkg_data["name"]
                existing.code = pkg_data["code"]
                existing.price_member = pkg_data["price_member"]
                existing.price_reseller = pkg_data["price_reseller"]
                existing.package_ewallet = pkg_data["package_ewallet"]
                existing.payment_methods = pkg_data["payment_methods"]
                existing.is_active = True
                
                print(f"✅ Updated package: {pkg_data['name']} ({pkg_data['code']})")
                updated_count += 1
            else:
                # Buat package baru
                new_package = Package(
                    name=pkg_data["name"],
                    code=pkg_data["code"],
                    price_member=pkg_data["price_member"],
                    price_reseller=pkg_data["price_reseller"],
                    api_code=pkg_data["api_code"],
                    package_ewallet=pkg_data["package_ewallet"],
                    payment_methods=pkg_data["payment_methods"],
                    is_active=True
                )
                
                db.session.add(new_package)
                print(f"✅ Added new package: {pkg_data['name']} ({pkg_data['code']})")
                added_count += 1
        
        try:
            db.session.commit()
            print(f"\n🎉 Berhasil! Added: {added_count}, Updated: {updated_count} packages")
            
            # Tampilkan daftar paket XUT yang tersedia
            print("\n📦 Paket XUT yang tersedia:")
            xut_packages_db = Package.query.filter(
                Package.package_ewallet.in_(['PREMIUMXC', 'SUPERXC'])
            ).all()
            
            for pkg in xut_packages_db:
                print(f"  - {pkg.name} ({pkg.code}): {pkg.api_code}")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    add_xut_packages()
