#!/bin/bash

# Single Instance Deployment Script for GoatMorpho
# Oracle Cloud Infrastructure - VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)
# Domain: goatmorpho.info (130.61.39.212)
# 
# This script sets up everything on one instance:
# - PostgreSQL Database
# - Redis Cache
# - Django Application
# - CV Processing Service
# - Nginx Web Server
# - SSL Certificate

set -e  # Exit on any error

# Configuration
DOMAIN="goatmorpho.info"
PUBLIC_IP="130.61.39.212"
PRIVATE_IP="10.0.0.163"
APP_USER="goat_morpho"
APP_DIR="/opt/goat_morpho"
PYTHON_VERSION="3.11"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log_info "Starting GoatMorpho single instance deployment..."
log_info "Instance: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)"
log_info "Domain: $DOMAIN ($PUBLIC_IP)"

# Update system packages
log_info "Updating system packages..."
apt update && apt upgrade -y

# Detect Python version
log_info "Detecting available Python version..."
if command -v python3.12 &> /dev/null; then
    PYTHON_VERSION="3.12"
    PYTHON_CMD="python3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_VERSION="3.11"
    PYTHON_CMD="python3.11"
else
    PYTHON_VERSION="3"
    PYTHON_CMD="python3"
fi
log_info "Using Python $PYTHON_VERSION"

# Install essential packages
log_info "Installing essential packages..."
apt install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    postgresql \
    postgresql-contrib \
    redis-server \
    nginx \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    pkg-config \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libjpeg-dev \
    libpng-dev \
    libopencv-dev \
    certbot \
    python3-certbot-nginx \
    htop \
    ufw \
    fail2ban

# ARM64 optimized packages for Oracle Cloud
log_info "Installing ARM64 optimized packages..."
apt install -y \
    libblas3 \
    liblapack3 \
    libatlas-base-dev \
    gfortran \
    libhdf5-dev

# Configure PostgreSQL
log_info "Configuring PostgreSQL..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE goat_morpho;
CREATE USER goat_morpho_user WITH PASSWORD 'GoatMorpho2024!Secure';
ALTER ROLE goat_morpho_user SET client_encoding TO 'utf8';
ALTER ROLE goat_morpho_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE goat_morpho_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE goat_morpho TO goat_morpho_user;
\q
EOF

# Optimize PostgreSQL for 24GB RAM instance
log_info "Optimizing PostgreSQL configuration..."
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG="/etc/postgresql/$PG_VERSION/main/postgresql.conf"

# Backup original config
cp "$PG_CONFIG" "$PG_CONFIG.backup"

# Apply optimizations for 24GB RAM
cat >> "$PG_CONFIG" << EOF

# GoatMorpho optimizations for 24GB RAM instance
shared_buffers = 6GB                    # 25% of RAM
effective_cache_size = 18GB             # 75% of RAM
maintenance_work_mem = 1GB              # For maintenance operations
work_mem = 64MB                         # For complex queries
wal_buffers = 64MB                      # WAL buffer size
checkpoint_completion_target = 0.9      # Checkpoint completion target
max_connections = 200                   # Maximum connections
random_page_cost = 1.1                 # SSD optimization
effective_io_concurrency = 200         # Concurrent I/O operations
EOF

systemctl restart postgresql

# Configure Redis
log_info "Configuring Redis..."
systemctl start redis-server
systemctl enable redis-server

# Optimize Redis for 24GB RAM (allocate 2GB)
REDIS_CONFIG="/etc/redis/redis.conf"
cp "$REDIS_CONFIG" "$REDIS_CONFIG.backup"

sed -i 's/# maxmemory <bytes>/maxmemory 2gb/' "$REDIS_CONFIG"
sed -i 's/# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' "$REDIS_CONFIG"
sed -i 's/save 900 1/# save 900 1/' "$REDIS_CONFIG"
sed -i 's/save 300 10/# save 300 10/' "$REDIS_CONFIG"
sed -i 's/save 60 10000/# save 60 10000/' "$REDIS_CONFIG"

systemctl restart redis-server

# Create application user
log_info "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -s /bin/bash "$APP_USER"
fi

# Create application directory
log_info "Setting up application directory..."
mkdir -p "$APP_DIR"
chown "$APP_USER:$APP_USER" "$APP_DIR"

