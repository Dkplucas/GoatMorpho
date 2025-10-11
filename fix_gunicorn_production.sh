#!/bin/bash
# Fix Gunicorn production deployment issues
# Run this script on the production server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_status "🔧 Fixing Gunicorn Production Issues"
print_status "===================================="

# Configuration
APP_NAME="goatmorpho"
APP_DIR="/opt/goat_morpho"
USER="ubuntu"
GROUP="ubuntu"

# Stop existing services
print_status "Stopping existing services..."
sudo systemctl stop goat_morpho.service 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

# Kill any running gunicorn processes
print_status "Cleaning up existing gunicorn processes..."
sudo pkill -f gunicorn || true
sleep 2

# Create necessary directories
print_status "Creating required directories..."
sudo mkdir -p /run/gunicorn
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p $APP_DIR/logs

# Set proper ownership and permissions
sudo chown $USER:$GROUP /run/gunicorn
sudo chown $USER:$GROUP /var/log/gunicorn
sudo chown -R $USER:$GROUP $APP_DIR

# Set permissions
sudo chmod 755 /run/gunicorn
sudo chmod 755 /var/log/gunicorn

print_success "Directories created and permissions set"

# Create improved systemd service file
print_status "Creating improved systemd service..."
sudo tee /etc/systemd/system/goat_morpho.service > /dev/null << EOF
[Unit]
Description=Gunicorn for Django (GoatMorpho)
After=network.target
Requires=redis-server.service
After=redis-server.service

[Service]
Type=notify
User=$USER
Group=$GROUP
RuntimeDirectory=gunicorn
RuntimeDirectoryMode=755
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/gunicorn \\
    --name goatmorpho \\
    --workers 3 \\
    --max-requests 1000 \\
    --max-requests-jitter 100 \\
    --timeout 120 \\
    --keep-alive 2 \\
    --bind unix:/run/gunicorn/sock \\
    --user $USER \\
    --group $GROUP \\
    --log-level info \\
    --log-file /var/log/gunicorn/gunicorn.log \\
    --access-logfile /var/log/gunicorn/access.log \\
    --error-logfile /var/log/gunicorn/error.log \\
    --capture-output \\
    --enable-stdio-inheritance \\
    goat_morpho.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create Gunicorn configuration file
print_status "Creating Gunicorn configuration file..."
cat > $APP_DIR/gunicorn.conf.py << EOF
# Gunicorn configuration file for GoatMorpho
import multiprocessing
import os

# Server socket
bind = "unix:/run/gunicorn/sock"
umask = 0

# Worker processes
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 2
preload_app = True

# Restart workers after this many requests, with up to 100 random
max_requests = 1000
max_requests_jitter = 100

# Restart workers after this many seconds
max_worker_memory = 250000000  # 250MB
worker_tmp_dir = "/dev/shm"

# Logging
loglevel = "info"
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
access_log_format = '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "goatmorpho"

# Server mechanics
daemon = False
pidfile = "/run/gunicorn/gunicorn.pid"
user = "$USER"
group = "$GROUP"
tmp_upload_dir = None

# SSL (if needed later)
# keyfile = None
# certfile = None

# Environment
raw_env = [
    'DJANGO_SETTINGS_MODULE=goat_morpho.settings',
]

# Preload application
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
EOF

# Update Nginx configuration
print_status "Updating Nginx configuration..."
sudo tee /etc/nginx/sites-available/goatmorpho > /dev/null << EOF
upstream goatmorpho {
    server unix:/run/gunicorn/sock fail_timeout=0;
}

server {
    listen 80;
    server_name goatmorpho.info www.goatmorpho.info 130.61.39.212 _;
    
    client_max_body_size 20M;
    client_body_timeout 120s;
    client_header_timeout 120s;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Logging
    access_log /var/log/nginx/goatmorpho_access.log;
    error_log /var/log/nginx/goatmorpho_error.log;
    
    location = /favicon.ico { 
        access_log off; 
        log_not_found off; 
    }
    
    location /static/ {
        alias $APP_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
        gzip on;
        gzip_types text/css application/javascript image/svg+xml;
    }
    
    location /media/ {
        alias $APP_DIR/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_buffering off;
        proxy_pass http://goatmorpho;
        
        # Timeouts
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
    
    # Health check endpoint
    location /health/ {
        access_log off;
        proxy_pass http://goatmorpho;
        proxy_set_header Host \$http_host;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/goatmorpho /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
print_status "Testing Nginx configuration..."
if sudo nginx -t; then
    print_success "Nginx configuration is valid"
else
    print_error "Nginx configuration has errors"
    exit 1
fi

# Create log rotation for Gunicorn
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/gunicorn > /dev/null << EOF
/var/log/gunicorn/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $GROUP
    postrotate
        systemctl reload goat_morpho.service
    endscript
}
EOF

# Create startup script for manual testing
print_status "Creating manual startup script..."
cat > $APP_DIR/start_gunicorn.sh << 'EOF'
#!/bin/bash
# Manual Gunicorn startup script for testing

cd /opt/goat_morpho
source venv/bin/activate

# Kill any existing gunicorn processes
pkill -f gunicorn || true
sleep 2

# Remove old socket file
rm -f /run/gunicorn/sock

# Start Gunicorn
exec gunicorn \
    --config gunicorn.conf.py \
    --bind unix:/run/gunicorn/sock \
    --workers 3 \
    --timeout 120 \
    --log-level info \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    goat_morpho.wsgi:application
EOF

chmod +x $APP_DIR/start_gunicorn.sh

# Reload systemd and start services
print_status "Reloading systemd and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable goat_morpho.service

# Test Django application first
print_status "Testing Django application..."
cd $APP_DIR
source venv/bin/activate

if python manage.py check --deploy; then
    print_success "Django application check passed"
else
    print_warning "Django check had issues, but continuing..."
fi

# Start Redis if not running
print_status "Ensuring Redis is running..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Start the application service
print_status "Starting GoatMorpho service..."
sudo systemctl start goat_morpho.service

# Wait a moment for service to start
sleep 5

# Check service status
if sudo systemctl is-active --quiet goat_morpho.service; then
    print_success "GoatMorpho service is running"
else
    print_error "GoatMorpho service failed to start"
    print_status "Checking service logs..."
    sudo journalctl -u goat_morpho.service -n 20 --no-pager
    exit 1
fi

# Start Nginx
print_status "Starting Nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

# Final status check
print_status "Performing final status check..."
echo
print_status "Service Status:"
echo "---------------"
for service in redis-server goat_morpho nginx; do
    if sudo systemctl is-active --quiet $service; then
        print_success "✓ $service is running"
    else
        print_error "✗ $service is not running"
    fi
done

echo
print_status "Socket file check:"
if [ -S "/run/gunicorn/sock" ]; then
    print_success "✓ Gunicorn socket exists"
    ls -la /run/gunicorn/sock
else
    print_error "✗ Gunicorn socket not found"
fi

echo
print_status "Log files:"
echo "- Gunicorn logs: /var/log/gunicorn/"
echo "- Nginx logs: /var/log/nginx/"
echo "- Service logs: sudo journalctl -u goat_morpho.service -f"

echo
print_success "🎉 Gunicorn deployment fix completed!"
print_status "Test your application: curl -I http://localhost"
print_status "Monitor logs: sudo journalctl -u goat_morpho.service -f"
