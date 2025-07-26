#!/bin/bash

# GoatMorpho Budget Deployment Script for Oracle Cloud
# Single instance setup for cost optimization
# Target: VM.Standard.A1.Flex (2 OCPU, 12GB RAM) - Always Free Tier Eligible

set -e

echo "💰 GoatMorpho Budget Deployment for Oracle Cloud"
echo "================================================"
echo "Single instance architecture optimized for cost"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="goatmorpho.info"
PUBLIC_IP="130.61.39.212"

echo -e "${BLUE}📋 Budget Configuration:${NC}"
echo "   Instance: Single VM.Standard.A1.Flex"
echo "   Resources: 2 OCPU, 12GB RAM"
echo "   Domain: $DOMAIN"
echo "   Public IP: $PUBLIC_IP"
echo "   Database: SQLite (no separate DB instance)"
echo "   Cache: File-based (no Redis instance)"
echo ""

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Install essential packages (minimal set)
echo -e "${YELLOW}🔧 Installing essential packages...${NC}"
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    nginx \
    git \
    curl \
    wget \
    htop \
    vim \
    certbot \
    python3-certbot-nginx \
    supervisor \
    ufw \
    build-essential \
    pkg-config \
    libjpeg-dev \
    libpng-dev

# Create application user
echo -e "${YELLOW}👤 Creating application user...${NC}"
sudo useradd -m -s /bin/bash goatmorpho || true
sudo usermod -aG www-data goatmorpho

# Setup application directory
echo -e "${YELLOW}📁 Setting up application directory...${NC}"
sudo mkdir -p /opt/goatmorpho
sudo chown goatmorpho:goatmorpho /opt/goatmorpho

# Create Python virtual environment
echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
sudo -u goatmorpho python3.11 -m venv /opt/goatmorpho/venv

# Install minimal Python dependencies
echo -e "${YELLOW}📋 Installing minimal Python dependencies...${NC}"
sudo -u goatmorpho bash -c "
    source /opt/goatmorpho/venv/bin/activate
    pip install --upgrade pip
    pip install wheel
    
    # Core Django dependencies
    pip install Django==5.2.4
    pip install djangorestframework==3.15.2
    pip install django-cors-headers==4.6.0
    pip install gunicorn==23.0.0
    pip install whitenoise==6.8.2
    pip install Pillow==11.0.0
    pip install pandas==2.2.3
    pip install openpyxl==3.1.5
    pip install requests==2.32.3
    
    # Lightweight CV libraries for ARM64
    pip install opencv-python-headless==4.10.0.84
    pip install mediapipe==0.10.20
    pip install scikit-image==0.24.0
    pip install numpy==1.26.4
"

# Setup directories
echo -e "${YELLOW}📂 Setting up directories...${NC}"
sudo mkdir -p /opt/goatmorpho/app/media/goat_images/{original,processed,samples}
sudo mkdir -p /opt/goatmorpho/app/staticfiles
sudo mkdir -p /tmp/django_cache
sudo chown -R goatmorpho:www-data /opt/goatmorpho/app/media
sudo chown -R goatmorpho:www-data /opt/goatmorpho/app/staticfiles
sudo chown -R goatmorpho:www-data /tmp/django_cache

# Create environment variables file
echo -e "${YELLOW}🔐 Creating environment file...${NC}"
sudo -u goatmorpho tee /opt/goatmorpho/.env << EOF
# Django Settings for Budget Deployment
DJANGO_SECRET_KEY=your-super-secret-key-change-this-in-production
DJANGO_SETTINGS_MODULE=goat_morpho.budget_settings
DEBUG=False

# No external database or cache needed for budget deployment
# SQLite and file cache are configured in settings
EOF

# Create Gunicorn configuration (optimized for 2 OCPU)
echo -e "${YELLOW}🦄 Creating Gunicorn configuration...${NC}"
sudo -u goatmorpho tee /opt/goatmorpho/gunicorn.conf.py << EOF
# Gunicorn configuration for Budget GoatMorpho deployment
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 1024

# Worker processes (conservative for budget instance)
workers = 2  # Perfect for 2 OCPU
worker_class = "sync"
worker_connections = 500
timeout = 60  # Reduced timeout for budget
keepalive = 2

# Restart workers after processing requests
max_requests = 500
max_requests_jitter = 25

# Logging
accesslog = "/opt/goatmorpho/logs/gunicorn_access.log"
errorlog = "/opt/goatmorpho/logs/gunicorn_error.log"
loglevel = "warning"  # Reduced logging for budget

# Process naming
proc_name = 'goatmorpho_budget'

# Server mechanics
preload_app = True
daemon = False
pidfile = "/opt/goatmorpho/gunicorn.pid"
user = "goatmorpho"
group = "goatmorpho"
tmp_upload_dir = None

# SSL settings
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
}
EOF

