#!/bin/bash
# GoatMorpho Simple Deployment Script - Compatible with Ubuntu 18.04/20.04/22.04
# Use this if the main deployment script fails due to package availability

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
APP_NAME="goatmorpho"
APP_DIR="/var/www/goatmorpho"
USER="www-data"

print_status "Starting GoatMorpho simple deployment..."

# Check Ubuntu version
UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
print_status "Detected Ubuntu version: $UBUNTU_VERSION"

# Update system
print_status "Updating system packages..."
sudo apt update

# Install basic packages
print_status "Installing basic packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    redis-server \
    nginx \
    git \
    curl \
    wget \
    build-essential \
    pkg-config

# Install PostgreSQL client if not present
if ! command -v psql >/dev/null 2>&1; then
    print_status "Installing PostgreSQL client..."
    sudo apt install -y postgresql-client
fi

# Try to install additional packages
print_status "Installing additional packages..."
for pkg in libpq-dev libffi-dev libssl-dev; do
    if sudo apt install -y $pkg; then
        print_success "Installed $pkg"
    else
        print_warning "Could not install $pkg - continuing anyway"
    fi
done

# Get Redis password
read -s -p "Enter Redis password (or press Enter to use default): " REDIS_PASSWORD
echo
if [ -z "$REDIS_PASSWORD" ]; then
    REDIS_PASSWORD="goatmorpho2024"
    print_success "Using default Redis password: $REDIS_PASSWORD"
fi

# Test existing PostgreSQL connection
print_status "Testing existing PostgreSQL connection..."
if PGPASSWORD="123456789" psql -h localhost -U goat_morpho_user -d goat_morpho -c "SELECT version();" > /dev/null 2>&1; then
    print_success "PostgreSQL connection successful"
else
    print_error "Cannot connect to existing PostgreSQL database"
    print_error "Please ensure PostgreSQL is running and accessible"
    exit 1
fi

# Configure Redis (simple configuration)
print_status "Configuring Redis..."
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup 2>/dev/null || true

# Create a simple Redis configuration
sudo tee /etc/redis/redis.conf > /dev/null << EOF
bind 127.0.0.1
port 6379
timeout 0
tcp-keepalive 300
daemonize yes
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
save 300 10
save 60 10000
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
requirepass $REDIS_PASSWORD
maxmemory 512mb
maxmemory-policy allkeys-lru
EOF

# Start Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Test Redis
print_status "Testing Redis..."
if redis-cli -a "$REDIS_PASSWORD" ping | grep -q "PONG"; then
    print_success "Redis is working"
else
    print_error "Redis test failed"
    exit 1
fi

# Setup application directory
print_status "Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone or update application
if [ -d "$APP_DIR/.git" ]; then
    print_status "Updating application..."
    cd $APP_DIR
    git pull origin master
else
    print_status "Cloning application..."
    git clone https://github.com/Dkplucas/GoatMorpho.git $APP_DIR
    cd $APP_DIR
fi

# Create virtual environment with available Python
print_status "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install basic Python packages first
print_status "Installing basic Python packages..."
pip install wheel setuptools

# Install Django and basic requirements
print_status "Installing core requirements..."
pip install \
    Django==5.2.4 \
    psycopg2-binary \
    redis \
    django-redis \
    gunicorn \
    whitenoise

# Try to install other requirements
print_status "Installing additional requirements..."
if [ -f "requirements_fixed.txt" ]; then
    # Install packages one by one to avoid complete failure
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^# ]] && [[ -n "$line" ]]; then
            package=$(echo "$line" | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'<' -f1)
            if pip install "$line"; then
                print_success "Installed $package"
            else
                print_warning "Could not install $package - skipping"
            fi
        fi
    done < requirements_fixed.txt
else
    print_warning "requirements_fixed.txt not found"
fi

# Create environment file
print_status "Creating environment file..."
cat > .env << EOF
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-50)
DB_NAME=goat_morpho
DB_USER=goat_morpho_user
DB_PASSWORD=123456789
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_DB=1
REDIS_TIMEOUT=5
REDIS_MAX_CONNECTIONS=20
CACHE_TIMEOUT=600
SESSION_COOKIE_AGE=1209600
EOF

chmod 600 .env

# Run Django setup
print_status "Running Django migrations..."
python manage.py migrate

print_status "Collecting static files..."
python manage.py collectstatic --noinput

print_status "Creating media directories..."
mkdir -p media/goat_images/{original,processed,samples}
sudo chown -R $USER:$USER media/

# Test Django with Redis
print_status "Testing Django Redis connection..."
if python manage.py check; then
    print_success "Django check passed"
else
    print_warning "Django check had issues - but continuing"
fi

# Create systemd service
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/goatmorpho.service > /dev/null << EOF
[Unit]
Description=GoatMorpho Gunicorn daemon
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --workers 2 \\
    --timeout 120 \\
    --bind unix:$APP_DIR/goatmorpho.sock \\
    goat_morpho.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable goatmorpho
sudo systemctl start goatmorpho

# Configure Nginx
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/goatmorpho > /dev/null << EOF
server {
    listen 80;
    server_name goatmorpho.info www.goatmorpho.info 130.61.39.212 _;
    
    client_max_body_size 20M;
    
    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        root $APP_DIR;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location /media/ {
        root $APP_DIR;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/goatmorpho.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/goatmorpho /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Final checks
print_status "Performing final checks..."

# Check services
for service in redis-server goatmorpho nginx; do
    if sudo systemctl is-active --quiet $service; then
        print_success "$service is running"
    else
        print_error "$service is not running"
        sudo systemctl status $service
    fi
done

# Create admin user
print_status "Creating Django superuser..."
echo "Please create an admin user:"
python manage.py createsuperuser || print_warning "Superuser creation skipped"

print_success "Simple deployment completed!"
print_status "Access your application at: http://$(curl -s ifconfig.me || echo 'your-server-ip')"
print_status "Redis password: $REDIS_PASSWORD"
print_status ""
print_status "Next steps:"
print_status "1. Configure SSL: sudo apt install certbot python3-certbot-nginx && sudo certbot --nginx"
print_status "2. Update DNS to point to this server"
print_status "3. Configure email settings in .env"
print_status ""
print_success "🎉 GoatMorpho is now running!"
