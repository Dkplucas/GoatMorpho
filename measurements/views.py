from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.files.base import ContentFile
from django.views.decorators.http import require_http_methods
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models
import json
try:
    import cv2
except ImportError:
    cv2 = None
import numpy as np
from io import BytesIO
import base64

from .models import Goat, MorphometricMeasurement, KeyPoint, MeasurementSession, UserProfile
from .cv_processor import GoatMorphometryProcessor
from .forms import CustomUserRegistrationForm, UserProfileForm
from .excel_export import GoatMeasurementExporter
from .serializers import (
    GoatSerializer, MorphometricMeasurementSerializer,
    KeyPointSerializer, MeasurementSessionSerializer
)


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
        
        # Process image with computer vision
        processor = GoatMorphometryProcessor()
        result = processor.process_uploaded_image(uploaded_image, reference_length)
        
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


@login_required
def measurement_dashboard(request):
    """Dashboard view for measurements"""
    user_goats = Goat.objects.filter(owner=request.user)
    recent_measurements = MorphometricMeasurement.objects.filter(
        goat__owner=request.user
    ).order_by('-measurement_date')[:10]
    
    context = {
        'goats': user_goats,
        'recent_measurements': recent_measurements,
        'total_goats': user_goats.count(),
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
    
    context = {
        'form': form,
        'profile': profile,
        'total_goats': Goat.objects.filter(owner=request.user).count(),
        'recent_measurements': MorphometricMeasurement.objects.filter(
            goat__owner=request.user
        ).order_by('-measurement_date')[:5]
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