# Clone or copy application code
log_info "Setting up application code..."
if [ -d "/tmp/goat_morpho_source" ]; then
    cp -r /tmp/goat_morpho_source/* "$APP_DIR/"
else
    log_warning "Application source not found in /tmp/goat_morpho_source"
    log_info "Please copy your GoatMorpho source code to $APP_DIR"
fi

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Setup Python virtual environment
log_info "Setting up Python virtual environment..."
sudo -u "$APP_USER" $PYTHON_CMD -m venv "$APP_DIR/venv"

# Install Python dependencies
log_info "Installing Python dependencies..."
sudo -u "$APP_USER" bash << EOF
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip setuptools wheel

# Install core dependencies
pip install \
    Django==5.2.4 \
    psycopg2-binary \
    redis \
    djangorestframework \
    django-cors-headers \
    whitenoise \
    gunicorn[gevent] \
    celery[redis] \
    Pillow \
    numpy \
    opencv-python-headless \
    mediapipe \
    tensorflow-cpu \
    scikit-learn \
    pandas \
    openpyxl

# Install additional requirements if available
if [ -f "$APP_DIR/requirements.txt" ]; then
    pip install -r "$APP_DIR/requirements.txt"
fi
EOF

# Create environment file
log_info "Creating environment configuration..."
cat > "$APP_DIR/.env" << EOF
DJANGO_SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DJANGO_SETTINGS_MODULE=goat_morpho.single_instance_settings
DB_NAME=goat_morpho
DB_USER=goat_morpho_user
DB_PASSWORD=GoatMorpho2024!Secure
DB_HOST=localhost
DB_PORT=5432
REDIS_HOST=127.0.0.1
CV_PROCESSING_URL=http://127.0.0.1:8001
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@goatmorpho.info
EOF

chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
chmod 600 "$APP_DIR/.env"

# Copy single instance settings
log_info "Configuring Django settings..."
if [ -f "$APP_DIR/deploy/single_instance_settings.py" ]; then
    cp "$APP_DIR/deploy/single_instance_settings.py" "$APP_DIR/goat_morpho/single_instance_settings.py"
else
    log_warning "Single instance settings not found, using production settings"
fi

# Run Django migrations and setup
log_info "Setting up Django application..."
sudo -u "$APP_USER" bash << EOF
source "$APP_DIR/venv/bin/activate"
export \$(cat "$APP_DIR/.env" | xargs)
cd "$APP_DIR"

python manage.py migrate
python manage.py collectstatic --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@goatmorpho.info', 'GoatMorpho2024!Admin') if not User.objects.filter(username='admin').exists() else None" | python manage.py shell
EOF

# Create directories
log_info "Creating application directories..."
mkdir -p /var/log/goat_morpho
mkdir -p "$APP_DIR/media/goat_images/original"
mkdir -p "$APP_DIR/media/goat_images/processed"
mkdir -p "$APP_DIR/media/goat_images/samples"
chown -R "$APP_USER:$APP_USER" /var/log/goat_morpho
chown -R "$APP_USER:$APP_USER" "$APP_DIR/media"

# Create Gunicorn systemd service
log_info "Setting up Gunicorn service..."
cat > /etc/systemd/system/goat-morpho.service << EOF
[Unit]
Description=GoatMorpho Gunicorn daemon
Requires=goat-morpho.socket
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
RuntimeDirectory=gunicorn
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --access-logfile - \\
    --workers 8 \\
    --worker-class gevent \\
    --worker-connections 1000 \\
    --max-requests 1000 \\
    --max-requests-jitter 50 \\
    --preload \\
    --bind unix:/run/gunicorn/goat-morpho.sock \\
    goat_morpho.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/goat-morpho.socket << EOF
[Unit]
Description=GoatMorpho gunicorn socket

[Socket]
ListenStream=/run/gunicorn/goat-morpho.sock
SocketUser=$APP_USER
SocketGroup=$APP_USER
SocketMode=0660

[Install]
WantedBy=sockets.target
EOF

# Create CV processing service
log_info "Setting up CV processing service..."
cat > /etc/systemd/system/goat-morpho-cv.service << EOF
[Unit]
Description=GoatMorpho CV Processing Service
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python -m measurements.cv_processor --port 8001 --workers 3
Restart=always
RestartSec=5
EnvironmentFile=$APP_DIR/.env

[Install]
WantedBy=multi-user.target
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable goat-morpho.socket
systemctl enable goat-morpho.service
systemctl enable goat-morpho-cv.service
systemctl start goat-morpho.socket
systemctl start goat-morpho.service
systemctl start goat-morpho-cv.service

# Configure Nginx
log_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/goat-morpho << EOF
upstream app_server {
    server unix:/run/gunicorn/goat-morpho.sock fail_timeout=0;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN $PUBLIC_IP;
    
    # Security headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=1r/s;
    
    client_max_body_size 50M;
    client_body_timeout 60s;
    client_header_timeout 60s;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        try_files \$uri @proxy_to_app;
    }
    
    location /accounts/login/ {
        limit_req zone=login burst=5 nodelay;
        try_files \$uri @proxy_to_app;
    }
    
    location @proxy_to_app {
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        proxy_pass http://app_server;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }
    
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/goat-morpho /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Configure UFW firewall
log_info "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'

# Configure fail2ban
log_info "Configuring fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# Optimize system for 4 OCPU / 24GB RAM
log_info "Applying system optimizations..."
cat >> /etc/sysctl.conf << EOF

# GoatMorpho optimizations for 4 OCPU / 24GB RAM
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.core.netdev_max_backlog = 5000
fs.file-max = 100000
EOF

sysctl -p

# Set up log rotation
log_info "Setting up log rotation..."
cat > /etc/logrotate.d/goat-morpho << EOF
/var/log/goat_morpho/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    copytruncate
    postrotate
        systemctl reload goat-morpho
    endscript
}
EOF

# Start Nginx
systemctl restart nginx
systemctl enable nginx

# Install SSL certificate
log_info "Installing SSL certificate..."
if command -v certbot &> /dev/null; then
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN" --redirect
else
    log_warning "Certbot not available. SSL certificate not installed."
    log_info "Install SSL certificate manually: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
fi

# Create monitoring script
log_info "Setting up monitoring..."
cat > "$APP_DIR/monitor.sh" << EOF
#!/bin/bash
# GoatMorpho monitoring script

echo "=== GoatMorpho System Status ==="
echo "Date: \$(date)"
echo

echo "=== System Resources ==="
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - \$1"%"}'
echo "Memory Usage:"
free -h
echo "Disk Usage:"
df -h /
echo

echo "=== Services Status ==="
systemctl is-active postgresql
systemctl is-active redis-server
systemctl is-active goat-morpho
systemctl is-active goat-morpho-cv
systemctl is-active nginx
echo

echo "=== Application Status ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/
echo

echo "=== Database Connections ==="
sudo -u postgres psql -d goat_morpho -c "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';"
echo

echo "=== Recent Logs ==="
tail -n 5 /var/log/goat_morpho/app.log
EOF

chmod +x "$APP_DIR/monitor.sh"
chown "$APP_USER:$APP_USER" "$APP_DIR/monitor.sh"

# Final status check
log_info "Performing final status check..."
sleep 10

if systemctl is-active --quiet goat-morpho && systemctl is-active --quiet nginx; then
    log_success "GoatMorpho deployed successfully!"
    echo
    log_info "=== Deployment Summary ==="
    log_info "Domain: https://$DOMAIN"
    log_info "Admin URL: https://$DOMAIN/admin/"
    log_info "Admin credentials: admin / GoatMorpho2024!Admin"
    log_info "Application directory: $APP_DIR"
    log_info "Logs: /var/log/goat_morpho/"
    log_info "Monitor script: $APP_DIR/monitor.sh"
    echo
    log_info "=== Next Steps ==="
    log_info "1. Update DNS to point $DOMAIN to $PUBLIC_IP"
    log_info "2. Test the application: https://$DOMAIN"
    log_info "3. Change default admin password"
    log_info "4. Configure email settings in $APP_DIR/.env"
    log_info "5. Run monitoring: $APP_DIR/monitor.sh"
else
    log_error "Deployment completed with errors. Check service status:"
    systemctl status goat-morpho
    systemctl status nginx
fi

log_success "Single instance deployment script completed!"
