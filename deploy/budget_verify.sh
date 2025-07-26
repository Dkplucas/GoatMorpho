#!/bin/bash

# Budget Deployment Verification Script
# Quick check for single-instance GoatMorpho setup

echo "💰 GoatMorpho Budget Deployment Verification"
echo "============================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to check file existence
check_file() {
    local file=$1
    local name=$2
    
    if [ -f "$file" ]; then
        echo -e "✅ $name: ${GREEN}Present${NC}"
    else
        echo -e "❌ $name: ${RED}Missing${NC}"
        ((ERRORS++))
    fi
}

echo ""
echo "🔧 System Services"
echo "=================="
check_service "goatmorpho" "Django Application"
check_service "nginx" "Nginx Web Server"

echo ""
echo "🌐 Network Ports"
echo "================"
if ss -tlnp | grep -q ":80 "; then
    echo -e "✅ HTTP (80): ${GREEN}Listening${NC}"
else
    echo -e "❌ HTTP (80): ${RED}Not listening${NC}"
    ((ERRORS++))
fi

if ss -tlnp | grep -q ":443 "; then
    echo -e "✅ HTTPS (443): ${GREEN}Listening${NC}"
else
    echo -e "⚠️  HTTPS (443): ${YELLOW}Not listening (SSL not configured)${NC}"
fi

if ss -tlnp | grep -q ":8000 "; then
    echo -e "✅ Gunicorn (8000): ${GREEN}Listening${NC}"
else
    echo -e "❌ Gunicorn (8000): ${RED}Not listening${NC}"
    ((ERRORS++))
fi

echo ""
echo "📁 Critical Files & Directories"
echo "==============================="
check_file "/opt/goatmorpho/.env" "Environment file"
check_file "/opt/goatmorpho/app/db.sqlite3" "SQLite database"
check_file "/opt/goatmorpho/app/measurements/cv_processor.py" "CV Processor"

# Check if integrated CV processor is in use
if [ -f "/opt/goatmorpho/app/measurements/cv_processor.py" ]; then
    if grep -q "Budget deployment" /opt/goatmorpho/app/measurements/cv_processor.py 2>/dev/null; then
        echo -e "✅ Integrated CV: ${GREEN}Configured${NC}"
    else
        echo -e "⚠️  CV Processor: ${YELLOW}Not budget version${NC}"
    fi
fi

echo ""
echo "🗄️ Database"
echo "==========="
if [ -f "/opt/goatmorpho/app/db.sqlite3" ]; then
    db_size=$(du -h /opt/goatmorpho/app/db.sqlite3 | cut -f1)
    echo -e "✅ SQLite Database: ${GREEN}Present (${db_size})${NC}"
else
    echo -e "❌ SQLite Database: ${RED}Missing${NC}"
    ((ERRORS++))
fi

echo ""
echo "💾 Cache System"
echo "==============="
if [ -d "/tmp/django_cache" ]; then
    cache_files=$(find /tmp/django_cache -type f | wc -l)
    echo -e "✅ File Cache: ${GREEN}Active (${cache_files} files)${NC}"
else
    echo -e "⚠️  File Cache: ${YELLOW}Directory missing${NC}"
fi

echo ""
echo "🔐 SSL Certificate"
echo "=================="
if [ -f "/etc/letsencrypt/live/goatmorpho.info/fullchain.pem" ]; then
    echo -e "✅ SSL Certificate: ${GREEN}Installed${NC}"
    expiry=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/goatmorpho.info/fullchain.pem | cut -d= -f2)
    echo "   Expires: $expiry"
else
    echo -e "⚠️  SSL Certificate: ${YELLOW}Not installed${NC}"
    echo "   Run: sudo certbot --nginx -d goatmorpho.info -d www.goatmorpho.info"
fi

echo ""
echo "📊 Resource Usage (Budget Monitoring)"
echo "====================================="

# Memory usage
mem_total=$(free -m | grep Mem | awk '{print $2}')
mem_used=$(free -m | grep Mem | awk '{print $3}')
mem_percent=$(echo "scale=1; $mem_used * 100 / $mem_total" | bc)
echo "Memory: ${mem_used}MB/${mem_total}MB (${mem_percent}%)"

