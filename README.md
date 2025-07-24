# XL Package Manager

Aplikasi web manajemen paket XL dengan sistem admin panel, kontrol akses berbasis peran, dan fungsionalitas shooting paket otomatis.

## 🚀 Fitur Utama

- **Sistem Autentikasi**: Registrasi dan login dengan validasi email
- **Kontrol Akses Berbasis Peran**: Admin, Reseller, dan Member dengan harga berbeda
- **Manajemen Paket**: CRUD paket data XL dengan harga tier yang berbeda
- **Shooting Paket Otomatis**: Integrasi dengan API XL untuk pembelian paket
- **Admin Panel**: Pengelolaan paket, member, saldo, dan statistik sistem
- **Sistem Top-up Saldo**: Berbagai metode pembayaran (QRIS, transfer bank)
- **Riwayat Transaksi**: Pelacakan semua pembelian dan top-up
- **UI Professional**: Tema dark Bootstrap yang responsif

## 🛠️ Teknologi

- **Backend**: Flask + SQLAlchemy ORM
- **Database**: PostgreSQL (production) / SQLite (development)
- **Frontend**: Server-side rendering dengan Jinja2 + Bootstrap
- **Authentication**: Flask-Login untuk session management
- **Forms**: WTForms untuk validasi
- **API Integration**: aiohttp untuk komunikasi dengan XL API

## 📦 Instalasi

### Instalasi Otomatis VPS

Untuk instalasi lengkap di VPS dengan satu perintah:

```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/xl-package-manager/main/install.sh | bash
```

Script ini akan:
- Menginstall semua dependensi sistem
- Mengkonfigurasi PostgreSQL
- Setup environment variables
- Mengkonfigurasi Nginx sebagai reverse proxy
- Membuat systemd service
- Setup firewall dan keamanan
- Mengkonfigurasi backup otomatis
- Membuat akun admin default

### Instalasi dengan Docker

Untuk instalasi cepat menggunakan Docker:

```bash
# Clone repository
git clone https://github.com/your-repo/xl-package-manager.git
cd xl-package-manager

# Jalankan installer Docker
chmod +x docker-install.sh
./docker-install.sh
```

Atau untuk development mode:

```bash
./docker-install.sh dev
```

### Instalasi Manual

1. **Clone Repository**
```bash
git clone https://github.com/your-repo/xl-package-manager.git
cd xl-package-manager
```

2. **Setup Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Setup Database**
```bash
# PostgreSQL (recommended)
createdb xl_package_db
export DATABASE_URL="postgresql://username:password@localhost/xl_package_db"

# Atau SQLite untuk development
export DATABASE_URL="sqlite:///xl_package.db"
```

5. **Setup Environment Variables**
```bash
cp .env.example .env
# Edit .env dengan konfigurasi Anda
```

6. **Initialize Database**
```bash
python create_admin.py
```

7. **Run Application**
```bash
# Development
flask run --host=0.0.0.0 --port=5000

# Production
gunicorn --bind 0.0.0.0:5000 main:app
```

## 🔐 Login Default

Setelah instalasi, gunakan kredensial berikut untuk login sebagai admin:

- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@xlpackage.com`

⚠️ **Penting**: Ganti password default setelah login pertama!

## 🏗️ Struktur Aplikasi

```
xl-package-manager/
├── app.py                 # Konfigurasi Flask utama
├── main.py               # Entry point aplikasi
├── models.py             # Model database SQLAlchemy
├── routes.py             # Route handlers
├── forms.py              # Form WTForms
├── xl_api.py             # Integrasi XL API
├── utils.py              # Utility functions
├── create_admin.py       # Script create admin
├── templates/            # Template Jinja2
├── static/               # File static (CSS, JS, images)
├── install.sh            # Auto installer VPS
├── docker-install.sh     # Docker installer
├── docker-compose.yml    # Docker compose config
├── Dockerfile            # Docker image config
├── nginx.conf            # Nginx configuration
└── requirements.txt      # Python dependencies
```

## 🎯 Penggunaan

### Admin Panel

Sebagai admin, Anda dapat:
- Mengelola paket data (tambah, edit, hapus)
- Mengatur member dan reseller
- Mengelola saldo member
- Melihat statistik dan laporan
- Konfigurasi sistem

### Member/Reseller

Sebagai member atau reseller:
- Membeli paket data XL
- Top-up saldo melalui berbagai metode
- Melihat riwayat transaksi
- Mengelola profil dan akun XL

### Integrasi XL API

Aplikasi menggunakan API XL untuk:
- Validasi nomor XL
- Pembelian paket data otomatis
- Cek status transaksi
- Manajemen akun XL

## 🔧 Konfigurasi

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Flask
SESSION_SECRET=your-secret-key
FLASK_ENV=production

# XL API
XL_API_URL=https://api.xl.co.id
XL_API_TOKEN=your-xl-api-token
```

### Nginx Configuration

Untuk production, gunakan Nginx sebagai reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🔒 Keamanan

### SSL/HTTPS

Untuk mengaktifkan SSL dengan Let's Encrypt:

```bash
sudo certbot --nginx -d yourdomain.com
```

### Firewall

Setup firewall dengan UFW:

```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
```

### Database Security

- Gunakan password yang kuat untuk database
- Batasi akses database hanya dari localhost jika memungkinkan
- Enable SSL untuk koneksi database di production

## 📊 Monitoring

### Log Files

- Application logs: `journalctl -f -u xl-package-manager`
- Nginx logs: `/var/log/nginx/access.log` dan `/var/log/nginx/error.log`
- Database logs: Sesuai konfigurasi PostgreSQL

### Health Check

Aplikasi menyediakan endpoint health check di `/health`

### Backup

Script backup otomatis tersedia di `/usr/local/bin/xl-package-backup.sh` yang akan:
- Backup database PostgreSQL
- Backup file aplikasi
- Menjalankan cleanup backup lama

## 🔄 Update

### Manual Update

```bash
cd /path/to/xl-package-manager
git pull origin main
pip install -r requirements.txt
sudo systemctl restart xl-package-manager
```

### Auto Update Script

```bash
sudo /usr/local/bin/xl-package-update.sh
```

### Docker Update

```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone dan setup
git clone https://github.com/your-repo/xl-package-manager.git
cd xl-package-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup database development
export DATABASE_URL="sqlite:///xl_package.db"
python create_admin.py

# Run development server
flask run --debug
```

### Docker Development

```bash
./docker-install.sh dev
```

## 📝 API Documentation

### Authentication

Semua endpoint memerlukan autentikasi kecuali halaman publik.

### Main Endpoints

- `GET /` - Homepage
- `GET /dashboard` - User dashboard
- `GET /packages` - Daftar paket
- `POST /purchase` - Beli paket
- `GET /admin` - Admin panel (admin only)

## 🤝 Contributing

1. Fork repository
2. Buat feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Support

Untuk bantuan dan support:
- Email: support@xlpackage.com
- Issues: GitHub Issues
- Documentation: [Wiki](https://github.com/your-repo/xl-package-manager/wiki)

## 🙏 Acknowledgments

- Flask dan ekosistem Python
- Bootstrap untuk UI framework
- PostgreSQL untuk database
- Nginx untuk web server
- Docker untuk containerization