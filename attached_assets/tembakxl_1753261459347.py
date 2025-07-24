import asyncio
import aiohttp
import sqlite3
import pytz
from telethon import events, Button
from bot import bot
import qrcode
from PIL import Image
from PIL import ImageDraw
import os
import time
import random
from datetime import datetime
import requests
from colorthief import ColorThief 
from datetime import datetime, timedelta
import json
import re
from PIL import Image, ImageDraw, ImageOps
import traceback  
from utils.db_settings import is_maintenance_tembakxl  # pastikan ini ada
from io import BytesIO
from telethon import types
JAKARTA = pytz.timezone('Asia/Jakarta')

# Zona waktu Indonesia
WIB = pytz.timezone('Asia/Jakarta')   # UTC+7
WITA = pytz.timezone('Asia/Makassar') # UTC+8
WIT  = pytz.timezone('Asia/Jayapura') # UTC+9

# Fungsi waktu batas pembayaran
def waktu_pembayaran():
    from datetime import datetime, timedelta
    import pytz

    WIB = pytz.timezone('Asia/Jakarta')   # UTC+7
    WITA = pytz.timezone('Asia/Makassar') # UTC+8
    WIT  = pytz.timezone('Asia/Jayapura') # UTC+9

    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    
    batas_wib = (now_utc.astimezone(WIB) + timedelta(minutes=5)).strftime('%H:%M WIB')
    batas_wita = (now_utc.astimezone(WITA) + timedelta(minutes=5)).strftime('%H:%M WITA')
    batas_wit = (now_utc.astimezone(WIT) + timedelta(minutes=5)).strftime('%H:%M WIT')

    return batas_wib, batas_wita, batas_wit


def waktu_sekarang():
    from datetime import datetime, timedelta
    import pytz

    WIB = pytz.timezone('Asia/Jakarta')   # UTC+7
    WITA = pytz.timezone('Asia/Makassar') # UTC+8
    WIT  = pytz.timezone('Asia/Jayapura') # UTC+9
	
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

    jam_wib = now_utc.astimezone(WIB).strftime('%H:%M WIB')
    jam_wita = now_utc.astimezone(WITA).strftime('%H:%M WITA')
    jam_wit = now_utc.astimezone(WIT).strftime('%H:%M WIT')

    return jam_wib, jam_wita, jam_wit
# Fungsi untuk ambil tanggal batas pembayaran
def tanggal_pembayaran():
    return (datetime.now(JAKARTA) + timedelta(minutes=5)).strftime('%d %B %Y')

# Fungsi untuk ambil waktu +1 jam dari sekarang

def waktu_plus_1jam():
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc) + timedelta(hours=2)
    wib = now_utc.astimezone(WIB).strftime('%H:%M WIB')
    wita = now_utc.astimezone(WITA).strftime('%H:%M WITA')
    wit = now_utc.astimezone(WIT).strftime('%H:%M WIT')
    return wib, wita, wit

def tanggal_sekarang():
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    tanggal = now_utc.astimezone(WIB).strftime('%d-%m-%Y')
    return tanggal

def is_admin(user_id):
    db = get_db()
    admin = db.execute("SELECT 1 FROM admin WHERE user_id = ?", (user_id,)).fetchone()
    return True if admin else False

# Koneksi ke database
def get_db():
    db_path = 'bot/biji22.db'  # Sesuaikan dengan path database Anda
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Allows fetching results as dictionaries
    return conn

# Function to close the database connection safely
def close_db(conn):
    if conn:
        conn.close()

def get_user_line(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT member FROM user WHERE member = ?", (user_id,))
    result = cursor.fetchone()
    close_db(conn)
    return result["member"] if result else None
    
# ==================== KONSTANTA DAN VARIABEL =====================

API_KEY = "91e30218-7148-4ab8-bd84-a98c89fa2ba7"
user_sessions = {}
used_amounts = set()
otp_timers = {}
phone_timers = {}
reseller_ids = set()

paket_aktif_cache = {}  

mutasi_api_url = "https://gateway.okeconnect.com/api/mutasi/qris/OK2188560/750533817389052712188560OKCT1E273EEEB2731D80D4DFD95163D1879B"  # Ganti dengan merchant ID dan API key QRIS
API_KEY = "91e30218-7148-4ab8-bd84-a98c89fa2ba7" 
DOR_API_KEY = "0a1ccba4-e6fc-498c-af2f-5f889c765aaa"  # Ganti dengan API key DOR
QRIS_BASE_QR_STRING = "00020101021126670016COM.NOBUBANK.WWW01189360050300000879140214528415756549050303UMI51440014ID.CO.QRIS.WWW0215ID20253753827490303UMI5204481253033605802ID5921RIZYULSTORE OK21885606005BOGOR61051611062070703A0163048CCF"  # Ganti dengan base QR string
ID_TELEGRAM = "5730784044"  # Ganti dengan ID Telegram mang
PASSWORD = "03juni1998"  # Ganti dengan password mang
used_amounts = set()  # Menyimpan nominal yang sudah digunakan dalam bentuk set (agar tidak ada duplikasi)
user_sessions = {}
admin_chat_id = 5730784044  # ID Admin
admin_ids = [5730784044]
group_id = -1001911780985  # Ganti dengan ID grup log kamu
group_id_kedua = -1001872029038  # Ganti dengan ID grup log kamu
TOPIK_ASLI = 58638
# ==================== DATABASE HELPERS =====================

def get_db():
    conn = sqlite3.connect('bot/biji22.db')
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    if conn:
        conn.close()

def create_user_sessions_table():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            user_id INTEGER PRIMARY KEY,
            phone TEXT,
            token TEXT,
            verified INTEGER,
            token_time REAL
        )
    """)
    conn.commit()
    close_db(conn)


def buat_tabel_transaksi_dor():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaksi_dor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            nomor TEXT,
            paket TEXT,
            harga INTEGER,
            ref TEXT,
            trx_id TEXT,
            tanggal TEXT,
            waktu TEXT
        )
    """)
    conn.commit()
    conn.close()

def buat_tabel_paket_aktif():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS paket_aktif (
            user_id INTEGER,
            name TEXT,
            encrypted_code TEXT
        )
    """)
    conn.commit()
    conn.close()
    
def alter_user_table_add_token():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE user ADD COLUMN token TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    close_db(conn)

# ==================== FUNGSI USER =====================

def is_reseller(user_id):
    db = get_db()
    result = db.execute("SELECT role FROM user WHERE member = ?", (user_id,)).fetchone()
    close_db(db)
    return result and result[0] == 'reseller'

def get_user_balance(user_id):
    db = get_db()
    row = db.execute("SELECT saldo_dor FROM user WHERE member = ?", (user_id,)).fetchone()
    close_db(db)
    if row:
        return row[0]
    raise ValueError("User tidak ditemukan di database.")

def kurangi_saldo(user_id, amount):
    db = get_db()
    db.execute("UPDATE user SET saldo_dor = saldo_dor - ? WHERE member = ?", (amount, user_id))
    db.commit()
    close_db(db)

def tambah_saldo(user_id, nominal):
    db = get_db()
    user_exists = db.execute("SELECT 1 FROM user WHERE member = ?", (user_id,)).fetchone()
    if not user_exists:
        raise ValueError("User tidak ditemukan di database.")
    db.execute("UPDATE user SET saldo_dor = saldo_dor + ? WHERE member = ?", (nominal, user_id))
    db.commit()
    close_db(db)

def increment_all_user_counts():
    db = get_db()
    db.execute("UPDATE user SET counted = counted + 1")
    db.commit()
    close_db(db)

def get_user_counted(user_id):
    db = get_db()
    result = db.execute("SELECT counted FROM user WHERE member = ?", (user_id,)).fetchone()
    close_db(db)
    return result[0] if result else 0

def increment_all_user_counted_dor():
    db = get_db()
    try:
        db.execute("UPDATE user SET counted_dor = counted_dor + 1")
        db.commit()
    finally:
        close_db(db)
def get_user_counted_dor(user_id):
    db = get_db()
    result = db.execute("SELECT counted_dor FROM user WHERE member = ?", (user_id,)).fetchone()
    close_db(db)
    return result[0] if result else 0
    
def get_riwayat_dor(user_id, offset=0, limit=5, tanggal_filter=None):
    conn = get_db()
    c = conn.cursor()
    if tanggal_filter:
        c.execute("""
            SELECT id, nomor, paket, harga, ref, trx_id, tanggal, waktu 
            FROM transaksi_dor 
            WHERE user_id = ? AND tanggal = ? 
            ORDER BY id DESC LIMIT ? OFFSET ?
        """, (user_id, tanggal_filter, limit, offset))
    else:
        c.execute("""
            SELECT id, nomor, paket, harga, ref, trx_id, tanggal, waktu 
            FROM transaksi_dor 
            WHERE user_id = ? 
            ORDER BY id DESC LIMIT ? OFFSET ?
        """, (user_id, limit, offset))
    rows = c.fetchall()
    conn.close()
    return rows
    
def simpan_riwayat_dor(user_id, nomor, paket, harga, ref, trx_id, tanggal, waktu):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO transaksi_dor (user_id, nomor, paket, harga, ref, trx_id, tanggal, waktu)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, nomor, paket, harga, ref, trx_id, tanggal, waktu))
    conn.commit()
    conn.close()

def hitung_total_riwayat(user_id, tanggal_filter=None):
    conn = get_db()
    c = conn.cursor()
    if tanggal_filter:
        c.execute("SELECT COUNT(*) FROM transaksi_dor WHERE user_id = ? AND tanggal = ?", (user_id, tanggal_filter))
    else:
        c.execute("SELECT COUNT(*) FROM transaksi_dor WHERE user_id = ?", (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def hapus_semua_riwayat(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM transaksi_dor WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()    
# ==================== SESSION HANDLING =====================
def save_user_session(user_id, phone, token):
    conn = get_db()
    cur = conn.cursor()
    print(f"[SAVE] user_id={user_id}, phone={phone}, token={token}")
    cur.execute("""
        REPLACE INTO user_sessions (user_id, phone, token, verified, token_time)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, phone, token, 1, time.time()))
    conn.commit()
    close_db(conn)
    
