#!/bin/bash

# GoatMorpho CV Processing Instance Setup Script
# For Oracle Cloud VM.Standard.A1.Flex (ARM64)
# Instance: cv-instance (10.0.1.25)

set -e

echo "🔬 Setting up GoatMorpho CV Processing Instance on Oracle Cloud ARM64..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install essential packages and ARM64 optimized libraries
echo "🔧 Installing essential packages..."
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    git \
    curl \
    wget \
    htop \
    vim \
    supervisor \
    ufw \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libatlas-base-dev \
    gfortran \
    python3-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    libqtgui4 \
    libqtwebkit4 \
    libqt4-test \
    python3-pyqt5 \
    libopenblas-dev \
    liblapack-dev

# Create application user
echo "👤 Creating application user..."
sudo useradd -m -s /bin/bash cvprocessor || true

# Setup application directory
echo "📁 Setting up application directory..."
sudo mkdir -p /opt/cvprocessor
sudo chown cvprocessor:cvprocessor /opt/cvprocessor

# Create Python virtual environment
echo "🐍 Creating Python virtual environment..."
sudo -u cvprocessor python3.11 -m venv /opt/cvprocessor/venv

# Install Python dependencies for CV processing
echo "📋 Installing CV processing dependencies..."
sudo -u cvprocessor bash -c "
    source /opt/cvprocessor/venv/bin/activate
    pip install --upgrade pip
    pip install wheel
    pip install numpy==1.26.4
    pip install opencv-python-headless==4.10.0.84
    pip install mediapipe==0.10.20
    pip install scikit-image==0.24.0
    pip install Pillow==11.0.0
    pip install fastapi==0.115.6
    pip install uvicorn==0.32.1
    pip install python-multipart==0.0.20
    pip install requests==2.32.3
    pip install redis==5.2.1
"

# Create CV processing service
echo "🔬 Creating CV processing service..."
sudo -u cvprocessor tee /opt/cvprocessor/cv_service.py << 'EOF'
"""
Computer Vision Processing Service for GoatMorpho
Microservice for handling CV operations on dedicated instance
"""

import os
import io
import logging
import asyncio
from typing import Optional, Dict, List
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import json
import uvicorn
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/cvprocessor/service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GoatMorpho CV Service",
    description="Computer Vision processing microservice for morphometric analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Django instance IP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection for caching
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    logger.info("Redis connection established")
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None

