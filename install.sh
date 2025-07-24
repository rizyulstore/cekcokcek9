#!/bin/bash

# XL Package Manager - Auto VPS Installation Script
# This script automatically installs and configures the XL Package Manager on a VPS

set -e

echo "========================================"
echo "  XL Package Manager - VPS Installer"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
print_status "Installing required packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    nginx \
    git \
    curl \
    wget \
    unzip \
    supervisor \
    ufw \
    certbot \
    python3-certbot-nginx

# Create application user
APP_USER="xlpackage"
APP_HOME="/home/$APP_USER"
APP_DIR="$APP_HOME/xl-package-manager"

if ! id "$APP_USER" &>/dev/null; then
    print_status "Creating application user: $APP_USER"
    sudo useradd -m -s /bin/bash $APP_USER
    sudo usermod -aG www-data $APP_USER
fi

# Setup PostgreSQL
print_status "Configuring PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
DB_NAME="xl_package_db"
DB_USER="xl_package_user"
DB_PASSWORD=$(openssl rand -base64 32)

sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH ENCRYPTED PASSWORD '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
\q
EOF

# Clone or copy application
print_status "Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# If this script is run from the project directory, copy files
if [ -f "main.py" ] && [ -f "requirements.txt" ]; then
    print_status "Copying application files..."
    sudo cp -r . $APP_DIR/
    sudo chown -R $APP_USER:$APP_USER $APP_DIR
else
    print_warning "Application files not found in current directory"
    print_status "Please upload your application files to $APP_DIR"
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    print_status "Creating requirements.txt..."
    sudo -u $APP_USER cat > $APP_DIR/requirements.txt <<EOF
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.3
Flask-WTF==1.1.1
WTForms==3.0.1
psycopg2-binary==2.9.7
gunicorn==21.2.0
python-dotenv==1.0.0
aiohttp==3.8.5
Pillow==10.0.0
qrcode==7.4.2
pytz==2023.3
email-validator==2.0.0
Werkzeug==2.3.7
SQLAlchemy==2.0.21
EOF
fi

# Setup Python virtual environment
print_status "Creating Python virtual environment..."
sudo -u $APP_USER python3 -m venv $APP_DIR/venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r $APP_DIR/requirements.txt

# Create environment configuration
ENV_FILE="$APP_DIR/.env"
SESSION_SECRET=$(openssl rand -base64 32)

print_status "Creating environment configuration..."
sudo -u $APP_USER cat > $ENV_FILE <<EOF
# Database Configuration
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
PGDATABASE=$DB_NAME
PGUSER=$DB_USER
PGPASSWORD=$DB_PASSWORD
PGHOST=localhost
PGPORT=5432

# Flask Configuration
SESSION_SECRET=$SESSION_SECRET
FLASK_ENV=production
FLASK_DEBUG=False

# Application Configuration
APP_NAME="XL Package Manager"
APP_VERSION="1.0.0"
ADMIN_EMAIL=admin@yourdomain.com

# XL API Configuration (to be configured later)
XL_API_URL=
XL_API_TOKEN=
EOF

# Initialize database
print_status "Initializing database..."
cd $APP_DIR
sudo -u $APP_USER $APP_DIR/venv/bin/python create_admin.py

# Create systemd service
print_status "Creating systemd service..."
sudo cat > /etc/systemd/system/xl-package-manager.service <<EOF
[Unit]
Description=XL Package Manager
After=network.target postgresql.service
Requires=postgresql.service

[Service]
User=$APP_USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 3 --timeout 120 main:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start and enable service
sudo systemctl daemon-reload
sudo systemctl start xl-package-manager
sudo systemctl enable xl-package-manager

# Configure Nginx
print_status "Configuring Nginx..."
sudo cat > /etc/nginx/sites-available/xl-package-manager <<EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /static {
        alias $APP_DIR/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/xl-package-manager /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx

# Configure firewall
print_status "Configuring firewall..."
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw allow 5432/tcp  # PostgreSQL (only if needed for external access)

# Create backup script
print_status "Creating backup script..."
sudo cat > /usr/local/bin/xl-package-backup.sh <<EOF
#!/bin/bash
BACKUP_DIR="/var/backups/xl-package-manager"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Backup database
sudo -u postgres pg_dump $DB_NAME > \$BACKUP_DIR/database_\$DATE.sql

# Backup application files
tar -czf \$BACKUP_DIR/app_\$DATE.tar.gz -C $APP_HOME xl-package-manager

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "*.sql" -mtime +7 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: \$DATE"
EOF

sudo chmod +x /usr/local/bin/xl-package-backup.sh

# Add backup to crontab
print_status "Setting up automated backups..."
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/xl-package-backup.sh") | sudo crontab -

# Create update script
print_status "Creating update script..."
sudo cat > /usr/local/bin/xl-package-update.sh <<EOF
#!/bin/bash
cd $APP_DIR
sudo -u $APP_USER git pull origin main
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt
sudo systemctl restart xl-package-manager
echo "Application updated successfully"
EOF

sudo chmod +x /usr/local/bin/xl-package-update.sh

# Get server IP
SERVER_IP=$(curl -s ifconfig.me || echo "Unable to detect IP")

print_status "Installation completed successfully!"
echo
echo "========================================"
echo "  Installation Summary"
echo "========================================"
echo
echo -e "${GREEN}✓ Database:${NC} PostgreSQL configured"
echo -e "${GREEN}✓ Application:${NC} Installed in $APP_DIR"
echo -e "${GREEN}✓ Web Server:${NC} Nginx configured"
echo -e "${GREEN}✓ Service:${NC} Systemd service created"
echo -e "${GREEN}✓ Firewall:${NC} UFW configured"
echo -e "${GREEN}✓ Backups:${NC} Daily automated backups"
echo
echo "========================================"
echo "  Access Information"
echo "========================================"
echo
echo -e "${BLUE}Server IP:${NC} $SERVER_IP"
echo -e "${BLUE}Web URL:${NC} http://$SERVER_IP"
echo -e "${BLUE}Admin Login:${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo
echo "========================================"
echo "  Important Files"
echo "========================================"
echo
echo -e "${BLUE}Application Directory:${NC} $APP_DIR"
echo -e "${BLUE}Environment File:${NC} $APP_DIR/.env"
echo -e "${BLUE}Service Config:${NC} /etc/systemd/system/xl-package-manager.service"
echo -e "${BLUE}Nginx Config:${NC} /etc/nginx/sites-available/xl-package-manager"
echo
echo "========================================"
echo "  Useful Commands"
echo "========================================"
echo
echo "Check service status:"
echo "  sudo systemctl status xl-package-manager"
echo
echo "View logs:"
echo "  sudo journalctl -f -u xl-package-manager"
echo
echo "Restart application:"
echo "  sudo systemctl restart xl-package-manager"
echo
echo "Update application:"
echo "  sudo /usr/local/bin/xl-package-update.sh"
echo
echo "Manual backup:"
echo "  sudo /usr/local/bin/xl-package-backup.sh"
echo
echo "========================================"
echo "  Security Recommendations"
echo "========================================"
echo
echo -e "${YELLOW}1.${NC} Change default admin password immediately"
echo -e "${YELLOW}2.${NC} Configure domain and SSL certificate:"
echo "   sudo certbot --nginx -d yourdomain.com"
echo -e "${YELLOW}3.${NC} Update XL API credentials in $APP_DIR/.env"
echo -e "${YELLOW}4.${NC} Consider disabling PostgreSQL external access if not needed"
echo
echo -e "${GREEN}Installation completed! Your XL Package Manager is ready to use.${NC}"