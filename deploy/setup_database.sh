#!/bin/bash

# Database Setup Script for GoatMorpho
# Sets up PostgreSQL on Django instance

set -e

echo "🐘 Setting up PostgreSQL database for GoatMorpho..."

# Install PostgreSQL
echo "📦 Installing PostgreSQL..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
echo "👤 Creating database and user..."
sudo -u postgres psql << EOF
CREATE USER goat_morpho_user WITH ENCRYPTED PASSWORD 'secure_password_change_this';
CREATE DATABASE goat_morpho OWNER goat_morpho_user;
GRANT ALL PRIVILEGES ON DATABASE goat_morpho TO goat_morpho_user;
ALTER USER goat_morpho_user CREATEDB;
\q
EOF

# Configure PostgreSQL
echo "⚙️ Configuring PostgreSQL..."
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = 'localhost'/" /etc/postgresql/*/main/postgresql.conf

# Update pg_hba.conf for local connections
sudo tee -a /etc/postgresql/*/main/pg_hba.conf << EOF

# GoatMorpho application access
local   goat_morpho     goat_morpho_user                        md5
host    goat_morpho     goat_morpho_user     127.0.0.1/32       md5
host    goat_morpho     goat_morpho_user     ::1/128            md5
EOF

# Restart PostgreSQL
sudo systemctl restart postgresql

# Test connection
echo "🧪 Testing database connection..."
sudo -u postgres psql -d goat_morpho -U goat_morpho_user -h localhost -c "SELECT version();" || echo "⚠️  Test connection failed - check credentials"

echo "✅ PostgreSQL setup complete!"
echo ""
echo "📋 Database Details:"
echo "   Database: goat_morpho"
echo "   User: goat_morpho_user"
echo "   Password: secure_password_change_this"
echo "   Host: localhost"
echo "   Port: 5432"
echo ""
echo "⚠️  Remember to:"
echo "1. Change the default password in production"
echo "2. Update the password in /opt/goatmorpho/.env"
echo "3. Run Django migrations after updating settings"
