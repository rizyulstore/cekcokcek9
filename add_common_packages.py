
#!/usr/bin/env python3
"""
Script untuk menambahkan package-package XL yang umum digunakan
"""

from app import app, db
from models import Package

def add_common_xl_packages():
    """Menambahkan package-package XL yang umum"""
    
    # Daftar package XL yang umum
    packages_data = [
        {
            "name": "XL Unlimited Turbo Vidio",
            "code": "XUT_VIDIO", 
            "price_member": 5000.0,
            "price_reseller": 3500.0,
            "api_code": "XLUNLITURBOVIDIO_PULSA"
        },
        {
            "name": "XL Combo Xtra 1GB",
            "code": "XCX_1GB",
            "price_member": 15000.0,
            "price_reseller": 12000.0,
            "api_code": "XLCOMBOXTRA1GB"
        },
        {
            "name": "XL Combo Xtra 2GB", 
            "code": "XCX_2GB",
            "price_member": 25000.0,
            "price_reseller": 22000.0,
            "api_code": "XLCOMBOXTRA2GB"
        },
        {
            "name": "XL Combo Xtra 5GB",
            "code": "XCX_5GB", 
            "price_member": 50000.0,
            "price_reseller": 45000.0,
            "api_code": "XLCOMBOXTRA5GB"
        },
        {
            "name": "XL Hot Deal 3GB",
            "code": "XHD_3GB",
            "price_member": 20000.0,
            "price_reseller": 17000.0,
            "api_code": "XLHOTDEAL3GB"
        },
        {
            "name": "XL Hot Deal 5GB",
            "code": "XHD_5GB",
            "price_member": 30000.0, 
            "price_reseller": 26000.0,
            "api_code": "XLHOTDEAL5GB"
        },
        {
            "name": "XUT Premium",
            "code": "XUTP",
            "price_member": 25000.0,
            "price_reseller": 23000.0,
            "api_code": "XLUNLITURBOPREMIUMXC_PULSA",
            "package_ewallet": "PREMIUMXC"
        },
        {
            "name": "XUT Super", 
            "code": "XUTS",
            "price_member": 12500.0,
            "price_reseller": 11000.0,
            "api_code": "XLUNLITURBOSUPERXC_PULSA",
            "package_ewallet": "SUPERXC"
        },
        {
            "name": "XCS Bonus (Premium)",
            "code": "XCS_PREMIUM",
            "price_member": 6000.0,
            "price_reseller": 5500.0,
            "api_code": "bdb392a7aa12b21851960b7e7d54af2c"
        },
        {
            "name": "XC 1+1 GB (Super)",
            "code": "XC1PLUS1",
            "price_member": 6000.0,
            "price_reseller": 5500.0,
            "api_code": "XL_XC1PLUS1DISC_PULSA"
        }
    ]
    
    with app.app_context():
        added_count = 0
        
        for pkg_data in packages_data:
            # Cek apakah package sudah ada
            existing = Package.query.filter_by(api_code=pkg_data["api_code"]).first()
            
            if existing:
                print(f"⚠️  Package {pkg_data['name']} sudah ada, dilewati.")
                continue
            
            # Buat package baru
            new_package = Package(
                name=pkg_data["name"],
                code=pkg_data["code"],
                price_member=pkg_data["price_member"],
                price_reseller=pkg_data["price_reseller"],
                api_code=pkg_data["api_code"],
                package_ewallet=pkg_data.get("package_ewallet"),
                payment_methods="PULSA,DANA,QRIS",
                is_active=True
            )
            
            db.session.add(new_package)
            added_count += 1
            print(f"✅ Menambahkan: {pkg_data['name']}")
        
        # Commit semua perubahan
        if added_count > 0:
            db.session.commit()
            print(f"\n🎉 Berhasil menambahkan {added_count} package baru!")
        else:
            print("\n📦 Semua package sudah ada, tidak ada yang ditambahkan.")
        
        # Tampilkan semua packages
        print("\n📋 Daftar semua packages:")
        all_packages = Package.query.all()
        for i, pkg in enumerate(all_packages, 1):
            status = "✅" if pkg.is_active else "❌"
            print(f"   {i:2d}. {pkg.name:<25} - Member: Rp {pkg.price_member:>7,.0f} | Reseller: Rp {pkg.price_reseller:>7,.0f} {status}")

if __name__ == "__main__":
    add_common_xl_packages()
