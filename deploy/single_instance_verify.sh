#!/bin/bash

# Single Instance Verification Script for GoatMorpho
# Oracle Cloud Infrastructure - VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)
# Verifies all services and configurations

set -e

# Configuration
DOMAIN="goatmorpho.info"
PUBLIC_IP="130.61.39.212"
PRIVATE_IP="10.0.0.163"
APP_USER="goat_morpho"
APP_DIR="/opt/goat_morpho"

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

check_service() {
    local service=$1
    if systemctl is-active --quiet "$service"; then
        log_success "$service is running"
        return 0
    else
        log_error "$service is not running"
        return 1
    fi
}

check_port() {
    local port=$1
    local description=$2
    if netstat -tuln | grep -q ":$port "; then
        log_success "$description (port $port) is listening"
        return 0
    else
        log_error "$description (port $port) is not listening"
        return 1
    fi
}

check_url() {
    local url=$1
    local description=$2
    local expected_code=${3:-200}
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [ "$response" -eq "$expected_code" ]; then
        log_success "$description: HTTP $response"
        return 0
    else
        log_error "$description: HTTP $response (expected $expected_code)"
        return 1
    fi
}

log_info "Starting GoatMorpho single instance verification..."
log_info "Instance: VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)"
log_info "Domain: $DOMAIN ($PUBLIC_IP)"
echo

# System information
log_info "=== System Information ==="
echo "Hostname: $(hostname)"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Architecture: $(uname -m)"
echo "Uptime: $(uptime | awk '{print $3,$4}' | sed 's/,//')"
echo

# CPU and Memory
log_info "=== Resource Usage ==="
echo "CPU Cores: $(nproc)"
echo "Total Memory: $(free -h | awk '/^Mem:/ {print $2}')"
echo "Available Memory: $(free -h | awk '/^Mem:/ {print $7}')"
echo "Current CPU Usage: $(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}')"
echo "Disk Usage (/):"
df -h / | tail -n 1
echo

# Network configuration
log_info "=== Network Configuration ==="
echo "Public IP: $PUBLIC_IP"
echo "Private IP: $PRIVATE_IP"
echo "Current IP addresses:"
ip addr show | grep -E "inet (10\.|172\.|192\.168\.|$PUBLIC_IP)" || true
echo

# Service status
log_info "=== Service Status ==="
services=("postgresql" "redis-server" "goat-morpho.socket" "goat-morpho.service" "goat-morpho-cv.service" "nginx")
all_services_ok=true

for service in "${services[@]}"; do
    if ! check_service "$service"; then
        all_services_ok=false
    fi
done
echo

# Port checks
log_info "=== Port Status ==="
ports=(
    "22:SSH"
    "80:HTTP"
    "443:HTTPS"
    "5432:PostgreSQL"
    "6379:Redis"
    "8001:CV Processing"
)

all_ports_ok=true
for port_desc in "${ports[@]}"; do
    port=$(echo "$port_desc" | cut -d: -f1)
    desc=$(echo "$port_desc" | cut -d: -f2)
    if ! check_port "$port" "$desc"; then
        all_ports_ok=false
    fi
done
echo

