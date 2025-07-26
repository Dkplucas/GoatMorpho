#!/bin/bash

# Complete Deployment Script for GoatMorpho on Oracle Cloud
# Coordinates setup of both Django and CV instances

echo "🐐 GoatMorpho Oracle Cloud Deployment"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DJANGO_INSTANCE_IP="130.61.39.212"
CV_INSTANCE_IP="10.0.1.25"
DOMAIN="goatmorpho.info"

echo "📋 Deployment Configuration:"
echo "   Django Instance: $DJANGO_INSTANCE_IP (Public)"
echo "   CV Instance: $CV_INSTANCE_IP (Private)"
echo "   Domain: $DOMAIN"
echo ""

# Check if we're on the correct instance
detect_instance() {
    local ip=$(hostname -I | awk '{print $1}')
    if [[ "$ip" == "10.0.0.163" ]]; then
        echo "django"
    elif [[ "$ip" == "$CV_INSTANCE_IP" ]]; then
        echo "cv"
    else
        echo "unknown"
    fi
}

INSTANCE_TYPE=$(detect_instance)

case $INSTANCE_TYPE in
    "django")
        echo -e "${GREEN}🌐 Setting up Django Instance${NC}"
        echo "================================================"
        
        # Run Django instance setup
        chmod +x setup_django_instance.sh
        ./setup_django_instance.sh
        
        # Setup database
        echo ""
        echo -e "${YELLOW}🐘 Setting up Database${NC}"
        chmod +x setup_database.sh
        ./setup_database.sh
        
        # Replace CV processor with distributed version
        echo ""
        echo -e "${YELLOW}🔄 Configuring distributed CV processing${NC}"
        if [ -f "/opt/goatmorpho/app/measurements/cv_processor.py" ]; then
            sudo cp /opt/goatmorpho/app/measurements/cv_processor.py /opt/goatmorpho/app/measurements/cv_processor.py.backup
            sudo cp distributed_cv_processor.py /opt/goatmorpho/app/measurements/cv_processor.py
            sudo chown goatmorpho:goatmorpho /opt/goatmorpho/app/measurements/cv_processor.py
        fi
        
        echo ""
        echo -e "${GREEN}✅ Django Instance Setup Complete${NC}"
        echo ""
        echo "📋 Next steps for Django instance:"
        echo "1. Copy your application code to /opt/goatmorpho/app"
        echo "2. Run migrations: sudo -u goatmorpho /opt/goatmorpho/manage.sh migrate"
        echo "3. Create superuser: sudo -u goatmorpho /opt/goatmorpho/manage.sh createsuperuser"
        echo "4. Collect static files: sudo -u goatmorpho /opt/goatmorpho/manage.sh collectstatic --noinput"
        echo "5. Setup SSL: sudo certbot --nginx -d goatmorpho.info -d www.goatmorpho.info"
        echo "6. Start application: sudo systemctl start goatmorpho"
        ;;
        
    "cv")
        echo -e "${GREEN}🔬 Setting up CV Processing Instance${NC}"
        echo "================================================"
        
        # Run CV instance setup
        chmod +x setup_cv_instance.sh
        ./setup_cv_instance.sh
        
        echo ""
        echo -e "${GREEN}✅ CV Instance Setup Complete${NC}"
        echo ""
        echo "📋 Next steps for CV instance:"
        echo "1. Start CV service: sudo systemctl start cvprocessor"
        echo "2. Test service: sudo -u cvprocessor /opt/cvprocessor/venv/bin/python /opt/cvprocessor/test_service.py"
        echo "3. Check status: sudo systemctl status cvprocessor"
        ;;
        
    "unknown")
        echo -e "${RED}❌ Cannot detect instance type${NC}"
        echo "Please run this script on either:"
        echo "  - Django instance (10.0.0.163)"
        echo "  - CV instance ($CV_INSTANCE_IP)"
        echo ""
        echo "Manual setup options:"
        echo "  Django instance: ./setup_django_instance.sh"
        echo "  CV instance: ./setup_cv_instance.sh"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🚀 Instance setup completed!${NC}"
echo ""
echo "🔍 Monitoring commands:"
if [[ "$INSTANCE_TYPE" == "django" ]]; then
    echo "   Django status: sudo systemctl status goatmorpho"
    echo "   Django logs: sudo journalctl -u goatmorpho -f"
    echo "   Nginx status: sudo systemctl status nginx"
    echo "   Database: sudo -u postgres psql -d goat_morpho"
elif [[ "$INSTANCE_TYPE" == "cv" ]]; then
    echo "   CV service status: sudo systemctl status cvprocessor"
    echo "   CV service logs: sudo journalctl -u cvprocessor -f"
    echo "   Test endpoint: curl http://localhost:8001/health"
fi

echo ""
echo "📊 System monitoring:"
echo "   Resources: htop"
echo "   Disk usage: df -h"
echo "   Memory: free -h"
echo "   Network: ss -tulpn"

echo ""
echo -e "${YELLOW}⚠️  Security reminders:${NC}"
echo "1. Change default database passwords"
echo "2. Update SECRET_KEY in production settings"
echo "3. Configure proper backup procedures"
echo "4. Monitor system logs regularly"
echo "5. Keep system packages updated"

echo ""
echo -e "${GREEN}🎉 GoatMorpho deployment ready!${NC}"