if (( $(echo "$mem_percent > 80" | bc -l) )); then
    echo -e "⚠️  ${YELLOW}High memory usage${NC}"
fi

# Disk usage
disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
disk_used=$(df -h / | tail -1 | awk '{print $3}')
disk_total=$(df -h / | tail -1 | awk '{print $2}')
echo "Disk: ${disk_used}/${disk_total} (${disk_usage}%)"

if [ "$disk_usage" -gt 80 ]; then
    echo -e "⚠️  ${YELLOW}High disk usage${NC}"
fi

# Load average
load_1min=$(uptime | awk -F'load average:' '{print $2}' | awk -F',' '{print $1}' | xargs)
echo "Load (1min): $load_1min"

# Check if CV processing works
echo ""
echo "🔬 CV Processing Test"
echo "===================="
if [ -f "/opt/goatmorpho/app/media/goat_images/samples/sample_goat_profile.jpg" ]; then
    echo -e "✅ Sample images: ${GREEN}Available${NC}"
else
    echo -e "⚠️  Sample images: ${YELLOW}Not found${NC}"
    echo "   You may need to upload test images"
fi

echo ""
echo "📝 Recent Application Logs"
echo "=========================="
if [ -f "/opt/goatmorpho/logs/gunicorn_error.log" ]; then
    echo "Last 3 error log entries:"
    tail -3 /opt/goatmorpho/logs/gunicorn_error.log 2>/dev/null || echo "No recent errors"
else
    echo "No error log found"
fi

echo ""
echo "💰 Budget Optimization Status"
echo "=============================="

# Check if budget settings are in use
if grep -q "budget_settings" /opt/goatmorpho/.env 2>/dev/null; then
    echo -e "✅ Budget Settings: ${GREEN}Active${NC}"
else
    echo -e "⚠️  Budget Settings: ${YELLOW}Not configured${NC}"
fi

# Check file cache
if [ -d "/tmp/django_cache" ]; then
    echo -e "✅ File Cache: ${GREEN}Enabled${NC}"
else
    echo -e "❌ File Cache: ${RED}Not configured${NC}"
fi

# Check SQLite
if [ -f "/opt/goatmorpho/app/db.sqlite3" ]; then
    echo -e "✅ SQLite Database: ${GREEN}In use${NC}"
else
    echo -e "❌ Database: ${RED}Missing${NC}"
fi

echo ""
echo "🎯 Summary"
echo "=========="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Budget deployment is working correctly!${NC}"
    echo ""
    echo -e "${BLUE}🌍 Your application should be available at:${NC}"
    echo "   http://goatmorpho.info (redirects to HTTPS if SSL configured)"
    echo "   https://goatmorpho.info (if SSL is configured)"
    echo ""
    echo -e "${BLUE}🔧 Admin interface:${NC}"
    echo "   https://goatmorpho.info/admin/"
    echo ""
    echo -e "${GREEN}💰 Estimated costs: $15-17/month${NC}"
else
    echo -e "${RED}❌ Found $ERRORS issues that need attention.${NC}"
fi

echo ""
echo -e "${BLUE}📞 Budget Support Commands:${NC}"
echo "   Restart app: sudo systemctl restart goatmorpho"
echo "   View logs: sudo journalctl -u goatmorpho -f"
echo "   Check resources: htop"
echo "   Database size: ls -lh /opt/goatmorpho/app/db.sqlite3"
echo "   Cache cleanup: sudo rm -rf /tmp/django_cache/*"
echo "   SSL setup: sudo certbot --nginx -d goatmorpho.info"

echo ""
echo -e "${YELLOW}💡 Budget Tips:${NC}"
echo "   • Monitor resource usage regularly"
echo "   • Keep images under 5MB for faster processing"
echo "   • Clean cache weekly: sudo rm -rf /tmp/django_cache/*"
echo "   • Backup database: cp /opt/goatmorpho/app/db.sqlite3 ~/backup.db"
