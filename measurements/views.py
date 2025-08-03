from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.files.base import ContentFile
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models
import json
import logging
try:
    import cv2
except ImportError:
    cv2 = None
import numpy as np
import pandas as pd
import joblib
from typing import Dict, List, Optional
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

from .models import Goat, MorphometricMeasurement, KeyPoint, MeasurementSession, UserProfile
from .cv_processor import GoatMorphometryProcessor
from .cv_processor_advanced import AdvancedGoatMorphometryProcessor
from .ml_trainer_advanced import AdvancedMLTrainer
from .forms import CustomUserRegistrationForm, UserProfileForm
from .excel_export import GoatMeasurementExporter
from .serializers import (
    GoatSerializer, MorphometricMeasurementSerializer,
    KeyPointSerializer, MeasurementSessionSerializer
)


def validate_image_file(uploaded_file):
    """Validate uploaded image file"""
    # Check file extension
    allowed_extensions = ['jpg', 'jpeg', 'png', 'bmp']
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
        raise ValidationError(f'File type not allowed. Allowed types: {", ".join(allowed_extensions)}')
    
    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if uploaded_file.size > max_size:
        raise ValidationError('File size too large. Maximum size is 10MB.')
    
    # Check if it's actually an image
    try:
        from PIL import Image
        image = Image.open(uploaded_file)
        image.verify()
    except Exception:
        raise ValidationError('Invalid image file.')
    
    return True


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_and_process_image(request):
    """
    API endpoint to upload goat image and process morphometric measurements
    """
    try:
        # Get uploaded image
        if 'image' not in request.FILES:
            return Response({
                'success': False,
                'error': 'No image file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_image = request.FILES['image']
        
        # Validate image file
        try:
            validate_image_file(uploaded_image)
        except ValidationError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get optional parameters
        goat_id = request.data.get('goat_id')
        reference_length = request.data.get('reference_length_cm')
        
        if reference_length:
            try:
                reference_length = float(reference_length)
            except ValueError:
                reference_length = None
        
        # Get or create goat
        goat = None
        if goat_id:
            try:
                goat = Goat.objects.get(id=goat_id, owner=request.user)
            except Goat.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Goat not found'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Create new goat
            goat_name = request.data.get('goat_name', f'Goat_{uploaded_image.name}')
            goat = Goat.objects.create(
                name=goat_name,
                owner=request.user
            )
        
        # Process image with advanced computer vision and AI/ML
        # Check if user prefers advanced processing (can be a user setting)
        use_advanced_processing = request.data.get('use_advanced_ai', True)
        breed = request.data.get('breed', None)
        
        if use_advanced_processing:
            try:
                processor = AdvancedGoatMorphometryProcessor()
                
                logger.info(f"Processing image with advanced AI for user {request.user.username}", extra={
                    'user_id': request.user.id,
                    'goat_id': goat.id if goat else None,
                    'image_name': uploaded_image.name,
                    'image_size': uploaded_image.size,
                    'breed': breed,
                    'processing_type': 'advanced_ai'
                })
                
                # Convert uploaded file to bytes for advanced processing
                uploaded_image.seek(0)
                image_bytes = uploaded_image.read()
                
                result = processor.process_goat_image_advanced(
                    image_data=image_bytes,
                    reference_length=reference_length,
                    breed=breed
                )
                
                # Add AI/ML enhanced metadata
                result['processing_metadata'] = result.get('processing_metadata', {})
                result['processing_metadata']['ai_enhanced'] = True
                result['processing_metadata']['breed_specific'] = breed is not None
                
            except Exception as e:
                logger.warning(f"Advanced AI processing failed, falling back to standard: {e}")
                # Fallback to standard processing
                processor = GoatMorphometryProcessor()
                result = processor.process_uploaded_image(uploaded_image, reference_length)
                result['processing_metadata'] = {'ai_enhanced': False, 'fallback_used': True}
        else:
            # Standard processing
            processor = GoatMorphometryProcessor()
            
            logger.info(f"Processing image with standard CV for user {request.user.username}", extra={
                'user_id': request.user.id,
                'goat_id': goat.id if goat else None,
                'image_name': uploaded_image.name,
                'image_size': uploaded_image.size,
                'processing_type': 'standard'
            })
            
            result = processor.process_uploaded_image(uploaded_image, reference_length)
            result['processing_metadata'] = {'ai_enhanced': False}
        
        if not result['success']:
            logger.warning(f"Image processing failed: {result.get('error')}", extra={
                'user_id': request.user.id,
                'image_name': uploaded_image.name
            })
            return Response({
                'success': False,
                'error': result.get('error', 'Processing failed')
            }, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        if not result['success']:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create measurement record
        measurement = MorphometricMeasurement.objects.create(
            goat=goat,
            original_image=uploaded_image,
            measured_by=request.user,
            confidence_score=result['confidence_score'],
            reference_object_length_cm=reference_length,
            **result['measurements']
        )
        
        # Save processed image
        if 'processed_image' in result:
            processed_img_array = result['processed_image']
            _, buffer = cv2.imencode('.jpg', processed_img_array)
            processed_img_bytes = BytesIO(buffer)
            
            measurement.processed_image.save(
                f'processed_{uploaded_image.name}',
                ContentFile(processed_img_bytes.getvalue()),
                save=True
            )
        
        # Save keypoints
        for kp_data in result['keypoints']:
            KeyPoint.objects.create(
                measurement=measurement,
                name=kp_data['name'],
                x_coordinate=kp_data['x'],
                y_coordinate=kp_data['y'],
                confidence=kp_data.get('visibility', 0.0)
            )
        
        # Serialize and return data
        measurement_serializer = MorphometricMeasurementSerializer(measurement)
        
        return Response({
            'success': True,
            'measurement': measurement_serializer.data,
            'goat': GoatSerializer(goat).data,
            'processing_info': {
                'confidence_score': result['confidence_score'],
                'scale_factor': result.get('scale_factor', 1.0),
                'keypoints_detected': len(result['keypoints'])
            }
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_goats(request):
    """List all goats belonging to the authenticated user"""
    goats = Goat.objects.filter(owner=request.user).order_by('-created_at')
    serializer = GoatSerializer(goats, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_goat(request):
    """Create a new goat"""
    serializer = GoatSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_goat_measurements(request, goat_id):
    """Get all measurements for a specific goat"""
    try:
        goat = Goat.objects.get(id=goat_id, owner=request.user)
        measurements = MorphometricMeasurement.objects.filter(goat=goat).order_by('-measurement_date')
        serializer = MorphometricMeasurementSerializer(measurements, many=True)
        return Response({
            'goat': GoatSerializer(goat).data,
            'measurements': serializer.data
        })
    except Goat.DoesNotExist:
        return Response({
            'error': 'Goat not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_measurement_detail(request, measurement_id):
    """Get detailed information about a specific measurement"""
    try:
        measurement = MorphometricMeasurement.objects.get(
            id=measurement_id, 
            goat__owner=request.user
        )
        keypoints = KeyPoint.objects.filter(measurement=measurement)
        
        return Response({
            'measurement': MorphometricMeasurementSerializer(measurement).data,
            'keypoints': KeyPointSerializer(keypoints, many=True).data,
            'goat': GoatSerializer(measurement.goat).data
        })
    except MorphometricMeasurement.DoesNotExist:
        return Response({
            'error': 'Measurement not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_measurement(request, measurement_id):
    """Update measurement values (for manual corrections)"""
    try:
        measurement = MorphometricMeasurement.objects.get(
            id=measurement_id,
            goat__owner=request.user
        )
        
        # Update measurement fields
        serializer = MorphometricMeasurementSerializer(
            measurement, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            # If any measurements were manually updated, change method to HYBRID
            manual_fields = [
                'hauteur_au_garrot', 'hauteur_au_dos', 'hauteur_au_sternum',
                'hauteur_au_sacrum', 'tour_de_poitrine', 'perimetre_thoracique',
                'tour_abdominal', 'diametre_biscotal', 'largeur_poitrine',
                'largeur_hanche', 'longueur_oreille', 'longueur_tete',
                'largeur_tete', 'body_length', 'longueur_cou', 'tour_du_cou',
                'longueur_queue'
            ]
            
            for field in manual_fields:
                if field in request.data:
                    measurement.measurement_method = 'HYBRID'
                    break
            
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except MorphometricMeasurement.DoesNotExist:
        return Response({
            'error': 'Measurement not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def measurement_statistics(request):
    """Get statistics about measurements for the user"""
    measurements = MorphometricMeasurement.objects.filter(goat__owner=request.user)
    
    stats = {
        'total_measurements': measurements.count(),
        'total_goats': Goat.objects.filter(owner=request.user).count(),
        'avg_confidence_score': measurements.aggregate(
            avg_confidence=models.Avg('confidence_score')
        )['avg_confidence'] or 0,
        'measurements_by_method': {
            'AUTO': measurements.filter(measurement_method='AUTO').count(),
            'MANUAL': measurements.filter(measurement_method='MANUAL').count(),
            'HYBRID': measurements.filter(measurement_method='HYBRID').count(),
        }
    }
    
    return Response(stats)


def get_user_measurement_stats(user_id):
    """Get user measurement statistics with caching"""
    cache_key = f'user_stats_{user_id}'
    stats = cache.get(cache_key)
    
    if not stats:
        user_goats = Goat.objects.filter(owner_id=user_id)
        total_measurements = MorphometricMeasurement.objects.filter(
            goat__owner_id=user_id
        ).count()
        
        stats = {
            'total_goats': user_goats.count(),
            'total_measurements': total_measurements,
            'recent_measurements': MorphometricMeasurement.objects.filter(
                goat__owner_id=user_id
            ).order_by('-measurement_date')[:5].values(
                'id', 'goat__name', 'measurement_date', 'confidence_score'
            )
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, stats, 300)
    
    return stats


@login_required
def measurement_dashboard(request):
    """Dashboard view for measurements"""
    # Use cached stats
    stats = get_user_measurement_stats(request.user.id)
    
    user_goats = Goat.objects.filter(owner=request.user).select_related()
    recent_measurements = MorphometricMeasurement.objects.filter(
        goat__owner=request.user
    ).select_related('goat').order_by('-measurement_date')[:10]
    
    context = {
        'goats': user_goats,
        'recent_measurements': recent_measurements,
        'total_goats': stats['total_goats'],
        'total_measurements': stats['total_measurements'],
        'total_measurements': MorphometricMeasurement.objects.filter(
            goat__owner=request.user
        ).count()
    }
    
    return render(request, 'measurements/dashboard.html', context)


@login_required
def upload_image_view(request):
    """View for uploading goat images"""
    user_goats = Goat.objects.filter(owner=request.user)
    return render(request, 'measurements/upload.html', {'goats': user_goats})


@login_required
def confirm_logout_view(request):
    """Confirmation view before logging out"""
    if request.method == 'POST':
        from django.contrib.auth import logout
        logout(request)
        return redirect('login')
    
    # Calculate total measurements for the user
    total_measurements = MorphometricMeasurement.objects.filter(goat__owner=request.user).count()
    
    context = {
        'total_measurements': total_measurements,
    }
    
    return render(request, 'measurements/confirm_logout.html', context)


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('measurements:dashboard')
    
    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome to GoatMorpho, {user.username}! Your account has been created successfully.')
            return redirect('measurements:dashboard')
    else:
        form = CustomUserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_view(request):
    """User profile view and editing"""
    try:
        profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            profile.organization = form.cleaned_data.get('organization', '')
            profile.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('measurements:profile')
    else:
        form = UserProfileForm(instance=request.user, initial={'organization': profile.organization})
    
    # Update measurement count
    profile.update_measurement_count()
    
    # Optimized queries
    user_goats = Goat.objects.filter(owner=request.user).prefetch_related('measurements')
    recent_measurements = MorphometricMeasurement.objects.filter(
        goat__owner=request.user
    ).select_related('goat').order_by('-measurement_date')[:5]
    
    context = {
        'form': form,
        'profile': profile,
        'total_goats': user_goats.count(),
        'recent_measurements': recent_measurements,
    }
    
    return render(request, 'measurements/profile.html', context)


@login_required
def export_measurements_excel(request):
    """Export user's measurements to Excel"""
    try:
        # Get filter parameters
        goat_id = request.GET.get('goat_id')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        
        # Build queryset
        measurements = MorphometricMeasurement.objects.filter(goat__owner=request.user)
        
        if goat_id:
            measurements = measurements.filter(goat__id=goat_id)
        
        if date_from:
            from datetime import datetime
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            measurements = measurements.filter(measurement_date__gte=date_from_obj)
        
        if date_to:
            from datetime import datetime
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            measurements = measurements.filter(measurement_date__lte=date_to_obj)
        
        # Create and return Excel file
        exporter = GoatMeasurementExporter()
        return exporter.export_user_measurements(request.user, measurements)
        
    except Exception as e:
        messages.error(request, f'Error generating Excel file: {str(e)}')
        return redirect('measurements:dashboard')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_measurements(request):
    """
    AI-powered measurement prediction based on partial measurements or image features
    """
    try:
        # Get input data
        input_data = request.data.get('measurements', {})
        breed = request.data.get('breed', None)
        confidence_threshold = float(request.data.get('confidence_threshold', 0.7))
        
        if not input_data:
            return Response({
                'success': False,
                'error': 'No measurement data provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize ML trainer for predictions
        trainer = AdvancedMLTrainer()
        
        # Prepare input data
        import pandas as pd
        df_input = pd.DataFrame([input_data])
        
        # Add breed information if provided
        if breed:
            df_input['breed'] = breed
        
        predictions = {}
        uncertainties = {}
        
        # Define measurement targets
        measurement_targets = [
            'hauteur_au_garrot', 'hauteur_au_dos', 'hauteur_au_sternum',
            'hauteur_au_sacrum', 'body_length', 'tour_de_poitrine',
            'perimetre_thoracique', 'largeur_poitrine', 'largeur_hanche',
            'largeur_tete', 'longueur_tete', 'longueur_oreille',
            'longueur_cou', 'tour_du_cou', 'longueur_queue'
        ]
        
        # Make predictions for missing measurements
        for measurement in measurement_targets:
            if measurement not in input_data or input_data[measurement] is None:
                try:
                    pred, uncertainty = trainer.predict_with_uncertainty(df_input, measurement)
                    if len(pred) > 0:
                        predictions[measurement] = float(pred[0])
                        uncertainties[measurement] = float(uncertainty[0])
                except Exception as e:
                    logger.warning(f"Prediction failed for {measurement}: {e}")
                    continue
        
        # Filter predictions by confidence (inverse of uncertainty)
        high_confidence_predictions = {}
        for measurement, pred_value in predictions.items():
            uncertainty = uncertainties.get(measurement, float('inf'))
            confidence = 1.0 / (1.0 + uncertainty) if uncertainty > 0 else 0.0
            
            if confidence >= confidence_threshold:
                high_confidence_predictions[measurement] = {
                    'predicted_value': pred_value,
                    'confidence': confidence,
                    'uncertainty': uncertainty
                }
        
        return Response({
            'success': True,
            'predictions': high_confidence_predictions,
            'all_predictions': predictions,
            'uncertainties': uncertainties,
            'metadata': {
                'breed': breed,
                'confidence_threshold': confidence_threshold,
                'total_predictions': len(predictions),
                'high_confidence_predictions': len(high_confidence_predictions)
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"AI prediction failed: {e}")
        return Response({
            'success': False,
            'error': f'Prediction failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_measurement_trends(request):
    """
    AI-powered analysis of measurement trends and growth patterns
    """
    try:
        goat_id = request.data.get('goat_id')
        analysis_type = request.data.get('analysis_type', 'growth_trend')
        
        if not goat_id:
            return Response({
                'success': False,
                'error': 'Goat ID required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get goat and verify ownership
        try:
            goat = Goat.objects.get(id=goat_id, owner=request.user)
        except Goat.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Goat not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get measurement history
        measurements = MorphometricMeasurement.objects.filter(goat=goat).order_by('measurement_date')
        
        if measurements.count() < 2:
            return Response({
                'success': False,
                'error': 'Insufficient measurement history for analysis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert to DataFrame for analysis
        data = []
        for m in measurements:
            row = {
                'date': m.measurement_date,
                'hauteur_au_garrot': m.hauteur_au_garrot,
                'hauteur_au_dos': m.hauteur_au_dos,
                'body_length': m.body_length,
                'tour_de_poitrine': m.tour_de_poitrine,
                'largeur_poitrine': m.largeur_poitrine,
                'confidence_score': m.confidence_score,
                'age_days': (m.measurement_date - goat.birth_date).days if goat.birth_date else None
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        analysis_result = {}
        
        if analysis_type == 'growth_trend':
            # Growth trend analysis
            analysis_result = _analyze_growth_trends(df, goat)
        elif analysis_type == 'anomaly_detection':
            # Anomaly detection in measurements
            analysis_result = _detect_measurement_anomalies(df, goat)
        elif analysis_type == 'breed_comparison':
            # Compare with breed standards
            analysis_result = _compare_with_breed_standards(df, goat)
        elif analysis_type == 'health_indicators':
            # Health indicator analysis
            analysis_result = _analyze_health_indicators(df, goat)
        else:
            return Response({
                'success': False,
                'error': 'Invalid analysis type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'analysis_type': analysis_type,
            'goat_info': {
                'id': goat.id,
                'name': goat.name,
                'breed': goat.breed,
                'birth_date': goat.birth_date,
                'sex': goat.sex
            },
            'analysis_result': analysis_result,
            'measurement_count': len(data),
            'date_range': {
                'start': df['date'].min().isoformat() if len(df) > 0 else None,
                'end': df['date'].max().isoformat() if len(df) > 0 else None
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Trend analysis failed: {e}")
        return Response({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ai_insights(request):
    """
    Get AI-generated insights and recommendations for the user's goats
    """
    try:
        # Get user's goats and measurements
        goats = Goat.objects.filter(owner=request.user).prefetch_related('morphometricmeasurement_set')
        
        if not goats.exists():
            return Response({
                'success': False,
                'error': 'No goats found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        insights = []
        
        for goat in goats:
            measurements = goat.morphometricmeasurement_set.all().order_by('-measurement_date')
            
            if measurements.count() == 0:
                continue
            
            # Generate insights for this goat
            goat_insights = _generate_goat_insights(goat, measurements)
            insights.append(goat_insights)
        
        # Generate overall herd insights
        herd_insights = _generate_herd_insights(goats)
        
        return Response({
            'success': True,
            'individual_insights': insights,
            'herd_insights': herd_insights,
            'total_goats': goats.count(),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"AI insights generation failed: {e}")
        return Response({
            'success': False,
            'error': f'Insights generation failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _analyze_growth_trends(df: pd.DataFrame, goat) -> Dict:
    """Analyze growth trends using AI/ML techniques"""
    try:
        from scipy import stats
        from sklearn.linear_model import LinearRegression
        
        analysis = {}
        
        # Key measurements for growth analysis
        growth_measurements = ['hauteur_au_garrot', 'body_length', 'tour_de_poitrine']
        
        for measurement in growth_measurements:
            if measurement in df.columns and not df[measurement].isna().all():
                values = df[measurement].dropna()
                dates = df.loc[values.index, 'date']
                
                if len(values) >= 2:
                    # Calculate growth rate
                    X = np.array([(d - dates.min()).days for d in dates]).reshape(-1, 1)
                    y = values.values
                    
                    model = LinearRegression()
                    model.fit(X, y)
                    
                    growth_rate = model.coef_[0]  # cm per day
                    r_squared = model.score(X, y)
                    
                    # Statistical tests
                    slope, intercept, r_value, p_value, std_err = stats.linregress(X.flatten(), y)
                    
                    analysis[measurement] = {
                        'growth_rate_per_day': growth_rate,
                        'growth_rate_per_month': growth_rate * 30,
                        'r_squared': r_squared,
                        'p_value': p_value,
                        'trend_significance': 'significant' if p_value < 0.05 else 'not_significant',
                        'current_value': float(values.iloc[-1]),
                        'initial_value': float(values.iloc[0]),
                        'total_growth': float(values.iloc[-1] - values.iloc[0]),
                        'measurement_count': len(values)
                    }
        
        # Overall growth assessment
        significant_trends = sum(1 for m in analysis.values() if m['trend_significance'] == 'significant')
        analysis['summary'] = {
            'measurements_analyzed': len(analysis) - 1,  # Exclude summary itself
            'significant_trends': significant_trends,
            'growth_status': 'healthy' if significant_trends > 0 else 'stable'
        }
        
        return analysis
        
    except Exception as e:
        logger.error(f"Growth trend analysis failed: {e}")
        return {'error': str(e)}


def _detect_measurement_anomalies(df: pd.DataFrame, goat) -> Dict:
    """Detect anomalies in measurements using statistical methods"""
    try:
        from sklearn.ensemble import IsolationForest
        from scipy import stats
        
        anomalies = {}
        
        # Prepare data for anomaly detection
        measurement_cols = ['hauteur_au_garrot', 'hauteur_au_dos', 'body_length', 'tour_de_poitrine']
        available_cols = [col for col in measurement_cols if col in df.columns]
        
        if not available_cols:
            return {'error': 'No suitable measurements for anomaly detection'}
        
        # Clean data
        clean_df = df[available_cols].dropna()
        
        if len(clean_df) < 3:
            return {'error': 'Insufficient data for anomaly detection'}
        
        # Z-score based anomaly detection
        z_scores = np.abs(stats.zscore(clean_df))
        z_anomalies = (z_scores > 2.5).any(axis=1)
        
        # Isolation Forest anomaly detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        iso_anomalies = iso_forest.fit_predict(clean_df) == -1
        
        # Combine results
        combined_anomalies = z_anomalies | iso_anomalies
        anomaly_indices = clean_df.index[combined_anomalies]
        
        anomalies['detected_anomalies'] = []
        for idx in anomaly_indices:
            original_idx = df.index[idx]
            anomaly_info = {
                'date': df.loc[original_idx, 'date'].isoformat(),
                'measurements': {}
            }
            
            for col in available_cols:
                value = df.loc[original_idx, col]
                z_score = z_scores.loc[idx, col]
                anomaly_info['measurements'][col] = {
                    'value': float(value),
                    'z_score': float(z_score),
                    'is_outlier': z_score > 2.5
                }
            
            anomalies['detected_anomalies'].append(anomaly_info)
        
        anomalies['summary'] = {
            'total_measurements': len(clean_df),
            'anomalies_detected': len(anomaly_indices),
            'anomaly_percentage': (len(anomaly_indices) / len(clean_df)) * 100 if len(clean_df) > 0 else 0
        }
        
        return anomalies
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        return {'error': str(e)}


def _compare_with_breed_standards(df: pd.DataFrame, goat) -> Dict:
    """Compare measurements with breed standards"""
    try:
        # Breed standards (example data - should be loaded from database or config)
        breed_standards = {
            'boer': {
                'hauteur_au_garrot': {'min': 60, 'max': 75, 'average': 67.5},
                'body_length': {'min': 70, 'max': 85, 'average': 77.5},
                'tour_de_poitrine': {'min': 85, 'max': 100, 'average': 92.5}
            },
            'nubian': {
                'hauteur_au_garrot': {'min': 70, 'max': 85, 'average': 77.5},
                'body_length': {'min': 75, 'max': 90, 'average': 82.5},
                'tour_de_poitrine': {'min': 90, 'max': 105, 'average': 97.5}
            },
            'alpine': {
                'hauteur_au_garrot': {'min': 68, 'max': 80, 'average': 74},
                'body_length': {'min': 72, 'max': 87, 'average': 79.5},
                'tour_de_poitrine': {'min': 88, 'max': 103, 'average': 95.5}
            }
        }
        
        comparison = {}
        
        if not goat.breed or goat.breed.lower() not in breed_standards:
            return {'error': f'No standards available for breed: {goat.breed}'}
        
        standards = breed_standards[goat.breed.lower()]
        latest_measurements = df.iloc[-1] if len(df) > 0 else None
        
        if latest_measurements is None:
            return {'error': 'No measurements available'}
        
        for measurement, standard in standards.items():
            if measurement in df.columns and not pd.isna(latest_measurements[measurement]):
                value = float(latest_measurements[measurement])
                
                # Calculate percentile within breed range
                range_position = (value - standard['min']) / (standard['max'] - standard['min'])
                percentile = max(0, min(100, range_position * 100))
                
                # Classification
                if value < standard['min']:
                    classification = 'below_standard'
                elif value > standard['max']:
                    classification = 'above_standard'
                else:
                    classification = 'within_standard'
                
                comparison[measurement] = {
                    'current_value': value,
                    'breed_min': standard['min'],
                    'breed_max': standard['max'],
                    'breed_average': standard['average'],
                    'percentile': percentile,
                    'classification': classification,
                    'deviation_from_average': value - standard['average']
                }
        
        return comparison
        
    except Exception as e:
        logger.error(f"Breed comparison failed: {e}")
        return {'error': str(e)}


def _analyze_health_indicators(df: pd.DataFrame, goat) -> Dict:
    """Analyze health indicators from measurement patterns"""
    try:
        health_analysis = {}
        
        # Body condition assessment
        if 'tour_de_poitrine' in df.columns and 'hauteur_au_garrot' in df.columns:
            latest = df.iloc[-1]
            heart_girth = latest['tour_de_poitrine']
            height = latest['hauteur_au_garrot']
            
            if not (pd.isna(heart_girth) or pd.isna(height)):
                # Body condition score estimation
                body_condition_ratio = heart_girth / height
                
                if body_condition_ratio < 1.3:
                    body_condition = 'thin'
                elif body_condition_ratio > 1.6:
                    body_condition = 'overweight'
                else:
                    body_condition = 'normal'
                
                health_analysis['body_condition'] = {
                    'ratio': float(body_condition_ratio),
                    'assessment': body_condition,
                    'heart_girth': float(heart_girth),
                    'height': float(height)
                }
        
        # Growth consistency check
        if len(df) >= 3:
            measurement_cols = ['hauteur_au_garrot', 'body_length', 'tour_de_poitrine']
            growth_consistency = {}
            
            for col in measurement_cols:
                if col in df.columns:
                    values = df[col].dropna()
                    if len(values) >= 3:
                        # Calculate coefficient of variation
                        cv = values.std() / values.mean() if values.mean() > 0 else 0
                        growth_consistency[col] = {
                            'coefficient_of_variation': float(cv),
                            'consistency': 'high' if cv < 0.1 else 'moderate' if cv < 0.2 else 'low'
                        }
            
            health_analysis['growth_consistency'] = growth_consistency
        
        # Measurement confidence trends
        if 'confidence_score' in df.columns:
            confidence_scores = df['confidence_score'].dropna()
            if len(confidence_scores) > 0:
                health_analysis['measurement_quality'] = {
                    'average_confidence': float(confidence_scores.mean()),
                    'latest_confidence': float(confidence_scores.iloc[-1]),
                    'quality_trend': 'improving' if len(confidence_scores) > 1 and confidence_scores.iloc[-1] > confidence_scores.mean() else 'stable'
                }
        
        return health_analysis
        
    except Exception as e:
        logger.error(f"Health analysis failed: {e}")
        return {'error': str(e)}


def _generate_goat_insights(goat, measurements) -> Dict:
    """Generate AI insights for individual goat"""
    try:
        insights = {
            'goat_id': goat.id,
            'goat_name': goat.name,
            'breed': goat.breed,
            'insights': [],
            'recommendations': []
        }
        
        if measurements.count() == 0:
            insights['insights'].append("No measurements available for analysis")
            return insights
        
        latest = measurements.first()
        
        # Confidence-based insights
        if latest.confidence_score < 0.6:
            insights['insights'].append(f"Latest measurement has low confidence ({latest.confidence_score:.1%})")
            insights['recommendations'].append("Consider retaking measurements with better lighting and positioning")
        
        # Growth insights for young goats
        if goat.birth_date:
            age_months = (timezone.now().date() - goat.birth_date).days / 30.44
            if age_months < 12:  # Young goat
                if measurements.count() >= 2:
                    first_measurement = measurements.last()
                    growth_rate = (latest.hauteur_au_garrot - first_measurement.hauteur_au_garrot) / max(1, (latest.measurement_date - first_measurement.measurement_date).days) * 30
                    
                    if growth_rate > 0:
                        insights['insights'].append(f"Growing at {growth_rate:.1f} cm/month in height")
                        if growth_rate < 2:
                            insights['recommendations'].append("Growth rate is below average - consider nutritional assessment")
                    else:
                        insights['insights'].append("No height growth detected in recent measurements")
        
        # Breed-specific insights
        if goat.breed:
            if goat.breed.lower() == 'boer' and latest.hauteur_au_garrot:
                if latest.hauteur_au_garrot > 75:
                    insights['insights'].append("Height is above typical Boer breed standard")
                elif latest.hauteur_au_garrot < 60:
                    insights['insights'].append("Height is below typical Boer breed standard")
        
        return insights
        
    except Exception as e:
        logger.error(f"Individual goat insights failed: {e}")
        return {'error': str(e)}


def _generate_herd_insights(goats) -> Dict:
    """Generate insights for the entire herd"""
    try:
        herd_insights = {
            'total_goats': goats.count(),
            'insights': [],
            'recommendations': []
        }
        
        # Breed distribution
        breed_counts = {}
        for goat in goats:
            breed = goat.breed or 'Unknown'
            breed_counts[breed] = breed_counts.get(breed, 0) + 1
        
        most_common_breed = max(breed_counts, key=breed_counts.get) if breed_counts else None
        
        if most_common_breed and most_common_breed != 'Unknown':
            herd_insights['insights'].append(f"Most common breed: {most_common_breed} ({breed_counts[most_common_breed]} goats)")
        
        # Measurement coverage
        goats_with_measurements = sum(1 for goat in goats if goat.morphometricmeasurement_set.exists())
        coverage_percentage = (goats_with_measurements / goats.count()) * 100 if goats.count() > 0 else 0
        
        herd_insights['insights'].append(f"Measurement coverage: {coverage_percentage:.0f}% of goats")
        
        if coverage_percentage < 80:
            herd_insights['recommendations'].append("Consider measuring remaining goats for complete herd analysis")
        
        # Recent activity
        from datetime import timedelta
        recent_measurements = 0
        cutoff_date = timezone.now() - timedelta(days=30)
        
        for goat in goats:
            if goat.morphometricmeasurement_set.filter(measurement_date__gte=cutoff_date).exists():
                recent_measurements += 1
        
        if recent_measurements > 0:
            herd_insights['insights'].append(f"{recent_measurements} goats measured in the last 30 days")
        else:
            herd_insights['recommendations'].append("No recent measurements - consider regular monitoring schedule")
        
        return herd_insights
        
    except Exception as e:
        logger.error(f"Herd insights failed: {e}")
        return {'error': str(e)}


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_user_specific_model(request):
    """
    Train a user-specific ML model based on their measurement data
    """
    try:
        # Check if user has enough data
        user_measurements = MorphometricMeasurement.objects.filter(goat__owner=request.user)
        
        if user_measurements.count() < 10:
            return Response({
                'success': False,
                'error': 'Insufficient data for training (minimum 10 measurements required)',
                'current_count': user_measurements.count()
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare training data
        data = []
        for measurement in user_measurements:
            row = {
                'goat_id': measurement.goat.id,
                'breed': measurement.goat.breed,
                'sex': measurement.goat.sex,
                'confidence_score': measurement.confidence_score,
                'hauteur_au_garrot': measurement.hauteur_au_garrot,
                'hauteur_au_dos': measurement.hauteur_au_dos,
                'hauteur_au_sternum': measurement.hauteur_au_sternum,
                'hauteur_au_sacrum': measurement.hauteur_au_sacrum,
                'body_length': measurement.body_length,
                'tour_de_poitrine': measurement.tour_de_poitrine,
                'perimetre_thoracique': measurement.perimetre_thoracique,
                'largeur_poitrine': measurement.largeur_poitrine,
                'largeur_hanche': measurement.largeur_hanche,
                'largeur_tete': measurement.largeur_tete,
                'longueur_tete': measurement.longueur_tete,
                'longueur_oreille': measurement.longueur_oreille,
                'longueur_cou': measurement.longueur_cou,
                'tour_du_cou': measurement.tour_du_cou,
                'longueur_queue': measurement.longueur_queue,
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Initialize trainer
        trainer = AdvancedMLTrainer()
        
        # Prepare data
        X, y = trainer.prepare_training_data(df)
        
        # Train models
        results = trainer.train_ensemble_models(X, y, test_size=0.2)
        
        # Save user-specific model
        user_model_path = trainer.model_dir / f"user_{request.user.id}_model.joblib"
        joblib.dump(results, user_model_path)
        
        # Calculate model performance summary
        performance_summary = {}
        for measurement, models in results.items():
            best_model = min(models.items(), key=lambda x: x[1]['test_mae'])
            performance_summary[measurement] = {
                'best_model': best_model[0],
                'test_mae': best_model[1]['test_mae'],
                'test_r2': best_model[1]['test_r2']
            }
        
        return Response({
            'success': True,
            'message': 'User-specific model trained successfully',
            'training_data_count': len(df),
            'model_performance': performance_summary,
            'model_path': str(user_model_path),
            'measurements_modeled': list(results.keys())
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"User model training failed: {e}")
        return Response({
            'success': False,
            'error': f'Model training failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required 
def export_options_view(request):
    """View for choosing export options"""
    user_goats = Goat.objects.filter(owner=request.user)
    measurements_count = MorphometricMeasurement.objects.filter(goat__owner=request.user).count()
    
    context = {
        'goats': user_goats,
    }
    
    return render(request, 'measurements/export_options.html', context)


def custom_404_view(request, exception):
    """
    Custom 404 error handler with GoatMorpho branding and quick logout option
    """
    return render(request, '404.html', status=404)


def test_404_view(request):
    """
    Temporary view to test 404 page functionality during development
    """
    # Simulate a 404 error page for testing
    context = {
        'request_path': request.path,
        'request_method': request.method,
    }
    return render(request, '404.html', context, status=404)


def home_view(request):
    """
    Home page view that explains the application and its features
    """
    context = {
        'page_title': 'Welcome to GoatMorpho',
        'is_home_page': True,
    }
    return render(request, 'measurements/home.html', context)
