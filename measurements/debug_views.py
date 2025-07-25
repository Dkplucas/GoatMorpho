from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging
from .cv_processor import GoatMorphometryProcessor

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_cv_setup(request):
    """Test endpoint to verify computer vision setup"""
    try:
        import cv2
        import mediapipe as mp
        import numpy as np
        
        # Test MediaPipe initialization
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=True,
            model_complexity=2,
            enable_segmentation=False,
            min_detection_confidence=0.3
        )
        
        return Response({
            'success': True,
            'message': 'Computer vision setup is working correctly',
            'versions': {
                'opencv': cv2.__version__,
                'mediapipe': mp.__version__,
                'numpy': np.__version__
            }
        })
        
    except Exception as e:
        logger.error(f"CV setup test failed: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])  # Temporarily allow without auth for testing
def test_image_upload(request):
    """Test endpoint for image upload without full processing"""
    try:
        if 'image' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No image file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_image = request.FILES['image']
        
        # Basic file validation
        logger.info(f"Received file: {uploaded_image.name}, size: {uploaded_image.size}")
        
        if uploaded_image.size > 10 * 1024 * 1024:  # 10MB
            return Response({
                'success': False,
                'error': 'File too large (max 10MB)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to decode image
        import cv2
        import numpy as np
        
        image_array = np.asarray(bytearray(uploaded_image.read()), dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            return Response({
                'success': False,
                'error': 'Could not decode image file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        height, width, channels = image.shape
        
        return Response({
            'success': True,
            'message': 'Image uploaded and decoded successfully',
            'image_info': {
                'filename': uploaded_image.name,
                'size_bytes': uploaded_image.size,
                'dimensions': f'{width}x{height}',
                'channels': channels
            }
        })
        
    except Exception as e:
        logger.error(f"Test upload failed: {e}")
        return Response({
            'success': False,
            'error': f'Upload test failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def test_sample_images(request):
    """Test processing with generated sample images"""
    try:
        import os
        from django.conf import settings
        
        sample_dir = os.path.join(settings.MEDIA_ROOT, 'goat_images', 'samples')
        results = {}
        
        # Test each sample image
        sample_files = ['sample_goat_profile.jpg', 'detection_test.jpg']
        
        processor = GoatMorphometryProcessor()
        
        for filename in sample_files:
            filepath = os.path.join(sample_dir, filename)
            if os.path.exists(filepath):
                try:
                    result = processor.process_image(filepath)
                    results[filename] = {
                        'success': result['success'],
                        'confidence': result.get('confidence_score', 0),
                        'num_keypoints': len(result.get('keypoints', [])),
                        'error': result.get('error', 'None'),
                        'note': result.get('note', 'None')
                    }
                except Exception as e:
                    results[filename] = {
                        'success': False,
                        'error': str(e)
                    }
            else:
                results[filename] = {
                    'success': False,
                    'error': f'File not found: {filepath}'
                }
        
        return Response({
            'success': True,
            'sample_results': results,
            'message': 'Sample image testing complete'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        })
