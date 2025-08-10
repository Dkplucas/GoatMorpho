#!/bin/bash
# GoatMorpho Production Deployment Script with Redis
# Run this script on your production server

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="goatmorpho"
APP_DIR="/var/www/goatmorpho"
USER="www-data"
PYTHON_VERSION="3.11"
REDIS_PASSWORD=""
DB_PASSWORD=""

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to generate secure password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root"
    exit 1
fi

print_status "Starting GoatMorpho production deployment with Redis..."

# Get Redis password from user
read -s -p "Enter Redis password (or press Enter to generate): " REDIS_PASSWORD
echo
if [ -z "$REDIS_PASSWORD" ]; then
    REDIS_PASSWORD=$(generate_password)
    print_success "Generated Redis password: $REDIS_PASSWORD"
fi

# Use existing database credentials
DB_PASSWORD="123456789"
print_status "Using existing PostgreSQL database with:"
print_status "  Database: goat_morpho"
print_status "  User: goat_morpho_user"
print_status "  Password: 123456789"

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Detect available Python version
print_status "Detecting available Python version..."
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON_VERSION="3.12"
elif command -v python3.11 >/dev/null 2>&1; then
    PYTHON_VERSION="3.11"
elif command -v python3.10 >/dev/null 2>&1; then
    PYTHON_VERSION="3.10"
elif command -v python3.9 >/dev/null 2>&1; then
    PYTHON_VERSION="3.9"
elif apt-cache search python3.12-dev | grep -q python3.12-dev; then
    PYTHON_VERSION="3.12"
elif apt-cache search python3.11-dev | grep -q python3.11-dev; then
    PYTHON_VERSION="3.11"
elif apt-cache search python3.10-dev | grep -q python3.10-dev; then
    PYTHON_VERSION="3.10"
else
    # Fallback to system python3
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+' | head -1)
    if [ -z "$PYTHON_VERSION" ]; then
        PYTHON_VERSION="3.12"  # Default fallback
    fi
fi

print_success "Using Python $PYTHON_VERSION"

# Install required packages (compatible with different Ubuntu versions)
print_status "Installing required system packages..."

# Core packages that should be available on most systems
print_status "Installing core packages..."
sudo apt install -y \
    redis-server \
    nginx \
    git curl wget \
    build-essential \
    libpq-dev \
    supervisor

# Install Python packages with fallback
print_status "Installing Python packages..."
# Try version-specific packages first
if sudo apt install -y python${PYTHON_VERSION} python${PYTHON_VERSION}-venv python${PYTHON_VERSION}-dev python3-pip 2>/dev/null; then
    print_success "Installed Python ${PYTHON_VERSION} packages"
else
    print_warning "Version-specific Python packages not available, using generic python3"
    sudo apt install -y python3 python3-venv python3-dev python3-pip
fi

# Additional packages - install if available
print_status "Installing additional packages (if available)..."

# Try to install OpenGL libraries (for OpenCV)
if apt-cache search libgl1-mesa-glx | grep -q libgl1-mesa-glx; then
    sudo apt install -y libgl1-mesa-glx
elif apt-cache search libgl1-mesa-dev | grep -q libgl1-mesa-dev; then
    sudo apt install -y libgl1-mesa-dev
else
    print_warning "OpenGL libraries not found - OpenCV may have display issues"
fi

# Install other optional packages
for pkg in libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 libgtk-3-0; do
    if apt-cache search $pkg | grep -q "^$pkg "; then
        sudo apt install -y $pkg
    else
        print_warning "Package $pkg not available - skipping"
    fi
done

# Test existing PostgreSQL connection
print_status "Testing existing PostgreSQL connection..."
if PGPASSWORD="123456789" psql -h localhost -U goat_morpho_user -d goat_morpho -c "SELECT version();" > /dev/null 2>&1; then
    print_success "PostgreSQL connection successful"
else
    print_error "Cannot connect to existing PostgreSQL database"
    print_error "Please verify the database is running and credentials are correct:"
    print_error "  Database: goat_morpho"
    print_error "  User: goat_morpho_user"
    print_error "  Password: 123456789"
    print_error "  Host: localhost"
    print_error "  Port: 5432"
    exit 1
fi

# Configure Redis
print_status "Configuring Redis..."
sudo cp /etc/redis/redis.conf /etc/redis/redis.conf.backup

# Update Redis configuration
sudo tee /etc/redis/redis.conf > /dev/null << EOF
bind 127.0.0.1 ::1
port 6379
timeout 0
tcp-keepalive 300
daemonize yes
supervised systemd
pidfile /var/run/redis/redis-server.pid
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
requirepass $REDIS_PASSWORD
maxclients 10000
maxmemory 1gb
maxmemory-policy allkeys-lru
maxmemory-samples 5
lazyfree-lazy-eviction yes
lazyfree-lazy-expire yes
lazyfree-lazy-server-del yes
appendonly no
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
hz 10
dynamic-hz yes
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
EOF

