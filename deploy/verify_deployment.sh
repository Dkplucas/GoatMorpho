#!/bin/bash

# Quick verification script for GoatMorpho deployment
# Run on Django instance to verify complete setup

echo "🔍 GoatMorpho Deployment Verification"
echo "====================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

# Function to check status
check_service() {
    local service=$1
    local name=$2
    
    if systemctl is-active --quiet $service; then
        echo -e "✅ $name: ${GREEN}Running${NC}"
    else
        echo -e "❌ $name: ${RED}Not running${NC}"
        ((ERRORS++))
    fi
}

# Function to check port
check_port() {
    local port=$1
    local name=$2
    
    if ss -tlnp | grep -q ":$port "; then
        echo -e "✅ $name (port $port): ${GREEN}Listening${NC}"
    else
        echo -e "❌ $name (port $port): ${RED}Not listening${NC}"
        ((ERRORS++))
    fi
}

# Function to check URL
check_url() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        echo -e "✅ $name: ${GREEN}Responding${NC}"
    else
        echo -e "❌ $name: ${RED}Not responding${NC}"
        ((ERRORS++))
    fi
}

echo ""
echo "🔧 System Services"
echo "=================="
check_service "goatmorpho" "Django Application"
check_service "nginx" "Nginx Web Server"
check_service "postgresql" "PostgreSQL Database"
check_service "redis-server" "Redis Cache"

echo ""
echo "🌐 Network Ports"
echo "================"
check_port "80" "HTTP"
check_port "443" "HTTPS"
check_port "8000" "Gunicorn"
check_port "5432" "PostgreSQL"
check_port "6379" "Redis"

echo ""
echo "🔗 URL Endpoints"
echo "================"
check_url "http://localhost:8000" "Django App (local)"

# Check CV service connectivity
echo ""
echo "🔬 CV Processing Service"
echo "======================="
if curl -s -m 5 http://10.0.1.25:8001/health >/dev/null 2>&1; then
    echo -e "✅ CV Service: ${GREEN}Reachable${NC}"
else
    echo -e "❌ CV Service: ${RED}Not reachable${NC}"
    ((ERRORS++))
fi

echo ""
echo "📁 File Permissions"
echo "==================="

# Check critical directories
check_directory() {
    local dir=$1
    local owner=$2
    local name=$3
    
    if [ -d "$dir" ] && [ "$(stat -c '%U' "$dir")" = "$owner" ]; then
        echo -e "✅ $name: ${GREEN}Correct ownership${NC}"
    else
        echo -e "❌ $name: ${RED}Incorrect ownership${NC}"
        ((ERRORS++))
    fi
}

check_directory "/opt/goatmorpho" "goatmorpho" "Application directory"
check_directory "/var/log/goat_morpho" "goatmorpho" "Log directory"

echo ""
echo "🗄️ Database Connectivity"
echo "========================"
if sudo -u postgres psql -d goat_morpho -c "SELECT 1;" >/dev/null 2>&1; then
    echo -e "✅ Database: ${GREEN}Connected${NC}"
else
    echo -e "❌ Database: ${RED}Connection failed${NC}"
    ((ERRORS++))
fi

echo ""
echo "🔐 SSL Certificate"
echo "=================="
if [ -f "/etc/letsencrypt/live/goatmorpho.info/fullchain.pem" ]; then
    echo -e "✅ SSL Certificate: ${GREEN}Installed${NC}"
    
    # Check certificate expiry
    expiry=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/goatmorpho.info/fullchain.pem | cut -d= -f2)
    echo "   Expires: $expiry"
else
    echo -e "⚠️  SSL Certificate: ${YELLOW}Not installed${NC}"
    echo "   Run: sudo certbot --nginx -d goatmorpho.info -d www.goatmorpho.info"
fi

echo ""
echo "📋 Configuration Files"
echo "====================="

# Check environment file
if [ -f "/opt/goatmorpho/.env" ]; then
    echo -e "✅ Environment file: ${GREEN}Present${NC}"
    
    # Check if default values are still in use
    if grep -q "your-super-secret-key-change-this" /opt/goatmorpho/.env; then
        echo -e "⚠️  Secret key: ${YELLOW}Using default value${NC}"
    fi
    
    if grep -q "secure_password_change_this" /opt/goatmorpho/.env; then
        echo -e "⚠️  Database password: ${YELLOW}Using default value${NC}"
    fi
else
    echo -e "❌ Environment file: ${RED}Missing${NC}"
    ((ERRORS++))
fi

echo ""
echo "📊 System Resources"
echo "==================="

# Memory usage
mem_usage=$(free | grep Mem | awk '{printf "%.1f", ($3/$2) * 100.0}')
echo "Memory usage: ${mem_usage}%"

# Disk usage
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
echo "Disk usage: ${disk_usage}%"

# Load average
load_avg=$(uptime | awk -F'load average:' '{print $2}')
echo "Load average:$load_avg"

echo ""
echo "📝 Recent Logs"
echo "=============="
echo "Last 5 application log entries:"
if [ -f "/var/log/goat_morpho/app.log" ]; then
    tail -5 /var/log/goat_morpho/app.log 2>/dev/null || echo "No recent logs"
else
    echo "Log file not found"
fi

echo ""
echo "🎯 Summary"
echo "=========="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! GoatMorpho is ready.${NC}"
    echo ""
    echo "🌍 Your application should be available at:"
    echo "   https://goatmorpho.info"
    echo ""
    echo "🔧 Admin interface:"
    echo "   https://goatmorpho.info/admin/"
    echo ""
    echo "📊 Next steps:"
    echo "   1. Test image upload functionality"
    echo "   2. Monitor performance and logs"
    echo "   3. Setup automated backups"
else
    echo -e "${RED}❌ Found $ERRORS issues that need attention.${NC}"
    echo ""
    echo "🔧 Common fixes:"
    echo "   - Start services: sudo systemctl start <service-name>"
    echo "   - Check logs: sudo journalctl -u <service-name> -f"
    echo "   - Verify configuration files"
    echo "   - Check firewall rules: sudo ufw status"
fi

echo ""
echo "📞 Support commands:"
echo "   View this script: cat verify_deployment.sh"
echo "   Check all services: sudo systemctl status goatmorpho nginx postgresql redis-server"
echo "   Monitor logs: sudo journalctl -f"
echo "   Test CV service: curl http://10.0.1.25:8001/health"
