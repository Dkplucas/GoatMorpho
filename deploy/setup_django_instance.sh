#!/bin/bash

# GoatMorpho Django Instance Setup Script
# For Oracle Cloud VM.Standard.A1.Flex (ARM64)
# Instance: django-instance (130.61.39.212)

set -e

echo "🐐 Setting up GoatMorpho Django Instance on Oracle Cloud ARM64..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages
echo "🔧 Installing essential packages..."
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    nginx \
    postgresql-client \
    redis-server \
    git \
    curl \
    wget \
    htop \
    vim \
    certbot \
    python3-certbot-nginx \
    supervisor \
    ufw

# Create application user
echo "👤 Creating application user..."
sudo useradd -m -s /bin/bash goatmorpho || true
sudo usermod -aG www-data goatmorpho

# Setup application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/goatmorpho
sudo chown goatmorpho:goatmorpho /opt/goatmorpho

# Clone or setup application code
echo "💾 Setting up application code..."
sudo -u goatmorpho git clone https://github.com/Dkplucas/GoatMorpho.git /opt/goatmorpho/app || true

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
sudo -u goatmorpho python3.11 -m venv /opt/goatmorpho/venv

# Activate virtual environment and install dependencies
echo "📋 Installing Python dependencies..."
sudo -u goatmorpho bash -c "
    source /opt/goatmorpho/venv/bin/activate
    pip install --upgrade pip
    pip install wheel
    pip install gunicorn
    pip install whitenoise
    pip install psycopg2-binary
    pip install redis
    pip install requests
"

# Install only web-related dependencies (not CV libraries)
echo "🌐 Installing web dependencies..."
sudo -u goatmorpho bash -c "
    source /opt/goatmorpho/venv/bin/activate
    cd /opt/goatmorpho/app
    # Create minimal requirements for Django instance
    cat > requirements_django.txt << EOF
Django==5.2.4
djangorestframework==3.15.2
django-cors-headers==4.6.0
gunicorn==23.0.0
whitenoise==6.8.2
psycopg2-binary==2.9.10
redis==5.2.1
requests==2.32.3
Pillow==11.0.0
pandas==2.2.3
openpyxl==3.1.5
EOF
    pip install -r requirements_django.txt
"

# Setup directories
echo "📂 Setting up directories..."
sudo mkdir -p /var/log/goat_morpho
sudo mkdir -p /opt/goatmorpho/app/media/goat_images/{original,processed,samples}
sudo mkdir -p /opt/goatmorpho/app/staticfiles
sudo chown -R goatmorpho:www-data /var/log/goat_morpho
sudo chown -R goatmorpho:www-data /opt/goatmorpho/app/media
sudo chown -R goatmorpho:www-data /opt/goatmorpho/app/staticfiles

# Create environment variables file
echo "🔐 Creating environment file..."
sudo -u goatmorpho tee /opt/goatmorpho/.env << EOF
# Django Settings
DJANGO_SECRET_KEY=your-super-secret-key-change-this-in-production
DJANGO_SETTINGS_MODULE=goat_morpho.production_settings
DEBUG=False

# Database Configuration
DB_NAME=goat_morpho
DB_USER=goat_morpho_user
DB_PASSWORD=secure_password_change_this
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=127.0.0.1

# CV Processing Service
CV_PROCESSING_URL=http://10.0.1.25:8001

# Email Configuration (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@goatmorpho.info
EOF

# Copy production settings
echo "⚙️ Setting up production configuration..."
sudo -u goatmorpho cp /opt/goatmorpho/app/deploy/production_settings.py /opt/goatmorpho/app/goat_morpho/production_settings.py

# Create Gunicorn configuration
echo "🦄 Creating Gunicorn configuration..."
sudo -u goatmorpho tee /opt/goatmorpho/gunicorn.conf.py << EOF
# Gunicorn configuration for GoatMorpho Django instance
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = 2  # Conservative for 1 OCPU, 6GB RAM
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after processing this many requests
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "/var/log/goat_morpho/gunicorn_access.log"
errorlog = "/var/log/goat_morpho/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = 'goatmorpho_django'