# Create log directory
sudo mkdir -p /opt/goatmorpho/logs
sudo chown goatmorpho:goatmorpho /opt/goatmorpho/logs

# Create systemd service for Gunicorn
echo -e "${YELLOW}🔧 Creating systemd service...${NC}"
sudo tee /etc/systemd/system/goatmorpho.service << EOF
[Unit]
Description=GoatMorpho Budget Django Application
After=network.target

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

# Configure Nginx (optimized for single instance)
echo -e "${YELLOW}🌐 Configuring Nginx...${NC}"
sudo tee /etc/nginx/sites-available/goatmorpho << EOF
# Nginx configuration for Budget GoatMorpho
upstream goatmorpho_django {
    server 127.0.0.1:8000 fail_timeout=0;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name goatmorpho.info www.goatmorpho.info;
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server (simplified for budget)
server {
    listen 443 ssl http2;
    server_name goatmorpho.info www.goatmorpho.info;

    # SSL configuration (will be configured by certbot)
    ssl_certificate /etc/letsencrypt/live/goatmorpho.info/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/goatmorpho.info/privkey.pem;
    
    # Basic SSL security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    
    # Basic security headers
    add_header X-Frame-Options SAMEORIGIN always;
    add_header X-Content-Type-Options nosniff always;

    # Upload size limit (reduced for budget)
    client_max_body_size 6M;

    # Static files
    location /static/ {
        alias /opt/goatmorpho/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Media files
    location /media/ {
        alias /opt/goatmorpho/app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Django application
    location / {
        proxy_pass http://goatmorpho_django;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Health check
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

# Configure firewall (minimal for budget)
echo -e "${YELLOW}🔥 Configuring firewall...${NC}"
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Start Nginx
echo -e "${YELLOW}🚀 Starting services...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable nginx
sudo systemctl start nginx

# Create Django management script
echo -e "${YELLOW}🐍 Creating Django management script...${NC}"
sudo -u goatmorpho tee /opt/goatmorpho/manage.sh << 'EOF'
#!/bin/bash
source /opt/goatmorpho/venv/bin/activate
source /opt/goatmorpho/.env
cd /opt/goatmorpho/app
python manage.py "$@"
EOF
sudo chmod +x /opt/goatmorpho/manage.sh

# Create simple CV processor (integrated, not distributed)
echo -e "${YELLOW}🔬 Creating integrated CV processor...${NC}"
sudo -u goatmorpho tee /opt/goatmorpho/integrated_cv_processor.py << 'EOF'
"""
Integrated CV processor for budget deployment
Runs CV processing in the same instance as Django
"""

import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import math
from typing import Dict, List, Tuple, Optional
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
import logging

logger = logging.getLogger(__name__)

class GoatMorphometryProcessor:
    """
    Lightweight CV processor for budget deployment
    Optimized for ARM64 and limited resources
    """
    
    def __init__(self):
        try:
            # Initialize MediaPipe with minimal resources
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=0,  # Lightest model for budget
                enable_segmentation=False,
                min_detection_confidence=0.3  # Higher threshold for reliability
            )
            self.mp_drawing = mp.solutions.drawing_utils
            
            # Goat keypoints mapping (essential ones only)
            self.goat_keypoints = {
                'nose': 0, 'left_shoulder': 11, 'right_shoulder': 12,
                'left_hip': 23, 'right_hip': 24,
                'left_knee': 25, 'right_knee': 26,
                'left_ankle': 27, 'right_ankle': 28,
            }
            
            logger.info("Budget CV processor initialized")
            
        except Exception as e:
            logger.error(f"Error initializing CV processor: {e}")
            raise
    
    def process_uploaded_image(self, uploaded_file: InMemoryUploadedFile, 
                             reference_length_cm: Optional[float] = None) -> Dict:
        """Process uploaded image with resource optimization"""
        try:
            # Validate file size (reduced for budget)
            if uploaded_file.size > 5 * 1024 * 1024:  # 5MB limit
                return {
                    'success': False,
                    'error': 'Image too large (max 5MB for budget deployment)',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Convert to OpenCV format
            image_array = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                return {
                    'success': False,
                    'error': 'Could not decode image',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Resize for budget processing (smaller images)
            height, width = image.shape[:2]
            if width > 800 or height > 600:
                scale = min(800/width, 600/height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height))
                logger.info(f"Resized to {new_width}x{new_height} for budget processing")
            
            # Process with MediaPipe
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)
            
            if not results.pose_landmarks:
                return {
                    'success': False,
                    'error': 'No pose detected. Try a clearer side-view image.',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Extract keypoints
            keypoints = self._extract_keypoints(results.pose_landmarks, image.shape)
            
            # Calculate basic measurements
            scale_factor = reference_length_cm / 100.0 if reference_length_cm else 1.0
            measurements = self._calculate_basic_measurements(keypoints, scale_factor)
            
            # Calculate confidence
            confidence_score = self._calculate_confidence(results.pose_landmarks)
            
            return {
                'success': True,
                'measurements': measurements,
                'keypoints': keypoints,
                'confidence_score': confidence_score,
                'processed_image': None,  # Skip processed image to save memory
                'scale_factor': scale_factor
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {
                'success': False,
                'error': f'Processing error: {str(e)}',
                'measurements': {},
                'keypoints': [],
                'confidence_score': 0.0
            }
        finally:
            uploaded_file.seek(0)
    
    def _extract_keypoints(self, pose_landmarks, image_shape) -> List[Dict]:
        """Extract essential keypoints only"""
        height, width = image_shape[:2]
        keypoints = []
        
        for name, idx in self.goat_keypoints.items():
            if idx < len(pose_landmarks.landmark):
                landmark = pose_landmarks.landmark[idx]
                keypoints.append({
                    'name': name,
                    'x': landmark.x * width,
                    'y': landmark.y * height,
                    'visibility': landmark.visibility
                })
        
        return keypoints
    
    def _calculate_basic_measurements(self, keypoints: List[Dict], scale_factor: float) -> Dict:
        """Calculate basic measurements for budget deployment"""
        measurements = {}
        kp_dict = {kp['name']: kp for kp in keypoints}
        
        try:
            # Height (wither height approximation)
            if 'left_shoulder' in kp_dict and 'left_ankle' in kp_dict:
                height_px = abs(kp_dict['left_shoulder']['y'] - kp_dict['left_ankle']['y'])
                measurements['hauteur_au_garrot'] = round(height_px * scale_factor, 2)
            
            # Body length
            if 'left_shoulder' in kp_dict and 'left_hip' in kp_dict:
                length_px = math.sqrt(
                    (kp_dict['left_shoulder']['x'] - kp_dict['left_hip']['x'])**2 +
                    (kp_dict['left_shoulder']['y'] - kp_dict['left_hip']['y'])**2
                )
                measurements['body_length'] = round(length_px * scale_factor, 2)
            
            # Chest width approximation
            if 'left_shoulder' in kp_dict and 'right_shoulder' in kp_dict:
                width_px = abs(kp_dict['left_shoulder']['x'] - kp_dict['right_shoulder']['x'])
                measurements['largeur_poitrine'] = round(width_px * scale_factor, 2)
            
        except Exception as e:
            logger.error(f"Error calculating measurements: {e}")
        
        return measurements
    
    def _calculate_confidence(self, pose_landmarks) -> float:
        """Calculate simple confidence score"""
        total_visibility = sum(landmark.visibility for landmark in pose_landmarks.landmark)
        return round(total_visibility / len(pose_landmarks.landmark), 3)
EOF

# Setup log rotation (simplified)
echo -e "${YELLOW}📋 Setting up log rotation...${NC}"
sudo tee /etc/logrotate.d/goatmorpho << EOF
/opt/goatmorpho/logs/*.log {
    weekly
    missingok
    rotate 4
    compress
    delaycompress
    notifempty
    create 644 goatmorpho goatmorpho
    postrotate
        systemctl reload goatmorpho
    endscript
}
EOF

echo -e "${GREEN}✅ Budget deployment setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Point your domain DNS to $PUBLIC_IP"
echo "2. Copy your application code to /opt/goatmorpho/app"
echo "3. Replace cv_processor.py with integrated version:"
echo "   sudo cp /opt/goatmorpho/integrated_cv_processor.py /opt/goatmorpho/app/measurements/cv_processor.py"
echo "4. Run migrations: sudo -u goatmorpho /opt/goatmorpho/manage.sh migrate"
echo "5. Create superuser: sudo -u goatmorpho /opt/goatmorpho/manage.sh createsuperuser"
echo "6. Collect static files: sudo -u goatmorpho /opt/goatmorpho/manage.sh collectstatic --noinput"
echo "7. Setup SSL: sudo certbot --nginx -d goatmorpho.info -d www.goatmorpho.info"
echo "8. Start application: sudo systemctl start goatmorpho"
echo ""
echo -e "${YELLOW}💰 Budget Optimization Features:${NC}"
echo "• Single instance architecture"
echo "• SQLite database (no separate DB instance)"
echo "• File-based caching (no Redis instance)"
echo "• Integrated CV processing"
echo "• Reduced resource usage"
echo "• Simplified logging"
echo ""
echo -e "${GREEN}💵 Estimated Monthly Cost: \$15-35 USD${NC}"
echo "   (Using Oracle Cloud Always Free Tier + minimal paid resources)"
echo ""
echo -e "${BLUE}🔍 Useful commands:${NC}"
echo "   Check status: sudo systemctl status goatmorpho nginx"
echo "   View logs: sudo journalctl -u goatmorpho -f"
echo "   Monitor resources: htop"
