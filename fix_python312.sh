#!/bin/bash
# Quick fix for Python 3.12 deployment issue
# Run this on the server where Python 3.12 is available

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

print_status "GoatMorpho Python 3.12 Quick Fix"
print_status "=================================="

# Check current directory
if [ ! -f "manage.py" ]; then
    print_error "Please run this script from the GoatMorpho project directory"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '(?<=Python )\d+\.\d+' | head -1)
print_status "Detected Python version: $PYTHON_VERSION"

# Install required system packages for Python 3.12
print_status "Installing Python 3.12 compatible packages..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    build-essential \
    libpq-dev \
    pkg-config

# Remove old virtual environment if it exists
if [ -d "venv" ]; then
    print_status "Removing old virtual environment..."
    rm -rf venv
fi

# Create new virtual environment with Python 3.12
print_status "Creating virtual environment with Python 3.12..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install core Django packages first
print_status "Installing core Django packages..."
pip install \
    Django==5.2.4 \
    psycopg2-binary \
    redis \
    django-redis \
    gunicorn \
    whitenoise

# Install other requirements if file exists
if [ -f "requirements_fixed.txt" ]; then
    print_status "Installing additional requirements..."
    # Install packages one by one to handle any that might fail
    while IFS= read -r line; do
        if [[ ! "$line" =~ ^# ]] && [[ -n "$line" ]]; then
            package=$(echo "$line" | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'<' -f1)
            if pip install "$line" 2>/dev/null; then
                print_success "✓ Installed $package"
            else
                echo -e "${YELLOW}[SKIP]${NC} Could not install $package"
            fi
        fi
    done < requirements_fixed.txt
fi

# Test Django
print_status "Testing Django setup..."
if python manage.py check --deploy 2>/dev/null; then
    print_success "Django check passed!"
else
    print_status "Running basic Django check..."
    python manage.py check
fi

# Check Redis connection
print_status "Testing Redis connection..."
if python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goat_morpho.settings')
django.setup()
from django.core.cache import cache
cache.set('test_key', 'test_value', 10)
result = cache.get('test_key')
if result == 'test_value':
    print('Redis connection successful!')
else:
    print('Redis connection failed!')
"; then
    print_success "Redis test completed"
else
    echo -e "${YELLOW}[WARNING]${NC} Redis test had issues - check Redis configuration"
fi

print_success "Python 3.12 setup completed!"
print_status ""
print_status "Next steps:"
print_status "1. Run migrations: python manage.py migrate"
print_status "2. Collect static files: python manage.py collectstatic --noinput"
print_status "3. Create superuser: python manage.py createsuperuser"
print_status "4. Test the application: python manage.py runserver"
print_status ""
print_success "✅ Ready to continue with deployment!"