def get_user_session(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM user_sessions WHERE user_id = ? AND verified = 1", (user_id,)).fetchone()
    close_db(db)
    print(f"[GET] user_id={user_id} -> {row}")
    return dict(row) if row else None
    
def delete_user_session(user_id):
    db = get_db()
    db.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
    db.commit()
    close_db(db)

def save_token_db(user_id, nomor, token):
    db = get_db()
    # Kolom user_id, bukan member; karena di user_sessions kolom user_id
    db.execute("UPDATE user_sessions SET token = ?, token_time = ? WHERE user_id = ?", (token, time.time(), user_id))
    db.commit()
    close_db(db)

def get_token_db(user_id):
    db = get_db()
    # Ambil kolom token dari tabel user_sessions berdasarkan user_id
    row = db.execute("SELECT token FROM user_sessions WHERE user_id = ? AND verified = 1", (user_id,)).fetchone()
    close_db(db)
    return row[0] if row else None

def delete_token_db(user_id):
    db = get_db()
    # Set token jadi NULL berdasarkan user_id
    db.execute("UPDATE user_sessions SET token = NULL WHERE user_id = ?", (user_id,))
    db.commit()
    close_db(db)

def sensor_hp(nomor):
    if len(nomor) >= 10:
        return nomor[:3] + "****" + nomor[7:]
    return nomor

# ==================== TOKEN VALIDATION =====================

async def get_valid_token(nomor, user_id=None):
    if user_id:
        token = get_token_db(user_id)
        if token:
            return token

    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-accesstokenlist-xltembakservice.kmsp-store.com/v1"
        async with session.get(url, params={"api_key": API_KEY}) as resp:
            res = await resp.json()
            if not res.get("status") or not res.get("data"):
                return None
            for d in res["data"]:
                if d.get("msisdn") == nomor:
                    return d.get("token")
    return None


from typing import Optional

async def extend_token_xl(phone: str, session_id: str, token: str) -> Optional[str]:
    auth_id = f"{session_id}:{token}"
    url = "https://golang-openapi-login-xltembakservice.kmsp-store.com/v1"
    params = {
        "api_key": API_KEY,
        "phone": phone,
        "method": "LOGIN_BY_ACCESS_TOKEN",
        "auth_id": auth_id
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                if data.get("status") and "access_token" in data.get("data", {}):
                    return data["data"]["access_token"]
                else:
                    print("Extend token gagal:", data)
                    return None
    except Exception as e:
        print(f"Error saat extend token: {e}")
        return None

async def get_token_or_refresh(nomor, user_id):
    session_data = get_user_session(user_id)
    if not session_data:
        return None

    token_lama = session_data["token"]
    if not token_lama:
        return None

    # Coba akses data kuota dulu untuk cek token valid
    cek_url = "https://golang-openapi-quotadetails-xltembakservice.kmsp-store.com/v1"
    params = {
        "api_key": API_KEY,
        "access_token": token_lama
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(cek_url, params=params) as resp:
                data = await resp.json()

        if data.get("status") is True:
            return token_lama  # Token masih valid

    except Exception as e:
        print(f"Error saat cek token: {e}")

    # Jika gagal, coba refresh dengan login ulang
    try:
        session_id = token_lama.split(":")[0]
        login_url = "https://golang-openapi-login-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "phone": nomor,
            "method": "LOGIN_BY_ACCESS_TOKEN",
            "auth_id": f"{session_id}:{token_lama}"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(login_url, params=params) as resp:
                result = await resp.json()

        if result.get("status") and "access_token" in result.get("data", {}):
            new_token = result["data"]["access_token"]
            save_user_session(user_id, nomor, new_token)
            return new_token
        else:
            print("❌ Gagal login ulang XL:", result)
            return None

    except Exception as e:
        print(f"❌ Gagal extend token XL: {e}")
        return None  
# ==================== QRIS FUNGSI =====================
def calculate_crc16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF

def generate_qr_string(amount):
    qris_base = QRIS_BASE_QR_STRING[:-4].replace("010211", "010212")
    nominal_str = str(amount)
    nominal_tag = f"54{len(nominal_str):02d}{nominal_str}"
    insert_position = qris_base.find("5802ID")
    if insert_position == -1:
        raise ValueError("Format QRIS tidak valid, tidak ditemukan tag '5802ID'")
    qris_with_nominal = qris_base[:insert_position] + nominal_tag + qris_base[insert_position:]
    checksum = format(calculate_crc16(qris_with_nominal.encode()), '04X')
    return qris_with_nominal + checksum



def generate_qr_with_logo(qr_string):
    # Buat QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)

    dodger_blue = (30, 144, 255)
    qr_img = qr.make_image(fill_color=dodger_blue, back_color="white").convert("RGB")

    # Buat background dengan rounded corner
    border_padding = 20
    corner_radius = 30
    outer_size = (qr_img.size[0] + 2 * border_padding, qr_img.size[1] + 2 * border_padding)
    
    # Background putih
    background = Image.new("RGB", outer_size, "white")
    
    # Mask untuk rounded corners
    rounded_mask = Image.new("L", outer_size, 0)
    draw_mask = ImageDraw.Draw(rounded_mask)
    draw_mask.rounded_rectangle(
        [0, 0, outer_size[0] - 1, outer_size[1] - 1],
        radius=corner_radius,
        fill=255
    )

    # Bingkai warna
    draw_border = ImageDraw.Draw(background)
    draw_border.rounded_rectangle(
        [0, 0, outer_size[0] - 1, outer_size[1] - 1],
        radius=corner_radius,
        outline=dodger_blue,
        width=4
    )

    # Tempelkan QR di tengah background
    background.paste(qr_img, (border_padding, border_padding))

    # Tempel logo original jika ada
    logo_path = "/root/bot/image/logoqr.png"
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo_size = qr_img.size[0] // 4
        logo = logo.resize((logo_size, logo_size))
        logo_pos = (
            (background.size[0] - logo_size) // 2,
            (background.size[1] - logo_size) // 2
        )
        background.paste(logo, logo_pos, logo)  # tanpa latar putih tambahan

    # Terapkan rounded mask ke hasil akhir
    final_image = Image.new("RGB", outer_size, "white")
    final_image.paste(background, (0, 0), mask=rounded_mask)

    return final_image


MAX_RETRIES = 3
RETRY_DELAY = 10  # detik

def check_payment(expected_amount, payment_start_time):
    retries = 0

    while retries < MAX_RETRIES:
        try:
            response = requests.get(mutasi_api_url, timeout=10)

            # Penanganan status 429 (Too Many Requests)
            if response.status_code == 429:
                print(f"[WARNING] Too Many Requests (429). Menunggu {RETRY_DELAY} detik sebelum coba lagi...")
                retries += 1
                time.sleep(RETRY_DELAY)
                continue

            # Status lain yang bukan 200
            if response.status_code != 200:
                print(f"[ERROR] Status Code: {response.status_code}")
                return False

            data = response.json()
            if data.get("status") != "success":
                print(f"[ERROR] Status bukan success: {data}")
                return False

            for trx in data.get("data", []):
                try:
                    if trx.get("type") != "CR":
                        continue

                    trx_amount = int(trx.get("amount"))
                    trx_time_str = trx.get("date")  # format: "2025-05-12 22:50:31"
                    trx_time = datetime.strptime(trx_time_str, "%Y-%m-%d %H:%M:%S")

                    print(f"[DEBUG] Cek trx: amount={trx_amount}, time={trx_time}, after_start={trx_time >= payment_start_time}")

                    if trx_amount == expected_amount and trx_time >= payment_start_time:
                        print(f"[PAYMENT MATCH] Ditemukan pembayaran valid: Rp {trx_amount} pada {trx_time}")
                        return True
                except Exception as e:
                    print(f"[WARNING] Error parsing trx: {e}")
                    continue

            return False

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request exception: {e}")
            retries += 1
            time.sleep(RETRY_DELAY)
        except Exception as e:
            print(f"[ERROR] Unexpected: {e}")
            return False

    print("[ERROR] Gagal cek mutasi setelah beberapa kali percobaan.")
    return False
        
def sensor_hp(nomor):
    if len(nomor) >= 10:
        return nomor[:3] + "****" + nomor[7:]
    return nomor  # jika nomor terlalu pendek, kembalikan apa adanya
    
# ==================== MENU DOR =====================

def generate_dor_menu(is_verified: bool) -> str:
    return f"""
╔══════════════════════════╗
           🧨 𝗣𝗔𝗡𝗘𝗟 𝗧𝗘𝗠𝗕𝗔𝗞 𝗫𝗟 🧨
╚══════════════════════════╝
╭── 🔐 𝗜𝗡𝗙𝗢 𝗔𝗞𝗨𝗡 ─────────────╮
│ 🧾 Status   : {'Terverifikasi ✅' if is_verified else 'Belum Verifikasi ❌'}
│ ⚙️ Aksi     : {'🚀 Mulai DOR' if is_verified else '📱 Minta OTP (masukkan nomor)'}
╰──────────────────────────╯
╭── 🎁 𝗣𝗔𝗞𝗘𝗧 𝗬𝗔𝗡𝗚 𝗧𝗘𝗥𝗦𝗘𝗗𝗜𝗔 ────╮
│ 📦 XUTS + 1GB
│ 📦 XUTP + XCS
│ 📦 XUT VIDIO
│ 📦 XUT IFLIX
│ 📦 XCS ADD-ON BYPASS
│ 📦 XC FLEX S PROMO
│ 📦 XCP MIRIP BIZZ
│ 📦 Masaaktif 1 Tahun
╰──────────────────────────╯
"""

@bot.on(events.NewMessage(pattern="/tembakxl"))
@bot.on(events.CallbackQuery(data=b'tembakxl'))
async def start_menu(event):
    user_id = event.sender_id

    if is_maintenance_tembakxl() and not is_admin(user_id):
        await event.answer("🚧 Tembak XL sedang MAINTENANCE!!", alert=True)
        return

    session_data = get_user_session(user_id)
    is_verified = False
    hp = None

    if session_data:
        hp = session_data["phone"]
        token = session_data["token"]
        token_time = session_data.get("token_time") or 0
        token_age = time.time() - token_time

        if token_age < 86400:
            is_verified = True
            user_sessions[user_id] = {"step": "otp_verified", "hp": hp, "token": token}
        else:
            async with aiohttp.ClientSession() as session:
                try:
                    url = "https://golang-openapi-login-xltembakservice.kmsp-store.com/v1"
                    params = {
                        "api_key": API_KEY,
                        "phone": hp,
                        "method": "LOGIN_BY_ACCESS_TOKEN",
                        "auth_id": f"{user_id}:{token}"
                    }
                    async with session.get(url, params=params) as resp:
                        data = await resp.json()
                        if data.get("status") is True:
                            new_token = data["data"].get("access_token")
                            is_verified = True
                            save_user_session(user_id, hp, new_token)
                            user_sessions[user_id] = {"step": "otp_verified", "hp": hp, "token": new_token}
                        else:
                            delete_user_session(user_id)
                except Exception as e:
                    await event.respond(f"⚠️ Gagal perpanjang token: {e}")
                    return

    buttons = []
    if is_verified:
        buttons.append([Button.inline("🚀 Mulai Dor", b"dor"), Button.inline("🗑️ Hapus OTP", b"hapus_otp")])
    else:
        buttons.append([Button.inline("🔑 Minta OTP", b"otp")])

    buttons.append([
        Button.inline("📶 Cek Kuota by login", b"cek_kuota_xl"),Button.inline("📶 Cek Kuota", b"cek_kuota_start")])     
    buttons.append([Button.inline("🧾 Cek TRX", b"cek_trx"),Button.inline("📋 Riwayat DOR", b"riwayat_dor")])    
    buttons.append([Button.inline("📘 Tutorial Pembelian XUTS & ADD-ON XCS BYPASS", b"addon_info")])
    buttons.append([Button.inline("🧹 Unreg Paket Aktif", b'unreg_paket')])  
    buttons.append([Button.inline("🔙 Kembali ke Menu", b"menu")])
    await event.edit(generate_dor_menu(is_verified), buttons=buttons)

# Untuk kelanjutan `@bot.on(events.CallbackQuery(data=b'otp'))` dan OTP handler, silakan beri kode lanjutannya agar bisa diperbaiki juga.# ==================== OTP FLOW =====================
@bot.on(events.CallbackQuery(data=b'otp'))
async def menu_otp(event):
    user_id = event.sender_id
    await event.respond("📱 Masukkan nomor XL kamu (contoh: 62877xxxx):")
    user_sessions[user_id] = {"step": "awaiting_phone"}

    # Cancel timer lama jika ada
    if user_id in phone_timers:
        phone_timers[user_id].cancel()

    # Timer 60 detik tunggu input nomor
    async def nomor_timeout():
        await asyncio.sleep(60)
        if user_sessions.get(user_id, {}).get("step") == "awaiting_phone":
            user_sessions.pop(user_id, None)
            try:
                await event.respond(
                    "⏰ Waktu input nomor habis!\nKlik **Minta OTP** lagi untuk mengulang.",
                    buttons=[Button.inline("🔁 Minta OTP", b"otp")]
                )
            except:
                pass

    phone_timers[user_id] = asyncio.create_task(nomor_timeout())
    
@bot.on(events.NewMessage)
async def handle_otp_input(event):
    user_id = event.sender_id
    text = event.raw_text.strip()

    if user_id in user_sessions and user_sessions[user_id].get("step") == "awaiting_phone":
        phone = text
        if not phone.startswith("628") or len(phone) < 10:
            await event.respond("❌ Nomor tidak valid. Masukkan nomor yang benar (contoh: 62877xxxx).")
            return

        user_sessions[user_id]["hp"] = phone
        user_sessions[user_id]["step"] = "otp_sent"

        if user_id in phone_timers:
            phone_timers[user_id].cancel()

        async with aiohttp.ClientSession() as session:
            try:
                url = "https://golang-openapi-reqotp-xltembakservice.kmsp-store.com/v1"
                params = {
                    "api_key": API_KEY,
                    "phone": phone,
                    "method": "OTP"
                }
                async with session.get(url, params=params) as resp:
                    data = await resp.json()

                    if data.get("status") is True:
                        auth_id = data["data"].get("auth_id")
                        user_sessions[user_id]["step"] = "awaiting_otp"
                        user_sessions[user_id]["auth_id"] = auth_id

                        await event.respond(
                            f"✅ OTP sudah dikirim ke nomor {phone}.\nMasukkan kode OTP yang kamu terima:"
                        )

                        if user_id in otp_timers:
                            otp_timers[user_id].cancel()

                        async def otp_timeout():
                            await asyncio.sleep(90)
                            if user_sessions.get(user_id, {}).get("step") == "awaiting_otp":
                                user_sessions.pop(user_id, None)
                                try:
                                    await event.respond(
                                        "⏰ Waktu input OTP habis!\nKlik **Minta OTP** lagi untuk mengulang.",
                                        buttons=[Button.inline("🔁 Minta OTP", b"otp")]
                                    )
                                except:
                                    pass

                        otp_timers[user_id] = asyncio.create_task(otp_timeout())
                    else:
                        await event.respond(f"❌ Gagal mengirim OTP: {data.get('message', 'Unknown error')}")
                        user_sessions.pop(user_id, None)

            except Exception:
                await event.respond("❌ Terjadi kesalahan saat mengirim OTP. Coba lagi nanti.")
                user_sessions.pop(user_id, None)
   
    
    
    elif user_id in user_sessions and user_sessions[user_id].get("step") == "awaiting_otp":
        otp_code = text
        phone = user_sessions[user_id]["hp"]
        auth_id = user_sessions[user_id].get("auth_id")

        if not auth_id:
            await event.respond("❌ Gagal login dengan OTP: Auth ID Kosong!")
            return

        async with aiohttp.ClientSession() as session:
            try:
                url = "https://golang-openapi-login-xltembakservice.kmsp-store.com/v1"
                params = {
                    "api_key": API_KEY,
                    "phone": phone,
                    "method": "OTP",
                    "auth_id": auth_id,
                    "otp": otp_code
                }
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    if data.get("status") is True:
                        token = data["data"].get("access_token")

                        save_user_session(user_id, phone, token)
                        save_token_db(user_id, phone, token)

                        user_sessions[user_id] = {
                            "step": "otp_verified",
                            "hp": phone,
                            "token": token
                        }

                        if user_id in otp_timers:
                            otp_timers[user_id].cancel()

                        await event.respond("✅ OTP berhasil diverifikasi! Kamu sekarang bisa menggunakan fitur tembak XL.",
                            buttons=[[Button.inline("🚀 Mulai Dor", b"dor")]])
                    else:
                        await event.respond(f"❌ Gagal login dengan OTP: {data.get('message', 'Unknown error')}")
            except Exception:
                await event.respond("❌ Terjadi kesalahan saat login OTP. Silakan coba kembali.")               
 
    
@bot.on(events.CallbackQuery(data=b'hapus_otp'))
async def hapus_otp(event):
    user_id = event.sender_id
    delete_user_session(user_id)
    user_sessions.pop(user_id, None)
    await event.edit("✅ OTP dan sesi berhasil dihapus.\nSilakan verifikasi ulang jika ingin lanjut.", buttons=[
        [Button.inline("🔑 Minta OTP", b"otp")],
        [Button.inline("🔙 Kembali", b"tembakxl")]
    ])


async def unreg_paket(api_key, access_token, encrypted_code):
    url = "https://golang-openapi-unregpackage-xltembakservice.kmsp-store.com/v1"
    params = {
        "api_key": api_key,
        "access_token": access_token,
        "encrypted_package_code": encrypted_code
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return await resp.json()
            
@bot.on(events.CallbackQuery(data=b'login_ulang_token'))
async def login_ulang_token(event):
    user_id = event.sender_id
    session = get_user_session(user_id)

    if not session:
        await event.answer("Data sesi tidak ditemukan. Silakan login ulang.", alert=True)
        return

    phone = session.get("phone")
    access_token = session.get("token")  # Format: session_id:token

    if not phone or not access_token:
        await event.answer("Token atau nomor tidak valid.", alert=True)
        return

    url = "https://golang-openapi-login-xltembakservice.kmsp-store.com/v1"
    params = {
        "api_key": API_KEY,
        "phone": phone,
        "method": "LOGIN_BY_ACCESS_TOKEN",
        "auth_id": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status"):
            new_token = data["data"]["access_token"]
            save_user_session(user_id, phone, new_token)  # update token
            await event.answer("Berhasil login ulang!", alert=True)
        else:
            await event.answer(f"Gagal: {data.get('message')}", alert=True)

    except Exception as e:
        await event.answer(f"Error: {str(e)}", alert=True)   


# Tombol menu utama
@bot.on(events.NewMessage(pattern='/list_token'))
async def menu_handler(event):
    buttons = [
        [Button.inline("Daftar Token Aktif", data="list_token_aktif")]
    ]
    await event.respond("Pilih menu:", buttons=buttons)

# Handler tombol callback
@bot.on(events.CallbackQuery(data=b"list_token_aktif"))
async def list_token_handler(event):
    await event.answer()  # HANYA untuk CallbackQuery
    api_key = "API_KEY"
    url = f"https://golang-openapi-accesstokenlist-xltembakservice.kmsp-store.com/v1?api_key={api_key}"

    try:
        response = requests.get(url)
        result = response.json()

        if result.get("status") and result.get("data"):
            text = "**Daftar Access Token Aktif:**\n"
            for idx, token_info in enumerate(result["data"], 1):
                msisdn = token_info["msisdn"]
                time = token_info["time"]
                session_id = token_info["session_id"]
                token = token_info["token"][:10] + "..."  # ringkas token
                text += f"\n{idx}. **{msisdn}**\nWaktu: `{time}`\nSession ID: `{session_id}`\nToken: `{token}`\n"
        else:
            text = "Tidak ada access token aktif yang ditemukan."
    except Exception as e:
        text = f"Gagal mengambil data:\n{str(e)}"

    await event.edit(text)
# ==================== DOR BUTTON: QRIS + TEMBAK OTOMATIS =====================

@bot.on(events.CallbackQuery(data=b'dor'))
async def handle_dor(event):
    user_id = event.sender_id
    nomor = user_sessions[user_id].get("hp")

    text = f"""
╔══════════════════════════╗
           🧨 𝗣𝗔𝗡𝗘𝗟 𝗧𝗘𝗠𝗕𝗔𝗞 𝗫𝗟 🧨
╚══════════════════════════╝
╭── 🎯 𝗗𝗘𝗧𝗔𝗜𝗟 𝗧𝗔𝗥𝗚𝗘𝗧 ─────────╮
│ 📱 Nomor : {nomor}
╰──────────────────────────╯
Silakan pilih jenis paket tembak:
"""

    buttons = [
        [Button.inline("📦 ADD-ON XCS BYPASS", b"menu_xcs"),Button.inline("📦 XUTP & XUTS", b"menu_xutsp")],
        [Button.inline("📦 XUT VIDIO & IFLIX", b"menu_vix"),Button.inline("📦 Xtra Combo Flex S Promo", b"menu_flex")],
        [Button.inline("📦 Xl DATA REGULER", b"menu_data")],
        [Button.inline("📦 Paket Lainnya", b"menu_lainnya")],
        [Button.inline("🔙 Kembali", b"tembakxl")]
    ]

    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'dor_xutp'))
async def dor_xutp(event):
    text = """
━━━━━━━━〔 XUTP  〕━━━━━━━━

```📦 Xtra Unlimited Turbo Premium   
Harga: Rp10.000 (saldo bot/QRIS)
➣ Catatan   :
- Kartu tidak dalam masa tenggang.
- Pastikan pulsa 16k (jangan lebih dari 50k).
- WAJIB UNREG semua paket lama: DIAL 808# > STOP LANGGANAN.
- Tidak ada xtra combo 100gb atau Xtra Combo Sejenisnya sampai hilang.
- JIKA GAGAL UNREG LAKUKAN TERUS MENERUS SAMPAI BERHASIL.
- Tidak ada GARANSI/REFUND Jika dor tidak masuk.
- semua risiko ditanggung pembeli.
- Setelah proses tembak, akan ada notif SMS Xtra Combo blablabla diikuti.
"Mohon maaf transaksi Anda tidak dapat diproses....."
"Mohon jangan unreg paket Xtra Combo blablabla..
- Jangan beli paket apa-apa dulu selama 2 jam hingga ada notif.
"SMS paket Xtra Unlimited Turbo Premium 50k telah aktif."``
    
➣ Bonus:
- Unlimited YouTube, WhatsApp, IG, dll.
- Bisa FUP hingga 300GB/bulan```
"""

    buttons = [
        [Button.inline("🚀 Mulai Tembak Paket XUTP", b"paket_xutp")],
        [Button.inline("🔙 Kembali", b"dor")]
    ]
    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'menu_lainnya'))
async def dor_xutp(event):
    text = (
        "╔══════════════════════╗\n"
        "      📦 PAKET XCP & MASAAKTIF     \n"
        "╚══════════════════════╝\n\n"
        "📦 Paket: XCP MIRIP BIZZ\n"
        "📦 Paket: Masa Aktif 1 Tahun\n\n"
        "📌 *Catatan Penting:*\n"
        "• Kartu tidak dalam masa tenggang\n"
        "• WAJIB UNREG semua paket lama:\n"
        "  ➤ DIAL *808# ➜ STOP Langganan\n"
        "• Untuk tembak *XCP MIRIP BIZZ*:\n"
        "  ➤ Tidak boleh ada Xtra Combo 100GB\n"
        "  ➤ Tidak boleh ada Xtra Combo lainnya\n"
        "• Untuk tembak *ADD-ON XCL*:\n"
        "  ➤ Wajib ada paket *Xtra Combo Lite*\n"
        "• Jika gagal UNREG, coba terus hingga berhasil\n"
        "• Tidak ada *garansi/refund* jika paket tidak masuk\n"
        "• Semua risiko ditanggung pembeli\n"
        "• Jangan beli paket apapun dulu selama 2 jam\n"
        "  hingga muncul notifikasi masuk\n"
    )

    buttons = [
        [Button.inline("🎯 XCP 10GB", b"dor_xcp"), Button.inline("⏳ Masa Aktif 1 Tahun", b"dor_masaaktif")],
        [Button.inline("🔙 Kembali", b"dor")]
    ]
    await event.edit(text, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'dor_xcs'))
async def dor_xcs(event):
    text = """
```📦 Add-On Tersedia:
- Turbo Premium 50k
- Turbo Super 30k
- Turbo Standart 20k 
- Turbo Basic 10k
- Netflix, TikTok, Viu, Joox, Youtube 25k
- Pembayaran via DANA  
- Saldo refund

➣ Catatan   :
- Kartu tidak dalam masa tenggang.
- WAJIB UNREG semua paket lama: DIAL 808# > STOP LANGGANAN.
- Tidak ada xtra combo 100gb atau Xtra Combo Sejenisnya sampai hilang.
- JIKA GAGAL UNREG LAKUKAN TERUS MENERUS SAMPAI BERHASIL.
- Setelah tembak, tunggu SMS aktivasi hingga MAKSIMAL 2 JAM.
- Jangan membeli paket lain selama menunggu aktivasi.
- Tidak ada GARANSI/REFUND Jika dor tidak masuk
- Dor semua risiko ditanggung pembeli.  

➣ Info Biaya Jasa:
- Paket XCS: Rp5.000
- Add-on: Rp500```
"""

    buttons = [
        [Button.inline("🚀 Mulai Tembak Paket XCS", b"paket_xcs")],
        [Button.inline("🔙 Kembali", b"dor")]
    ]
    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'dor_bundle'))
async def dor_bundle(event):
    await event.answer("Mengecek stok...")

    package_id = "XLUNLITURBOBUNDLEPROMO25K"  # ID produk untuk Bundle XUT
    url = f"https://golang-openapi-checkpackagestock-xltembakservice.kmsp-store.com/v1"
    params = {
        "api_key": API_KEY,
        "package_id": package_id
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                if data.get("status") and not data["data"].get("is_out_of_stock"):
                    # Jika stok tersedia, tampilkan menu
                    text = """
━━━━━━━━〔 Bundle XUT 〕━━━━━━━━

```📦 Paket: Bundle Xtra Unlimited Turbo  

➣ Fitur :
- WhatsApp, Line, Gojek, Facebook, IG, YouTube
- Bonus Turbo: Netflix, Viu, TikTok, Joox
    (Bonus tidak dijamin semua aktif)

➣ Catatan   :
- Kartu tidak dalam masa tenggang.
- WAJIB UNREG semua paket lama: DIAL 808# > STOP LANGGANAN.
- Tidak ada xtra combo 100gb atau Xtra Combo Sejenisnya sampai hilang.
- JIKA GAGAL UNREG LAKUKAN TERUS MENERUS SAMPAI BERHASIL.
- Jika di kartu kalian masih ada Xtra Unlimited Turbo, maka akan kami unreg.
- Tidak ada GARANSI/REFUND Jika dor tidak masuk
- Dor semua risiko ditanggung pembeli.  
- Selama status transaksi masih Pending, mohon jangan belikan paket apapun dulu baik dari myXL atau aplikasi server pulsa.
- Harus sabar menunggu maksimal 2 jam (memang harus begini dari sistemnya XL), 
- jika status sukses maka akan diubah oleh sistem ke Transaksi sukses.
- Tidak membutuhkan Pulsa dsj, One click Payment!
- PASANG KARTU XL KALIAN KE MODEM/HP YANG AKAN DIPAKAI UNTUK INJECT VPN.

➣ Info Biaya Jasa:
- Harga : Rp40.000 (member) / Rp32000 (reseller)```
                    """
                    buttons = [
                        [Button.inline("🚀 Mulai Tembak Bundle XUT", b"paket_xut")],
                        [Button.inline("🔙 Kembali", b"dor")]
                    ]
                    await event.edit(text, buttons=buttons)
                else:
                    await event.edit("❌ Maaf, stok *Bundle XUT* sedang kosong.\nSilakan coba lagi nanti.", buttons=[
                        [Button.inline("🔙 Kembali", b"dor")]
                    ])
        except Exception as e:
            await event.edit(f"❌ Gagal mengecek stok:\n{e}", buttons=[
                [Button.inline("🔙 Kembali", b"dor")]
            ])

@bot.on(events.CallbackQuery(data=b'dor_masaaktif'))
async def dor_masaaktif(event):
    text = """
━━━━━━━━〔 Masa Aktif 1 Tahun 〕━━━━━━━━

```📦 Paket Masaaktif Tahunan  
- Perpanjangan per bulan

➣ Catatan   :
- Pastikan kartu tidak masa tenggang
- Masa aktif akan diperpanjang otomatis per bulan
- Tidak ada garansi jika gagal

➣ Info Biaya Jasa:
- Harga : Rp8.000 ```
    
"""

    buttons = [
        [Button.inline("🚀 Mulai Tembak Masa Aktif", b"paket_masaaktif")],
        [Button.inline("🔙 Kembali", b"dor")]
    ]
    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'dor_xcp'))
async def dor_xcp(event):
    text = """
━━━━━━━━〔 XCP MIRIP BIZ 〕━━━━━━━━

```📦 Xtra Combo Plus 10GB (Unlimited Apps Produktivitas Mirip Paket Biz untuk Inject SSH/VPN).
Harga: Rp10.000 (saldo bot)
➣ Catatan   :
- Kartu tidak dalam masa tenggang.
- Abaikan FUP Kuota Harian Aplikasi Produktivitas 20 GB atau 100MB. Tetap Unlimited walaupun sudah lewat 20GB atau 100MB.
- Sediakan saldo E-wallet Dana Rp64.000 (Akan terpotong segini). Klik tombol Bayar ketika sudah Beli Paket.
- WAJIB UNREG semua paket lama: DIAL 808# > STOP LANGGANAN.
- JIKA MASIH ADA PAKET XTRA COMBO PLUS LAINNYA, WAJIB UNREG DULU SEBELUM TEMBAK PAKET INI Sejenisnya sampai hilang.
- JIKA GAGAL UNREG LAKUKAN TERUS MENERUS SAMPAI BERHASIL.
- Tidak ada GARANSI/REFUND Jika dor tidak masuk.
- semua risiko ditanggung pembeli.

➣ Bonus:
- Bisa juga untuk syarat sikat bonus Addon Xtra Combo Plus, seperti Addon XCP 15GB / 10GB.
- Bisa FUP Unlimited/bulan```
"""

    buttons = [
        [Button.inline("🚀 Mulai Tembak Paket XCP", b"paket_xcp")],
        [Button.inline("🔙 Kembali", b"dor")]
    ]
    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'dor_xcl'))
