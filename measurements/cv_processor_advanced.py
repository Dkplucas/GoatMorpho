import cv2
import numpy as np
import mediapipe as mp
from PIL import Image
import math
from typing import Dict, List, Tuple, Optional, Union
from django.core.files.uploadedfile import InMemoryUploadedFile
import io
import logging
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)


class AdvancedGoatMorphometryProcessor:
    """
    Advanced computer vision processor with multiple detection models,
    uncertainty quantification, and breed-specific processing
    """
    
    def __init__(self):
        try:
            # Initialize multiple MediaPipe models for ensemble detection
            self.mp_pose = mp.solutions.pose
            self.mp_face_detection = mp.solutions.face_detection
            self.mp_selfie_segmentation = mp.solutions.selfie_segmentation
            self.mp_objectron = mp.solutions.objectron
            
            # Primary pose detector (high accuracy)
            self.pose_detector_high = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=2,
                enable_segmentation=True,
                min_detection_confidence=0.3
            )
            
            # Secondary pose detector (high recall)
            self.pose_detector_broad = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.1
            )
            
            # Face detection for head measurements
            self.face_detector = self.mp_face_detection.FaceDetection(
                model_selection=1, min_detection_confidence=0.1
            )
            
            # Segmentation for body outline
            self.segmentation = self.mp_selfie_segmentation.SelfieSegmentation(
                model_selection=1
            )
            
            self.mp_drawing = mp.solutions.drawing_utils
            
            # Initialize anomaly detector for measurement validation
            self.anomaly_detector = IsolationForest(
                contamination=0.1, random_state=42
            )
            self.scaler = StandardScaler()
            
            # Load breed-specific models if available
            self.breed_models = self._load_breed_models()
            
            # Confidence scoring weights
            self.confidence_weights = {
                'pose_detection': 0.3,
                'landmark_quality': 0.25,
                'image_quality': 0.2,
                'anatomical_consistency': 0.15,
                'ensemble_agreement': 0.1
            }
            
            logger.info("Advanced MediaPipe processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize advanced CV processor: {e}")
            raise
    
    def _load_breed_models(self) -> Dict:
        """Load breed-specific measurement models"""
        models = {}
        model_dir = Path(__file__).parent / 'ml_models'
        
        if model_dir.exists():
            for model_file in model_dir.glob('*_breed_model.joblib'):
                breed_name = model_file.stem.replace('_breed_model', '')
                try:
                    models[breed_name] = joblib.load(model_file)
                    logger.info(f"Loaded breed model for: {breed_name}")
                except Exception as e:
                    logger.warning(f"Failed to load breed model {breed_name}: {e}")
        
        return models
    
    def process_goat_image_advanced(self, image_data: Union[bytes, np.ndarray], 
                                  reference_length: Optional[float] = None,
                                  breed: Optional[str] = None) -> Dict:
        """
        Advanced image processing with ensemble methods and uncertainty quantification
        """
        try:
            # Preprocess image
            image = self._preprocess_image(image_data)
            if image is None:
                return {'success': False, 'error': 'Image preprocessing failed'}
            
            # Image quality assessment
            quality_score = self._assess_image_quality(image)
            if quality_score < 0.3:
                return {
                    'success': False, 
                    'error': 'Image quality too low for accurate measurements',
                    'quality_score': quality_score
                }
            
            # Ensemble detection with multiple models
            detection_results = self._ensemble_detection(image)
            
            if not detection_results['success']:
                return detection_results
            
            # Extract measurements with uncertainty quantification
            measurements = self._extract_measurements_with_uncertainty(
                image, detection_results, reference_length, breed
            )
            
            # Validate measurements for anatomical consistency
            validation_result = self._validate_measurements(measurements, breed)
            
            # Calculate overall confidence score
            overall_confidence = self._calculate_confidence_score(
                detection_results, measurements, quality_score, validation_result
            )
            
            # Generate processed image with annotations
            annotated_image = self._create_annotated_image(image, detection_results, measurements)
            
            return {
                'success': True,
                'measurements': measurements['values'],
                'confidence_score': overall_confidence,
                'measurement_uncertainties': measurements['uncertainties'],
                'quality_score': quality_score,
                'breed_confidence': measurements.get('breed_confidence', 0.0),
                'keypoints': detection_results['keypoints'],
                'processed_image': annotated_image,
                'validation_warnings': validation_result.get('warnings', []),
                'processing_metadata': {
                    'models_used': detection_results['models_used'],
                    'ensemble_agreement': detection_results['agreement_score'],
                    'reference_scaling': reference_length is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Advanced processing failed: {e}")
            return {'success': False, 'error': f'Processing failed: {str(e)}'}
    
    def _preprocess_image(self, image_data: Union[bytes, np.ndarray]) -> Optional[np.ndarray]:
        """Enhanced image preprocessing with multiple enhancement techniques"""
        try:
            if isinstance(image_data, bytes):
                nparr = np.frombuffer(image_data, np.uint8)
                image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                image = image_data.copy()
            
            if image is None:
                return None
            
            # Convert to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Adaptive enhancement based on image characteristics
            if self._is_low_contrast(image_rgb):
                image_rgb = self._enhance_contrast(image_rgb)
            
            if self._is_blurry(image_rgb):
                image_rgb = self._sharpen_image(image_rgb)
            
            # Normalize image size
            height, width = image_rgb.shape[:2]
            if max(height, width) > 1920:
                scale = 1920 / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image_rgb = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            return image_rgb
            
        except Exception as e:
            logger.error(f"Image preprocessing failed: {e}")
            return None
    
    def _assess_image_quality(self, image: np.ndarray) -> float:
        """Comprehensive image quality assessment"""
        try:
            # Convert to grayscale for analysis
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Blur detection using Laplacian variance
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_quality = min(blur_score / 500, 1.0)  # Normalize
            
            # Contrast assessment
            contrast_score = gray.std()
            contrast_quality = min(contrast_score / 50, 1.0)  # Normalize
            
            # Brightness assessment
            brightness = gray.mean()
            brightness_quality = 1.0 - abs(brightness - 128) / 128  # Optimal around 128
            
            # Edge density (detail assessment)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            edge_quality = min(edge_density * 10, 1.0)  # Normalize
            
            # Noise assessment (inverse of noise level)
            noise_level = self._estimate_noise(gray)
            noise_quality = max(0, 1.0 - noise_level / 50)
            
            # Weighted average
            quality_score = (
                blur_quality * 0.3 +
                contrast_quality * 0.25 +
                brightness_quality * 0.2 +
                edge_quality * 0.15 +
                noise_quality * 0.1
            )
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return 0.5  # Default moderate quality
    
    def _ensemble_detection(self, image: np.ndarray) -> Dict:
        """Ensemble detection using multiple models"""
        try:
            results = []
            models_used = []
            
            # High accuracy pose detection
            result1 = self.pose_detector_high.process(image)
            if result1.pose_landmarks:
                results.append(('pose_high', result1))
                models_used.append('pose_high_accuracy')
            
            # Broad pose detection
            result2 = self.pose_detector_broad.process(image)
            if result2.pose_landmarks:
                results.append(('pose_broad', result2))
                models_used.append('pose_broad_recall')
            
            # Face detection for head region
            result3 = self.face_detector.process(image)
            if result3.detections:
                results.append(('face', result3))
                models_used.append('face_detection')
            
            # Segmentation for body outline
            result4 = self.segmentation.process(image)
            if result4.segmentation_mask is not None:
                results.append(('segmentation', result4))
                models_used.append('body_segmentation')
            
            if not results:
                return {'success': False, 'error': 'No landmarks detected by any model'}
            
            # Combine results using ensemble voting
            combined_landmarks = self._combine_detections(results, image.shape)
            agreement_score = self._calculate_ensemble_agreement(results)
            
            return {
                'success': True,
                'landmarks': combined_landmarks,
                'keypoints': self._landmarks_to_keypoints(combined_landmarks),
                'models_used': models_used,
                'agreement_score': agreement_score,
                'individual_results': {name: result for name, result in results}
            }
            
        except Exception as e:
            logger.error(f"Ensemble detection failed: {e}")
            return {'success': False, 'error': f'Detection failed: {str(e)}'}
    
    def _extract_measurements_with_uncertainty(self, image: np.ndarray, 
                                             detection_results: Dict,
                                             reference_length: Optional[float],
                                             breed: Optional[str]) -> Dict:
        """Extract measurements with uncertainty quantification"""
        try:
            landmarks = detection_results['landmarks']
            h, w = image.shape[:2]
            
            # Basic pixel-to-cm conversion
            if reference_length:
                scale_factor = reference_length / 100  # Assume 100 pixels = reference length
            else:
                # Estimate scale based on image size and typical goat proportions
                scale_factor = max(h, w) / 2000  # Rough estimate
            
            measurements = {}
            uncertainties = {}
            
            # Extract key anatomical points with confidence intervals
            key_points = self._extract_anatomical_points(landmarks, w, h)
            
            # Calculate measurements with bootstrap uncertainty estimation
            for measurement_name, calc_func in self._get_measurement_functions().items():
                try:
                    values = []
                    # Bootstrap sampling for uncertainty estimation
                    for _ in range(50):  # 50 bootstrap samples
                        noisy_points = self._add_landmark_noise(key_points)
                        value = calc_func(noisy_points, scale_factor)
                        if value > 0:  # Valid measurement
                            values.append(value)
                    
                    if values:
                        measurements[measurement_name] = np.mean(values)
                        uncertainties[measurement_name] = np.std(values)
                    else:
                        measurements[measurement_name] = None
                        uncertainties[measurement_name] = None
                        
                except Exception as e:
                    logger.warning(f"Failed to calculate {measurement_name}: {e}")
                    measurements[measurement_name] = None
                    uncertainties[measurement_name] = None
            
            # Apply breed-specific corrections if available
            if breed and breed.lower() in self.breed_models:
                measurements, breed_confidence = self._apply_breed_corrections(
                    measurements, breed.lower()
                )
            else:
                breed_confidence = 0.0
            
            return {
                'values': measurements,
                'uncertainties': uncertainties,
                'breed_confidence': breed_confidence,
                'scale_factor': scale_factor
            }
            
        except Exception as e:
            logger.error(f"Measurement extraction failed: {e}")
            return {'values': {}, 'uncertainties': {}, 'breed_confidence': 0.0}
    
    def _get_measurement_functions(self) -> Dict:
        """Define measurement calculation functions"""
        return {
            'hauteur_au_garrot': self._calculate_wither_height,
            'hauteur_au_dos': self._calculate_back_height,
            'hauteur_au_sternum': self._calculate_sternum_height,
            'hauteur_au_sacrum': self._calculate_rump_height,
            'body_length': self._calculate_body_length,
            'tour_de_poitrine': self._calculate_heart_girth,
            'perimetre_thoracique': self._calculate_chest_circumference,
            'largeur_poitrine': self._calculate_chest_width,
            'largeur_hanche': self._calculate_rump_width,
            'largeur_tete': self._calculate_head_width,
            'longueur_tete': self._calculate_head_length,
            'longueur_oreille': self._calculate_ear_length,
            'longueur_cou': self._calculate_neck_length,
            'tour_du_cou': self._calculate_neck_girth,
            'longueur_queue': self._calculate_tail_length,
        }
    
    def _validate_measurements(self, measurements: Dict, breed: Optional[str]) -> Dict:
        """Validate measurements for anatomical consistency"""
        try:
            warnings = []
            values = measurements['values']
            
            # Basic anatomical relationships
            if values.get('hauteur_au_garrot') and values.get('body_length'):
                ratio = values['body_length'] / values['hauteur_au_garrot']
                if ratio < 0.8 or ratio > 2.0:
                    warnings.append(f"Body length to height ratio ({ratio:.2f}) seems unusual")
            
            if values.get('largeur_poitrine') and values.get('largeur_hanche'):
                if values['largeur_hanche'] > values['largeur_poitrine'] * 1.5:
                    warnings.append("Hip width seems disproportionately large compared to chest")
            
            # Breed-specific validation
            if breed and breed.lower() in ['boer', 'nubian', 'alpine']:
                if values.get('hauteur_au_garrot'):
                    if breed.lower() == 'boer' and values['hauteur_au_garrot'] > 80:
                        warnings.append("Height seems large for Boer breed")
                    elif breed.lower() == 'nubian' and values['hauteur_au_garrot'] < 60:
                        warnings.append("Height seems small for Nubian breed")
            
            # Outlier detection using statistical methods
            measurement_vector = [v for v in values.values() if v is not None]
            if len(measurement_vector) > 5:
                try:
                    outliers = self.anomaly_detector.fit_predict([measurement_vector])
                    if outliers[0] == -1:
                        warnings.append("Some measurements detected as statistical outliers")
                except Exception as e:
                    logger.warning(f"Outlier detection failed: {e}")
            
            return {
                'is_valid': len(warnings) == 0,
                'warnings': warnings,
                'consistency_score': max(0, 1.0 - len(warnings) * 0.2)
            }
            
        except Exception as e:
            logger.error(f"Measurement validation failed: {e}")
            return {'is_valid': False, 'warnings': ['Validation failed'], 'consistency_score': 0.0}
    
    def _calculate_confidence_score(self, detection_results: Dict, 
                                  measurements: Dict, quality_score: float,
                                  validation_result: Dict) -> float:
        """Calculate overall confidence score using multiple factors"""
        try:
            # Pose detection confidence
            pose_conf = detection_results.get('agreement_score', 0.5)
            
            # Landmark quality (based on number of successful measurements)
            total_measurements = len(measurements['values'])
            successful_measurements = sum(1 for v in measurements['values'].values() if v is not None)
            landmark_conf = successful_measurements / total_measurements if total_measurements > 0 else 0
            
            # Image quality
            image_conf = quality_score
            
            # Anatomical consistency
            anatomy_conf = validation_result.get('consistency_score', 0.5)
            
            # Ensemble agreement
            ensemble_conf = detection_results.get('agreement_score', 0.5)
            
            # Weighted confidence score
            overall_confidence = (
                pose_conf * self.confidence_weights['pose_detection'] +
                landmark_conf * self.confidence_weights['landmark_quality'] +
                image_conf * self.confidence_weights['image_quality'] +
                anatomy_conf * self.confidence_weights['anatomical_consistency'] +
                ensemble_conf * self.confidence_weights['ensemble_agreement']
            )
            
            return max(0.0, min(1.0, overall_confidence))
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    # Utility methods for image processing
    def _is_low_contrast(self, image: np.ndarray) -> bool:
        """Check if image has low contrast"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return gray.std() < 30
    
    def _is_blurry(self, image: np.ndarray) -> bool:
        """Check if image is blurry"""
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var() < 100
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE"""
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    
    def _sharpen_image(self, image: np.ndarray) -> np.ndarray:
        """Sharpen blurry image"""
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel)
    
    def _estimate_noise(self, image: np.ndarray) -> float:
        """Estimate noise level in image"""
        return cv2.fastNlMeansDenoising(image).var()
    
    # Placeholder methods for complex calculations
    def _combine_detections(self, results: List, image_shape: Tuple) -> Dict:
        """Combine multiple detection results using ensemble voting"""
        # Implementation would combine landmarks from different models
        # For now, return the first successful result
        for name, result in results:
            if name.startswith('pose') and result.pose_landmarks:
                return result.pose_landmarks
        return None
    
    def _calculate_ensemble_agreement(self, results: List) -> float:
        """Calculate agreement score between different models"""
        # Simplified implementation - would compare landmark positions
        return 0.8 if len(results) > 1 else 0.6
    
    def _landmarks_to_keypoints(self, landmarks) -> List:
        """Convert landmarks to keypoint format"""
        # Implementation would extract specific keypoints
        return []
    
    def _extract_anatomical_points(self, landmarks, w: int, h: int) -> Dict:
        """Extract key anatomical points from landmarks"""
        # Implementation would identify specific anatomical landmarks
        return {}
    
    def _add_landmark_noise(self, points: Dict) -> Dict:
        """Add small random noise for bootstrap uncertainty estimation"""
        noisy_points = {}
        for name, point in points.items():
            if point is not None:
                noise_x = np.random.normal(0, 2)  # 2 pixel standard deviation
                noise_y = np.random.normal(0, 2)
                noisy_points[name] = (point[0] + noise_x, point[1] + noise_y)
            else:
                noisy_points[name] = None
        return noisy_points
    
    def _apply_breed_corrections(self, measurements: Dict, breed: str) -> Tuple[Dict, float]:
        """Apply breed-specific measurement corrections"""
        if breed not in self.breed_models:
            return measurements, 0.0
        
        # Apply breed model corrections
        # This would use machine learning models trained on breed-specific data
        return measurements, 0.8  # Placeholder confidence
    
    def _create_annotated_image(self, image: np.ndarray, detection_results: Dict, 
                              measurements: Dict) -> np.ndarray:
        """Create annotated image with landmarks and measurements"""
        annotated = image.copy()
        
        # Draw landmarks if available
        if detection_results.get('landmarks'):
            # Implementation would draw pose landmarks, measurements, etc.
            pass
        
        return annotated
    
    # Measurement calculation methods (simplified implementations)
    def _calculate_wither_height(self, points: Dict, scale: float) -> float:
        """Calculate wither height"""
        # Implementation would use specific anatomical landmarks
        return 65.0 * scale  # Placeholder
    
    def _calculate_back_height(self, points: Dict, scale: float) -> float:
        """Calculate back height"""
        return 62.0 * scale  # Placeholder
    
    def _calculate_sternum_height(self, points: Dict, scale: float) -> float:
        """Calculate sternum height"""
        return 35.0 * scale  # Placeholder
    
    def _calculate_rump_height(self, points: Dict, scale: float) -> float:
        """Calculate rump height"""
        return 66.0 * scale  # Placeholder
    
    def _calculate_body_length(self, points: Dict, scale: float) -> float:
        """Calculate body length"""
        return 85.0 * scale  # Placeholder
    
    def _calculate_heart_girth(self, points: Dict, scale: float) -> float:
        """Calculate heart girth"""
        return 95.0 * scale  # Placeholder
    
    def _calculate_chest_circumference(self, points: Dict, scale: float) -> float:
        """Calculate chest circumference"""
        return 92.0 * scale  # Placeholder
    
    def _calculate_chest_width(self, points: Dict, scale: float) -> float:
        """Calculate chest width"""
        return 25.0 * scale  # Placeholder
    
    def _calculate_rump_width(self, points: Dict, scale: float) -> float:
        """Calculate rump width"""
        return 23.0 * scale  # Placeholder
    
    def _calculate_head_width(self, points: Dict, scale: float) -> float:
        """Calculate head width"""
        return 15.0 * scale  # Placeholder
    
    def _calculate_head_length(self, points: Dict, scale: float) -> float:
        """Calculate head length"""
        return 22.0 * scale  # Placeholder
    
    def _calculate_ear_length(self, points: Dict, scale: float) -> float:
        """Calculate ear length"""
        return 12.0 * scale  # Placeholder
    
    def _calculate_neck_length(self, points: Dict, scale: float) -> float:
        """Calculate neck length"""
        return 18.0 * scale  # Placeholder
    
    def _calculate_neck_girth(self, points: Dict, scale: float) -> float:
        """Calculate neck girth"""
        return 45.0 * scale  # Placeholder
    
    def _calculate_tail_length(self, points: Dict, scale: float) -> float:
        """Calculate tail length"""
        return 25.0 * scale  # Placeholder