# Server mechanics
preload_app = True
daemon = False
pidfile = "/opt/goatmorpho/gunicorn.pid"
user = "goatmorpho"
group = "goatmorpho"
tmp_upload_dir = None

# SSL (if needed)
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}
EOF

# Create systemd service for Gunicorn
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/goatmorpho.service << EOF
[Unit]
Description=GoatMorpho Django Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=goatmorpho
Group=goatmorpho
WorkingDirectory=/opt/goatmorpho/app
Environment=PATH=/opt/goatmorpho/venv/bin
EnvironmentFile=/opt/goatmorpho/.env
ExecStart=/opt/goatmorpho/venv/bin/gunicorn --config /opt/goatmorpho/gunicorn.conf.py goat_morpho.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/goatmorpho << EOF
# Nginx configuration for GoatMorpho
upstream goatmorpho_django {
    server 127.0.0.1:8000 fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name goatmorpho.info www.goatmorpho.info;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name goatmorpho.info www.goatmorpho.info;

    # SSL configuration (will be configured by certbot)
    ssl_certificate /etc/letsencrypt/live/goatmorpho.info/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/goatmorpho.info/privkey.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Upload size limit
    client_max_body_size 12M;

    # Static files
    location /static/ {
        alias /opt/goatmorpho/app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /opt/goatmorpho/app/media/;
        expires 1d;
        add_header Cache-Control "public";
    }

    # Django application
    location / {
        proxy_pass http://goatmorpho_django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health/ {
        access_log off;
        proxy_pass http://goatmorpho_django;
        proxy_set_header Host \$host;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/goatmorpho /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Configure Redis
echo "💾 Configuring Redis..."
sudo sed -i 's/^bind 127.0.0.1 ::1/bind 127.0.0.1/' /etc/redis/redis.conf
sudo sed -i 's/^# maxmemory <bytes>/maxmemory 1gb/' /etc/redis/redis.conf
sudo sed -i 's/^# maxmemory-policy noeviction/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf

# Start and enable services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable redis-server
sudo systemctl start redis-server
sudo systemctl enable nginx
sudo systemctl start nginx

# Create Django management script
echo "🐍 Creating Django management script..."
sudo -u goatmorpho tee /opt/goatmorpho/manage.sh << 'EOF'
#!/bin/bash
source /opt/goatmorpho/venv/bin/activate
source /opt/goatmorpho/.env
cd /opt/goatmorpho/app
python manage.py "$@"
EOF
sudo chmod +x /opt/goatmorpho/manage.sh

# Setup SSL certificate with certbot
echo "🔒 Setting up SSL certificate..."
echo "⚠️  SSL setup requires manual intervention:"
echo "   Run: sudo certbot --nginx -d goatmorpho.info -d www.goatmorpho.info"

# Setup log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/goatmorpho << EOF
/var/log/goat_morpho/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 goatmorpho goatmorpho
    postrotate
        systemctl reload goatmorpho
    endscript
}
EOF

echo "✅ Django instance setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your domain DNS to point to 130.61.39.212"
echo "2. Setup PostgreSQL database (see setup_database.sh)"
echo "3. Run SSL certificate setup: sudo certbot --nginx -d goatmorpho.info -d www.goatmorpho.info"
echo "4. Copy your application code to /opt/goatmorpho/app"
echo "5. Run database migrations: sudo -u goatmorpho /opt/goatmorpho/manage.sh migrate"
echo "6. Collect static files: sudo -u goatmorpho /opt/goatmorpho/manage.sh collectstatic --noinput"
echo "7. Start the application: sudo systemctl start goatmorpho"
echo ""
echo "🔍 Useful commands:"
echo "   Check status: sudo systemctl status goatmorpho"
echo "   View logs: sudo journalctl -u goatmorpho -f"
echo "   Nginx logs: sudo tail -f /var/log/nginx/error.log"
echo "   App logs: sudo tail -f /var/log/goat_morpho/app.log"
