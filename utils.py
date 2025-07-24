import re
from datetime import datetime
import pytz

# Timezone settings
WIB = pytz.timezone('Asia/Jakarta')   # UTC+7
WITA = pytz.timezone('Asia/Makassar') # UTC+8
WIT = pytz.timezone('Asia/Jayapura')  # UTC+9

def format_currency(amount):
    """Format amount as Indonesian Rupiah"""
    if amount is None:
        return "Rp 0"
    return f"Rp {amount:,.0f}".replace(',', '.')

def format_phone(phone):
    """Format phone number for display"""
    if not phone:
        return ""

    # Remove country code if present
    phone = str(phone)
    if phone.startswith('+62'):
        phone = '0' + phone[3:]
    elif phone.startswith('62'):
        phone = '0' + phone[2:]

    return phone

def is_valid_phone(phone):
    """Validate Indonesian phone number"""
    if not phone:
        return False

    # Remove spaces and dashes
    phone = re.sub(r'[\s\-]', '', str(phone))

    # Check if it's a valid Indonesian number
    patterns = [
        r'^0\d{9,12}$',           # 0811234567
        r'^\+62\d{9,12}$',        # +6281234567
        r'^62\d{9,12}$',          # 6281234567
    ]

    return any(re.match(pattern, phone) for pattern in patterns)

def normalize_phone(phone):
    """Normalize phone number to standard format"""
    if not phone:
        return ""

    phone = re.sub(r'[\s\-]', '', str(phone))

    if phone.startswith('+62'):
        return phone[3:]
    elif phone.startswith('62'):
        return phone[2:]
    elif phone.startswith('0'):
        return phone[1:]

    return phone

def get_indonesia_time():
    """Get current time in different Indonesian timezones"""
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    wib_time = now_utc.astimezone(WIB)
    wita_time = now_utc.astimezone(WITA)
    wit_time = now_utc.astimezone(WIT)

    return {
        'wib': wib_time.strftime('%H:%M WIB'),
        'wita': wita_time.strftime('%H:%M WITA'),
        'wit': wit_time.strftime('%H:%M WIT'),
        'date': wib_time.strftime('%d %B %Y')
    }

def sensor_phone(phone):
    """Sensor phone number for privacy"""
    if not phone:
        return ""

    phone = str(phone)
    if len(phone) >= 10:
        return phone[:3] + "****" + phone[7:]
    return phone

def censor_phone_filter(phone):
    """Censor phone number for privacy (alias for sensor_phone)"""
    return sensor_phone(phone)

def generate_reference():
    """Generate unique reference number"""
    now = datetime.now()
    return f"XL{now.strftime('%Y%m%d%H%M%S')}{now.microsecond // 1000:03d}"

def generate_package_trx_id():
    """Generate package transaction ID with format Package + 6 random letters"""
    import random
    import string
    random_letters = ''.join(random.choices(string.ascii_uppercase, k=6))
    return f"Package{random_letters}"

def format_datetime_wib(dt):
    """Format datetime to WIB timezone (UTC+7)"""
    if not dt:
        return ""

    # If datetime is naive, assume it's UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)

    # Convert to WIB
    wib_dt = dt.astimezone(WIB)
    return wib_dt.strftime('%d/%m/%Y %H:%M WIB')

def parse_transaction_status(status):
    """Parse transaction status for display"""
    status_map = {
        'pending': ('Pending', 'warning'),
        'processing': ('Processing', 'info'),
        'success': ('Success', 'success'),
        'failed': ('Failed', 'danger'),
        'cancelled': ('Cancelled', 'secondary')
    }

    return status_map.get(status, (status.title(), 'secondary'))

def calculate_reseller_discount(member_price, discount_percent=10):
    """Calculate reseller price with discount"""
    discount = member_price * (discount_percent / 100)
    return member_price - discount

def validate_package_code(code):
    """Validate package code format"""
    if not code:
        return False

    # Package codes should be alphanumeric and between 3-20 characters
    return bool(re.match(r'^[A-Za-z0-9_-]{3,20}$', code))

def format_datetime(dt, timezone='WIB'):
    """Format datetime for display"""
    if not dt:
        return ""

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.utc)

    tz_map = {
        'WIB': WIB,
        'WITA': WITA,
        'WIT': WIT
    }

    target_tz = tz_map.get(timezone, WIB)
    local_dt = dt.astimezone(target_tz)

    return local_dt.strftime('%d/%m/%Y %H:%M %Z')

def get_status_badge_class(status):
    """Get Bootstrap badge class for status"""
    classes = {
        'active': 'bg-success',
        'inactive': 'bg-secondary',
        'pending': 'bg-warning',
        'processing': 'bg-info',
        'success': 'bg-success',
        'failed': 'bg-danger',
        'cancelled': 'bg-secondary'
    }

    return classes.get(status, 'bg-secondary')