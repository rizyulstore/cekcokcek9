from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

class UserRole(enum.Enum):
    MEMBER = "member"
    RESELLER = "reseller"
    ADMIN = "admin"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.MEMBER, nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    counted = db.Column(db.Integer, default=0, nullable=False)
    counted_dor = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # XL Session data
    xl_phone = db.Column(db.String(20))
    xl_token = db.Column(db.Text)
    xl_verified = db.Column(db.Boolean, default=False)
    xl_token_time = db.Column(db.Float)
    xl_otp_verified = db.Column(db.Boolean, default=False)
    xl_last_otp_time = db.Column(db.DateTime)

    # Relationships
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    topups = db.relationship('TopUp', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == UserRole.ADMIN

    def is_reseller(self):
        return self.role == UserRole.RESELLER

    def get_display_role(self):
        return self.role.value.title()

class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(50), nullable=False)
    price_member = db.Column(db.Float, nullable=False)
    price_reseller = db.Column(db.Float, nullable=False)
    api_code = db.Column(db.String(100), nullable=False)  # Package code for PULSA
    package_ewallet = db.Column(db.String(100), nullable=True)  # Package code for e-wallet (QRIS/DANA)
    payment_methods = db.Column(db.String(100), default='PULSA,DANA,QRIS')  # Comma-separated payment methods
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # Addon pricing for XUT packages
    addon_price_member = db.Column(db.Float, default=6000, nullable=False)
    addon_price_reseller = db.Column(db.Float, default=6000, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    transactions = db.relationship('Transaction', backref='package', lazy=True)

    def get_price_for_user(self, user):
        if user.is_reseller() or user.is_admin():
            return self.price_reseller
        return self.price_member

    def get_addon_price_for_user(self, user):
        """Get addon price based on user role"""
        if user.is_reseller() or user.is_admin():
            return self.addon_price_reseller
        return self.addon_price_member

    def get_enabled_payment_methods(self):
        """Get list of enabled payment methods for this package"""
        if not self.payment_methods:
            return ['PULSA']
        return [method.strip() for method in self.payment_methods.split(',') if method.strip()]

    def set_payment_methods(self, methods_list):
        """Set payment methods from a list"""
        if isinstance(methods_list, list):
            self.payment_methods = ','.join(methods_list)
        else:
            self.payment_methods = methods_list

    def get_package_code_for_payment(self, payment_method):
        """Get appropriate package code based on payment method"""
        if payment_method == 'PULSA':
            return self.api_code
        elif payment_method in ['QRIS', 'DANA']:
            return self.package_ewallet if self.package_ewallet else self.api_code
        return self.api_code

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.Integer, db.ForeignKey('package.id'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, success, failed
    payment_method = db.Column(db.String(20), default='PULSA')  # PULSA, DANA, QRIS
    reference = db.Column(db.String(100))
    trx_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class TopUp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

class SystemSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class PaymentMethodSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pulsa_enabled = db.Column(db.Boolean, default=True)
    dana_enabled = db.Column(db.Boolean, default=True)
    qris_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_enabled_methods():
        settings = PaymentMethodSettings.query.first()
        if not settings:
            return ['PULSA', 'DANA', 'QRIS']  # Default all enabled
        
        enabled = []
        if settings.pulsa_enabled:
            enabled.append('PULSA')
        if settings.dana_enabled:
            enabled.append('DANA')
        if settings.qris_enabled:
            enabled.append('QRIS')
        return enabled if enabled else ['PULSA']  # At least one method

class WebsiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_title = db.Column(db.String(100), default='XL Package Manager')
    site_description = db.Column(db.Text, default='Manage your XL packages with ease. Purchase data packages, monitor usage, and track your transactions all in one place.')
    logo_url = db.Column(db.String(500), default='https://img.icons8.com/ios/100/ffffff/smartphone.png')
    favicon_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_settings():
        settings = WebsiteSettings.query.first()
        if not settings:
            settings = WebsiteSettings()
            db.session.add(settings)
            db.session.commit()
        return settings

class MultiAddonPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Premium", "Super", etc.
    package_code = db.Column(db.String(100), nullable=False)  # e.g., "PREMIUMXC", "SUPERXC"
    api_code = db.Column(db.String(100), nullable=False)  # e.g., "XLUNLITURBOPREMIUMXC_PULSA"
    price_member = db.Column(db.Float, default=1000, nullable=False)
    price_reseller = db.Column(db.Float, default=500, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_price_for_user(self, user):
        """Get price based on user role"""
        if user.is_reseller() or user.is_admin():
            return self.price_reseller
        return self.price_member

class MultiAddonTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    selected_packages = db.Column(db.Text, nullable=False)  # JSON string of selected package IDs
    total_amount = db.Column(db.Float, nullable=False)
    total_packages = db.Column(db.Integer, nullable=False)
    successful_packages = db.Column(db.Integer, default=0)
    failed_packages = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', backref='multiaddon_transactions')

class TelegramSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bot_token = db.Column(db.String(500))
    group_id = db.Column(db.String(100))
    website_name = db.Column(db.String(100), default='XL Package Manager')
    website_url = db.Column(db.String(200), default='https://yourwebsite.com')
    success_message_format = db.Column(db.Text, default="""⚡️ Transaksi Portal Ke-{transaction_count}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔢 TRX ID: {trx_id}
📆 Tanggal: {expired_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
💰 Harga: {amount}""")
    failed_message_format = db.Column(db.Text, default="""❌ Transaksi Portal Ke-{transaction_count} GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔢 TRX ID: {trx_id}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: Gagal
💰 Harga: {amount}
🔍 Error: {error_message}""")
    topup_pending_message_format = db.Column(db.Text, default="""💰 Top-Up Portal Ke-{topup_count} PENDING
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

⏳ Status: Menunggu Konfirmasi
💰 Jumlah: {amount}""")
    topup_success_message_format = db.Column(db.Text, default="""✅ Top-Up Portal Ke-{topup_count} BERHASIL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
💰 Jumlah: {amount}""")
    topup_failed_message_format = db.Column(db.Text, default="""❌ Top-Up Portal Ke-{topup_count} GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💳 Metode: {payment_method}
📆 Tanggal: {created_date}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: Gagal
💰 Jumlah: {amount}""")
    
    # XUT-specific notification formats
    xut_success_message_format = db.Column(db.Text, default="""⚡️ Transaksi Portal Ke-{transaction_count}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔢 TRX ID: {trx_id}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
💰 Harga: {amount}
📱 Respon: {response}""")
    
    xut_failed_message_format = db.Column(db.Text, default="""❌ Transaksi Portal Ke-{transaction_count} - {addon_name} GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📄 Transaksi: {package_name}
🔢 TRX ID: {trx_id}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: {addon_name} Gagal
💰 Harga: {amount}
🔍 Error: {error_message}""")
    
    # Multi-addon notification formats
    multiaddon_success_message_format = db.Column(db.Text, default="""✅ TRANSAKSI MULTI-ADDON SUKSES #{transaction_count}
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📦 Paket: {package_name} BYPASS
💰 Harga: {amount}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

✅ Status: Berhasil
📱 Respon: {response}""")
    
    multiaddon_failed_message_format = db.Column(db.Text, default="""❌ TRANSAKSI MULTI-ADDON GAGAL
━━━━━━━━━━━━━━━━━
👤 Pengguna: {username}
💼 Nomer: {phone}
📦 Paket: {package_name} BYPASS
💰 Harga: {amount}
━━━━━━━━━━━━━━━━━
💎 Official Website: {website_name}

❌ Status: Gagal
🔍 Error: {error_message}""")
    
    is_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)