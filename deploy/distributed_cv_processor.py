"""
Modified CV processor for distributed architecture
Sends CV processing requests to dedicated CV instance
"""

import requests
import json
import logging
from typing import Dict, Optional
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings

logger = logging.getLogger(__name__)

class GoatMorphometryProcessor:
    """
    Distributed CV processor that communicates with dedicated CV instance
    """
    
    def __init__(self):
        self.cv_service_url = getattr(settings, 'CV_PROCESSING_URL', 'http://10.0.1.25:8001')
        self.timeout = getattr(settings, 'CV_PROCESSING_TIMEOUT', 120)
        logger.info(f"Initialized distributed CV processor with URL: {self.cv_service_url}")
    
    def process_uploaded_image(self, uploaded_file: InMemoryUploadedFile, 
                             reference_length_cm: Optional[float] = None) -> Dict:
        """
        Process uploaded Django file by sending to CV service
        """
        try:
            logger.info(f"Processing uploaded image: {uploaded_file.name}, size: {uploaded_file.size}")
            
            # Validate file size
            if uploaded_file.size > 10 * 1024 * 1024:
                return {
                    'success': False,
                    'error': 'Image file too large (max 10MB)',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Prepare file for upload
            uploaded_file.seek(0)
            files = {
                'file': (uploaded_file.name, uploaded_file.read(), uploaded_file.content_type)
            }
            
            # Prepare data
            data = {}
            if reference_length_cm:
                data['reference_length_cm'] = reference_length_cm
            
            # Send request to CV service
            response = requests.post(
                f"{self.cv_service_url}/process",
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"CV processing successful, confidence: {result.get('confidence_score', 0)}")
                
                # Add processed image placeholder (actual image would be handled differently in production)
                if result.get('success'):
                    result['processed_image'] = None  # Placeholder
                
                return result
            else:
                logger.error(f"CV service error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'CV service error: {response.status_code}',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
                
        except requests.exceptions.Timeout:
            logger.error("CV service timeout")
            return {
                'success': False,
                'error': 'CV processing timeout - please try again',
                'measurements': {},
                'keypoints': [],
                'confidence_score': 0.0
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to CV service at {self.cv_service_url}")
            return {
                'success': False,
                'error': 'CV processing service unavailable',
                'measurements': {},
                'keypoints': [],
                'confidence_score': 0.0
            }
        except Exception as e:
            logger.error(f"Unexpected error in distributed CV processing: {e}")
            return {
                'success': False,
                'error': f'Processing error: {str(e)}',
                'measurements': {},
                'keypoints': [],
                'confidence_score': 0.0
            }
        finally:
            # Reset file pointer
            uploaded_file.seek(0)
    
    def process_image(self, image_path: str, reference_length_cm: Optional[float] = None) -> Dict:
        """
        Process image file by path (for testing/batch processing)
        """
        try:
            with open(image_path, 'rb') as f:
                files = {'file': ('image.jpg', f.read(), 'image/jpeg')}
            
            data = {}
            if reference_length_cm:
                data['reference_length_cm'] = reference_length_cm
            
            response = requests.post(
                f"{self.cv_service_url}/process",
                files=files,
                data=data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'CV service error: {response.status_code}',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
                
        except Exception as e:
            logger.error(f"Error processing image file: {e}")
            return {
                'success': False,
                'error': f'Processing error: {str(e)}',
                'measurements': {},
                'keypoints': [],
                'confidence_score': 0.0
            }
    
    def health_check(self) -> bool:
        """
        Check if CV service is available
        """
        try:
            response = requests.get(f"{self.cv_service_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
