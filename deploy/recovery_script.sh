#!/bin/bash

# GoatMorpho Deployment Recovery Script
# Fixes the issues encountered during deployment

set -e

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

# Configuration
APP_USER="goat_morpho"
APP_DIR="/opt/goat_morpho"
DOMAIN="goatmorpho.info"
PUBLIC_IP="130.61.39.212"

log_info "Starting GoatMorpho deployment recovery..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

# Step 1: Copy source code properly
log_info "Copying source code to application directory..."
if [ -d "/home/ubuntu/GoatMorpho" ]; then
    # Create app directory if it doesn't exist
    mkdir -p "$APP_DIR"
    
    # Copy all source files
    cp -r /home/ubuntu/GoatMorpho/* "$APP_DIR/"
    
    # Set proper ownership
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    
    log_success "Source code copied successfully"
else
    log_error "Source code not found at /home/ubuntu/GoatMorpho"
    exit 1
fi

# Step 2: Create virtual environment if it doesn't exist
log_info "Setting up Python virtual environment..."
if [ ! -d "$APP_DIR/venv" ]; then
    sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
fi

# Step 3: Install Python dependencies with ARM64 compatibility
log_info "Installing Python dependencies (ARM64 compatible)..."
sudo -u "$APP_USER" bash << 'EOF'
source /opt/goat_morpho/venv/bin/activate
cd /opt/goat_morpho

# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install core Django dependencies
pip install \
    Django==5.2.4 \
    psycopg2-binary \
    redis \
    djangorestframework \
    django-cors-headers \
    whitenoise \
    gunicorn[gevent] \
    celery[redis]

# Install image processing dependencies
pip install \
    Pillow \
    numpy \
    opencv-python-headless \
    scikit-learn \
    pandas \
    openpyxl

# Install MediaPipe (should work on ARM64)
pip install mediapipe

# For TensorFlow on ARM64, try tensorflow-aarch64 or skip if not available
echo "Attempting to install TensorFlow for ARM64..."
pip install tensorflow-aarch64 || echo "TensorFlow-aarch64 not available, continuing without TensorFlow"

# Install from requirements.txt if it exists
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || echo "Some requirements failed, continuing..."
fi

echo "Python dependencies installation completed"
EOF

# Step 4: Create environment configuration
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

# Step 5: Copy single instance settings
log_info "Configuring Django settings..."
if [ -f "$APP_DIR/deploy/single_instance_settings.py" ]; then
    cp "$APP_DIR/deploy/single_instance_settings.py" "$APP_DIR/goat_morpho/single_instance_settings.py"
    log_success "Single instance settings configured"
else
    log_warning "Single instance settings not found, will use default settings"
    # Create a basic settings file
    cat > "$APP_DIR/goat_morpho/single_instance_settings.py" << 'EOF'
from .settings import *
import os

DEBUG = False
ALLOWED_HOSTS = ['goatmorpho.info', 'www.goatmorpho.info', '130.61.39.212', 'localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'goat_morpho'),
        'USER': os.environ.get('DB_USER', 'goat_morpho_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
EOF
    chown "$APP_USER:$APP_USER" "$APP_DIR/goat_morpho/single_instance_settings.py"
fi

# Step 6: Run Django migrations and setup
log_info "Setting up Django application..."
sudo -u "$APP_USER" bash << 'EOF'
source /opt/goat_morpho/venv/bin/activate
export $(cat /opt/goat_morpho/.env | xargs)
cd /opt/goat_morpho

# Check if manage.py exists
if [ ! -f "manage.py" ]; then
    echo "ERROR: manage.py not found in /opt/goat_morpho"
    exit 1
fi

# Run migrations
python manage.py migrate --settings=goat_morpho.single_instance_settings

# Collect static files
python manage.py collectstatic --noinput --settings=goat_morpho.single_instance_settings

# Create superuser if it doesn't exist
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@goatmorpho.info', 'GoatMorpho2024!Admin') if not User.objects.filter(username='admin').exists() else print('Admin user already exists')" | python manage.py shell --settings=goat_morpho.single_instance_settings
EOF

# Step 7: Create necessary directories
log_info "Creating application directories..."
mkdir -p /var/log/goat_morpho
mkdir -p "$APP_DIR/media/goat_images/original"
mkdir -p "$APP_DIR/media/goat_images/processed"
mkdir -p "$APP_DIR/media/goat_images/samples"
chown -R "$APP_USER:$APP_USER" /var/log/goat_morpho
chown -R "$APP_USER:$APP_USER" "$APP_DIR/media"

# Step 8: Create Gunicorn systemd service
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
    --env DJANGO_SETTINGS_MODULE=goat_morpho.single_instance_settings \\
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

# Step 9: Configure Nginx
log_info "Configuring Nginx..."
cat > /etc/nginx/sites-available/goat-morpho << EOF
upstream app_server {
    server unix:/run/gunicorn/goat-morpho.sock fail_timeout=0;
}

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN $PUBLIC_IP;
    
    client_max_body_size 50M;
    
    location / {
        try_files \$uri @proxy_to_app;
    }
    
    location @proxy_to_app {
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Host \$http_host;
        proxy_redirect off;
        proxy_pass http://app_server;
    }
    
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 30d;
    }
    
    location /media/ {
        alias $APP_DIR/media/;
        expires 7d;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/goat-morpho /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Step 10: Start services
log_info "Starting services..."
systemctl daemon-reload
systemctl enable goat-morpho.socket
systemctl enable goat-morpho.service
systemctl start goat-morpho.socket
systemctl start goat-morpho.service
systemctl restart nginx

# Step 11: Configure basic firewall
log_info "Configuring firewall..."
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 'Nginx Full'

# Final status check
log_info "Checking service status..."
sleep 5

if systemctl is-active --quiet goat-morpho && systemctl is-active --quiet nginx; then
    log_success "GoatMorpho deployment recovery completed successfully!"
    echo
    log_info "=== Deployment Summary ==="
    log_info "Domain: http://$DOMAIN"
    log_info "IP Access: http://$PUBLIC_IP"
    log_info "Admin URL: http://$DOMAIN/admin/"
    log_info "Admin credentials: admin / GoatMorpho2024!Admin"
    echo
    log_info "=== Next Steps ==="
    log_info "1. Test the application: http://$DOMAIN"
    log_info "2. Install SSL certificate: certbot --nginx -d $DOMAIN -d www.$DOMAIN"
    log_info "3. Change default admin password"
else
    log_error "Some services failed to start. Check with:"
    log_error "systemctl status goat-morpho"
    log_error "systemctl status nginx"
    log_error "journalctl -u goat-morpho -n 50"
fi

log_success "Recovery script completed!"