async def dor_xcp(event):
    text = """
━━━━━━━━〔 ADD-ON XCL 〕━━━━━━━━

```📦 Addon Xtra Combo Lite Iflix, Facebook, Instagram FUP 190GB.
📦 Addon Xtra Combo Lite Vidio, Facebook, Instagram FUP 190GB.
📦 Addon Xtra Combo Lite Netflix, Facebook, Instagram FUP 190GB
📦 Addon Xtra Combo Lite Viu, Facebook, Instagram FUP 190GB
📦 Addon Xtra Combo Lite YouTube, Facebook, Instagram FUP 190GB

Harga : Rp500 (saldo bot)
➣ Catatan   :
- Wajib punya paket Xtra Combo Lite.
- Saat ini Xtra Combo Lite sudah tidak dapat ditembak lagi. 
- JAGA TERUS paket Xtra Combo Lite kamu yang masih aktif dengan menyediakan pulsa cukup (minimal 35K untuk Xtra Combo Lite M, minimal 25K untuk Xtra Combo Lite S) agar nanti auto perpanjangan sendiri saat paket mau expired..
- JIKA MASIH BELUM BISA DAN PEMBAYARAN ANDA DI-REFUND OLEH XL, CEK VIA DIAL *808# pergi ke menu Stop Paket/Langganan. 
- Pastikan tidak ada paket Addon Combo Lite sebelumnya yang masih nyangkut. Jika ada, unreg dulu addonnya.
- Membutuhkan Saldo E-wallet Dana Rp6.000 (akan terpotong segini).
- Klik tombol "Bayar" setelah beli paket.
- Masa aktif paket ini akan mengikuti sisa masa aktif paket Xtra Combo Lite saat ini.
- Tidak ada GARANSI/REFUND Jika dor tidak masuk.
- semua risiko ditanggung pembeli.

➣ Bonus:
- FUP 190GB. Tidak dapat diakumulasi. Jika kamu membelinya ulang sebelum FUP habis maka kuota FUP akan tereset ke posisi semula.```
"""

    buttons = [
        [Button.inline("🚀 Mulai Tembak Paket Add-on XCL", b"paket_xcl")],
        [Button.inline("🔙 Kembali", b"dor")]
    ]
    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'paket_xcl'))
async def paket_xcl(event):
    buttons = [
        [Button.inline("📺 ADD-ON Iflix", b'comfirm_paket_iflix')],
        [Button.inline("🎞️ ADD-ON Vidio", b'comfirm_paket_vidio'), Button.inline("🎬 ADD-ON Netflix", b'comfirm_paket_netflix')],
        [Button.inline("📺 ADD-ON Viu", b'comfirm_paket_viu'), Button.inline("▶️ ADD-ON Youtube", b'comfirm_paket_youtube')],
        [Button.inline("🔙 Kembali", b'dor')]
    ]

    teks = (
        "**📦 Paket Add-on XCL Dipilih**\n\n"
        " Wajib punya paket Xtra Combo Lite.\n"
        "Silakan pilih layanan Add-on yang ingin kamu aktifkan.\n"
        "Semua Add-on bersifat opsional dan bisa dilewati jika tidak dibutuhkan.\n\n"
        "_Klik salah satu tombol di bawah ini untuk melihat detail dan melanjutkan aktivasi._"
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_iflix'))
async def comfirm_paket_iflix(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")
    
    buttons = [
        [Button.inline("✅ Aktifkan IFLIX (DANA)", b"confirm_if_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcl")]
    ]

    teks = (
        f"**📺 Add-On IFLIX**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Siapkan saldo DANA Rp6.000\n\n"
        f"👉 Tekan tombol di bawah untuk aktivasi."
    )
    await event.edit(teks, buttons=buttons)


@bot.on(events.CallbackQuery(data=b'comfirm_paket_vidio'))
async def comfirm_paket_vidio(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")
    
    buttons = [
        [Button.inline("✅ Aktifkan VIDIO (DANA)", b"confirm_vid_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcl")]
    ]

    teks = (
        f"**🎞️ Add-On VIDIO**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Siapkan saldo DANA Rp10.000\n\n"
        f"👉 Tekan tombol di bawah untuk aktivasi."
    )
    await event.edit(teks, buttons=buttons)


@bot.on(events.CallbackQuery(data=b'comfirm_paket_netflix'))
async def comfirm_paket_netflix(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")
    
    buttons = [
        [Button.inline("✅ Aktifkan NETFLIX (DANA)", b"confirm_net_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcl")]
    ]

    teks = (
        f"**🎬 Add-On NETFLIX**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Siapkan saldo DANA Rp10.000\n\n"
        f"👉 Tekan tombol di bawah untuk aktivasi."
    )
    await event.edit(teks, buttons=buttons)


@bot.on(events.CallbackQuery(data=b'comfirm_paket_viu'))
async def comfirm_paket_viu(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")
    
    buttons = [
        [Button.inline("✅ Aktifkan VIU (DANA)", b"confirm_vu_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcl")]
    ]

    teks = (
        f"**📺 Add-On VIU**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Siapkan saldo DANA Rp8.000\n\n"
        f"👉 Tekan tombol di bawah untuk aktivasi."
    )
    await event.edit(teks, buttons=buttons)


@bot.on(events.CallbackQuery(data=b'comfirm_paket_youtube'))
async def comfirm_paket_youtube(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")
    
    buttons = [
        [Button.inline("✅ Aktifkan YOUTUBE (DANA)", b"confirm_ytb_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcl")]
    ]

    teks = (
        f"**▶️ Add-On YOUTUBE**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Siapkan saldo DANA Rp6.000\n\n"
        f"👉 Tekan tombol di bawah untuk aktivasi."
    )
    await event.edit(teks, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'paket_xutp'))
async def paket_xutp(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("💰 Bayar via Saldo", b"confirm_xutp_saldo")],
        [Button.inline("🔙 Kembali", b"dor_xutp")]
    ]

    teks = (
        f"**📦 Xtra Unlimited Turbo Premium Promo  **\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot Rp10.000 (member).\n"
        f"➣ Potong saldo Bot  Rp8.000\n"        
        f"➣ Siapkan Pulsa Rp16.000 \n"
        f"➣ Setelah langkah-langkah di atas, tekan **💰 Bayar via Saldo** untuk menyelesaikan pembelian:\n\n"
    )

    await event.edit(teks, buttons=buttons)
  
    
@bot.on(events.CallbackQuery(data=b'paket_xcp'))
async def paket_xcp(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("💰 Bayar via Saldo", b"confirm_xcp_saldo")],
        [Button.inline("🔙 Kembali", b"dor_xcp")]
    ]

    teks = (
        f"**📦 Paket XCP  **\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp8.000\n"    
        f"➣ Siapkan E-WALLET Rp64.000 \n"    
        f"➣ Setelah langkah-langkah di atas, tekan **💰 Bayar via Saldo** untuk menyelesaikan pembelian:\n\n"
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'paket_masaaktif'))
async def paket_masaaktif(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("💰 Bayar via Saldo", b"confirm_mastif1thn_saldo")],
        [Button.inline("🔙 Kembali", b"dor_masaaktif")]
    ]

    teks = (
        f"**📦 Masa Aktif 1 Tahun  **\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp8.000\n"        
        f"➣ Setelah langkah-langkah di atas, tekan **💰 Bayar via Saldo** untuk menyelesaikan pembelian:\n\n"
    )

    await event.edit(teks, buttons=buttons)
  
@bot.on(events.CallbackQuery(data=b'paket_xcs'))
async def paket_xcs(event):
    teks = (
        "**📦 Paket XCS Dipilih**\n\n"
        "**Urutan Aktivasi:**\n"
        "🟩 [STEP 1] ADS PREMIUM 30H\n"
        "🟨 [STEP 2] ADS SUPER 30H\n"
        "🟧 [STEP 3] ADS STANDART 30H\n"
        "🟥 [STEP 4] ADS BASIC 30H\n\n"
        "**Opsional Tambahan (boleh dilewati):**\n"
        "🎬 NETFLIX\n"
        "📺 VIU\n"
        "📱 TIKTOK\n"
        "🎵 JOOX\n"
        "▶️ YOUTUBE\n\n"
        "**Penutup:**\n"
        "📦 COMBO SPESIAL 8 GB \n\n"
        "_Silakan klik tombol sesuai urutan di bawah ini untuk membeli paket._"
    )

    buttons = [
        [Button.inline("[STEP 1] ADS PREMIUM 30H", b"comfirm_paket_prem"),
         Button.inline("[STEP 2] ADS SUPER 30H", b"comfirm_paket_super")],
        [Button.inline("[STEP 3] ADS STANDART 30H", b"comfirm_paket_sta"),
         Button.inline("[STEP 4] ADS BASIC 30H", b"comfirm_paket_bas")],
        [Button.inline("[OPSIONAL] NETFLIX", b"comfirm_paket_netflix"),
         Button.inline("[OPSIONAL] VIU", b"comfirm_paket_viu")],
        [Button.inline("[OPSIONAL] TIKTOK", b"comfirm_paket_tiktok"),
         Button.inline("[OPSIONAL] JOOX", b"comfirm_paket_joox")],
        [Button.inline("[OPSIONAL] YOUTUBE", b"comfirm_paket_youtube")],
        [Button.inline("[AKHIR] XCS 8 GB ", b"comfirm_paket_combos")],
        [Button.inline("🔙 Kembali", b"dor_xcs")]
    ]

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'menu_xcs'))
async def menu_xcs(event):
    teks = (
        "╔══════════════════════╗\n"
        "       📦 𝗣𝗔𝗞𝗘𝗧 𝗫𝗖𝗦 𝗗𝗜𝗣𝗜𝗟𝗜𝗛       \n"
        "╚══════════════════════╝\n\n"

        "╭── 🟩 𝗠𝗘𝗧𝗢𝗗𝗘 𝗕𝗬𝗣𝗔𝗦𝗦 ────╮\n"
        "│ 📌 ADD-ON tanpa pulsa & saldo DANA\n"
        "╰─────────────────────╯\n\n"
        "╭── 🟩 𝗠𝗘𝗧𝗢𝗗𝗘 𝗗𝗔𝗡𝗔 ──────╮\n"
        "│ 📦 XCS Kuota (1–8 GB)\n"
        "│ 🔹 Untuk Addon Premium / Multi Addon\n"
        "╰─────────────────────╯\n\n"
        "╭── 🟩 𝗠𝗘𝗧𝗢𝗗𝗘 𝗤𝗥𝗜𝗦 ──────╮\n"
        "│ 📦 XCS Kuota (1–8 GB)\n"
        "│ 🔹 Untuk Addon Premium / Multi Addon\n"
        "╰─────────────────────╯\n\n"
        "╭── 🟩 𝗠𝗘𝗧𝗢𝗗𝗘 𝗣𝗨𝗟𝗦𝗔 ─────╮\n"
        "│ 📦 XCS Tanpa Kuota\n"
        "│ 🔹 Untuk Addon Premium / Multi Addon\n"
        "╰─────────────────────╯\n\n"
        "╭── 🟩 𝗫𝗖 𝟭 + 𝟭𝗚𝗕 ─────────╮\n"
        "│ 🔹 Untuk Addon Super Saja\n"
        "│ 💸 DANA | 💳 QRIS | 📞 Pulsa\n"
        "╰──────────────────────╯\n\n"
        "📝 *Pilih salah satu metode untuk beli Addon dulu. Jika sudah, lanjut beli Extra Combonya.*"
    )

    buttons = [
        [Button.inline("[BYPASS] ADD-ON", b"menu_addon")],
        [Button.inline("[DANA] XCS (1-8GB)", b"comfirm_paket_combos"),
          Button.inline("[PULSA] XCS Tanpa Kuota", b"comfirm_paket_combos_pulsa")],
        [Button.inline("[QRIS] XCS (1-8GB)", b"comfirm_paket_combos_qris")],
        [Button.inline("[DANA] XC 1 + 1GB", b"comfirm_paket_cmbd"),
         Button.inline("[PULSA] XC 1 + 1GB", b"comfirm_paket_cmbp")],
        [Button.inline("[QRIS] XC 1 + 1GB", b"comfirm_paket_cmbq")],
        [Button.inline("🔙 Kembali", b"dor")]]
    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'menu_vix'))
async def menu_vix(event):
    teks = (
        "╔══════════════════════╗\n"
        "       📦 𝗣𝗔𝗞𝗘𝗧 𝗫𝗨𝗧 𝗗𝗜𝗣𝗜𝗟𝗜𝗛       \n"
        "╚══════════════════════╝\n\n"

        "╭── 🟩 𝗫𝗨𝗧 𝗩𝗜𝗗𝗜𝗢 ──────────╮\n"
        "│ 💸 Pembelian via PULSA / QRIS\n"
        "│ 📺 Untuk akses konten Vidio/untuk Injek\n"
        "╰──────────────────────╯\n\n"
        "╭── 🟩 𝗫𝗨𝗧 𝗜𝗙𝗟𝗜𝗫 ──────────╮\n"
        "│ 💸 Pembelian via PULSA / QRIS\n"
        "│ 🎬 Untuk akses konten Iflix/untuk Injek\n"
        "╰──────────────────────╯\n\n"
        "📝 *Pilih paket berdasarkan metode pembayaran yang kamu inginkan.*"
    )
    buttons = [
        [Button.inline("[PULSA] IFLIX", b"comfirm_paket_iflix_pulsa"),
         Button.inline("[PULSA] VIDIO", b"comfirm_paket_vidio_pulsa")],
        [Button.inline("[QRIS] IFLIX", b"comfirm_paket_iflix_qris"),
         Button.inline("[QRIS] VIDIO", b"comfirm_paket_vidio_qris")],
        [Button.inline("🔙 Kembali", b"dor")]]

    await event.edit(teks, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'menu_data'))
async def menu_data(event):
    teks = (
        "╔═════════════════════════╗\n"
        "     📦 𝗣𝗔𝗞𝗘𝗧 𝗗𝗔𝗧𝗔 𝗥𝗘𝗚𝗨𝗟𝗘𝗥 𝗫𝗟      \n"
        "╚═════════════════════════╝\n\n"

        "╭── 🟩 𝗣𝗔𝗞𝗘𝗧 𝟮.𝟴𝗚𝗕 𝟮𝟳 𝗝𝗔𝗠 ─────╮\n"
        "│ 📦 Kuota 2.8 GB • Masa Aktif 27 Jam\n"
        "│ 💸 Metode: Pulsa\n"
        "╰─────────────────────────╯\n\n"
        "╭── 🟩 𝗣𝗔𝗞𝗘𝗧 𝟭𝗚𝗕 𝟮 𝗛𝗔𝗥𝗜 ───────╮\n"
        "│ 📦 Kuota 1 GB • Masa Aktif 2 Hari\n"
        "│ 💸 Metode: Pulsa\n"
        "╰─────────────────────────╯\n\n"
        "📝 *Silakan pilih paket data sesuai kebutuhan Anda.*"
    )
    buttons = [
        [Button.inline("[PULSA] 2.8GB 27 JAM", b"comfirm_paket_2gb"),
         Button.inline("[PULSA] 1GB 2 HARI", b"comfirm_paket_1gb")],
        [Button.inline("🔙 Kembali", b"dor")]]

    await event.edit(teks, buttons=buttons)
     
@bot.on(events.CallbackQuery(data=b'menu_flex'))
async def menu_flex(event):
    teks = (
        "╔════════════════════════╗\n"
        "     📦 𝗣𝗔𝗞𝗘𝗧 𝗫𝗧𝗥𝗔 𝗖𝗢𝗠𝗕𝗢 𝗙𝗟𝗘𝗫      \n"
        "╚════════════════════════╝\n\n"

        "╭── 🟩 𝗣𝗔𝗞𝗘𝗧 𝗨𝗧𝗔𝗠𝗔 ─────────╮\n"
        "│ 📦 Xtra Combo Flex S Promo\n"
        "│ 💸 Metode: DANA\n"
        "╰────────────────────────╯\n\n"
        "╭── 🟩 𝗔𝗗𝗗-𝗢𝗡 𝗙𝗟𝗘𝗫 ─────────╮\n"
        "│ 📌 Tambahan kuota khusus\n"
        "│ ⚙️ Digunakan setelah beli paket utama\n"
        "╰────────────────────────╯\n\n"
        "📝 *Beli paket Xtra Combo Flex S Promo terlebih dahulu,\n"
        "lalu lanjut ke pembelian Add-On Flex.*"
    )

    buttons = [
        [Button.inline("[DANA] Xtra Combo Flex S Promo", b"comfirm_flex")],
        [Button.inline("[ADD-ON] FLEX", b"menu_flexbonus")],
        [Button.inline("🔙 Kembali", b"dor")]]

    await event.edit(teks, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'comfirm_flex'))
