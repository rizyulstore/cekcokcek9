#!/bin/bash

# XL Package Manager - Docker Installation Script
# Quick installation using Docker and Docker Compose

set -e

echo "========================================"
echo "  XL Package Manager - Docker Installer"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_warning "Please log out and log back in for Docker permissions to take effect"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Generate random passwords
DB_PASSWORD=$(openssl rand -base64 32)
SESSION_SECRET=$(openssl rand -base64 32)

# Create .env file
print_status "Creating environment configuration..."
cat > .env <<EOF
# Database Configuration
DATABASE_URL=postgresql://xl_package_user:${DB_PASSWORD}@db:5432/xl_package_db
PGDATABASE=xl_package_db
PGUSER=xl_package_user
PGPASSWORD=${DB_PASSWORD}
PGHOST=db
PGPORT=5432

# Flask Configuration
SESSION_SECRET=${SESSION_SECRET}
FLASK_ENV=production
FLASK_DEBUG=False

# Application Configuration
APP_NAME="XL Package Manager"
APP_VERSION="1.0.0"
ADMIN_EMAIL=admin@yourdomain.com

# Docker Compose Variables
DB_PASSWORD=${DB_PASSWORD}
EOF

# Create necessary directories
print_status "Creating directories..."
mkdir -p static/uploads
mkdir -p backups
mkdir -p ssl

# Create docker-compose override for development
if [ "$1" = "dev" ]; then
    print_status "Creating development configuration..."
    cat > docker-compose.override.yml <<EOF
version: '3.8'

services:
  web:
    build: .
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=True
    volumes:
      - .:/app
    command: flask run --host=0.0.0.0 --port=5000 --debug

  nginx:
    ports:
      - "8080:80"
EOF
fi

# Add health check route to main.py if it doesn't exist
if ! grep -q "/health" main.py 2>/dev/null; then
    print_status "Adding health check endpoint..."
    cat >> routes.py <<EOF

@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()}
EOF
fi

# Build and start containers
print_status "Building and starting containers..."
docker-compose build
docker-compose up -d

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 10

# Initialize database and create admin user
print_status "Initializing database..."
docker-compose exec web python create_admin.py

# Get server IP
SERVER_IP=$(curl -s ifconfig.me || echo "localhost")

print_status "Installation completed successfully!"
echo
echo "========================================"
echo "  Docker Installation Summary"
echo "========================================"
echo
echo -e "${GREEN}✓ Docker containers:${NC} Running"
echo -e "${GREEN}✓ Database:${NC} PostgreSQL in container"
echo -e "${GREEN}✓ Web server:${NC} Nginx reverse proxy"
echo -e "${GREEN}✓ Application:${NC} Flask app in container"
echo
echo "========================================"
echo "  Access Information"
echo "========================================"
echo
echo -e "${BLUE}Local URL:${NC} http://localhost"
echo -e "${BLUE}Server URL:${NC} http://$SERVER_IP"
echo -e "${BLUE}Admin Login:${NC}"
echo "  Username: admin"
echo "  Password: admin123"
echo
echo "========================================"
echo "  Docker Commands"
echo "========================================"
echo
echo "View logs:"
echo "  docker-compose logs -f"
echo
echo "View specific service logs:"
echo "  docker-compose logs -f web"
echo "  docker-compose logs -f db"
echo "  docker-compose logs -f nginx"
echo
echo "Restart services:"
echo "  docker-compose restart"
echo
echo "Stop services:"
echo "  docker-compose down"
echo
echo "Update and rebuild:"
echo "  docker-compose down"
echo "  docker-compose build --no-cache"
echo "  docker-compose up -d"
echo
echo "Access database:"
echo "  docker-compose exec db psql -U xl_package_user -d xl_package_db"
echo
echo "Access application shell:"
echo "  docker-compose exec web bash"
echo
echo "========================================"
echo "  Backup and Maintenance"
echo "========================================"
echo
echo "Create database backup:"
echo "  docker-compose exec db pg_dump -U xl_package_user xl_package_db > backup.sql"
echo
echo "Restore database backup:"
echo "  docker-compose exec -T db psql -U xl_package_user xl_package_db < backup.sql"
echo
echo -e "${GREEN}Your XL Package Manager is now running with Docker!${NC}"