# Database connectivity
log_info "=== Database Status ==="
if sudo -u postgres psql -d goat_morpho -c "SELECT 1;" >/dev/null 2>&1; then
    log_success "PostgreSQL database connection successful"
    
    # Check database size and connections
    db_size=$(sudo -u postgres psql -d goat_morpho -t -c "SELECT pg_size_pretty(pg_database_size('goat_morpho'));" | xargs)
    active_conn=$(sudo -u postgres psql -d goat_morpho -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" | xargs)
    total_conn=$(sudo -u postgres psql -d goat_morpho -t -c "SELECT count(*) FROM pg_stat_activity;" | xargs)
    
    echo "Database size: $db_size"
    echo "Active connections: $active_conn"
    echo "Total connections: $total_conn"
    
    # Check if migrations are applied
    if sudo -u "$APP_USER" bash -c "source $APP_DIR/venv/bin/activate && cd $APP_DIR && python manage.py showmigrations --plan | grep -q '\[X\]'"; then
        log_success "Django migrations are applied"
    else
        log_warning "Django migrations may not be fully applied"
    fi
else
    log_error "PostgreSQL database connection failed"
fi
echo

# Redis connectivity
log_info "=== Redis Status ==="
if redis-cli ping >/dev/null 2>&1; then
    log_success "Redis connection successful"
    redis_memory=$(redis-cli info memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r')
    redis_keys=$(redis-cli dbsize)
    echo "Memory usage: $redis_memory"
    echo "Keys in database: $redis_keys"
else
    log_error "Redis connection failed"
fi
echo

# Application files and permissions
log_info "=== Application Files ==="
if [ -d "$APP_DIR" ]; then
    log_success "Application directory exists: $APP_DIR"
    echo "Directory size: $(du -sh $APP_DIR | cut -f1)"
    
    # Check key files
    key_files=("manage.py" "goat_morpho/settings.py" "venv/bin/activate" ".env")
    for file in "${key_files[@]}"; do
        if [ -f "$APP_DIR/$file" ]; then
            log_success "File exists: $file"
        else
            log_error "Missing file: $file"
        fi
    done
    
    # Check permissions
    if [ -O "$APP_DIR" ] || [ "$(stat -c %U $APP_DIR)" = "$APP_USER" ]; then
        log_success "Application directory ownership is correct"
    else
        log_error "Application directory ownership is incorrect"
    fi
else
    log_error "Application directory does not exist: $APP_DIR"
fi
echo

# Nginx configuration
log_info "=== Nginx Configuration ==="
if nginx -t >/dev/null 2>&1; then
    log_success "Nginx configuration is valid"
else
    log_error "Nginx configuration has errors"
fi

if [ -f "/etc/nginx/sites-enabled/goat-morpho" ]; then
    log_success "GoatMorpho Nginx site is enabled"
else
    log_error "GoatMorpho Nginx site is not enabled"
fi
echo

# SSL Certificate
log_info "=== SSL Certificate ==="
if [ -f "/etc/letsencrypt/live/$DOMAIN/cert.pem" ]; then
    log_success "SSL certificate exists for $DOMAIN"
    cert_expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$DOMAIN/cert.pem" | cut -d= -f2)
    echo "Certificate expires: $cert_expiry"
else
    log_warning "SSL certificate not found for $DOMAIN"
fi
echo

# HTTP/HTTPS connectivity
log_info "=== Web Server Connectivity ==="
web_tests=(
    "http://localhost/:Local HTTP"
    "http://$DOMAIN/:Public HTTP"
    "https://$DOMAIN/:Public HTTPS"
    "http://localhost/admin/:Admin Interface"
)

web_ok=true
for test in "${web_tests[@]}"; do
    url=$(echo "$test" | cut -d: -f1-2)
    desc=$(echo "$test" | cut -d: -f3)
    if ! check_url "$url" "$desc"; then
        web_ok=false
    fi
done
echo

# CV Processing Service
log_info "=== CV Processing Service ==="
if check_url "http://localhost:8001/" "CV Processing Service" "404"; then
    log_success "CV Processing service is responding"
else
    log_error "CV Processing service is not responding"
fi
echo

# Log files
log_info "=== Log Files ==="
log_files=(
    "/var/log/goat_morpho/app.log:Application logs"
    "/var/log/nginx/access.log:Nginx access logs"
    "/var/log/nginx/error.log:Nginx error logs"
)

for log_desc in "${log_files[@]}"; do
    log_file=$(echo "$log_desc" | cut -d: -f1)
    desc=$(echo "$log_desc" | cut -d: -f2)
    if [ -f "$log_file" ]; then
        log_success "$desc exist"
        lines=$(wc -l < "$log_file" 2>/dev/null || echo "0")
        size=$(du -h "$log_file" 2>/dev/null | cut -f1 || echo "0")
        echo "  Lines: $lines, Size: $size"
    else
        log_error "$desc do not exist"
    fi
done
echo

# Firewall status
log_info "=== Firewall Status ==="
if ufw status | grep -q "Status: active"; then
    log_success "UFW firewall is active"
    echo "Allowed services:"
    ufw status numbered | grep ALLOW || echo "  No rules found"
else
    log_warning "UFW firewall is not active"
fi
echo

# Performance metrics
log_info "=== Performance Metrics ==="
echo "Load average: $(uptime | awk -F'load average:' '{print $2}')"
echo "Memory usage:"
free -h | awk 'NR==2{printf "  Used: %s/%s (%.2f%%)\n", $3,$2,$3*100/$2 }'
echo "Disk I/O:"
iostat -d 1 2 | tail -n +4 | tail -n 1 | awk '{printf "  %s: %.2f tps\n", $1, $4}' 2>/dev/null || echo "  iostat not available"
echo

# Security checks
log_info "=== Security Status ==="
if systemctl is-active --quiet fail2ban; then
    log_success "Fail2ban is running"
    banned=$(fail2ban-client status 2>/dev/null | grep "Jail list" | wc -l || echo "0")
    echo "  Active jails: $banned"
else
    log_warning "Fail2ban is not running"
fi

if [ -f "/etc/cron.d/certbot" ] || [ -f "/etc/crontab" ] && grep -q certbot /etc/crontab; then
    log_success "SSL certificate auto-renewal is configured"
else
    log_warning "SSL certificate auto-renewal may not be configured"
fi
echo

# Overall status
log_info "=== Overall Status ==="
if $all_services_ok && $all_ports_ok && $web_ok; then
    log_success "All systems operational! ✅"
    echo
    log_info "🎉 GoatMorpho is ready for use!"
    log_info "🌐 Access your application at: https://$DOMAIN"
    log_info "🔧 Admin interface: https://$DOMAIN/admin/"
    log_info "📊 Monitor with: $APP_DIR/monitor.sh"
else
    log_error "Some issues detected. Please review the errors above."
    echo
    log_info "🔧 Common troubleshooting steps:"
    log_info "   - Check service logs: journalctl -u [service-name]"
    log_info "   - Restart services: systemctl restart [service-name]"
    log_info "   - Check application logs: tail -f /var/log/goat_morpho/app.log"
    log_info "   - Verify DNS: nslookup $DOMAIN"
fi

echo
log_info "Verification complete. Summary:"
echo "  Domain: $DOMAIN"
echo "  Public IP: $PUBLIC_IP"
echo "  Instance: 4 OCPUs, 24GB RAM"
echo "  Services: PostgreSQL, Redis, Django, CV Processing, Nginx"
echo "  SSL: $([ -f "/etc/letsencrypt/live/$DOMAIN/cert.pem" ] && echo "Enabled" || echo "Pending")"
echo "  Firewall: $(ufw status | grep -q "Status: active" && echo "Active" || echo "Inactive")"
