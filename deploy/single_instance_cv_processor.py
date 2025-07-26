"""
Single Instance CV Processor for GoatMorpho
Optimized for Oracle Cloud VM.Standard.A1.Flex (4 OCPUs, 24GB RAM)
Integrated CV processing service running on the same instance as Django
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import time
import threading
from queue import Queue, Empty
import signal
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp_mediapipe
from datetime import datetime
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/goat_morpho/cv_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SingleInstanceCVProcessor:
    """
    Computer Vision processor optimized for single instance deployment
    Handles morphometric analysis with ARM64 optimizations
    """
    
    def __init__(self, max_workers=3, max_queue_size=50):
        """
        Initialize CV processor with optimized settings for 4 OCPU instance
        
        Args:
            max_workers: Maximum concurrent processing workers (default: 3 for 4 OCPU)
            max_queue_size: Maximum items in processing queue
        """
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.processing_queue = Queue(maxsize=max_queue_size)
        self.results_store = {}
        self.shutdown_event = threading.Event()
        
        # MediaPipe setup for ARM64
        self.mp_pose = mp_mediapipe.solutions.pose
        self.mp_drawing = mp_mediapipe.solutions.drawing_utils
        self.mp_hands = mp_mediapipe.solutions.hands
        
        # Processing statistics
        self.stats = {
            'processed_images': 0,
            'failed_images': 0,
            'queue_size': 0,
            'average_processing_time': 0,
            'start_time': datetime.now()
        }
        
        # Start worker threads
        self.workers = []
        for i in range(max_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,))
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
            
        logger.info(f"CV Processor initialized with {max_workers} workers")
    
    def _worker_loop(self, worker_id):
        """Worker thread loop for processing images"""
        logger.info(f"CV Worker {worker_id} started")
        
        while not self.shutdown_event.is_set():
            try:
                # Get task from queue with timeout
                task = self.processing_queue.get(timeout=1.0)
                if task is None:  # Shutdown signal
                    break
                    
                start_time = time.time()
                task_id, image_path, options = task
                
                try:
                    # Process the image
                    result = self._process_image(image_path, options)
                    processing_time = time.time() - start_time
                    
                    # Update statistics
                    self.stats['processed_images'] += 1
                    self._update_average_time(processing_time)
                    
                    # Store result
                    self.results_store[task_id] = {
                        'status': 'completed',
                        'result': result,
                        'processing_time': processing_time,
                        'worker_id': worker_id,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    logger.info(f"Worker {worker_id} completed task {task_id} in {processing_time:.2f}s")
                    
                except Exception as e:
                    self.stats['failed_images'] += 1
                    self.results_store[task_id] = {
                        'status': 'failed',
                        'error': str(e),
                        'worker_id': worker_id,
                        'timestamp': datetime.now().isoformat()
                    }
                    logger.error(f"Worker {worker_id} failed task {task_id}: {e}")
                
                finally:
                    self.processing_queue.task_done()
                    
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
        
        logger.info(f"CV Worker {worker_id} stopped")
    
    def _update_average_time(self, new_time):
        """Update rolling average processing time"""
        current_avg = self.stats['average_processing_time']
        processed = self.stats['processed_images']
        
        if processed == 1:
            self.stats['average_processing_time'] = new_time
        else:
            # Exponential moving average
            alpha = 0.1  # Weight for new measurement
            self.stats['average_processing_time'] = (alpha * new_time) + ((1 - alpha) * current_avg)
    
    def _process_image(self, image_path, options):
        """
        Process a single image for morphometric analysis
        Optimized for ARM64 and Oracle Cloud instance
        """
        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Get image dimensions
            height, width = image.shape[:2]
            
            # ARM64 optimization: Use efficient resize if image is too large
            max_dimension = options.get('max_dimension', 1920)
            if max(height, width) > max_dimension:
                scale = max_dimension / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
                height, width = new_height, new_width
            
            # Convert BGR to RGB for MediaPipe
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Initialize result structure
            result = {
                'image_info': {
                    'width': width,
                    'height': height,
                    'channels': image.shape[2] if len(image.shape) > 2 else 1,
                    'file_path': str(image_path)
                },
                'measurements': {},
                'landmarks': {},
                'quality_metrics': {}
            }
            
            # Quality assessment
            result['quality_metrics'] = self._assess_image_quality(image)
            
            # Detect pose landmarks for body measurements
            if options.get('detect_pose', True):
                pose_results = self._detect_pose_landmarks(rgb_image)
                if pose_results:
                    result['landmarks']['pose'] = pose_results
                    result['measurements'].update(self._calculate_body_measurements(pose_results, width, height))
            
            # Detect hand landmarks for detailed measurements
            if options.get('detect_hands', True):
                hand_results = self._detect_hand_landmarks(rgb_image)
                if hand_results:
                    result['landmarks']['hands'] = hand_results
                    result['measurements'].update(self._calculate_hand_measurements(hand_results, width, height))
            
            # Detect facial landmarks for head measurements
            if options.get('detect_face', True):
                face_results = self._detect_face_landmarks(rgb_image)
                if face_results:
                    result['landmarks']['face'] = face_results
                    result['measurements'].update(self._calculate_head_measurements(face_results, width, height))
            
            # Calculate derived measurements
            result['measurements'].update(self._calculate_derived_measurements(result['measurements']))
            
            # Save processed image if requested
            if options.get('save_processed', False):
                processed_image_path = self._save_processed_image(image, result, image_path)
                result['processed_image_path'] = processed_image_path
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            raise
    
    def _assess_image_quality(self, image):
        """Assess image quality metrics"""
        try:
            # Convert to grayscale for quality assessment
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate image quality metrics
            quality = {
                'brightness': float(np.mean(gray)),
                'contrast': float(np.std(gray)),
                'sharpness': float(cv2.Laplacian(gray, cv2.CV_64F).var()),
                'noise_level': 0.0  # Placeholder for noise estimation
            }
            
            # Estimate noise using local variance
            kernel = np.ones((5, 5), np.float32) / 25
            smoothed = cv2.filter2D(gray.astype(np.float32), -1, kernel)
            quality['noise_level'] = float(np.mean((gray.astype(np.float32) - smoothed) ** 2))
            
            return quality
            
        except Exception as e:
            logger.warning(f"Quality assessment failed: {e}")
            return {'brightness': 0, 'contrast': 0, 'sharpness': 0, 'noise_level': 0}
    
    def _detect_pose_landmarks(self, rgb_image):
        """Detect pose landmarks using MediaPipe"""
        try:
            with self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=1,  # Balanced for ARM64
                enable_segmentation=False,
                min_detection_confidence=0.5
            ) as pose:
                results = pose.process(rgb_image)
                
                if results.pose_landmarks:
                    landmarks = []
                    for landmark in results.pose_landmarks.landmark:
                        landmarks.append({
                            'x': float(landmark.x),
                            'y': float(landmark.y),
                            'z': float(landmark.z),
                            'visibility': float(landmark.visibility)
                        })
                    return landmarks
                    
        except Exception as e:
            logger.warning(f"Pose detection failed: {e}")
        
        return None
    
    def _detect_hand_landmarks(self, rgb_image):
        """Detect hand landmarks using MediaPipe"""
        try:
            with self.mp_hands.Hands(
                static_image_mode=True,
                max_num_hands=2,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            ) as hands:
                results = hands.process(rgb_image)
                
                if results.multi_hand_landmarks:
                    hand_data = []
                    for hand_landmarks in results.multi_hand_landmarks:
                        landmarks = []
                        for landmark in hand_landmarks.landmark:
                            landmarks.append({
                                'x': float(landmark.x),
                                'y': float(landmark.y),
                                'z': float(landmark.z)
                            })
                        hand_data.append(landmarks)
                    return hand_data
                    
        except Exception as e:
            logger.warning(f"Hand detection failed: {e}")
        
        return None
    
    def _detect_face_landmarks(self, rgb_image):
        """Detect facial landmarks using OpenCV"""
        try:
            # Use OpenCV's face detection as fallback
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                face_data = []
                for (x, y, w, h) in faces:
                    face_data.append({
                        'x': float(x / rgb_image.shape[1]),
                        'y': float(y / rgb_image.shape[0]),
                        'width': float(w / rgb_image.shape[1]),
                        'height': float(h / rgb_image.shape[0])
                    })
                return face_data
                
        except Exception as e:
            logger.warning(f"Face detection failed: {e}")
        
        return None
    
    def _calculate_body_measurements(self, pose_landmarks, width, height):
        """Calculate body measurements from pose landmarks"""
        measurements = {}
        
        try:
            if len(pose_landmarks) >= 33:  # MediaPipe pose has 33 landmarks
                # Convert relative coordinates to pixel coordinates
                landmarks_px = [(int(lm['x'] * width), int(lm['y'] * height)) for lm in pose_landmarks]
                
                # Calculate key body measurements
                # Shoulder width (left shoulder to right shoulder)
                left_shoulder = landmarks_px[11]
                right_shoulder = landmarks_px[12]
                measurements['shoulder_width'] = self._euclidean_distance(left_shoulder, right_shoulder)
                
                # Body height (top of head to feet)
                head_top = landmarks_px[0]  # Nose as proxy for head top
                left_foot = landmarks_px[31]
                right_foot = landmarks_px[32]
                foot_center = ((left_foot[0] + right_foot[0]) // 2, (left_foot[1] + right_foot[1]) // 2)
                measurements['body_height'] = self._euclidean_distance(head_top, foot_center)
                
                # Arm span (left wrist to right wrist)
                left_wrist = landmarks_px[15]
                right_wrist = landmarks_px[16]
                measurements['arm_span'] = self._euclidean_distance(left_wrist, right_wrist)
                
                # Torso length (shoulder center to hip center)
                shoulder_center = ((left_shoulder[0] + right_shoulder[0]) // 2, (left_shoulder[1] + right_shoulder[1]) // 2)
                left_hip = landmarks_px[23]
                right_hip = landmarks_px[24]
                hip_center = ((left_hip[0] + right_hip[0]) // 2, (left_hip[1] + right_hip[1]) // 2)
                measurements['torso_length'] = self._euclidean_distance(shoulder_center, hip_center)
                
        except Exception as e:
            logger.warning(f"Body measurement calculation failed: {e}")
        
        return measurements
    
    def _calculate_hand_measurements(self, hand_landmarks, width, height):
        """Calculate hand measurements from landmarks"""
        measurements = {}
        
        try:
            for i, hand in enumerate(hand_landmarks):
                if len(hand) >= 21:  # MediaPipe hand has 21 landmarks
                    landmarks_px = [(int(lm['x'] * width), int(lm['y'] * height)) for lm in hand]
                    
                    # Hand length (wrist to middle finger tip)
                    wrist = landmarks_px[0]
                    middle_tip = landmarks_px[12]
                    measurements[f'hand_{i}_length'] = self._euclidean_distance(wrist, middle_tip)
                    
                    # Hand width (thumb to pinky at base)
                    thumb_base = landmarks_px[2]
                    pinky_base = landmarks_px[17]
                    measurements[f'hand_{i}_width'] = self._euclidean_distance(thumb_base, pinky_base)
                    
        except Exception as e:
            logger.warning(f"Hand measurement calculation failed: {e}")
        
        return measurements
    
    def _calculate_head_measurements(self, face_landmarks, width, height):
        """Calculate head measurements from facial landmarks"""
        measurements = {}
        
        try:
            if face_landmarks:
                face = face_landmarks[0]  # Use first detected face
                
                # Head width and height in pixels
                face_width_px = face['width'] * width
                face_height_px = face['height'] * height
                
                measurements['head_width'] = face_width_px
                measurements['head_height'] = face_height_px
                measurements['head_area'] = face_width_px * face_height_px
                
        except Exception as e:
            logger.warning(f"Head measurement calculation failed: {e}")
        
        return measurements
    
    def _calculate_derived_measurements(self, measurements):
        """Calculate derived measurements and ratios"""
        derived = {}
        
        try:
            # Body proportions
            if 'body_height' in measurements and 'shoulder_width' in measurements:
                derived['shoulder_to_height_ratio'] = measurements['shoulder_width'] / measurements['body_height']
            
            if 'arm_span' in measurements and 'body_height' in measurements:
                derived['arm_span_to_height_ratio'] = measurements['arm_span'] / measurements['body_height']
            
            if 'torso_length' in measurements and 'body_height' in measurements:
                derived['torso_to_height_ratio'] = measurements['torso_length'] / measurements['body_height']
            
            # Hand proportions
            for key in measurements:
                if key.endswith('_length') and key.replace('_length', '_width') in measurements:
                    width_key = key.replace('_length', '_width')
                    derived[f"{key}_to_width_ratio"] = measurements[key] / measurements[width_key]
            
        except Exception as e:
            logger.warning(f"Derived measurement calculation failed: {e}")
        
        return derived
    
    def _euclidean_distance(self, point1, point2):
        """Calculate Euclidean distance between two points"""
        return float(np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2))
    
    def _save_processed_image(self, image, result, original_path):
        """Save processed image with annotations"""
        try:
            # Create output path
            original_path = Path(original_path)
            output_dir = original_path.parent / "processed"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"processed_{original_path.name}"
            
            # Draw landmarks if available
            annotated_image = image.copy()
            
            # Draw pose landmarks
            if 'pose' in result['landmarks'] and result['landmarks']['pose']:
                pose_landmarks = result['landmarks']['pose']
                height, width = image.shape[:2]
                
                for landmark in pose_landmarks:
                    x = int(landmark['x'] * width)
                    y = int(landmark['y'] * height)
                    cv2.circle(annotated_image, (x, y), 3, (0, 255, 0), -1)
            
            # Save annotated image
            cv2.imwrite(str(output_path), annotated_image)
            return str(output_path)
            
        except Exception as e:
            logger.warning(f"Failed to save processed image: {e}")
            return None
    
    def submit_task(self, image_path, options=None):
        """Submit image processing task to queue"""
        if options is None:
            options = {}
        
        # Generate unique task ID
        task_id = f"task_{int(time.time() * 1000)}_{hash(str(image_path)) % 10000}"
        
        try:
            # Add task to queue
            self.processing_queue.put_nowait((task_id, image_path, options))
            self.stats['queue_size'] = self.processing_queue.qsize()
            
            # Initialize task status
            self.results_store[task_id] = {
                'status': 'queued',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Task {task_id} submitted for processing")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to submit task: {e}")
    
    def get_result(self, task_id):
        """Get processing result for task"""
        return self.results_store.get(task_id)
    
    def get_stats(self):
        """Get processing statistics"""
        stats = self.stats.copy()
        stats['queue_size'] = self.processing_queue.qsize()
        stats['uptime_seconds'] = (datetime.now() - stats['start_time']).total_seconds()
        stats['active_workers'] = len([w for w in self.workers if w.is_alive()])
        return stats
    
    def shutdown(self):
        """Shutdown the CV processor"""
        logger.info("Shutting down CV processor...")
        self.shutdown_event.set()
        
        # Add shutdown signals to queue
        for _ in range(self.max_workers):
            try:
                self.processing_queue.put_nowait(None)
            except:
                pass
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5.0)
        
        logger.info("CV processor shutdown complete")

# FastAPI application
app = FastAPI(
    title="GoatMorpho CV Processor",
    description="Single Instance Computer Vision Processing Service",
    version="1.0.0"
)

# Global CV processor instance
cv_processor = None

@app.on_event("startup")
async def startup_event():
    global cv_processor
    cv_processor = SingleInstanceCVProcessor(max_workers=3)

@app.on_event("shutdown")
async def shutdown_event():
    global cv_processor
    if cv_processor:
        cv_processor.shutdown()

@app.get("/")
async def root():
    return {"message": "GoatMorpho CV Processor - Single Instance", "status": "running"}

@app.get("/health")
async def health_check():
    stats = cv_processor.get_stats() if cv_processor else {}
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "stats": stats
    }

@app.post("/process")
async def process_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    detect_pose: bool = True,
    detect_hands: bool = True,
    detect_face: bool = True,
    save_processed: bool = False,
    max_dimension: int = 1920
):
    """Process uploaded image for morphometric analysis"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Processing options
        options = {
            'detect_pose': detect_pose,
            'detect_hands': detect_hands,
            'detect_face': detect_face,
            'save_processed': save_processed,
            'max_dimension': max_dimension
        }
        
        # Submit processing task
        task_id = cv_processor.submit_task(tmp_path, options)
        
        # Schedule cleanup of temporary file
        background_tasks.add_task(lambda: os.unlink(tmp_path) if os.path.exists(tmp_path) else None)
        
        return {
            "task_id": task_id,
            "status": "submitted",
            "message": "Image processing started"
        }
        
    except Exception as e:
        logger.error(f"Error in process_image: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """Get processing result for task"""
    result = cv_processor.get_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return result

@app.get("/stats")
async def get_stats():
    """Get processing statistics"""
    return cv_processor.get_stats()

def main():
    """Main entry point for CV processor service"""
    parser = argparse.ArgumentParser(description="GoatMorpho CV Processor - Single Instance")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=3, help="Number of CV processing workers")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Signal handling for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        if cv_processor:
            cv_processor.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the FastAPI server
    logger.info(f"Starting GoatMorpho CV Processor on {args.host}:{args.port}")
    logger.info(f"CV processing workers: {args.workers}")
    
    uvicorn.run(
        "single_instance_cv_processor:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=False,
        workers=1  # Use single worker for FastAPI, CV processing uses separate threads
    )

if __name__ == "__main__":
    main()