class GoatMorphometryProcessor:
    """
    Computer vision processor for extracting morphometric measurements from goat images
    Optimized for ARM64 Oracle Cloud instances
    """
    
    def __init__(self):
        try:
            # Initialize MediaPipe pose detection
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=1,  # Reduced for ARM64 performance
                enable_segmentation=False,
                min_detection_confidence=0.1
            )
            self.mp_drawing = mp.solutions.drawing_utils
            
            # Initialize face detection as fallback
            self.mp_face_detection = mp.solutions.face_detection
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.1
            )
            
            logger.info("MediaPipe initialized successfully")
            
            # Define goat-specific keypoints mapping
            self.goat_keypoints = {
                'nose': 0, 'left_eye': 2, 'right_eye': 5,
                'left_ear': 7, 'right_ear': 8,
                'left_shoulder': 11, 'right_shoulder': 12,
                'left_elbow': 13, 'right_elbow': 14,
                'left_wrist': 15, 'right_wrist': 16,
                'left_hip': 23, 'right_hip': 24,
                'left_knee': 25, 'right_knee': 26,
                'left_ankle': 27, 'right_ankle': 28,
            }
            
        except Exception as e:
            logger.error(f"Error initializing MediaPipe: {e}")
            raise
    
    def process_uploaded_image(self, image_bytes: bytes, reference_length_cm: Optional[float] = None) -> Dict:
        """Process uploaded image bytes and return morphometric measurements"""
        try:
            # Convert bytes to OpenCV format
            image_array = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            if image is None:
                return {
                    'success': False,
                    'error': 'Could not decode uploaded image',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Resize for processing efficiency on ARM64
            height, width = image.shape[:2]
            if width > 1280 or height > 720:
                scale_factor = min(1280/width, 720/height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = cv2.resize(image, (new_width, new_height))
                logger.info(f"Resized image to: {new_width}x{new_height}")
            
            # Process with MediaPipe
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image_rgb)
            
            if not results.pose_landmarks:
                # Try enhanced preprocessing
                enhanced_image = self._enhance_image_for_detection(image_rgb)
                results = self.pose.process(enhanced_image)
                
                if not results.pose_landmarks:
                    # Fallback to face detection
                    return self._fallback_face_detection(image_rgb, reference_length_cm)
            
            # Extract keypoints
            keypoints = self._extract_keypoints(results.pose_landmarks, image.shape)
            
            # Calculate measurements
            scale_factor = self._calculate_scale_factor(keypoints, reference_length_cm) if reference_length_cm else 1.0
            measurements = self._calculate_measurements(keypoints, scale_factor)
            
            # Generate processed image
            processed_image = self._annotate_image(image.copy(), results.pose_landmarks)
            
            # Calculate confidence
            confidence_score = self._calculate_confidence(results.pose_landmarks)
            
            return {
                'success': True,
                'measurements': measurements,
                'keypoints': keypoints,
                'confidence_score': confidence_score,
                'processed_image_shape': processed_image.shape,
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
    
    def _extract_keypoints(self, pose_landmarks, image_shape) -> List[Dict]:
        """Extract keypoint coordinates from pose landmarks"""
        height, width = image_shape[:2]
        keypoints = []
        
        for name, idx in self.goat_keypoints.items():
            if idx < len(pose_landmarks.landmark):
                landmark = pose_landmarks.landmark[idx]
                keypoints.append({
                    'name': name,
                    'x': landmark.x * width,
                    'y': landmark.y * height,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                })
        
        return keypoints
    
    def _calculate_scale_factor(self, keypoints: List[Dict], reference_length_cm: float) -> float:
        """Calculate scale factor based on reference object"""
        # Simplified scaling for ARM64 performance
        return reference_length_cm / 100.0 if reference_length_cm else 1.0
    
    def _calculate_measurements(self, keypoints: List[Dict], scale_factor: float) -> Dict:
        """Calculate morphometric measurements from keypoints"""
        measurements = {}
        kp_dict = {kp['name']: kp for kp in keypoints}
        
        try:
            # Basic measurements for demonstration
            if 'left_shoulder' in kp_dict and 'left_ankle' in kp_dict:
                height_px = abs(kp_dict['left_shoulder']['y'] - kp_dict['left_ankle']['y'])
                measurements['hauteur_au_garrot'] = round(height_px * scale_factor, 2)
            
            if 'left_shoulder' in kp_dict and 'left_hip' in kp_dict:
                length_px = ((kp_dict['left_shoulder']['x'] - kp_dict['left_hip']['x'])**2 + 
                           (kp_dict['left_shoulder']['y'] - kp_dict['left_hip']['y'])**2)**0.5
                measurements['body_length'] = round(length_px * scale_factor, 2)
            
        except Exception as e:
            logger.error(f"Error calculating measurements: {e}")
        
        return measurements
    
    def _enhance_image_for_detection(self, image_rgb):
        """Enhance image for better detection"""
        try:
            # Simple contrast enhancement
            lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
            l_channel, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            l_channel = clahe.apply(l_channel)
            lab = cv2.merge((l_channel, a, b))
            return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        except:
            return image_rgb
    
    def _fallback_face_detection(self, image_rgb, reference_length_cm=None):
        """Fallback using face detection"""
        return {
            'success': False,
            'error': 'Pose detection failed, face detection not implemented in this version',
            'measurements': {},
            'keypoints': [],
            'confidence_score': 0.0
        }
    
    def _annotate_image(self, image, pose_landmarks):
        """Annotate image with landmarks"""
        self.mp_drawing.draw_landmarks(image, pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
        return image
    
    def _calculate_confidence(self, pose_landmarks) -> float:
        """Calculate confidence score"""
        total_visibility = sum(landmark.visibility for landmark in pose_landmarks.landmark)
        return round(total_visibility / len(pose_landmarks.landmark), 3)

# Initialize processor
processor = GoatMorphometryProcessor()

@app.get("/")
async def root():
    return {"message": "GoatMorpho CV Processing Service", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cv-processor"}

@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    reference_length_cm: Optional[float] = None
):
    """Process goat image for morphometric measurements"""
    try:
        # Validate file
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image bytes
        image_bytes = await file.read()
        
        if len(image_bytes) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
        
        # Process image
        result = processor.process_uploaded_image(image_bytes, reference_length_cm)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "cv_service:app",
        host="0.0.0.0",
        port=8001,
        workers=2,  # Conservative for ARM64
        loop="asyncio"
    )
EOF

# Create environment file for CV service
echo "🔐 Creating CV service environment..."
sudo -u cvprocessor tee /opt/cvprocessor/.env << EOF
# CV Processing Service Configuration
LOG_LEVEL=INFO
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
WORKERS=2
EOF

# Setup directories
echo "📂 Setting up directories..."
sudo mkdir -p /var/log/cvprocessor
sudo chown -R cvprocessor:cvprocessor /var/log/cvprocessor

# Create systemd service for CV processor
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/cvprocessor.service << EOF
[Unit]
Description=GoatMorpho CV Processing Service
After=network.target

[Service]
Type=exec
User=cvprocessor
Group=cvprocessor
WorkingDirectory=/opt/cvprocessor
Environment=PATH=/opt/cvprocessor/venv/bin
EnvironmentFile=/opt/cvprocessor/.env
ExecStart=/opt/cvprocessor/venv/bin/python cv_service.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall (only allow internal communication)
echo "🔥 Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow from 10.0.0.0/24 to any port 8001  # Allow from Django instance subnet
sudo ufw --force enable

# Setup log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/cvprocessor << EOF
/var/log/cvprocessor/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 cvprocessor cvprocessor
    postrotate
        systemctl reload cvprocessor
    endscript
}
EOF

# Create test script
echo "🧪 Creating test script..."
sudo -u cvprocessor tee /opt/cvprocessor/test_service.py << 'EOF'
#!/usr/bin/env python3
import requests
import sys

def test_cv_service():
    """Test CV processing service"""
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ CV Service is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_cv_service()
    sys.exit(0 if success else 1)
EOF

sudo chmod +x /opt/cvprocessor/test_service.py

# Enable and start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable cvprocessor

echo "✅ CV Processing instance setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Start the CV service: sudo systemctl start cvprocessor"
echo "2. Test the service: sudo -u cvprocessor /opt/cvprocessor/venv/bin/python /opt/cvprocessor/test_service.py"
echo "3. Check service status: sudo systemctl status cvprocessor"
echo ""
echo "🔍 Useful commands:"
echo "   Service status: sudo systemctl status cvprocessor"
echo "   View logs: sudo journalctl -u cvprocessor -f"
echo "   Service logs: sudo tail -f /var/log/cvprocessor/service.log"
echo "   Test endpoint: curl http://localhost:8001/health"
echo ""
echo "🌐 Service will be available at:"
echo "   Internal: http://10.0.1.25:8001"
echo "   Health check: http://10.0.1.25:8001/health"
echo "   Processing: POST http://10.0.1.25:8001/process"