async def comfirm_flex(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[DANA] Xtra Combo Flex S Promo", b"confirm_flex_dana")],
        [Button.inline("🔙 Kembali", b"menu_flex")]
    ]
    
    teks = (
        f"**📦 Paket Xtra Combo Flex S Promo**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp6.000.\n"        
        f"➣ Siapkan Saldo E-WALLET DANA Rp16.000 \n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )

    await event.edit(teks, buttons=buttons)
      
@bot.on(events.CallbackQuery(data=b'comfirm_paket_prem'))
async def comfirm_paket_prem(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[STEP 1] ADS PREMIUM DANA", b"confirm_prem_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]
    
    teks = (
        f"**📦 Paket Unlimited Turbo premium**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp500.\n"        
        f"➣ Siapkan Saldo E-WALLET DANA Rp50.000 \n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_super'))
async def comfirm_paket_super(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")
    
    buttons = [
        [Button.inline("[STEP 2] ADS SUPER DANA", b"confirm_sup_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]
    
    teks = (
        f"**📦 Paket Unlimited Turbo Super**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp500\n"        
        f"➣ Siapkan Saldo E-WALLET DANA Rp30.000 \n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_sta'))
async def comfirm_paket_sta(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[STEP 3] ADS STANDART DANA", b"confirm_sta_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]
    
    teks = (
        f"**📦 Paket Unlimited Turbo Standart**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp500\n"        
        f"➣ Siapkan Saldo E-WALLET DANA Rp20.000 \n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_bas'))
async def comfirm_paket_bas(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[STEP 4] ADS BASIC DANA", b"confirm_bas_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]
    
    teks = (
        f"**📦 Paket Unlimited Turbo Basic**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp500\n"        
        f"➣ Siapkan saldo E-WALLET DANA Rp10.000\n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_netflix'))
async def comfirm_paket_netflix(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[OPSIONAL] NETFLIX DANA", b"confirm_net_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]

    teks = (
        f"**🎬 Paket Tambahan NETFLIX**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Hanya opsional, bisa dilewati.\n"
        f"➣ Potong saldo Bot  Rp500\n"        
        f"➣ Siapkan saldo E-WALLET DANA Rp25.000\n"
        f"➣ Tekan tombol di bawah jika ingin mengaktifkan Netflix."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_viu'))
async def comfirm_paket_viu(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[OPSIONAL] VIU DANA", b"confirm_viu_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]

    teks = (
        f"**📺 Paket Tambahan VIU**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Potong saldo Bot  Rp500\n"        
        f"➣ Siapkan saldo DANA Rp25000\n"
        f"➣ Tekan tombol di bawah jika ingin mengaktifkan VIU."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_tiktok'))
async def comfirm_paket_tiktok(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[OPSIONAL] TIKTOK DANA", b"confirm_tik_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]

    teks = (
        f"**📱 Paket Tambahan TIKTOK**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Potong saldo Bot  Rp500\n"        
        f"➣ Siapkan saldo E-WALLET DANA Rp25000\n"
        f"➣ Tekan tombol di bawah jika ingin mengaktifkan TikTok."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_joox'))
async def comfirm_paket_joox(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[OPSIONAL] JOOX DANA", b"confirm_joox_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]

    teks = (
        f"**🎵 Paket Tambahan JOOX**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Potong saldo Bot  Rp500\n"        
        f"➣ Siapkan saldo E-WALLET DANA Rp10.000\n"
        f"➣ Tekan tombol di bawah jika ingin mengaktifkan Joox."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_youtube'))
async def comfirm_paket_youtube(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[OPSIONAL] YOUTUBE DANA", b"confirm_yt_dana")],
        [Button.inline("🔙 Kembali", b"paket_xcs")]
    ]

    teks = (
        f"**▶️ Paket Tambahan YOUTUBE**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Opsional, bisa dilewati.\n"
        f"➣ Potong saldo Bot  Rp500\n"        
        f"➣ Siapkan saldo E-WALLET DANA Rp25000\n"
        f"➣ Tekan tombol di bawah jika ingin mengaktifkan YouTube."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_combos'))
async def comfirm_paket_combo(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[AKHIR] COMBO SPESIAL Dana ", b"confirm_xcs_dana")],
        [Button.inline("🔙 Kembali", b"menu_xcs")]
    ]

    teks = (
        f"**📦 Paket Penutup COMBO SPESIAL **\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp6.000\n"        
        f"➣ Siapkan saldo E-WALLET DANA Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan seluruh paket XCS."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_combos_qris'))
async def comfirm_paket_combo(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[AKHIR] COMBO SPESIAL ", b"confirm_xcs_qris")],
        [Button.inline("🔙 Kembali", b"menu_xcs")]
    ]

    teks = (
        f"**📦 Paket Penutup COMBO SPESIAL Qris**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp6.000\n"        
        f"➣ Siapkan saldo E-WALLET DANA Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan seluruh paket XCS."
    )

    await event.edit(teks, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'comfirm_paket_combos_pulsa'))
async def comfirm_paket_combos_pulsa(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[AKHIR] COMBO SPESIAL ", b"confirm_xcs_pulsa")],
        [Button.inline("🔙 Kembali", b"menu_xcs")]
    ]

    teks = (
        f"**📦 Paket Penutup COMBO SPESIAL Pulsa**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp5.000\n"        
        f"➣ Siapkan PULSA Sebesar Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan seluruh paket XCS."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_xutvidio'))
async def comfirm_paket_xutvidio(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("Paket XUT VIDIO ", b"confirm_vidio_dana")],
        [Button.inline("🔙 Kembali", b"menu_vix")]
    ]

    teks = (
        f"**📦 Paket XUT VIDIO **\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp5.000 Member\n"        
        f"➣ Potong saldo Bot  Rp3.500 Reseller\n"                
        f"➣ Siapkan saldo E-WALLET DANA Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk membeli paket vidio."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_vidio_pulsa'))
async def comfirm_paket_vidio_pulsa(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("Paket XUT VIDIO", b"confirm_vidio_pulsa")],
        [Button.inline("🔙 Kembali", b"menu_vix")]
    ]

    teks = (
        f"**📦 Paket XUT VIDIO**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp5.000 Member\n"        
        f"➣ Potong saldo Bot  Rp3.500 Reseller\n"                
        f"➣ Siapkan PULSA Sebesar Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk membeli paket vidio."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_xutiflix'))
async def comfirm_paket_xutiflix(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("Paket XUT IFLIX ", b"confirm_iflix_dana")],
        [Button.inline("🔙 Kembali", b"menu_vix")]
    ]

    teks = (
        f"**📦 Paket XUT IFLIX **\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp5.000 Member\n"        
        f"➣ Potong saldo Bot  Rp3.500 Reseller\n"                
        f"➣ Siapkan saldo E-WALLET DANA Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk membeli paket iflix."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_iflix_pulsa'))
async def comfirm_paket_iflix_pulsa(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("Paket XUT IFLIX", b"confirm_iflix_pulsa")],
        [Button.inline("🔙 Kembali", b"menu_vix")]
    ]

    teks = (
        f"**📦 Paket XUT IFLIX**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp5.000 Member\n"        
        f"➣ Potong saldo Bot  Rp3.500 Reseller\n"                
        f"➣ Siapkan PULSA Sebesar Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk membeli paket iflix."
    )

    await event.edit(teks, buttons=buttons)    
    
@bot.on(events.CallbackQuery(data=b'comfirm_paket_iflix_qris'))
async def comfirm_paket_iflix_qris(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("Paket XUT IFLIX", b"confirm_iflix_qris")],
        [Button.inline("🔙 Kembali", b"menu_vix")]
    ]

    teks = (
        f"**📦 Paket XUT IFLIX**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp5.000 Member\n"        
        f"➣ Potong saldo Bot  Rp3.500 Reseller\n"                
        f"➣ Siapkan SALDO E-WALEET Sebesar Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk membeli paket iflix."
    )

    await event.edit(teks, buttons=buttons)  

@bot.on(events.CallbackQuery(data=b'comfirm_paket_vidio_qris'))
async def comfirm_paket_vidio_qris(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("Paket XUT VIDIO", b"confirm_vidio_qris")],
        [Button.inline("🔙 Kembali", b"menu_vix")]
    ]

    teks = (
        f"**📦 Paket XUT VIDIO**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Wajib dilakukan di akhir setelah semua aktivasi selesai.\n"
        f"➣ Potong saldo Bot  Rp5.000 Member\n"        
        f"➣ Potong saldo Bot  Rp3.500 Reseller\n"                
        f"➣ Siapkan SALDO E-WALEET Sebesar Rp25.000\n"
        f"➣ Tekan tombol di bawah untuk membeli paket vidio."
    )

    await event.edit(teks, buttons=buttons)      
@bot.on(events.CallbackQuery(data=b'comfirm_paket_2gb'))
async def comfirm_paket_2gb(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("Paket XL DATA REGULER 2.8GB 27 JAM ", b"confirm_data_2gb")],
        [Button.inline("🔙 Kembali", b"menu_data")]
    ]

    teks = (
        f"**📦 Paket XL DATA REGULER 2.8GB 27 JAM **\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp2.500\n"        
        f"➣ Siapkan pulsa Rp500\n"
        f"➣ Tekan tombol di bawah untuk membeli paket."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_1gb'))
async def comfirm_paket_1gb(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("XL DATA REGULER 1GB 2 HAR ", b"confirm_data_1gb")],
        [Button.inline("🔙 Kembali", b"menu_data")]
    ]

    teks = (
        f"**📦 Paket XL DATA REGULER 1GB 2 HARI **\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp2.500\n"        
        f"➣ Siapkan pulsa Rp500\n"
        f"➣ Tekan tombol di bawah untuk membeli paket."
    )

    await event.edit(teks, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'paket_xuts'))
async def aket_xuts(event):
    buttons = [
        [Button.inline("🚀 XUT PREMIUM BYPASS", b"comfirm_paket_xuts")],
        [Button.inline("🚀 XUT SUPER BYPASS", b"comfirm_paket_xuts")],
        [Button.inline("🔥 XTRA COMBO 1 + 1GB DANA", b"comfirm_paket_cmbd")],
        [Button.inline("🔥 XTRA COMBO 1 + 1GB PULSA", b"comfirm_paket_cmbp")],
        [Button.inline("🔙 Kembali", b"dor_xuts")]
    ]
    
    teks = (
        "**📦 Paket XUTS + COMBO 1GB Dipilih**\n\n"
        "**Langkah Pembelian:**\n"
        "1️⃣ Tekan tombol **[STEP 1] ADS-ON XTRA TURBO SUPER DANA** untuk aktivasi awal.\n"
        "2️⃣ Lanjutkan dengan memilih salah satu dari **[STEP 2]**:\n"
        "    ├ 📱 XTRA COMBO 1 + 1GB DANA\n"
        "    └ 📞 XTRA COMBO 1 + 1GB PULSA\n"
        "3️⃣ Selesai ✅ \n\n"
        "Silakan pilih paket yang tersedia di bawah ini:"
    )

    await event.edit(teks, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'comfirm_paket_xuts'))
async def comfirm_paket_xuts(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[STEP 1] ADS SUPER BYPASS", b"confirm_sup_dana")],
        [Button.inline("🔙 Kembali", b"paket_xuts")]
    ]
    
    teks = (
        f"**📦 Paket Unlimited Turbo Super**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp1.000\n"        
        f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_xuts'))
async def comfirm_paket_xuts(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[STEP 1] ADS  BYPASS", b"confirm_sup_dana")],
        [Button.inline("🔙 Kembali", b"paket_xuts")]
    ]
    
    teks = (
        f"**📦 Paket Unlimited Turbo Premium**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp1.000\n"        
        f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )

    await event.edit(teks, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'comfirm_paket_cmbd'))
async def comfirm_paket_cmbd(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[STEP 2] COMBO 1 + 1GB DANA", b"confirm_cmb_dana")],
        [Button.inline("🔙 Kembali", b"menu_xcs")]
    ]
    
    teks = (
        f"**📦 Paket Xtra Combo 1 + 1 GB Dana**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp5.000\n"        
        f"➣ Siapkan Saldo E-WALLET DANA Rp12.500 \n"
       f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )
    await event.edit(teks, buttons=buttons)
    
@bot.on(events.CallbackQuery(data=b'comfirm_paket_cmbp'))
async def comfirm_paket_cmbp(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[STEP 2] COMBO 1 + 1GB PULSA", b"confirm_cmb_pulsa")],
        [Button.inline("🔙 Kembali", b"menu_xcs")]
    ]
    
    teks = (
        f"**📦 Paket Xtra Combo 1 + 1 GB Pulsa**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp5.000\n"        
        f"➣ Siapkan Pulsa Rp12.500 \n"
        f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )

    await event.edit(teks, buttons=buttons)

@bot.on(events.CallbackQuery(data=b'comfirm_paket_cmbq'))
async def comfirm_paket_cmbd(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp", "❌ Tidak ditemukan")

    buttons = [
        [Button.inline("[STEP 2] COMBO 1 + 1GB QRIS", b"confirm_cmb_qris")],
        [Button.inline("🔙 Kembali", b"menu_xcs")]
    ]
    
    teks = (
        f"**📦 Paket Xtra Combo 1 + 1 GB Qris**\n\n"
        f"📱 Nomor: {nomor}\n"
        f"➣ Potong saldo Bot  Rp5.000\n"        
        f"➣ Siapkan Saldo E-WALLET DANA Rp12.500 \n"
       f"➣ Tekan tombol di bawah untuk menyelesaikan pembelian."
    )
    await event.edit(teks, buttons=buttons)
        
@bot.on(events.CallbackQuery(data=b'paket_xut'))
async def paket_xut(event):
    buttons = [
        [Button.inline("💰 Bayar via Saldo", b"confirm_xut_saldo")],
        [Button.inline("✅ Bayar via QRIS", b"confirm_xut_qris")],
        [Button.inline("🔙 Kembali", b"dor")]
    ]
    await event.edit("**Paket Bundle XUT dipilih**. Pilih metode pembayaran:", buttons=buttons)
     
def get_user_role(user_id):
    # Contoh fungsi cek role user
    if user_id in admin_ids:
        return "admin"
    elif is_reseller(user_id):
        return "reseller"
    else:
        return "user"

        
@bot.on(events.CallbackQuery(data=b'confirm_xcp_saldo'))
async def confirm_xcp_saldo(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 8000

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "97520d9ebea7d72cec0ae29e7b65e1fc",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
╔═════════════════════╗
║ ⚠️  SELESAIKAN PEMBAYARAN DANA              
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor     : {sensor_hp(nomor)}
║  Paket     : XCP 10GB
║  Metode    : DANA Rp64.000
║  Terpotong : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
{trx_id}
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Simpan ke riwayat DOR
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket=code,
                        harga=harga_per_paket,
                        ref=ref,
                        trx_id=hasil.get("trx_id", "-"),
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )                    
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XCP 10GB
║  Harga Dor  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi()) 

@bot.on(events.CallbackQuery(data=b'confirm_flex_dana'))
async def confirm_flex_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 6000

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "6b699877e423e526d8c2502f48ba0a1d",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
╔═════════════════════╗
║ ⚠️  SELESAIKAN PEMBAYARAN DANA              
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor     : {sensor_hp(nomor)}
║  Paket     : XC Flex S Promo
║  Metode    : DANA Rp16.000
║  Terpotong : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
{trx_id}
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Simpan ke riwayat DOR
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket=code,
                        harga=harga_per_paket,
                        ref=ref,
                        trx_id=hasil.get("trx_id", "-"),
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )                   
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XC Flex S Promo
║  Harga Dor  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi())        

        
@bot.on(events.CallbackQuery(data=b'confirm_xcs_dana'))
async def confirm_xcs_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 6000
    
    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "c03be70fb3523ac2ac440966d3a5920e",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
╔═════════════════════╗
║ ⚠️  SELESAIKAN PEMBAYARAN DANA              
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor     : {sensor_hp(nomor)}
║  Paket     : XCS 1-8 GB DANA
║  Metode    : DANA Rp25.000
║  Terpotong : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
{trx_id}
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Simpan ke riwayat DOR
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket=code,
                        harga=harga_per_paket,
                        ref=ref,
                        trx_id=hasil.get("trx_id", "-"),
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )   
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XCS 1-8GB DANA
║  Harga Dor  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi()) 
    
@bot.on(events.CallbackQuery(data=b'confirm_xcs_qris'))
async def confirm_vidio_qris(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 6000
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket via QRIS, mohon tunggu...")

    # Panggil API pembelian QRIS
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "c03be70fb3523ac2ac440966d3a5920e",  # ganti sesuai paket
            "phone": nomor,
            "access_token": token,
            "payment_method": "QRIS"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    qris_info = data.get("qris_data", {})
    qr_code_string = qris_info.get("qr_code", "")
    expired_unix = qris_info.get("payment_expired_at", 0)

    if not trx_id or not qr_code_string:
        tambah_saldo(user_id, harga_jasa)
        await event.respond("❌ Gagal mendapatkan data QRIS.")
        return

    # Data pendukung lainnya
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)
    expired_time = datetime.fromtimestamp(expired_unix).strftime("%H:%M:%S")

    # 🔁 Generate gambar QR
    qr_img = qrcode.make(qr_code_string)
    img_buf = BytesIO()
    qr_img.save(img_buf, format='PNG')
    img_buf.seek(0)

    # ✅ Upload file dengan nama agar tidak "unnamed"
    qr_file = await bot.upload_file(img_buf, file_name="qris_xut_iflix.png")

    # Kirim QR ke pengguna
    await bot.send_file(
        user_id,
        file=qr_file,
        caption=f"""
╔═════════════════════╗
║ ✅ SCAN QRIS UNTUK BAYAR KE XL
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XCS 1-8 GB QRIS
║  Harga      : Rp 25.000
║  Kadaluarsa : {expired_time} WIB
╟═════════════════════╝
║📎 PETUNJUK:
║  Scan QR menggunakan DANA, OVO,
║  Gopay, LinkAja, BCA Mobile, dll.
╚═════════════════════╝
{trx_id}
"""
    )

    # 🔁 Cek status pembayaran berkala
    async def cek_status_transaksi():
        for _ in range(20):  # 10 menit (20 x 30 detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket="XCS 1-8 GB",
                        harga=harga_jasa,
                        ref=ref,
                        trx_id=trx_id,
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)

                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XCS 1–8 GB QRIS
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
""")
                    user_sessions.pop(user_id, None)
                    return

                elif status == 0 or is_refunded == 1:
                    tambah_saldo(user_id, harga_jasa)
                    await bot.send_message(user_id, "❌ Pembayaran QRIS gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan ulangi pembelian.")
        user_sessions.pop(user_id, None)

    asyncio.create_task(cek_status_transaksi())

@bot.on(events.CallbackQuery(data=b'confirm_vidio_dana'))
async def confirm_vidio_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 3500 if role == "reseller" else 5000 
    
    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XLUNLITURBOVIDIO_DANA",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
╔═════════════════════╗
║ ⚠️  SELESAIKAN PEMBAYARAN DANA              
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor     : {sensor_hp(nomor)}
║  Paket     : XUT VIDIO
║  Metode    : DANA Rp25.000
║  Terpotong : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
{trx_id}
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Simpan ke riwayat DOR
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket=code,
                        harga=harga_per_paket,
                        ref=ref,
                        trx_id=hasil.get("trx_id", "-"),
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )   
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XUT VIDIO
║  Harga Dor  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi()) 

@bot.on(events.CallbackQuery(data=b'confirm_iflix_dana'))
async def confirm_iflix_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 3500 if role == "reseller" else 5000 
    
    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XLUNLITURBOIFLIXXC_EWALLET",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
╔═════════════════════╗
║ ⚠️  SELESAIKAN PEMBAYARAN DANA              
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor     : {sensor_hp(nomor)}
║  Paket     : XUT IFLIX
║  Metode    : DANA Rp25.000
║  Terpotong : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
{trx_id}
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Simpan ke riwayat DOR
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket=code,
                        harga=harga_per_paket,
                        ref=ref,
                        trx_id=hasil.get("trx_id", "-"),
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )   
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XUT IFLIX
║  Harga Dor  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi()) 

@bot.on(events.CallbackQuery(data=b'confirm_vidio_qris'))
async def confirm_vidio_qris(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 3500 if role == "reseller" else 5000
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket via QRIS, mohon tunggu...")

    # Panggil API pembelian QRIS
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XLUNLITURBOVIDIO_DANA",  # ganti sesuai paket
            "phone": nomor,
            "access_token": token,
            "payment_method": "QRIS"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    qris_info = data.get("qris_data", {})
    qr_code_string = qris_info.get("qr_code", "")
    expired_unix = qris_info.get("payment_expired_at", 0)

    if not trx_id or not qr_code_string:
        tambah_saldo(user_id, harga_jasa)
        await event.respond("❌ Gagal mendapatkan data QRIS.")
        return

    # Data pendukung lainnya
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)
    expired_time = datetime.fromtimestamp(expired_unix).strftime("%H:%M:%S")

    # 🔁 Generate gambar QR
    qr_img = qrcode.make(qr_code_string)
    img_buf = BytesIO()
    qr_img.save(img_buf, format='PNG')
    img_buf.seek(0)

    # ✅ Upload file dengan nama agar tidak "unnamed"
    qr_file = await bot.upload_file(img_buf, file_name="qris_xut_iflix.png")

    # Kirim QR ke pengguna
    await bot.send_file(
        user_id,
        file=qr_file,
        caption=f"""
╔═════════════════════╗
║ ✅ SCAN QRIS UNTUK BAYAR KE XL
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XUT VIDIO 
║  Harga      : Rp 25.000
║  Kadaluarsa : {expired_time} WIB
╟═════════════════════╝
║📎 PETUNJUK:
║  Scan QR menggunakan DANA, OVO,
║  Gopay, LinkAja, BCA Mobile, dll.
╚═════════════════════╝
{trx_id}
"""
    )

    # 🔁 Cek status pembayaran berkala
    async def cek_status_transaksi():
        for _ in range(20):  # 10 menit (20 x 30 detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket="XUT VIDIO QRIS",
                        harga=harga_jasa,
                        ref=ref,
                        trx_id=trx_id,
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)

                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XUT VIDIO QRIS
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
""")
                    user_sessions.pop(user_id, None)
                    return

                elif status == 0 or is_refunded == 1:
                    tambah_saldo(user_id, harga_jasa)
                    await bot.send_message(user_id, "❌ Pembayaran QRIS gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan ulangi pembelian.")
        user_sessions.pop(user_id, None)

    asyncio.create_task(cek_status_transaksi())

@bot.on(events.CallbackQuery(data=b'confirm_iflix_qris'))
async def confirm_iflix_qris(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 3500 if role == "reseller" else 5000
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket via QRIS, mohon tunggu...")

    # Panggil API pembelian QRIS
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XLUNLITURBOIFLIXXC_EWALLET",  # ganti sesuai paket
            "phone": nomor,
            "access_token": token,
            "payment_method": "QRIS"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    qris_info = data.get("qris_data", {})
    qr_code_string = qris_info.get("qr_code", "")
    expired_unix = qris_info.get("payment_expired_at", 0)

    if not trx_id or not qr_code_string:
        tambah_saldo(user_id, harga_jasa)
        await event.respond("❌ Gagal mendapatkan data QRIS.")
        return

    # Data pendukung lainnya
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)
    expired_time = datetime.fromtimestamp(expired_unix).strftime("%H:%M:%S")

    # 🔁 Generate gambar QR
    qr_img = qrcode.make(qr_code_string)
    img_buf = BytesIO()
    qr_img.save(img_buf, format='PNG')
    img_buf.seek(0)

    # ✅ Upload file dengan nama agar tidak "unnamed"
    qr_file = await bot.upload_file(img_buf, file_name="qris_xut_iflix.png")

    # Kirim QR ke pengguna
    await bot.send_file(
        user_id,
        file=qr_file,
        caption=f"""
╔═════════════════════╗
║ ⚠️ SCAN QRIS UNTUK BAYAR KE XL
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XUT IFLIX 
║  Harga      : Rp 25.000
║  Kadaluarsa : {expired_time} WIB
╟═════════════════════╝
║📎 PETUNJUK:
║  Scan QR menggunakan DANA, OVO,
║  Gopay, LinkAja, BCA Mobile, dll.
╚═════════════════════╝
{trx_id}
"""
    )

    # 🔁 Cek status pembayaran berkala
    async def cek_status_transaksi():
        for _ in range(20):  # 10 menit (20 x 30 detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket="XUT IFLIX QRIS",
                        harga=harga_jasa,
                        ref=ref,
                        trx_id=trx_id,
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)

                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XUT IFLIX QRIS
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")
                    user_sessions.pop(user_id, None)
                    return

                elif status == 0 or is_refunded == 1:
                    tambah_saldo(user_id, harga_jasa)
                    await bot.send_message(user_id, "❌ Pembayaran QRIS gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan ulangi pembelian.")
        user_sessions.pop(user_id, None)

    asyncio.create_task(cek_status_transaksi())


@bot.on(events.CallbackQuery(data=b'confirm_xcs_pulsa'))
async def confirm_xcs_pulsa(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 5000
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    # Potong saldo
    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Panggil API pulsa
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "bdb392a7aa12b21851960b7e7d54af2c",  # kode paket XCS 
            "phone": nomor,
            "access_token": token,
            "payment_method": "PULSA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    # Jika gagal
    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    # Jika berhasil
    hasil = result
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    increment_all_user_counted_dor()
    increment_all_user_counts()
    count_dor = get_user_counted_dor(user_id)

    # Simpan ke riwayat DOR
    try:
        simpan_riwayat_dor(
            user_id=user_id,
            nomor=nomor,
            paket="XUT VIDIO",
            harga=harga_jasa,
            ref=ref,
            trx_id=hasil.get("trx_id", "-"),
            tanggal=tanggalsekarang,
            waktu=jam_wib
        )
    except Exception as e:
        print(f"[ERROR] Gagal simpan riwayat DOR: {e}")

    teks_konfirmasi = f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XCS PULSA
║  Harga Dor  : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
"""

    await event.respond(teks_konfirmasi)
    await bot.send_message(group_id, teks_konfirmasi)

    # Hapus sesi user
    user_sessions.pop(user_id, None)
    
@bot.on(events.CallbackQuery(data=b'confirm_vidio_pulsa'))
async def confirm_vido_pulsa(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 3500 if role == "reseller" else 5000 
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    # Potong saldo
    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Panggil API pulsa
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XLUNLITURBOVIDIO_PULSA",  # kode paket XCS 
            "phone": nomor,
            "access_token": token,
            "payment_method": "PULSA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    # Jika gagal
    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    # Jika berhasil
    hasil = result
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    increment_all_user_counted_dor()
    increment_all_user_counts()
    count_dor = get_user_counted_dor(user_id)

    # Simpan ke riwayat DOR
    try:
        simpan_riwayat_dor(
            user_id=user_id,
            nomor=nomor,
            paket="XUT VIDIO",
            harga=harga_jasa,
            ref=ref,
            trx_id=hasil.get("trx_id", "-"),
            tanggal=tanggalsekarang,
            waktu=jam_wib
        )
    except Exception as e:
        print(f"[ERROR] Gagal simpan riwayat DOR: {e}")

    teks_konfirmasi = f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XUT VIDIO 
║  Harga Dor  : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
"""

    await event.respond(teks_konfirmasi)
    await bot.send_message(group_id, teks_konfirmasi)

    # Hapus sesi user
    user_sessions.pop(user_id, None)

@bot.on(events.CallbackQuery(data=b'confirm_iflix_pulsa'))
async def confirm_iflix_pulsa(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 3500 if role == "reseller" else 5000 
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    # Potong saldo
    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Panggil API pulsa
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XLUNLITURBOIFLIXXC_PULSA",  # kode paket XCS 
            "phone": nomor,
            "access_token": token,
            "payment_method": "PULSA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    # Jika gagal
    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    # Jika berhasil
    hasil = result
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    increment_all_user_counted_dor()
    increment_all_user_counts()
    count_dor = get_user_counted_dor(user_id)

    # Simpan ke riwayat DOR
    try:
        simpan_riwayat_dor(
            user_id=user_id,
            nomor=nomor,
            paket="XUT IFLIX",
            harga=harga_jasa,
            ref=ref,
            trx_id=hasil.get("trx_id", "-"),
            tanggal=tanggalsekarang,
            waktu=jam_wib
        )
    except Exception as e:
        print(f"[ERROR] Gagal simpan riwayat DOR: {e}")

    teks_konfirmasi = f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XUT IFLIX 
║  Harga Dor  : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
"""

    await event.respond(teks_konfirmasi)
    await bot.send_message(group_id, teks_konfirmasi)

    # Hapus sesi user
    user_sessions.pop(user_id, None)

@bot.on(events.CallbackQuery(data=b'confirm_data_2gb'))
async def confirm_data_2gb(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 2500
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    # Potong saldo
    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Panggil API pulsa
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "f2fa05f28c146fdb67488ec53ce5c2cc",  # kode paket XCS 
            "phone": nomor,
            "access_token": token,
            "payment_method": "PULSA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    # Jika gagal
    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    # Jika berhasil
    hasil = result
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    increment_all_user_counted_dor()
    increment_all_user_counts()
    count_dor = get_user_counted_dor(user_id)

    # Simpan ke riwayat DOR
    try:
        simpan_riwayat_dor(
            user_id=user_id,
            nomor=nomor,
            paket="XL DATA REGULER",
            harga=harga_jasa,
            ref=ref,
            trx_id=hasil.get("trx_id", "-"),
            tanggal=tanggalsekarang,
            waktu=jam_wib
        )
    except Exception as e:
        print(f"[ERROR] Gagal simpan riwayat DOR: {e}")

    teks_konfirmasi = f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XL DATA REGULER 2.8GB 27 JAM
║  Harga Dor  : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
"""

    await event.respond(teks_konfirmasi)
    await bot.send_message(group_id, teks_konfirmasi)

    # Hapus sesi user
    user_sessions.pop(user_id, None)

@bot.on(events.CallbackQuery(data=b'confirm_data_1gb'))
async def confirm_data_2gb(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 2500
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    # Potong saldo
    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Panggil API pulsa
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "3bb29c47f33d1f2e7df95a2aaafe55bc",  # kode paket XCS 
            "phone": nomor,
            "access_token": token,
            "payment_method": "PULSA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    # Jika gagal
    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    # Jika berhasil
    hasil = result
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    increment_all_user_counted_dor()
    increment_all_user_counts()
    count_dor = get_user_counted_dor(user_id)

    # Simpan ke riwayat DOR
    try:
        simpan_riwayat_dor(
            user_id=user_id,
            nomor=nomor,
            paket="XL DATA REGULER",
            harga=harga_jasa,
            ref=ref,
            trx_id=hasil.get("trx_id", "-"),
            tanggal=tanggalsekarang,
            waktu=jam_wib
        )
    except Exception as e:
        print(f"[ERROR] Gagal simpan riwayat DOR: {e}")

    teks_konfirmasi = f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XL DATA REGULER 1GB 2 HARI
║  Harga Dor  : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
"""

    await event.respond(teks_konfirmasi)
    await bot.send_message(group_id, teks_konfirmasi)

    # Hapus sesi user
    user_sessions.pop(user_id, None)
  
    
@bot.on(events.CallbackQuery(data=b'confirm_xut_saldo'))
async def confirm_xut_saldo(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")

    if not nomor:
        await event.respond("❌ Nomor tidak ditemukan. Silakan ulangi proses.")
        return

    # Harga per role
    harga_admin = 500
    harga_reseller = 35000
    harga_member = 40000

    role = get_user_role(user_id)

    if role == "admin":
        harga_saldo = harga_admin
    elif role == "reseller":
        harga_saldo = harga_reseller
    else:
        harga_saldo = harga_member

    saldo = get_user_balance(user_id)
    if saldo < harga_saldo:
        await event.edit(
            f"""**❌ SALDO TIDAK CUKUP**
```➣ Harga : Rp {harga_saldo:,}
➣ Saldo : Rp {saldo:,}```

Silakan topup saldo terlebih dahulu.""",
            buttons=[[Button.inline("➕ Topup Saldo Dor", b"topup_saldo")]]
        )
        return

    try:
        # Cek token aktif
        async with aiohttp.ClientSession() as session:
            cek_token_url = "https://golang-openapi-accesstokenlist-xltembakservice.kmsp-store.com/v1"
            async with session.get(cek_token_url, params={"api_key": API_KEY}) as resp:
                res = await resp.json()
                if not res.get("status") or not res.get("data"):
                    raise Exception("Tidak ditemukan token aktif. Silakan login OTP terlebih dahulu.")

                token = None
                for d in res["data"]:
                    if d.get("msisdn") == nomor:
                        token = d.get("token")
                        break

                if not token:
                    raise Exception("Token untuk nomor ini tidak ditemukan. Silakan login OTP terlebih dahulu.")

        # Simpan ke riwayat DOR
        simpan_riwayat_dor(
            user_id=user_id,
            nomor=nomor,
            paket=code,
            harga=harga_per_paket,
            ref=ref,
            trx_id=hasil.get("trx_id", "-"),
            tanggal=tanggalsekarang,
            waktu=jam_wib
        )   
    
        # Kurangi saldo
        kurangi_saldo(user_id, harga_saldo)

        tanggalsekarang = tanggal_pembayaran()
        jam_wib, jam_wita, jam_wit = waktu_sekarang()
        ref = f"DOR{int(datetime.now().timestamp())}"
        trx_id = ref  # trx_id disamakan dengan ref
        user_line = f"[{user_id}](tg://user?id={user_id})"

        await event.respond(f"""
**━━━━━━━━━━━━━━━━━━━━━━**        
**✅ PEMBAYARAN DITERIMA**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Harga  : Rp {harga_saldo:,}
➣ Ref    : {ref}
➣ Trx ID : {trx_id}
➣ Tanggal: {tanggalsekarang}
➣ Waktu  : {jam_wib}`
**━━━━━━━━━━━━━━━━━━━━━━**
`⏳ Proses pembelian paket...`
""")

        # Proses pembelian paket
        async with aiohttp.ClientSession() as session:
            url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
            params = {
                "api_key": API_KEY,
                "package_code": "XLUNLITURBOBUNDLEPROMO25K",
                "phone": nomor,
                "access_token": token,
                "payment_method": "BALANCE"
            }
            async with session.get(url, params=params) as resp:
                result = await resp.json()

                if result.get("status") is True:
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_plus_1jam()
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
**━━━━━━━━━━━━━━━━━━━━━━**
**✅ TRANSAKSI DOR SUKSES #{count_dor}**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Pengguna : {user_line}
➣ Nomor    : {sensor_hp(nomor)}
➣ Paket    : BUNDLE XUT
➣ Harga    : Rp {harga_saldo:,}
➣ Waktu    : {jam_wib}
➣ Tanggal  : {tanggalsekarang}
➣ Trx ID   : {trx_id}`
**━━━━━━━━━━━━━━━━━━━━━━**
""")

                    await event.respond(f"""
**━━━━━━━━━━━━━━━━━━━━━━**                    
**✅ DOR BERHASIL**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Nomor     : {nomor}
➣ Paket     : BUNDLE XUT
➣ Estimasi  : ± 120 menit
➣ Tunggu    : {tunggu_wib}
➣ Tanggal   : {tanggalsekarang}
➣ Trx ID    : {trx_id}`
**━━━━━━━━━━━━━━━━━━━━━━**
""")
                    user_sessions.pop(user_id, None)
                else:
                    tambah_saldo(user_id, harga_saldo)
                    raise Exception(result.get("message", "Transaksi gagal diproses."))

    except Exception as e:
        print(f"[ERROR] confirm_xut_saldo: {e}")
        await event.respond(f"❌ Gagal memproses BUNLDE XUT:\n`{e}`\n\nSaldo telah dikembalikan.")
        user_sessions.pop(user_id, None)
        

@bot.on(events.CallbackQuery(data=b'confirm_mastif1thn_saldo'))
async def confirm_mastif1thn_saldo(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor:
        await event.respond("❌ Nomor tidak ditemukan. Silakan ulangi proses.")
        return

    if not token:
        await event.respond("❌ Token tidak ditemukan. Silakan login ulang terlebih dahulu.")
        return

    # Harga hanya untuk admin, lainnya flat
    role = get_user_role(user_id)
    harga_saldo = 100 if role == "admin" else 8000

    saldo = get_user_balance(user_id)
    if saldo < harga_saldo:
        await event.edit(
            f"""**❌ SALDO TIDAK CUKUP**
```➣ Harga : Rp {harga_saldo:,}
➣ Saldo : Rp {saldo:,}```

Silakan topup saldo terlebih dahulu.""",
            buttons=[[Button.inline("➕ Topup Saldo Dor", b"topup_saldo")]]
        )
        return

    try:
        kurangi_saldo(user_id, harga_saldo)

        tanggalsekarang = tanggal_pembayaran()
        jam_wib, jam_wita, jam_wit = waktu_sekarang()
        user_line = get_user_line(user_id)

        await event.respond(f"""
**━━━━━━━━━━━━━━━━━━━━━━**        
**✅ PEMBAYARAN DITERIMA**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Harga  : Rp {harga_saldo:,}
➣ Tanggal: {tanggalsekarang}
➣ Waktu  : {jam_wib}`
**━━━━━━━━━━━━━━━━━━━━━━**
`⏳ Proses pembelian paket...`
""")

        # Request API pembelian paket
        async with aiohttp.ClientSession() as session:
            url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
            params = {
                "api_key": API_KEY,
                "package_code": "b0012edd21983678eb7ebc08d8f04ecd",
                "phone": nomor,
                "access_token": token,
                "payment_method": "BALANCE"
            }

            async with session.get(url, params=params) as resp:
                result = await resp.json()

                if result.get("status") is True:
                    trx_id = result.get("data", {}).get("trx_id", f"DOR{int(datetime.now().timestamp())}")
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_plus_1jam()
                    increment_all_user_counts()
                    increment_all_user_counted_dor()
                    # Simpan ke riwayat DOR
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket=code,
                        harga=harga_per_paket,
                        ref=ref,
                        trx_id=hasil.get("trx_id", "-"),
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )   
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : MASTIF 1 TAHUN
║  Harga      : Rp {harga_saldo:,}
║  Trx ID     : {trx_id}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
""")

                    await event.respond(f"""

╔═════════════════════╗
║ ✅  DOR BERHASIL                          
╟═════════════════════╝
║📦 DETAIL PAKET:
║  Nomor     : {nomor}
║  Paket     : MASTIF 1 TAHUN
║  Estimasi  : ± Setelah mastif habis
║  Trx ID    : {trx_id}
╟═════════════════════╣
║📅 TANGGAL:
║  {tanggalsekarang}
╚═════════════════════╝
""")
                    user_sessions.pop(user_id, None)
                else:
                    # Gagal → saldo dikembalikan
                    tambah_saldo(user_id, harga_saldo)
                    raise Exception(result.get("message", "Transaksi gagal diproses."))

    except Exception as e:
        print(f"[ERROR] confirm_mastif1thn_saldo: {e}")
        await event.respond(f"❌ Gagal memproses MASTIF:\n`{e}`\n\nSaldo telah dikembalikan.")
        user_sessions.pop(user_id, None)

@bot.on(events.CallbackQuery(data=b'confirm_if_dana'))
async def confirm_if_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 500

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "49d1e047f7fc09be77dcb1bb2d4393cd",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
**━━━━━━━━━━━━━━━━━━━━━━**    
**✅ Silahkan Selesaikan pembayaran DANA.**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Nomor            : {sensor_hp(nomor)}
➣ Paket            : Add-on XCL Iflix
➣ Method           : DANA Rp6.000
➣ Refund Dana      : Ya
➣ Saldo Terpotong  : Rp {harga_jasa:,}
➣ Ref              : {ref}
➣ Tanggal          : {tanggalsekarang}
➣ Waktu            : {jam_wib}
➣ trx_id           : {trx_id}`
**━━━━━━━━━━━━━━━━━━━━━━**
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
**━━━━━━━━━━━━━━━━━━━━━━**
**✅ TRANSAKSI DOR SUKSES #{count_dor}**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Pengguna : {user_line}
➣ Nomor    : {sensor_hp(nomor)}
➣ Paket    : Add-on XCL Iflix
➣ Harga Dor: Rp {harga_jasa:,}
➣ Waktu    : {jam_wib}
➣ Tanggal  : {tanggalsekarang}
➣ Status   : Menunggu pembayaran E-Wallet DANA`
**━━━━━━━━━━━━━━━━━━━━━━**
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi())

@bot.on(events.CallbackQuery(data=b'confirm_vid_dana'))
async def confirm_vid_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 500

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "7edb228a26f1cdb8691d2fc23d75766e",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
**━━━━━━━━━━━━━━━━━━━━━━**    
**✅ Silahkan Selesaikan pembayaran DANA.**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Nomor            : {sensor_hp(nomor)}
➣ Paket            : Add-on XCL Vidio
➣ Method           : DANA Rp6.000
➣ Refund Dana      : Ya
➣ Saldo Terpotong  : Rp {harga_jasa:,}
➣ Ref              : {ref}
➣ Tanggal          : {tanggalsekarang}
➣ Waktu            : {jam_wib}
➣ trx_id           : {trx_id}`
**━━━━━━━━━━━━━━━━━━━━━━**
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
**━━━━━━━━━━━━━━━━━━━━━━**
**✅ TRANSAKSI DOR SUKSES #{count_dor}**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Pengguna : {user_line}
➣ Nomor    : {sensor_hp(nomor)}
➣ Paket    : Add-on XCL Vidio
➣ Harga Dor: Rp {harga_jasa:,}
➣ Waktu    : {jam_wib}
➣ Tanggal  : {tanggalsekarang}
➣ Status   : Menunggu pembayaran E-Wallet DANA`
**━━━━━━━━━━━━━━━━━━━━━━**
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi())

@bot.on(events.CallbackQuery(data=b'confirm_net_dana'))
async def confirm_net_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 500

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "e4b9610293057bf3bc0bc35288e22faa",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
**━━━━━━━━━━━━━━━━━━━━━━**    
**✅ Silahkan Selesaikan pembayaran DANA.**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Nomor            : {sensor_hp(nomor)}
➣ Paket            : Add-on XCL Netflix
➣ Method           : DANA Rp6.000
➣ Refund Dana      : Ya
➣ Saldo Terpotong  : Rp {harga_jasa:,}
➣ Ref              : {ref}
➣ Tanggal          : {tanggalsekarang}
➣ Waktu            : {jam_wib}
➣ trx_id           : {trx_id}`
**━━━━━━━━━━━━━━━━━━━━━━**
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
**━━━━━━━━━━━━━━━━━━━━━━**
**✅ TRANSAKSI DOR SUKSES #{count_dor}**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Pengguna : {user_line}
➣ Nomor    : {sensor_hp(nomor)}
➣ Paket    : Add-on XCL Netflix
➣ Harga Dor: Rp {harga_jasa:,}
➣ Waktu    : {jam_wib}
➣ Tanggal  : {tanggalsekarang}
➣ Status   : Menunggu pembayaran E-Wallet DANA`
**━━━━━━━━━━━━━━━━━━━━━━**
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi())
 
@bot.on(events.CallbackQuery(data=b'confirm_net_dana'))
async def confirm_net_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 500

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "dac06dd11e66ae88c09d43f8866ddd5e",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
**━━━━━━━━━━━━━━━━━━━━━━**    
**✅ Silahkan Selesaikan pembayaran DANA.**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Nomor            : {sensor_hp(nomor)}
➣ Paket            : Add-on XCL Viu
➣ Method           : DANA Rp6.000
➣ Refund Dana      : Ya
➣ Saldo Terpotong  : Rp {harga_jasa:,}
➣ Ref              : {ref}
➣ Tanggal          : {tanggalsekarang}
➣ Waktu            : {jam_wib}
➣ trx_id           : {trx_id}`
**━━━━━━━━━━━━━━━━━━━━━━**
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
**━━━━━━━━━━━━━━━━━━━━━━**
**✅ TRANSAKSI DOR SUKSES #{count_dor}**
**━━━━━━━━━━━━━━━━━━━━━━**
`➣ Pengguna : {user_line}
➣ Nomor    : {sensor_hp(nomor)}
➣ Paket    : Add-on XCL Viu
➣ Harga Dor: Rp {harga_jasa:,}
➣ Waktu    : {jam_wib}
➣ Tanggal  : {tanggalsekarang}
➣ Status   : Menunggu pembayaran E-Wallet DANA`
**━━━━━━━━━━━━━━━━━━━━━━**
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi())
 
@bot.on(events.CallbackQuery(data=b'confirm_ytb_dana'))
async def confirm_ytb_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 500

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "ce6a05ce7c0b47b7cfb5412e58b6222f",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
╔═════════════════════╗
║ ⚠️  SELESAIKAN PEMBAYARAN DANA              
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : Add-on XCL Youtube
║  Metode     : DANA Rp6.000
║  Refund     : Ya
║  Terpotong  : Rp {harga_jasa:,}
║  Ref        : {ref}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
{trx_id}
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : Add-on XCL Youtube
║  Harga Dor  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi())

@bot.on(events.CallbackQuery(data=b'confirm_cmb_dana'))
async def confirm_cmb_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 5000

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XL_XC1PLUS1DISC_EWALLET",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
╔═════════════════════╗
║ ⚠️  SELESAIKAN PEMBAYARAN DANA              
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor     : {sensor_hp(nomor)}
║  Paket     : XC 1+1GB DANA
║  Metode    : DANA Rp12.500
║  Terpotong : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
 {trx_id}
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}         
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XC 1+1GB 
║  Harga Dor  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")


                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi())    

@bot.on(events.CallbackQuery(data=b'confirm_cmb_qris'))
async def confirm_vidio_qris(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 5000
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket via QRIS, mohon tunggu...")

    # Panggil API pembelian QRIS
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XL_XC1PLUS1DISC_EWALLET",  # ganti sesuai paket
            "phone": nomor,
            "access_token": token,
            "payment_method": "QRIS"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    qris_info = data.get("qris_data", {})
    qr_code_string = qris_info.get("qr_code", "")
    expired_unix = qris_info.get("payment_expired_at", 0)

    if not trx_id or not qr_code_string:
        tambah_saldo(user_id, harga_jasa)
        await event.respond("❌ Gagal mendapatkan data QRIS.")
        return

    # Data pendukung lainnya
    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)
    expired_time = datetime.fromtimestamp(expired_unix).strftime("%H:%M:%S")

    # 🔁 Generate gambar QR
    qr_img = qrcode.make(qr_code_string)
    img_buf = BytesIO()
    qr_img.save(img_buf, format='PNG')
    img_buf.seek(0)

    # ✅ Upload file dengan nama agar tidak "unnamed"
    qr_file = await bot.upload_file(img_buf, file_name="qris_xut_iflix.png")

    # Kirim QR ke pengguna
    await bot.send_file(
        user_id,
        file=qr_file,
        caption=f"""
╔═════════════════════╗
║ ⚠️ SCAN QRIS UNTUK BAYAR KE XL
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XC 1+1GB QRIS
║  Harga      : Rp 12.500
║  Kadaluarsa : {expired_time} WIB
╟═════════════════════╝
║📎 PETUNJUK:
║  Scan QR menggunakan DANA, OVO,
║  Gopay, LinkAja, BCA Mobile, dll.
╚═════════════════════╝
{trx_id}
""")

    # 🔁 Cek status pembayaran berkala
    async def cek_status_transaksi():
        for _ in range(20):  # 10 menit (20 x 30 detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    simpan_riwayat_dor(
                        user_id=user_id,
                        nomor=nomor,
                        paket="XC 1 + 1GB QRIS",
                        harga=harga_jasa,
                        ref=ref,
                        trx_id=trx_id,
                        tanggal=tanggalsekarang,
                        waktu=jam_wib
                    )
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)

                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}              
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XC 1 + 1GB 
║  Harga DOR  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : QRIS
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
""")
                    user_sessions.pop(user_id, None)
                    return

                elif status == 0 or is_refunded == 1:
                    tambah_saldo(user_id, harga_jasa)
                    await bot.send_message(user_id, "❌ Pembayaran QRIS gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan ulangi pembelian.")
        user_sessions.pop(user_id, None)

    asyncio.create_task(cek_status_transaksi())


@bot.on(events.CallbackQuery(data=b'confirm_cmb_pulsa'))
async def confirm_cmb_pulsa(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    harga_jasa = 100 if role == "admin" else 5000
    saldo = get_user_balance(user_id)

    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)
    await event.respond("⏳ Memproses pembelian paket via pulsa, mohon tunggu...")

    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "XL_XC1PLUS1DISC_PULSA",
            "phone": nomor,
            "access_token": token,
            "payment_method": "PULSA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    if result.get("status"):
        increment_all_user_counted_dor()
        increment_all_user_counts()
        count_dor = get_user_counted_dor(user_id)

        await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}              
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XC 1 + 1GB PULSA
║  Harga DOR  : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
""")
        await bot.send_message(user_id, f"✅ Paket berhasil diproses via pulsa. Terima kasih!")
    else:
        pesan_error = result.get("message", "Tidak diketahui")
        tambah_saldo(user_id, harga_jasa)  # refund
        await bot.send_message(user_id, f"❌ Pembelian gagal: {pesan_error}\nSaldo jasa telah dikembalikan.")

    user_sessions.pop(user_id, None)

@bot.on(events.CallbackQuery(data=b'confirm_flex_dana'))
async def confirm_flex_dana(event):
    user_id = event.sender_id
    nomor = user_sessions.get(user_id, {}).get("hp")
    token = user_sessions.get(user_id, {}).get("token")

    if not nomor or not token:
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    role = get_user_role(user_id)
    # Harga jasa internal
    harga_jasa = 100 if role == "admin" else 5000

    saldo = get_user_balance(user_id)
    if saldo < harga_jasa:
        await event.edit(
            f"❌ SALDO TIDAK CUKUP\nHarga jasa: Rp {harga_jasa:,}\nSaldo: Rp {saldo:,}\nSilakan topup saldo dulu.",
            buttons=[[Button.inline("➕ Topup Saldo", b"topup_saldo")]]
        )
        return

    kurangi_saldo(user_id, harga_jasa)

    await event.respond("⏳ Memproses pembelian paket, mohon tunggu...")

    # Proses pembelian paket via API
    async with aiohttp.ClientSession() as session:
        url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"
        params = {
            "api_key": API_KEY,
            "package_code": "6b699877e423e526d8c2502f48ba0a1d",
            "phone": nomor,
            "access_token": token,
            "payment_method": "DANA"
        }
        async with session.get(url, params=params) as resp:
            result = await resp.json()

    if not result.get("status"):
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond(f"❌ Pembelian gagal: {result.get('message', 'Tidak diketahui')}")
        return

    data = result.get("data", {})
    trx_id = data.get("trx_id")
    deeplink_url = data.get("deeplink_data", {}).get("deeplink_url")

    if not trx_id or not deeplink_url:
        tambah_saldo(user_id, harga_jasa)  # refund saldo
        await event.respond("❌ Gagal mendapatkan info transaksi DANA.")
        return

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)

    await event.respond(f"""
╔═════════════════════╗
║ ⚠️  SELESAIKAN PEMBAYARAN DANA              
╟═════════════════════╝
║👤 DETAIL PEMBAYARAN:
║  Nomor     : {sensor_hp(nomor)}
║  Paket     : Xc Flex S Promo
║  Metode    : DANA Rp16.000
║  Terpotong : Rp {harga_jasa:,}
╟═════════════════════╣
║🕐 WAKTU:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
{trx_id}
""",
        buttons=[[Button.url("💳 Bayar via DANA", deeplink_url)]]
    )

    # Fungsi cek status transaksi berkala
    async def cek_status_transaksi():
        for _ in range(20):  # cek sampai 20x (10 menit @30detik)
            await asyncio.sleep(30)
            async with aiohttp.ClientSession() as session:
                check_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
                params_check = {"api_key": API_KEY, "trx_id": trx_id}
                async with session.get(check_url, params=params_check) as resp:
                    status_res = await resp.json()

            if status_res.get("status") and status_res.get("data"):
                status = status_res["data"].get("status")
                is_refunded = status_res["data"].get("is_refunded", 0)

                if status == 1 and is_refunded == 0:
                    # Berhasil bayar
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    tunggu_wib, tunggu_wita, tunggu_wit = waktu_sekarang()  # atau waktu plus estimasi
                    increment_all_user_counted_dor()
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}              
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XC Flex S Promo
║  Harga DOR  : Rp {harga_jasa:,}
║  Status     : Menunggu pembayaran 
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggalsekarang} — {jam_wib} 
╚═════════════════════╝
""")
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}              
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna   : {user_line}
║  Nomor      : {sensor_hp(nomor)}
║  Paket      : XC Flex S Promo
║  Status     : Menunggu pembayara
║  Metode    : E-Wallet DANA
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggalsekarang} — {jam_wib}
╚═════════════════════╝
""")

                    user_sessions.pop(user_id, None)
                    return  # selesai

                elif status == 0 or is_refunded == 1:
                    # Gagal / dibatalkan
                    tambah_saldo(user_id, harga_jasa)  # refund saldo

                    await bot.send_message(user_id, f"❌ Pembayaran DANA gagal atau dibatalkan.\nSaldo jasa sudah dikembalikan.")
                    user_sessions.pop(user_id, None)
                    return

            # status == 2 artinya pending, lanjut cek lagi

        # Jika habis timeout
        await bot.send_message(user_id, "⚠️ Pembayaran belum terkonfirmasi dalam waktu 10 menit. Silakan cek kembali atau ulangi pembelian.")
        user_sessions.pop(user_id, None)

    # Jalankan cek status transaksi di background tanpa blocking
    asyncio.create_task(cek_status_transaksi())    

# Konfigurasi
MAIN_PACKAGES = ["PREMIUMXC", "SUPERXC"]
BONUS_MAPPING = {
    "PREMIUMXC": "bdb392a7aa12b21851960b7e7d54af2c",
    "SUPERXC": "XL_XC1PLUS1DISC_PULSA"
}

paket_data = [
    ("📦 XUT Premium", "PREMIUMXC"),
    ("📦 XUT Super", "SUPERXC"),
    ("📦 XCS ", "bdb392a7aa12b21851960b7e7d54af2c"),
    ("📦 XC 1+1 GB", "XL_XC1PLUS1DISC_PULSA"),
]

# Buat mapping code → nama
NAMA_PAKET_MAP = {code: name for name, code in paket_data}

# Konfigurasi global
JEDA_PEMBELIAN_PAKET = 20  # Detik

def validasi_paket_combo(selected):
    main = [p for p in selected if p in MAIN_PACKAGES]
    bonus = [p for p in selected if p not in MAIN_PACKAGES]

    if len(set(main)) > 1:
        return False, "⚠️ Tidak boleh memilih Super dan Premium sekaligus."

    if not main and bonus:
        return False, "⚠️ Tidak bisa membeli Add-On tanpa memilih paket utama (Super/Premium)."

    if main:
        allowed_bonus = BONUS_MAPPING[main[0]]
        if set(bonus) != {allowed_bonus}:
            return False, f"⚠️ {NAMA_PAKET_MAP[main[0]]} hanya bisa dikombinasikan dengan {NAMA_PAKET_MAP.get(allowed_bonus, allowed_bonus)}."

    return True, ""

def harga_addon(code, user_id):
    if code in BONUS_MAPPING.values():
        return 6000
    return 500 if is_reseller(user_id) else 1000

@bot.on(events.CallbackQuery(data=b'menu_xutsp'))
async def menu_addon_handler(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id)
    if not sesi or not sesi.get("hp") or not sesi.get("token"):
        await event.respond("❌ Silakan login OTP terlebih dahulu.")
        return
    user_sessions[user_id] = {
        "selected_packages": [],
        "hp": sesi["hp"],
        "token": sesi["token"]
    }
    await show_addon_buttons(event, user_id)

# Menambahkan status pengguna pada bagian menu add-on
async def show_addon_buttons(event, user_id):
    selected = user_sessions[user_id].get("selected_packages", [])

    user_status = "Reseller" if is_reseller(user_id) else "Member"

    teks = (
        "╔════════════════════════╗\n"
        "     📦 𝗣𝗔𝗞𝗘𝗧  𝗫𝗨𝗧 (XUTS/XUTP)      \n"
        "╚════════════════════════╝\n\n"
        
        f"👤 Status: {user_status}\n"
    )

    # Tambah daftar paket terpilih
    if selected:
        daftar = "\n".join([f"• {NAMA_PAKET_MAP.get(code, code)}" for code in selected])
        teks += f"\n📝 Paket terpilih:\n{daftar}\n"
    else:
        teks += "\n📭 Belum ada paket dipilih.\n"

    teks += "\n🛒 *Pilih Paket Add-On XUT:*"

    # Deskripsi per paket (XUTS dan XUTP)
    teks += (
        "\n\n╭── 🟩 𝗫𝗨𝗧 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 ────────╮\n"
        "│ 💸 Metode: Pulsa • sedid: Rp25.000\n"
        "╰───────────────────────╯\n"
        "╭── 🟩 𝗫𝗨𝗧 𝗦𝗨𝗣𝗘𝗥 ──────────╮\n"
        "│ 💸 Metode: Pulsa • sedia: Rp12.500\n"
        "╰───────────────────────╯\n"
        "🧠 **Pastikan Sebelum Tembak:**\n"
        "➤ Tidak terpacu aplikasi MyXL\n"
        "➤ Cek *808*5*3# tidak ada XCS\n"
        "➤ Pulsa cukup (Rp12.500 / Rp25.000)\n"
        "➤ Tidak semua nomor support\n"
        "➤ Jika dapat SMS gagal, tunggu ±2 jam\n"
    )

    buttons, row = [], []  
    for name, code in paket_data:  
        label = f"✅ {name}" if code in selected else name  
        row.append(Button.inline(label, f"addon_toggle_{code}".encode()))  
        if len(row) == 2:  
            buttons.append(row)  
            row = []  
    if row: buttons.append(row)  


    buttons += [  
        [Button.inline("🛒 [PULSA] XUT Premium", b"addon_beli_premium")],
        [Button.inline("🛒 [PULSA] XUT Super", b"addon_beli_super")],
        [Button.inline("🚀 Tembak Paket", b"addon_konfirmasi"),Button.inline("🔁 Reset Paket", b"addon_reset")],
        [Button.inline("⬅️ Kembali", b"dor")]
    ]

    await event.edit(teks, buttons=buttons)


@bot.on(events.CallbackQuery(data=re.compile(b'^addon_toggle_')))
async def toggle_addon_handler(event):
    user_id = event.sender_id
    code = event.data.decode().replace("addon_toggle_", "")
    selected = user_sessions[user_id].setdefault("selected_packages", [])
    simulated = selected.copy()
    if code in simulated: simulated.remove(code)
    else: simulated.append(code)
    valid, msg = validasi_paket_combo(simulated)
    if not valid:
        await event.answer(msg, alert=True)
        return
    if code in selected:
        selected.remove(code)
        await event.answer(f"❌ {NAMA_PAKET_MAP.get(code, code)} dibatalkan", alert=False)
    else:
        selected.append(code)
        await event.answer(f"✅ {NAMA_PAKET_MAP.get(code, code)} ditambahkan", alert=False)
    await show_addon_buttons(event, user_id)

@bot.on(events.CallbackQuery(data=b'addon_reset'))
async def reset_addon_handler(event):
    user_id = event.sender_id
    user_sessions[user_id]["selected_packages"] = []
    await event.answer("✅ Paket direset.")
    await show_addon_buttons(event, user_id)

@bot.on(events.CallbackQuery(data=b'addon_beli_premium'))
async def beli_premium_handler(event):
    user_id = event.sender_id
    user_sessions[user_id]["selected_packages"] = [
        "PREMIUMXC", BONUS_MAPPING["PREMIUMXC"]
    ]
    await event.answer("✅ Premium + XCX  dipilih.")
    await show_addon_buttons(event, user_id)

@bot.on(events.CallbackQuery(data=b'addon_beli_super'))
async def beli_super_handler(event):
    user_id = event.sender_id
    user_sessions[user_id]["selected_packages"] = [
        "SUPERXC", BONUS_MAPPING["SUPERXC"]
    ]
    await event.answer("✅ Super + XC 1+1 dipilih.")
    await show_addon_buttons(event, user_id)

@bot.on(events.CallbackQuery(data=b'addon_konfirmasi'))
async def konfirmasi_addon_handler(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    selected = sesi.get("selected_packages", [])

    valid, msg = validasi_paket_combo(selected)
    if not valid:
        await event.answer(msg, alert=True)
        return

    if not selected:
        await event.answer("⚠️ Belum ada paket dipilih.", alert=True)
        return

    daftar = "\n".join([f"• {NAMA_PAKET_MAP.get(code, code)}" for code in selected])

    # ✅ Menggunakan harga_addon
    total = sum(harga_addon(code, user_id) for code in selected)
    saldo = get_user_balance(user_id)

    if saldo <= 0:
        await event.answer("❌ Saldo kamu 0. Isi saldo dulu sebelum bisa tembak paket.", alert=True)
        return

    if saldo < total:
        await event.answer(f"❌ Saldo kamu hanya Rp{saldo:,}. Tidak cukup untuk total paket Rp{total:,}.", alert=True)
        return

    user_status = "Reseller" if is_reseller(user_id) else "Member"

    await event.edit(
        f"📦 Kamu akan tembak paket:\n\n{daftar}\n\n👤 Status: {user_status}\n💰 Total potongan saldo: Rp {total:,}\nLanjutkan?",
        buttons=[
            [Button.inline("✅ Lanjutkan", b"addon_proses")],
            [Button.inline("❌ Batal", b"addon_batal")]
        ]
    )

@bot.on(events.CallbackQuery(data=b'addon_batal'))
async def batal_addon_handler(event):
    user_id = event.sender_id
    user_sessions[user_id]["selected_packages"] = []
    await event.delete()
    await event.edit("❌ Transaksi dibatalkan.")

@bot.on(events.CallbackQuery(data=b'addon_proses'))
async def proses_addon_handler(event):
    await event.delete()
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    selected = sesi.get("selected_packages", [])
    nomor, token = sesi.get("hp"), sesi.get("token")

    if not selected or not nomor or not token:
        await bot.send_message(user_id, "❌ Data tidak lengkap.")
        return

    saldo = get_user_balance(user_id)
    total_harga = sum(harga_addon(code, user_id) for code in selected)
    if saldo < total_harga:
        await bot.send_message(user_id, "❌ Saldo tidak cukup.")
        return

    def is_successful(code: str, message: str) -> bool:
        msg = message.lower()
        if code in ["PREMIUMXC", "SUPERXC"]:
            return "422" in msg
        elif code in ["XL_XC1PLUS1DISC_PULSA", "bdb392a7aa12b21851960b7e7d54af2c"]:
            return (
                "paket berhasil dibeli" in msg
                or "berhasil" in msg
                or "sukses" in msg
            )
        return "422" in msg  # default fallback

    user_status = "Reseller" if is_reseller(user_id) else "Member"
    await bot.send_message(user_id, f"⏳ Memproses {len(selected)} paket...\n👤 Status: {user_status}")

    berhasil, gagal, saldo_terpakai = 0, 0, 0
    ref_base = f"DOR{int(datetime.now().timestamp())}"
    jam_wib = waktu_sekarang()[0]
    tanggal = tanggal_pembayaran()
    user_line = get_user_line(user_id)
    url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"

    async with aiohttp.ClientSession() as session:
        for i, code in enumerate(selected, 1):
            harga = harga_addon(code, user_id)
            if i > 1:
                await asyncio.sleep(JEDA_PEMBELIAN_PAKET)

            if saldo < harga:
                await bot.send_message(user_id, f"❌ Saldo tidak cukup untuk {NAMA_PAKET_MAP.get(code, code)}.")
                continue

            ref = f"{ref_base}_{i}"
            trx_id = "-"
            response_message = "-"
            success = False
            attempt = 0
            max_forced = 5
            full_code = f"XLUNLITURBO{code}_PULSA" if code in MAIN_PACKAGES else code
            params = {
                "api_key": API_KEY,
                "package_code": full_code,
                "phone": nomor,
                "access_token": token,
                "payment_method": "PULSA"
            }

            if code in MAIN_PACKAGES:
                while True:
                    attempt += 1
                    if attempt > 1:
                        await asyncio.sleep(35)
                    async with session.get(url, params=params) as resp:
                        try:
                            hasil = await resp.json()
                        except Exception as e:
                            await bot.send_message(user_id, f"❌ Gagal parsing JSON: {e}")
                            break

                        response_message = hasil.get("message", "-")
                        trx_id = hasil.get("trx_id", "-")

                    if is_successful(code, response_message):
                        success = True
                        break
                    elif attempt < max_forced:
                        await asyncio.sleep(200)
            else:
                async with session.get(url, params=params) as resp:
                    try:
                        hasil = await resp.json()
                    except Exception as e:
                        await bot.send_message(user_id, f"❌ Gagal parsing JSON: {e}")
                        continue

                    response_message = hasil.get("message", "-")
                    trx_id = hasil.get("trx_id", "-")
                    if is_successful(code, response_message):
                        success = True

            respon_singkat = extract_status_code(response_message)

            if success:
                kurangi_saldo(user_id, harga)
                saldo_terpakai += harga
                berhasil += 1
                simpan_riwayat_dor(user_id, nomor, code, harga, ref, trx_id, tanggal, jam_wib)
                increment_all_user_counted_dor()
                increment_all_user_counts()
                count_dor = get_user_counted_dor(user_id)

                user_msg = f"✅ Paket {NAMA_PAKET_MAP.get(code, code)} sukses."
                await bot.send_message(user_id, user_msg)

                await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}      
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna : {user_line}
║  Nomor    : {sensor_hp(nomor)}
║  Paket    : {NAMA_PAKET_MAP.get(code, code)}
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggal} — {jam_wib}
╚═════════════════════╝
""")
                await bot.send_message(group_id_kedua, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}      
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna : {user_line}
║  Paket    : {NAMA_PAKET_MAP.get(code, code)}
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggal} — {jam_wib} 
╟═════════════════════╣
║📩 RESPON:
║  {respon_singkat}
╚═════════════════════╝
`{nomor}`
""")
            else:
                gagal += 1
                await bot.send_message(user_id, f"❌ Paket {NAMA_PAKET_MAP.get(code, code)} gagal: {respon_singkat}")
                await bot.send_message(group_id_kedua, f"""
╔═════════════════════╗
║ ❌  TRANSAKSI DOR GAGAL           
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna : {user_line}
║  Paket    : {code}
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggal} — {jam_wib} 
╚═════════════════════╝
`{nomor}`
""")
                if code in MAIN_PACKAGES:
                    break

    await bot.send_message(user_id, f"📦 Sukses: {berhasil}, Gagal: {gagal}, 💸 Potongan akhir: Rp {saldo_terpakai:,}")
    user_sessions.pop(user_id, None)
    
# Menu awal
@bot.on(events.CallbackQuery(data=b'menu_addon'))
async def menu_tembak(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id)
    if not sesi or not sesi.get("hp") or not sesi.get("token"):
        await event.respond("❌ Nomor atau token tidak ditemukan. Silakan login OTP terlebih dahulu.")
        return

    user_sessions[user_id] = {
        "selected_packages": [],
        "hp": sesi["hp"],
        "token": sesi["token"]
    }
    await show_paket_buttons(event, user_id)

# Tampilkan menu pilihan
async def show_paket_buttons(event, user_id):
    teks = ""
    selected = user_sessions[user_id].get("selected_packages", [])

    paket_data = [
        ("📦 Premium", "PREMIUMXC"),
        ("📦 Super", "SUPERXC"),
        ("📦 Standard", "STANDARDXC"),
        ("📦 Basic", "BASICXC"),
        ("📦 Netflix", "NETFLIXXC"),
        ("📦 Viu", "VIU"),
        ("📦 Youtube", "YOUTUBEXC"),
        ("📦 TikTok", "TIKTOK"),
        ("📦 Joox", "JOOXXC"),
    ]

    if selected:
        daftar = "\n".join(
            [f"• {name}" for name, code in paket_data if code in selected]
        )
        teks += f"\n📝 Paket terpilih:\n{daftar}\n"
    else:
        teks += "\n📭 Belum ada paket dipilih.\n"

    teks += (
        "\n📌 **Panduan Penting:**\n"
        "➤ Tanpa saldo Dana & pulsa\n"
        "➤ Tidak ada Xtra Combo kecuali Flex\n"
        "➤ Cek via *808#\n"
        "➤ Pulsa < Rp20.000\n"
        "➤ Setelah SMS gagal ➜ lanjut tembak XCS 8 GB\n"
        "➤ Tunggu ±1 jam agar AddOn masuk\n"
        "➤ Potong saldo bot:\n"
        "  - Rp500/paket (reseller)\n"
        "  - Rp1000/paket (member)\n"
    )

    # Tombol inline
    buttons = []
    row = []
    for name, code in paket_data:
        label = f"✅ {name}" if code in selected else f"{name}"
        row.append(Button.inline(label, f"toggle_{code}".encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([Button.inline("🛒 Beli Semua Paket", b"beli_semua_paket")])
    buttons.append([
        Button.inline("🚀 Tembak Paket", b"konfirmasi_paket"),
        Button.inline("🔁 Reset Paket", b"reset_paket")
    ])
    buttons.append([Button.inline("⬅️ Kembali", b"menu_xcs")])

    await event.edit(teks, buttons=buttons)
    
# Mapping nama kode paket ke nama bersih yang ditampilkan ke user
PAKET_NAMA_BERSIH = {
    "PREMIUMXC": "PREMIUM",
    "SUPERXC": "SUPER",
    "STANDARDXC": "STANDARD",
    "BASICXC": "BASIC",
    "NETFLIXXC": "NETFLIX",
    "VIU": "VIU",
    "YOUTUBEXC": "YOUTUBE",
    "TIKTOK": "TIKTOK",
    "JOOXXC": "JOOX"
}

def format_nama_paket(code: str) -> str:
    """Format nama paket dari kode ke nama bersih"""
    return PAKET_NAMA_BERSIH.get(code.strip(), code.strip())

# Toggle pilih paket
@bot.on(events.CallbackQuery(data=re.compile(b'^toggle_')))
async def toggle_paket(event):
    user_id = event.sender_id
    code = event.data.decode().split("_", 1)[1]
    selected = user_sessions.setdefault(user_id, {}).setdefault("selected_packages", [])
    if code in selected:
        selected.remove(code)
        await event.answer(f"❌ {code} dibatalkan", alert=False)
    else:
        selected.append(code)
        await event.answer(f"✅ {code} ditambahkan", alert=False)
    await show_paket_buttons(event, user_id)

# Reset pilihan
@bot.on(events.CallbackQuery(data=b'reset_paket'))
async def reset_paket(event):
    user_id = event.sender_id
    if user_id in user_sessions:
        user_sessions[user_id]["selected_packages"] = []
    await show_paket_buttons(event, user_id)
    await event.answer("✅ Paket direset.")

# Pilih semua paket
@bot.on(events.CallbackQuery(data=b'beli_semua_paket'))
async def beli_semua_paket(event):
    user_id = event.sender_id
    if user_id not in user_sessions:
        await event.answer("⚠️ Sesi tidak ditemukan.", alert=True)
        return

    # Daftar kode paket
    semua_kode = [
        "PREMIUMXC", "SUPERXC", "STANDARDXC", "BASICXC", 
        "NETFLIXXC", "VIU", "YOUTUBEXC", "TIKTOK", "JOOXXC"
    ]

    # Set semua kode ke selected_packages
    user_sessions[user_id]["selected_packages"] = semua_kode.copy()
    await event.answer("✅ Semua paket telah dipilih.", alert=False)
    await show_paket_buttons(event, user_id)

# Konfirmasi
@bot.on(events.CallbackQuery(data=b'konfirmasi_paket'))
async def konfirmasi_paket(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    selected = sesi.get("selected_packages", [])

    if not selected:
        await event.answer("⚠️ Belum ada paket yang dipilih.", alert=True)
        return

    daftar = "\n".join([f"• {format_nama_paket(code)}" for code in selected])
    
    # Menentukan harga berdasarkan status reseller atau member
    if is_reseller(user_id):  # Menggunakan fungsi is_reseller
        harga_per_paket = 500  # Harga untuk reseller
    else:
        harga_per_paket = 1000  # Harga untuk member

    total = len(selected) * harga_per_paket
    saldo = get_user_balance(user_id)

    if saldo <= 0:
        await event.answer("❌ Saldo kamu 0. Isi saldo dulu sebelum bisa tembak paket.", alert=True)
        return

    if saldo < total:
        await event.answer(f"❌ Saldo kamu hanya Rp{saldo:,}. Tidak cukup untuk total paket Rp{total:,}.", alert=True)
        return

    await event.edit(
        f"💬 Kamu akan menembak paket berikut:\n\n{daftar}\n\n💰 Total potongan saldo: Rp {total:,}\n\nLanjutkan transaksi?",
        buttons=[
            [
                Button.inline("✅ Lanjutkan", b"proses_paket"),
                Button.inline("❌ Batal", b"batal_paket")
            ]
        ]
    )


# Batal manual
@bot.on(events.CallbackQuery(data=b'batal_paket'))
async def batal_paket(event):
    user_id = event.sender_id
    user_sessions[user_id]["selected_packages"] = []
    await event.delete()
    await event.edit("❌ Transaksi dibatalkan.")

JEDA_PEMBELIAN_PAKET = 20  # Detik jeda antar pembelian paket

import re

def extract_status_code(msg):
    match = re.search(r"\b(4\d{2}|5\d{2})\b", msg)
    return match.group(1) if match else msg
    
@bot.on(events.CallbackQuery(data=b'proses_paket'))
async def proses_paket(event):
    await event.delete()
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    selected = sesi.get("selected_packages", [])
    nomor = sesi.get("hp")
    token = sesi.get("token")

    if is_reseller(user_id):
        harga_per_paket = 500
    else:
        harga_per_paket = 1000

    if not selected:
        await event.answer("Tidak ada paket yang diproses.", alert=True)
        return
    if not nomor or not token:
        await event.respond("Token atau nomor tidak ditemukan.")
        return

    saldo = get_user_balance(user_id)
    await event.respond(f"Memproses {len(selected)} paket... saldo hanya dipotong jika proses sudah selesai (paket pending).")

    berhasil, gagal = 0, 0
    gagal_list = []
    saldo_terpakai = 0

    tanggalsekarang = tanggal_pembayaran()
    jam_wib, jam_wita, jam_wit = waktu_sekarang()
    ref_base = f"DOR{int(datetime.now().timestamp())}"
    user_line = get_user_line(user_id)
    special_codes = ["PREMIUMXC", "SUPERXC", "STANDARDXC", "BASICXC", "YOUTUBEXC", "TIKTOK"]
    url = "https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1"

    async with aiohttp.ClientSession() as session:
        for i, code in enumerate(selected, 1):
            if i > 1:
                await asyncio.sleep(JEDA_PEMBELIAN_PAKET)

            ref = f"{ref_base}_{i}"
            trx_id = "-"
            response_message = "-"
            success = False
            attempt = 0
            max_forced = 5
            current_code = f"XLUNLITURBO{code}_PULSA"
            nama_paket_bersih = format_nama_paket(code)
            params = {
                "api_key": API_KEY,
                "package_code": current_code,
                "phone": nomor,
                "access_token": token,
                "payment_method": "PULSA"
            }

            if code in special_codes:
                while True:
                    attempt += 1
                    if attempt > 1:
                        await asyncio.sleep(35)
                    async with session.get(url, params=params) as resp:
                        hasil = await resp.json()
                        response_message = hasil.get("message", "-")
                        trx_id = hasil.get("trx_id", "-")
                    if "422" in response_message:
                        success = True
                        break
                    # Tidak kirim pesan retry ke user
            else:
                async with session.get(url, params=params) as resp:
                    hasil = await resp.json()
                    response_message = hasil.get("message", "-")
                    trx_id = hasil.get("trx_id", "-")
                    if "422" in response_message:
                        success = True

            respon_singkat = extract_status_code(response_message)

            if success:
                kurangi_saldo(user_id, harga_per_paket)
                saldo_terpakai += harga_per_paket
                berhasil += 1
                simpan_riwayat_dor(user_id, nomor, code, harga_per_paket, ref, trx_id, tanggalsekarang, jam_wib)
                increment_all_user_counted_dor()
                increment_all_user_counts()
                count_dor = get_user_counted_dor(user_id)
                user_msg = f"✅ Paket {nama_paket_bersih} sukses di proses."
                await bot.send_message(user_id, user_msg)

                await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}      
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna : {user_line}
║  Nomor    : {sensor_hp(nomor)}
║  Paket    : {nama_paket_bersih} BYPASS
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggalsekarang} — {jam_wib}
╟═════════════════════╣
║📩 RESPON:
║  {respon_singkat}
╚═════════════════════╝
""")
                await bot.send_message(group_id_kedua, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}      
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna : {user_line}
║  Paket    : {nama_paket_bersih} BYPASS
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggalsekarang} — {jam_wib} 
╟═════════════════════╣
║📩 RESPON:
║  {respon_singkat}
╚═════════════════════╝
`{nomor}`
""")
            else:
                gagal += 1
                gagal_list.append(f"{nama_paket_bersih} - {response_message}")
                await bot.send_message(user_id, f"❌ Paket {nama_paket_bersih} gagal setelah {attempt} percobaan.\n📩 Respon: {respon_singkat}")
                await bot.send_message(group_id_kedua, f"""
╔═════════════════════╗
║ ❌  TRANSAKSI DOR GAGAL           
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna : {user_line}
║  Paket    : {nama_paket_bersih} BYPASS
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggalsekarang} — {jam_wib} WIB
╟═════════════════════╣
║📩 RESPON:
║  {respon_singkat}
╚═════════════════════╝
`{nomor}`
""")

    if berhasil == 0:
        await bot.send_message(user_id, "❌ Semua transaksi gagal. Tidak ada saldo terpotong.")
    elif gagal > 0:
        await bot.send_message(user_id, f"✅ {berhasil} paket sukses, ❌ {gagal} gagal.\n💸 Total saldo terpakai: Rp {saldo_terpakai:,}")
        await bot.send_message(user_id, "Detail Gagal:\n" + "\n".join(f"- {x}" for x in gagal_list))
    else:
        await bot.send_message(user_id, f"✅ Semua {berhasil} paket berhasil. 💸 Total saldo terpotong: Rp {saldo_terpakai:,}")

    sesi.pop("auto_select_all", None)
    user_sessions.pop(user_id, None)
    
# ===============================
# FLEX BONUS FIXED HARGA + SALDO CHECK & REFUND
# ===============================

# Harga tetap semua paket bonus = Rp3.000
def harga_paket(code):
    return 3000

paket_data_flex = [
    ("🎁 Flex Kuota Utama 8GB", "BONUS_FLEX_KUOTAUTAMA_8GB"),
    ("🎁 Flex TikTok 14GB", "BONUS_FLEX_TT_14GB"),
    ("🎁 Flex YouTube 14GB", "BONUS_FLEX_YT_14GB"),
    ("🎁 Flex Kuota Malam 22GB", "BONUS_FLEX_KUOTAMALAM_22GB"),
]

FLEX_BONUS_LIST = [code for _, code in paket_data_flex]
NAMA_PAKET_MAP.update({code: name for name, code in paket_data_flex})

@bot.on(events.CallbackQuery(data=b'menu_flexbonus'))
async def bonus_flex_menu(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id)
    if not sesi or not sesi.get("hp") or not sesi.get("token"):
        await event.respond("❌ Silakan login OTP terlebih dahulu.")
        return
    user_sessions[user_id] = {
        "selected_packages_flex": [],
        "hp": sesi["hp"],
        "token": sesi["token"]
    }
    await show_flex_buttons(event, user_id)

async def show_flex_buttons(event, user_id):
    selected = user_sessions[user_id].get("selected_packages_flex", [])
    teks = "📦 Paket Bonus Flex:\n\n"
    if selected:
        daftar = "\n".join([f"• {NAMA_PAKET_MAP.get(code, code)}" for code in selected])
        teks += f"📝 Paket terpilih:\n{daftar}\n\nKlik untuk memilih/batal:"
    else:
        teks += "Belum ada paket dipilih. Klik untuk memilih:"
    
    buttons, row = [], []
    for name, code in paket_data_flex:
        label = f"✅ {name}" if code in selected else name
        row.append(Button.inline(label, f"flex_toggle_{code}".encode()))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)

    buttons += [
        [Button.inline("🚀 Tembak ADD-ON", b"flex_konfirmasi")],
        [Button.inline("🔁 Reset", b"flex_reset")],
        [Button.inline("⬅️ Kembali", b"menu_flex")]
    ]

    try:
        await event.edit(teks, buttons=buttons)
    except errors.MessageNotModifiedError:
        await event.answer("✅ Sudah diperbarui", alert=False)

@bot.on(events.CallbackQuery(data=re.compile(b'^flex_toggle_')))
async def toggle_flex_handler(event):
    user_id = event.sender_id
    code = event.data.decode().replace("flex_toggle_", "")
    selected = user_sessions[user_id].setdefault("selected_packages_flex", [])
    if code in selected:
        selected.remove(code)
        await event.answer("❌ Dihapus", alert=False)
    else:
        selected.append(code)
        await event.answer("✅ Ditambahkan", alert=False)
    await show_flex_buttons(event, user_id)

@bot.on(events.CallbackQuery(data=b'flex_reset'))
async def reset_flex_handler(event):
    user_id = event.sender_id
    user_sessions[user_id]["selected_packages_flex"] = []
    await event.answer("✅ Direset")
    await show_flex_buttons(event, user_id)

@bot.on(events.CallbackQuery(data=b'flex_konfirmasi'))
async def confirm_flex_bonus_only(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor, token = sesi.get("hp"), sesi.get("token")
    selected = sesi.get("selected_packages_flex", [])

    if not nomor or not token or not selected:
        await event.answer("❌ Tidak ada paket dipilih.", alert=True)
        return

    total = sum(harga_paket(code) for code in selected)
    saldo = get_user_balance(user_id)

    if saldo < total:
        return await event.respond(
            f"❌ Saldo kamu tidak cukup untuk klaim bonus.\n"
            f"🔢 Paket dipilih: {len(selected)}\n"
            f"💰 Biaya: Rp {total:,}\n"
            f"💸 Saldo: Rp {saldo:,}"
        )

    daftar_paket = "\n".join([f"• {NAMA_PAKET_MAP.get(code, code)}" for code in selected])
    try:
        await event.edit(
            f"⚠️ Kamu akan membeli {len(selected)} paket Bonus Flex:\n\n"
            f"{daftar_paket}\n\n"
            f"📌 Pastikan kamu sudah punya paket utama Xtra Combo Flex aktif dari MyXL atau Flex S Promo.\n"
            f"❗ Jika tidak, bonus bisa gagal masuk.\n\n"
            f"?? Total potongan saldo: Rp {total:,}\n\n"
            f"✅ Lanjutkan pembelian?",
            buttons=[
                [Button.inline("✅ Ya, lanjut", b"flex_proses_bonus")],
                [Button.inline("❌ Batal", b"flex_reset")]
            ]
        )
    except errors.MessageNotModifiedError:
        await event.answer("✅ Silakan lanjut.", alert=False)

@bot.on(events.CallbackQuery(data=b'flex_proses_bonus'))
async def trigger_proses_bonus(event):
    user_id = event.sender_id
    sesi = user_sessions.get(user_id, {})
    nomor, token = sesi.get("hp"), sesi.get("token")
    bonus_list = sesi.get("selected_packages_flex", [])
    await proses_bonus_flex(user_id, nomor, token, bonus_list)

async def proses_bonus_flex(user_id, nomor, token, bonus_list):
    jam_wib = waktu_sekarang()[0]
    tanggal = tanggal_pembayaran()
    user_line = get_user_line(user_id)
    ref_base = f"BONUSFLEX{int(datetime.now().timestamp())}"
    saldo_terpakai = berhasil = gagal = 0
    total_harga = sum(harga_paket(code) for code in bonus_list)
    saldo = get_user_balance(user_id)

    if saldo < total_harga:
        await bot.send_message(user_id, f"❌ Saldo tidak cukup. Total diperlukan Rp {total_harga:,}, saldo kamu Rp {saldo:,}.")
        return

    kurangi_saldo(user_id, total_harga)

    async with aiohttp.ClientSession() as session:
        for i, code in enumerate(bonus_list, 1):
            harga = harga_paket(code)
            params = {
                "api_key": API_KEY,
                "package_code": code,
                "phone": nomor,
                "access_token": token,
                "payment_method": "PULSA"
            }
            ref = f"{ref_base}_{i}"
            try:
                await asyncio.sleep(JEDA_PEMBELIAN_PAKET)
                async with session.get("https://golang-openapi-packagepurchase-xltembakservice.kmsp-store.com/v1", params=params) as resp:
                    hasil = await resp.json()
                if hasil.get("status") or "422" in hasil.get("message", ""):
                    saldo_terpakai += harga
                    berhasil += 1
                    simpan_riwayat_dor(user_id, nomor, code, harga, ref, hasil.get("trx_id", "-"), tanggal, jam_wib)
                    await bot.send_message(user_id, f"✅ Bonus {NAMA_PAKET_MAP.get(code, code)} berhasil diklaim.")
                    increment_all_user_counted_dor()
                    increment_all_user_counts()
                    count_dor = get_user_counted_dor(user_id)
                    await bot.send_message(group_id, f"""
╔═════════════════════╗
║ ✅  TRANSAKSI DOR SUKSES #{count_dor}      
╟═════════════════════╝
║👤 DETAIL TRANSAKSI:
║  Pengguna : {user_line}
║  Nomor   : {sensor_hp(nomor)}
║  Paket   : {NAMA_PAKET_MAP.get(code, code)}
║  Harga   : Rp {harga:,}
╟═════════════════════╣
║🕐 WAKTU TRANSAKSI:
║  {tanggal} — {jam_wib}
╚═════════════════════╝
""")
                else:
                    gagal += 1
                    await bot.send_message(user_id, f"❌ Bonus {NAMA_PAKET_MAP.get(code, code)} gagal: {hasil.get('message')}")
            except Exception as e:
                gagal += 1
                await bot.send_message(user_id, f"❌ Bonus {NAMA_PAKET_MAP.get(code, code)} gagal: {e}")

    refund = total_harga - saldo_terpakai
    if refund > 0:
        tambah_saldo(user_id, refund)
        await bot.send_message(user_id, f"💸 Sebagian paket gagal. Rp {refund:,} dikembalikan ke saldo kamu.")

    await bot.send_message(user_id, f"📦 BONUS: Sukses: {berhasil}, Gagal: {gagal}, 💸 Potongan akhir: Rp {saldo_terpakai:,}")
    user_sessions[user_id]["selected_packages_flex"] = []

    
# Saat user klik "cek_trx"
@bot.on(events.CallbackQuery(data=b'cek_trx'))
async def menu_cek_trx(event):
    msg = await event.edit(
        "Masukkan **TRX ID** yang ingin kamu cek statusnya.\n\nContoh:\n`bf722a64-3b7f-4569-a076-f7ac1fbc1881`",
        parse_mode='markdown'
    )
    # Simpan state + ID pesan yang akan diedit nanti
    user_sessions[event.sender_id] = {
        "state": "menunggu_trx_id",
        "edit_msg_id": msg.id
    }
@bot.on(events.NewMessage())
async def handle_trx_input(event):
    user_id = event.sender_id
    session = user_sessions.get(user_id)

    if session and session.get("state") == "menunggu_trx_id":
        trx_id = event.text.strip()
        api_url = "https://golang-openapi-checktransaction-xltembakservice.kmsp-store.com/v1"
        edit_msg_id = session.get("edit_msg_id")

        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(api_url, params={"api_key": API_KEY, "trx_id": trx_id}) as resp:
                    data = await resp.json()

            if not data.get("status"):
                raise Exception(data.get("message", "TRX ID tidak ditemukan."))

            result = data["data"]
            status_text = {
                1: "✅ **Sukses**",
                2: "⌛ **Pending**",
                0: "❌ **Gagal**"
            }.get(result["status"], "❓ *Tidak diketahui*")

            refund_text = "✅ Ya" if result["is_refunded"] else "❌ Tidak"
            harga = result.get("total_price", 0)

            await event.delete()
            # Edit pesan lama, bukan respond
            await bot.edit_message(
                entity=event.chat_id,
                message=edit_msg_id,
                text=f"""
Status Transaksi {status_text}
```➣ Nomor      : {result.get("destination_msisdn")}
➣ Tanggal    : {result.get("time_date")}
➣ Refund     : {refund_text}
➣ Paket      : {result.get("name")}
➣ TRX ID     : {trx_id}```
""", parse_mode='markdown')

            
        except Exception as e:
            await event.delete()
            await bot.edit_message(
                entity=event.chat_id,
                message=edit_msg_id,
                text=f"❌ Gagal mengambil data transaksi:\n`{e}`"
            )

        user_sessions.pop(user_id, None)
        


@bot.on(events.CallbackQuery(data=b"cek_kuota_xl"))
async def handle_cek_kuota(event):
    user_id = event.sender_id
    session = get_user_session(user_id)
    if not session or not session.get("phone"):
        return await event.respond("❌ Nomor tidak ditemukan. Silakan login OTP terlebih dahulu.")

    nomor = session["phone"]
    token = await get_token_or_refresh(nomor, user_id)
    if not token:
        return

    try:
        async with aiohttp.ClientSession() as session_http:
            url_kuota = "https://golang-openapi-quotadetails-xltembakservice.kmsp-store.com/v1"
            params = {
                "api_key": API_KEY,
                "access_token": token
            }

            async with session_http.get(url_kuota, params=params) as resp:
                data_kuota = await resp.json()
                print("[DEBUG] Data Kuota:", data_kuota)

        if not data_kuota.get("status") or data_kuota.get("statusCode") != 200:
            raise Exception(data_kuota.get("message", "Gagal mengambil data kuota."))

        quotas = data_kuota.get("data", {}).get("quotas", [])
        if not quotas:
            raise Exception("Tidak ada kuota aktif ditemukan.")

        from uuid import uuid4
        paket_aktif_cache[user_id] = []

        hasil = f"<b>📊 Kuota Aktif untuk {nomor}</b>\n\n"

        for q in quotas:
            nama_paket = q.get("name", "Tanpa Nama")
            expired = q.get("expired_at", "-")
            hasil += f"<b>📦 {nama_paket}</b>\n⏳ Berlaku sampai: <code>{expired}</code>\n"

            for b in q.get("benefits", []):
                hasil += (
                    f"• 🏷️ {b.get('name','-')}\n"
                    f"  ├─ 📦 Kuota: <code>{b.get('quota','-')}</code>\n"
                    f"  └─ 🔋 Sisa : <code>{b.get('remaining_quota','-')}</code>\n"
                )

            hasil += "\n"

            # Simpan ke cache jika bisa di-unreg
            enc = q.get("encrypted_package_code")
            if enc:
                paket_aktif_cache[user_id].append({
                    "id": str(uuid4())[:8],
                    "name": nama_paket,
                    "encrypted_code": enc
                })

        await event.respond(hasil, parse_mode='html')

    except Exception as e:
        await event.respond(f"❌ Gagal mengecek kuota:\n<code>{e}</code>", parse_mode='html')
        
XL_PREFIXES = ["817", "818", "819", "859", "877", "878"]  # tanpa '08' atau '628'

@bot.on(events.CallbackQuery(data=b"cek_kuota_start"))
async def ask_for_number(event):
    user_id = event.sender_id
    user_sessions[user_id] = {"step": "awaiting_cek_kuota"}
    await event.respond("Masukkan nomor XL Anda (contoh: 0877xxxxxxx atau 62877xxxxxxx):")

@bot.on(events.NewMessage)
async def handle_quota_input(event):
    user_id = event.sender_id
    text = event.raw_text.strip()

    if user_id in user_sessions and user_sessions[user_id].get("step") == "awaiting_cek_kuota":
        number = text

        # Ubah ke format lokal kalau dimulai dari +62
        if number.startswith("+62"):
            number = "62" + number[3:]
        # Ubah ke format internasional jika dimulai dari 08
        if number.startswith("08"):
            number = "62" + number[1:]

        # Ambil 3 digit prefix setelah 62
        if number.startswith("62") and len(number) >= 5:
            prefix = number[2:5]
        else:
            prefix = ""

        if prefix not in XL_PREFIXES or not number.isdigit() or len(number) < 11 or len(number) > 14:
            await event.respond("❌ Format nomor salah atau bukan XL. Masukkan nomor XL yang benar (contoh: 0877xxxxxxx atau 62877xxxxxxx).")
            return

        loading = await event.respond("⏳ Memeriksa kuota XL...")
        try:
            await check_quota(number, event)  # number sudah dalam format 62...
        finally:
            await loading.delete()

        user_sessions.pop(user_id, None)  # Hapus sesi setelah cek kuota
        
import aiohttp
import json

DOR_API_KEY = "0a1ccba4-e6fc-498c-af2f-5f889c765aaa"
ID_TELEGRAM = "5730784044"
PASSWORD = "03juni1998"

def format_kuota_response(info):
    nomor = info.get('msisdn', '-')
    owner = info.get('owner', '-')
    kategori = info.get('category', '-')
    status = info.get('status', '-')
    dukcapil = info.get('dukcapil', '-')
    tenure = info.get('tenure', '-')
    exp_kartu = info.get('expDate', '-')
    exp_sp = info.get('SPExpDate', '-')

    # Header info pelanggan
    output = [f"""🪪 Nomor    : {nomor}
📲 Provider : {owner}
📶 Jaringan : {status}
🧾 Dukcapil : {dukcapil}
⏱️ Umur     : {tenure}
📆 Aktif    : {exp_kartu}
🛑 Tenggang : {exp_sp}
━━━━━━━━━━━━━━━━━━━━━━━"""]

    # Paket utama
    packages = info.get("data", {}).get("packageInfo", [])
    for paket_group in packages:
        for paket in paket_group:
            p_info = paket.get("packages", {})
            name = p_info.get("name", "Tanpa Nama")
            exp = p_info.get("expDate", "-")
            benefits = paket.get("benefits", [])

            output.append(f"""📦 Paket    : {name}
📅 Kadaluarsa: {exp}""")

            if benefits:
                for b in benefits:
                    jenis = b.get("type", "-")
                    nama = b.get("bname", "-")
                    quota = b.get("quota", "-")
                    remaining = b.get("remaining", "-")

                    output.append(f"""• 📌 {nama}
  📈 Kuota  : {quota}
  📉 Sisa   : {remaining}""")
            else:
                output.append("• Tidak ada rincian benefit.")
            
            output.append("━━━━━━━━━━━━━━━━━━━━━━━")

    # Paket SP (jika ada)
    sp_info = info.get("data", {}).get("packageInfoSP", [])
    if sp_info:
        for paket_group in sp_info:
            for paket in paket_group:
                name = paket.get("name", "SP Paket")
                exp = paket.get("expDate", "-")
                benefits = paket.get("benefits", [])

                output.append(f"""🧧 SP Paket : {name}
📅 Kadaluarsa: {exp if exp else "-"}""")

                if benefits:
                    for b in benefits:
                        jenis = b.get("type", "-")
                        nama = b.get("bname", "-")
                        quota = b.get("quota", "-")
                        remaining = b.get("remaining", "-")

                        output.append(f"""• 📌 {nama}
  📈 Kuota  : {quota}
  📉 Sisa   : {remaining}""")
                else:
                    output.append("• Tidak ada rincian benefit.")

                output.append("━━━━━━━━━━━━━━━━━━━━━━━")

    return "\n".join(output)
    
async def check_quota(phone_number, event):
    try:
        url = "https://api.hidepulsa.com/api/tools"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DOR_API_KEY}"
        }
        payload = {
            "action": "cek_dompul",
            "id_telegram": ID_TELEGRAM,
            "password": PASSWORD,
            "nomor_hp": phone_number
        }

        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                result = await response.json()

                if result.get("status") != "success":
                    # Ambil pesan kesalahan dari field 'text' jika ada
                    error_message = result.get("data", {}).get("text", "Gagal mengambil data kuota.")
                    await event.respond(f"❌ {error_message}")
                    return

                info = result["data"]["data"]
                message = format_kuota_response(info)
                await event.respond(message)

    except Exception as e:
        await event.respond(f"❌ Terjadi kesalahan saat ambil data: {str(e)}")


@bot.on(events.CallbackQuery(pattern=b'riwayat_dor(?:_.*)?'))
async def riwayat_dor(event):
    user_id = event.sender_id
    data_parts = event.data.decode().split("_")
    page = int(data_parts[1]) if len(data_parts) > 1 and data_parts[1].isdigit() else 0
    offset = page * 5

    rows = get_riwayat_dor(user_id, offset=offset)
    total = hitung_total_riwayat(user_id)

    if not rows:
        await event.answer("📭 Tidak ada riwayat transaksi.", alert=True)
        return

    teks = f"📑 **Riwayat DOR (halaman {page+1}):**\n\n"
    for row in rows:
        nomor, paket, harga, ref, trx_id, tanggal, waktu = row[1:]
        teks += (
            f"📌 **{paket}**\n"
            f"➣ Nomor : `{nomor}`\n"
            f"➣ Harga : Rp {harga:,}\n"
            f"➣ Ref   : `{ref}`\n"
            f"➣ TRX ID: `{trx_id}`\n"
            f"➣ Tanggal: {tanggal}\n"
            f"➣ Waktu  : {waktu}\n\n"
        )

    buttons = []
    nav_buttons = []
    if page > 0:
        nav_buttons.append(Button.inline("⬅️ Prev", f"riwayat_dor_{page-1}".encode()))
    if offset + 5 < total:
        nav_buttons.append(Button.inline("➡️ Next", f"riwayat_dor_{page+1}".encode()))
    if nav_buttons:
        buttons.append(nav_buttons)

    buttons.append([Button.inline("🔄 Reload", b"riwayat_dor_reload")])
    if get_user_role(user_id) == "admin":
        buttons.append([Button.inline("🗑️ Hapus Semua", b"riwayat_dor_hapus")])

    try:
        message = await event.get_message()
        if message.text != teks:
            await event.edit(teks, buttons=buttons, parse_mode='markdown')
        else:
            await event.answer("⚠️ Tidak ada perubahan.", alert=False)
    except MessageNotModifiedError:
        await event.answer("⚠️ Tidak ada perubahan.", alert=False)


@bot.on(events.CallbackQuery(data=b'unreg_paket'))
async def show_unreg_menu(event):
    user_id = event.sender_id
    pakets = paket_aktif_cache.get(user_id)

    if not pakets:
        return await event.respond("🚫 Tidak ada paket aktif ditemukan.\nSilakan cek kuota terlebih dahulu.")

    buttons = [
        [Button.inline(p['name'], f"unreg_do|{p['id']}")]
        for p in pakets
    ]

    await event.respond("🔻 Pilih paket yang ingin dihentikan:", buttons=buttons)
    
@bot.on(events.CallbackQuery(pattern=b'unreg_do\|'))
async def handle_unreg(event):
    user_id = event.sender_id
    _, short_id = event.data.decode().split("|")

    paket = next((p for p in paket_aktif_cache.get(user_id, []) if p["id"] == short_id), None)

    if not paket:
        return await event.respond("❌ Data paket tidak ditemukan. Silakan cek kuota ulang.")

    session = get_user_session(user_id)
    nomor = session.get("phone") if session else None
    access_token = await get_token_or_refresh(nomor, user_id)
    if not access_token:
        return await event.respond("❌ Gagal mendapatkan token akses.")

    msg = await event.respond("⏳ Menghentikan paket...")

    hasil = await unreg_paket(API_KEY, access_token, paket["encrypted_code"])

    if hasil.get("status"):
        pesan = (
            f"✅ Paket <b>{paket['name']}</b> berhasil dihentikan!\n"
            f"📱 MSISDN: <code>{hasil['data'].get('msisdn')}</code>\n"
            f"🆔 TRX: <code>{hasil['data'].get('trx_id')}</code>"
        )
    else:
        pesan = f"❌ Gagal menghentikan paket:\n<b>{hasil.get('message')}</b>"

    await msg.edit(pesan, parse_mode="html")
        
@bot.on(events.CallbackQuery(data=b'riwayat_dor_reload'))
async def reload_riwayat(event):
    # Simulasikan seperti klik halaman pertama
    event.data = b'riwayat_dor_0'
    await riwayat_dor(event)
@bot.on(events.CallbackQuery(data=b'riwayat_dor_hapus'))
async def hapus_riwayat(event):
    user_id = event.sender_id
    if get_user_role(user_id) != "admin":
        await event.answer("❌ Hanya admin yang dapat menghapus.", alert=True)
        return

    hapus_semua_riwayat(user_id)
    await event.edit("🗑️ Semua riwayat DOR telah dihapus.")
    
@bot.on(events.CallbackQuery(data=b"addon_info"))
async def show_addon_info(event):
    menu_info = """
<b><u>⚠️ Syarat Ketentuan Pembelian Tembak</u></b>
<blockquote>
1. Pastikan tidak ada paket Xtra Combo varian apapun <b>kecuali XC Flex</b> di <code>*808# > INFO > Info Kartu XL-Ku > Cek Kuota</code>. Jika ada, unreg via dial.<br>
2. Kartu tidak boleh dalam masa tenggang.<br>
3. Saldo Ewallet <b>DANA</b> atau <b>PULSA</b>.<br>
4. Pastikan <b>saldo bot</b> cukup.
</blockquote>
<b><u>🏷 Tutorial Pembelian Add-on XCS</u></b>
<blockquote>
1. Minta OTP.<br>
2. Pilih Metode Pembelian AddOn:<br>
A. Metode DANA (Resiko tinggi):<br>
- Pilih Add on yang diinginkan & lakukan pembayaran E-wallet DANA (akan direfund asal bersih dari Xtra Combo).<br>
B. Metode BYPASS (Resiko rendah):<br>
- Tidak membutuhkan saldo E-wallet DANA & PULSA.<br>
3. Beli paket <b>Xtra Combo Spesial</b> (tidak di-refund, memotong saldo DANA atau PULSA: <b>Rp25.000</b>) setelah semua Add On berhasil di-refund.<br>
<b>4. Setelah Xtra Combo Spesial masuk, tunggu 1–2 jam sampai Add On masuk. Selama menunggu, jangan beli apapun di kartu XL.</b>
</blockquote>
<b><u>🏷 Tutorial Pembelian XC 1Gb + XUTS</u></b>
<blockquote>
1. Sediakan  Pulsa: Rp12.500
2. Minta OTP.<br>
3. Pilih XUTP&XUTS.<br>
4. Pilih XUT Super:<br>
<b>4. Setelah selesai tembak, tunggu AddOn Super masuk selama 30 menit - 2 jam. Saat menunggu mohon diamkan kartu, jangan transaksi apapun.</b>
</blockquote>
<b><u>🏷 Tutorial Pembelian XCS + XUTP</u></b>
<blockquote>
1. Sediakan Pulsa  Pulsa: Rp25.000  
2. Minta OTP.<br>
3. Pilih XUTP&XUTS.<br>
4. Pilih XUT Premium:<br>
<b>4. Setelah selesai tembak, tunggu AddOn Premium masuk selama 30 menit - 2 jam. Saat menunggu mohon diamkan kartu, jangan transaksi apapun.</b>
</blockquote>
<b><u>🏷 Tutorial Pembelian Xtra Combo Flex S Promo</u></b>
<blockquote>
1. Sediakan Pulsa  Pulsa: Rp16.000  
2. Minta OTP.<br>
3. Pilih Xtra Combo Flex S Promo.<br>
4. Pilih [DANA] Xtra Combo Flex S Promo lanjutkan pemebelian lalu<br>
4. Pilih [ADD-ON] FLEX pilih addon sesusi kebutuhan lajut pembeliannya
<b>pastikan pembelian xtra comblo flex s terlebih dahulu.</b>
</blockquote>
<b><u>💰 Keterangan Harga DOR</u></b>
<blockquote>
XUTP : Rp7.000<br>
XUTS : Rp7.000<br>
XUT VIDIO Member : Rp5.000<br>
XUT IFLIX Member: Rp5.000<br>
XUT VIDIO Reseller : Rp3.500<br>
XUT IFLIX Reseller : Rp3.500<br>
Add On DANA : Rp500 per paket<br>
Add On BYPAS Member: Rp1.000 per paket<br>
Add On BYPAS Reseller: Rp500 per paket<br>
Add On Flex : Rp3.000 per paket<br>
Xtra Combo Spesial Dana Kuota 1-8GB : Rp6.000<br>
Xtra Combo Spesial Pulsa Tanpa Kuota: Rp5.000<br>
Xtra Combo 1GB + 1GB : Rp5.000<br>
Xtra Combo Flex S Promo : Rp6.000<br>
Masa Aktif XL 1 Bulan : Rp8.000
</blockquote>
<b><u>📌 Catatan</u></b>
<blockquote>
1. Nomor yang di-DOR salah / belum unreg Xtra Combo / salah langkah pembelian <b>tidak ada refund</b>!<br>
2. <b>Add on</b> bersifat hoki-hokian (bisa masuk bisa tidak).<br>
3. Paket <b>Unofficial</b>, <i>tidak ada garansi</i>!
</blockquote>

"""

    buttons = [
        [Button.inline("🔙 Kembali", b"tembakxl")],
    ]

    await event.edit(menu_info, buttons=buttons, parse_mode="html")    
# Pastikan untuk memanggil fungsi `create_user_sessions_table` saat bot dimulai
create_user_sessions_table()
alter_user_table_add_token()
buat_tabel_transaksi_dor()
buat_tabel_paket_aktif()
