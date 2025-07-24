# XL Package Manager

## Overview

This is a Flask-based web application for managing XL mobile data packages. The system allows users to purchase data packages, manage their account balance through top-ups, and track transaction history. It includes role-based access control with different user tiers (member, reseller, admin) and integrates with XL's API for package purchasing.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a traditional Flask MVC pattern with the following structure:

- **Frontend**: Server-side rendered HTML templates using Jinja2, styled with Bootstrap CSS framework
- **Backend**: Flask web framework with SQLAlchemy ORM for database operations
- **Database**: SQLite (development) with support for PostgreSQL (production via DATABASE_URL)
- **Authentication**: Flask-Login for session management
- **Forms**: WTForms for form handling and validation

## Key Components

### Models (`models.py`)
- **User**: Core user entity with role-based permissions (member/reseller/admin), balance tracking, and XL API integration fields
- **Package**: Data package definitions with different pricing tiers for members and resellers
- **Transaction**: Purchase history and status tracking
- **TopUp**: Balance addition records
- **SystemSettings**: Application configuration storage

### Authentication & Authorization
- Flask-Login handles user sessions
- Role-based access control with three tiers:
  - Members: Basic package purchasing
  - Resellers: Discounted pricing
  - Admins: Full system management
- Password hashing using Werkzeug security utilities

### XL API Integration (`xl_api.py`)
- Async HTTP client using aiohttp for XL API communication
- Token management and validation
- Package purchase automation
- Session persistence for authenticated XL accounts

### Forms & Validation (`forms.py`)
- WTForms for server-side validation
- Custom validators for phone numbers and existing user checks
- Separate forms for registration, login, package management, purchases, and top-ups

### Utilities (`utils.py`)
- Currency formatting for Indonesian Rupiah
- Phone number validation and normalization for Indonesian numbers
- Timezone handling for Indonesian time zones (WIB, WITA, WIT)

## Data Flow

1. **User Registration/Login**: Users register with username, email, and phone number, then authenticate to access the system
2. **Balance Management**: Users can top up their balance through various payment methods
3. **Package Purchase**: Users browse available packages, select based on their role pricing, and initiate purchases
4. **XL API Integration**: System communicates with XL's API to execute package purchases on user's mobile numbers
5. **Transaction Tracking**: All purchases and top-ups are logged with status tracking

## External Dependencies

### Third-Party Services
- **XL API**: Core integration for package purchasing and account management
- **Payment Gateways**: QRIS and bank transfer support for balance top-ups

### Python Packages
- Flask ecosystem (Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF)
- SQLAlchemy for database ORM
- aiohttp for async HTTP requests
- Werkzeug for security utilities
- WTForms for form handling

### Frontend Dependencies
- Bootstrap CSS framework for responsive UI
- Font Awesome for icons
- Custom CSS for application-specific styling
- JavaScript for client-side interactions

## Deployment Strategy

The application is designed for flexible deployment:

- **Development**: SQLite database with Flask development server
- **Production**: PostgreSQL database via DATABASE_URL environment variable
- **Environment Configuration**: Uses environment variables for sensitive data (API keys, database URLs, session secrets)
- **Proxy Support**: Includes ProxyFix middleware for deployment behind reverse proxies
- **Session Management**: Configurable session security with environment-based secret keys

The application structure supports containerized deployment with proper environment variable configuration for different deployment environments.

## Recent Changes

### July 23, 2025 - VPS Auto Installation Capability Added

- **Automatic VPS Installation**: Created comprehensive installation script (`install.sh`) for one-command VPS deployment
- **Docker Support**: Added Docker and Docker Compose configurations for containerized deployment
- **Production Configuration**: Implemented Nginx reverse proxy, SSL support, and security configurations
- **Monitoring & Backup**: Added health check endpoints, automated backup scripts, and monitoring capabilities
- **Multi-deployment Options**: Three installation methods available:
  1. Automatic VPS installer with full system configuration
  2. Docker-based installation for container environments
  3. Manual installation for custom setups

### Installation Features Added:
- PostgreSQL database setup with secure credentials
- Nginx reverse proxy with security headers and rate limiting
- Systemd service configuration for auto-start
- UFW firewall configuration
- SSL/TLS certificate support via Let's Encrypt
- Automated daily backups with retention policy
- Update scripts for easy maintenance
- Health check monitoring endpoint
- Environment-based configuration management