#!/bin/bash

# Quick fix for Python version issue
# Run this to continue your deployment

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   log_error "This script must be run as root (use sudo)"
   exit 1
fi

log_info "Fixing Python installation issue..."

# Detect Python version
log_info "Detecting available Python version..."
if command -v python3.12 &> /dev/null; then
    PYTHON_VERSION="3.12"
    PYTHON_CMD="python3.12"
    log_success "Found Python 3.12"
elif command -v python3.11 &> /dev/null; then
    PYTHON_VERSION="3.11"
    PYTHON_CMD="python3.11"
    log_success "Found Python 3.11"
else
    PYTHON_VERSION="3"
    PYTHON_CMD="python3"
    log_success "Using default Python 3"
fi

# Install Python packages with correct version
log_info "Installing Python packages for version $PYTHON_VERSION..."
apt update

# Install essential Python packages
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

log_success "Python packages installed successfully!"
log_info "You can now continue with the deployment."
log_info "Run: ./single_instance_deploy.sh"