# Start and enable Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Test Redis
print_status "Testing Redis connection..."
if redis-cli -a "$REDIS_PASSWORD" ping | grep -q "PONG"; then
    print_success "Redis is working correctly"
else
    print_error "Redis connection failed"
    exit 1
fi

# Setup application directory
print_status "Setting up application directory..."
sudo mkdir -p $APP_DIR
sudo chown $USER:$USER $APP_DIR

# Clone or update application code
if [ -d "$APP_DIR/.git" ]; then
    print_status "Updating application code..."
    cd $APP_DIR
    git pull origin master
else
    print_status "Cloning application code..."
    git clone https://github.com/Dkplucas/GoatMorpho.git $APP_DIR
    cd $APP_DIR
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
# Try version-specific Python first, then fallback to python3
if command -v python${PYTHON_VERSION} >/dev/null 2>&1; then
    python${PYTHON_VERSION} -m venv venv
elif command -v python3 >/dev/null 2>&1; then
    python3 -m venv venv
else
    python -m venv venv
fi
source venv/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip setuptools wheel

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements_fixed.txt

# Create environment file
print_status "Creating environment configuration..."
cat > .env << EOF
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=$(generate_password)
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
REDIS_MAX_CONNECTIONS=50
CACHE_TIMEOUT=600
SESSION_COOKIE_AGE=1209600
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@goatmorpho.info
ENABLE_ADVANCED_CV=True
ENABLE_BREED_MODELS=True
CONFIDENCE_THRESHOLD=0.7
EOF

# Set proper file permissions
sudo chown -R $USER:$USER $APP_DIR
chmod 600 .env

# Run Django migrations
print_status "Running Django migrations..."
python manage.py migrate

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Create media directories
print_status "Creating media directories..."
mkdir -p media/goat_images/{original,processed,samples}
sudo chown -R $USER:$USER media/

# Test Redis with Django
print_status "Testing Django Redis integration..."
python manage.py check_redis

# Create superuser
print_status "Creating Django superuser..."
echo "Please create a superuser account:"
python manage.py createsuperuser

# Setup Gunicorn service
print_status "Setting up Gunicorn service..."
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
    --workers 3 \\
    --timeout 120 \\
    --bind unix:$APP_DIR/goatmorpho.sock \\
    goat_morpho.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start Gunicorn
sudo systemctl daemon-reload
sudo systemctl enable goatmorpho
sudo systemctl start goatmorpho

# Setup Nginx
print_status "Setting up Nginx..."
sudo tee /etc/nginx/sites-available/goatmorpho > /dev/null << EOF
server {
    listen 80;
    server_name goatmorpho.info www.goatmorpho.info 130.61.39.212;
    
    client_max_body_size 20M;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root $APP_DIR;
        expires 1y;
        add_header Cache-Control "public, immutable";
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

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/goatmorpho /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Setup Redis monitoring
print_status "Setting up Redis monitoring..."
sudo cp monitor_redis.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/monitor_redis.sh

# Update monitoring script with correct password
sudo sed -i "s/your_secure_redis_password_here/$REDIS_PASSWORD/g" /usr/local/bin/monitor_redis.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor_redis.sh") | crontab -

# Setup log rotation
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/goatmorpho > /dev/null << EOF
$APP_DIR/goat_morpho.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        systemctl reload goatmorpho
    endscript
}

/var/log/redis/redis-server.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        systemctl reload redis-server
    endscript
}
EOF

# Final checks
print_status "Running final system checks..."

# Check services
for service in postgresql redis-server goatmorpho nginx; do
    if sudo systemctl is-active --quiet $service; then
        print_success "$service is running"
    else
        print_error "$service is not running"
    fi
done

# Check Redis connection through Django
if python manage.py check_redis --verbose | grep -q "Redis connection successful"; then
    print_success "Django Redis integration is working"
else
    print_warning "Django Redis integration may have issues"
fi

print_success "GoatMorpho deployment completed!"
print_status "Configuration summary:"
echo "  - App Directory: $APP_DIR"
echo "  - Database: PostgreSQL (goat_morpho)"
echo "  - Cache: Redis with password protection"
echo "  - Web Server: Nginx + Gunicorn"
echo "  - Monitoring: Redis health checks every 5 minutes"
echo ""
print_status "Important credentials (save these securely):"
echo "  - Redis Password: $REDIS_PASSWORD"
echo "  - Database: Using existing PostgreSQL (goat_morpho/goat_morpho_user/123456789)"
echo ""
print_status "Next steps:"
echo "  1. Configure SSL certificate: sudo certbot --nginx -d goatmorpho.info"
echo "  2. Update DNS to point to this server"
echo "  3. Configure email settings in .env file"
echo "  4. Test the application: http://goatmorpho.info"
echo ""
print_success "Deployment completed successfully! 🎉"
