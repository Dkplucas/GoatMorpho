import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import math
from typing import Dict, List, Tuple, Optional
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
import logging

# Set up logging
logger = logging.getLogger(__name__)

class GoatMorphometryProcessor:
    """
    Computer vision processor for extracting morphometric measurements from goat images
    """
    
    def __init__(self):
        try:
            # Initialize MediaPipe pose detection
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=False,  # Disable segmentation to reduce errors
                min_detection_confidence=0.3  # Lower confidence threshold
            )
            self.mp_drawing = mp.solutions.drawing_utils
            logger.info("MediaPipe initialized successfully")
            
            # Define goat-specific keypoints mapping
            self.goat_keypoints = {
                'nose': 0,
                'left_eye': 2,
                'right_eye': 5,
                'left_ear': 7,
                'right_ear': 8,
                'left_shoulder': 11,
                'right_shoulder': 12,
                'left_elbow': 13,
                'right_elbow': 14,
                'left_wrist': 15,
                'right_wrist': 16,
                'left_hip': 23,
                'right_hip': 24,
                'left_knee': 25,
                'right_knee': 26,
                'left_ankle': 27,
                'right_ankle': 28,
            }
        except Exception as e:
            logger.error(f"Error initializing MediaPipe: {e}")
            raise
    
    def process_uploaded_image(self, uploaded_file: InMemoryUploadedFile, 
                             reference_length_cm: Optional[float] = None) -> Dict:
        """
        Process uploaded Django file with enhanced error handling
        """
        try:
            logger.info(f"Processing uploaded image: {uploaded_file.name}, size: {uploaded_file.size}")
            
            # Validate file size (max 10MB)
            if uploaded_file.size > 10 * 1024 * 1024:
                return {
                    'success': False,
                    'error': 'Image file too large (max 10MB)',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Validate file type
            valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            file_ext = uploaded_file.name.lower().split('.')[-1]
            if f'.{file_ext}' not in valid_extensions:
                return {
                    'success': False,
                    'error': f'Invalid file type. Supported: {", ".join(valid_extensions)}',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Convert uploaded file to OpenCV format
            try:
                image_array = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                
                if image is None:
                    return {
                        'success': False,
                        'error': 'Could not decode uploaded image. Please check if the file is a valid image.',
                        'measurements': {},
                        'keypoints': [],
                        'confidence_score': 0.0
                    }
                
                logger.info(f"Image decoded successfully. Shape: {image.shape}")
                
            except Exception as e:
                logger.error(f"Error decoding image: {e}")
                return {
                    'success': False,
                    'error': f'Error reading image file: {str(e)}',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            # Resize image if too large (for processing efficiency)
            height, width = image.shape[:2]
            if width > 1920 or height > 1080:
                scale_factor = min(1920/width, 1080/height)
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                image = cv2.resize(image, (new_width, new_height))
                logger.info(f"Resized image to: {new_width}x{new_height}")
            
            # Process with MediaPipe
            try:
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = self.pose.process(image_rgb)
                logger.info("MediaPipe processing completed")
                
            except Exception as e:
                logger.error(f"Error in MediaPipe processing: {e}")
                return {
                    'success': False,
                    'error': f'Error in pose detection: {str(e)}',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            if not results.pose_landmarks:
                logger.warning("No pose landmarks detected")
                return {
                    'success': False,
                    'error': 'No pose landmarks detected. Please ensure the image shows a clear view of the goat with good lighting.',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
            # Extract keypoints
            try:
                keypoints = self._extract_keypoints(results.pose_landmarks, image.shape)
                logger.info(f"Extracted {len(keypoints)} keypoints")
                
                # Calculate scale factor if reference object is provided
                scale_factor = self._calculate_scale_factor(keypoints, reference_length_cm) if reference_length_cm else 1.0
                
                # Calculate morphometric measurements
                measurements = self._calculate_measurements(keypoints, scale_factor)
                logger.info(f"Calculated {len(measurements)} measurements")
                
                # Generate processed image with annotations
                processed_image = self._annotate_image(image.copy(), results.pose_landmarks)
                
                # Calculate overall confidence score
                confidence_score = self._calculate_confidence(results.pose_landmarks)
                
                return {
                    'success': True,
                    'measurements': measurements,
                    'keypoints': keypoints,
                    'confidence_score': confidence_score,
                    'processed_image': processed_image,
                    'scale_factor': scale_factor
                }
                
            except Exception as e:
                logger.error(f"Error in measurement calculation: {e}")
                return {
                    'success': False,
                    'error': f'Error calculating measurements: {str(e)}',
                    'measurements': {},
                    'keypoints': [],
                    'confidence_score': 0.0
                }
            
        except Exception as e:
            logger.error(f"Unexpected error in image processing: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
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
        """
        Calculate scale factor based on reference object
        For now, using distance between shoulders as reference
        """
        try:
            left_shoulder = next((kp for kp in keypoints if kp['name'] == 'left_shoulder'), None)
            right_shoulder = next((kp for kp in keypoints if kp['name'] == 'right_shoulder'), None)
            
            if left_shoulder and right_shoulder:
                pixel_distance = math.sqrt(
                    (left_shoulder['x'] - right_shoulder['x'])**2 + 
                    (left_shoulder['y'] - right_shoulder['y'])**2
                )
                # Assume shoulder width is approximately 20% of reference length
                estimated_shoulder_width = reference_length_cm * 0.2
                return estimated_shoulder_width / pixel_distance if pixel_distance > 0 else 1.0
            
            return 1.0
        except Exception as e:
            logger.error(f"Error calculating scale factor: {e}")
            return 1.0
    
    def _calculate_measurements(self, keypoints: List[Dict], scale_factor: float) -> Dict:
        """Calculate morphometric measurements from keypoints"""
        measurements = {}
        
        # Create keypoint lookup dictionary
        kp_dict = {kp['name']: kp for kp in keypoints}
        
        try:
            # Height measurements (vertical distances)
            # Hauteur au garrot (Wither Height) - approximate with shoulder height
            if 'left_shoulder' in kp_dict and 'left_ankle' in kp_dict:
                wither_height_px = abs(kp_dict['left_shoulder']['y'] - kp_dict['left_ankle']['y'])
                measurements['hauteur_au_garrot'] = round(wither_height_px * scale_factor, 2)
            
            # Body Length - distance from shoulder to hip
            if 'left_shoulder' in kp_dict and 'left_hip' in kp_dict:
                body_length_px = math.sqrt(
                    (kp_dict['left_shoulder']['x'] - kp_dict['left_hip']['x'])**2 +
                    (kp_dict['left_shoulder']['y'] - kp_dict['left_hip']['y'])**2
                )
                measurements['body_length'] = round(body_length_px * scale_factor, 2)
            
            # Head Length - distance from nose to ear
            if 'nose' in kp_dict and 'left_ear' in kp_dict:
                head_length_px = math.sqrt(
                    (kp_dict['nose']['x'] - kp_dict['left_ear']['x'])**2 +
                    (kp_dict['nose']['y'] - kp_dict['left_ear']['y'])**2
                )
                measurements['longueur_tete'] = round(head_length_px * scale_factor, 2)
            
            # Head Width - distance between ears
            if 'left_ear' in kp_dict and 'right_ear' in kp_dict:
                head_width_px = math.sqrt(
                    (kp_dict['left_ear']['x'] - kp_dict['right_ear']['x'])**2 +
                    (kp_dict['left_ear']['y'] - kp_dict['right_ear']['y'])**2
                )
                measurements['largeur_tete'] = round(head_width_px * scale_factor, 2)
            
            # Chest Width - distance between shoulders
            if 'left_shoulder' in kp_dict and 'right_shoulder' in kp_dict:
                chest_width_px = math.sqrt(
                    (kp_dict['left_shoulder']['x'] - kp_dict['right_shoulder']['x'])**2 +
                    (kp_dict['left_shoulder']['y'] - kp_dict['right_shoulder']['y'])**2
                )
                measurements['largeur_poitrine'] = round(chest_width_px * scale_factor, 2)
            
            # Hip Width - distance between hips
            if 'left_hip' in kp_dict and 'right_hip' in kp_dict:
                hip_width_px = math.sqrt(
                    (kp_dict['left_hip']['x'] - kp_dict['right_hip']['x'])**2 +
                    (kp_dict['left_hip']['y'] - kp_dict['right_hip']['y'])**2
                )
                measurements['largeur_hanche'] = round(hip_width_px * scale_factor, 2)
            
            # Neck Length - distance from shoulder to head
            if 'left_shoulder' in kp_dict and 'nose' in kp_dict:
                neck_length_px = math.sqrt(
                    (kp_dict['left_shoulder']['x'] - kp_dict['nose']['x'])**2 +
                    (kp_dict['left_shoulder']['y'] - kp_dict['nose']['y'])**2
                )
                measurements['longueur_cou'] = round(neck_length_px * scale_factor, 2)
            
            logger.info(f"Successfully calculated measurements: {list(measurements.keys())}")
            
        except Exception as e:
            logger.error(f"Error calculating measurements: {e}")
        
        return measurements
    
    def _annotate_image(self, image: np.ndarray, pose_landmarks) -> np.ndarray:
        """Annotate image with detected keypoints and measurements"""
        try:
            # Draw pose landmarks
            self.mp_drawing.draw_landmarks(
                image, pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # Add title
            cv2.putText(image, 'Goat Morphometric Analysis', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            return image
        except Exception as e:
            logger.error(f"Error annotating image: {e}")
            return image
    
    def _calculate_confidence(self, pose_landmarks) -> float:
        """Calculate overall confidence score based on landmark visibility"""
        try:
            total_visibility = sum(landmark.visibility for landmark in pose_landmarks.landmark)
            avg_visibility = total_visibility / len(pose_landmarks.landmark)
            return round(avg_visibility, 3)
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
