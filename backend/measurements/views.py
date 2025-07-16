import csv
import io
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from PIL import Image
from .models import Measurement
from .serializers import MeasurementSerializer, MeasurementCreateSerializer, MeasurementUpdateSerializer
from .tasks import process_measurement_async


class MeasurementViewSet(viewsets.ModelViewSet):
    """ViewSet for managing measurements"""
    
    serializer_class = MeasurementSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter measurements by current user"""
        return Measurement.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return MeasurementCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MeasurementUpdateSerializer
        return MeasurementSerializer
    
    def perform_create(self, serializer):
        """Create measurement and start processing"""
        # Get image dimensions
        image = serializer.validated_data['image']
        try:
            with Image.open(image) as img:
                width, height = img.size
        except Exception:
            width, height = None, None
        
        # Save measurement
        measurement = serializer.save(
            user=self.request.user,
            image_width=width,
            image_height=height,
            status='processing'
        )
        
        # Start async processing
        process_measurement_async.delay(measurement.id)
    
    @action(detail=True, methods=['get'])
    def download_csv(self, request, pk=None):
        """Download measurement results as CSV"""
        measurement = self.get_object()
        
        if measurement.status != 'completed':
            return Response(
                {'error': 'Measurement not completed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="goat_measurements_{measurement.id}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Measurement', 'Value (cm)'])
        
        # Write measurements
        measurements = [
            ('Hauteur au garrot (WH)', measurement.wh),
            ('Hauteur au dos (BH)', measurement.bh),
            ('Hauteur au sternum (SH)', measurement.sh),
            ('Hauteur au Sacrum (RH)', measurement.rh),
            ('Tour de poitrine (HG)', measurement.hg),
            ('Périmètre thoracique (CC)', measurement.cc),
            ('Tour abdominal (AG)', measurement.ag),
            ('Tour du cou (NG)', measurement.ng),
            ('Diamètre biscotal (BD)', measurement.bd),
            ('Largeur poitrine (CW)', measurement.cw),
            ('Largeur de Hanche (RW)', measurement.rw),
            ('Largeur de la tête (HW)', measurement.hw),
            ('Body length (BL)', measurement.bl),
            ('Longueur de la tête (HL)', measurement.hl),
            ('Longueur du cou (NL)', measurement.nl),
            ('Longueur de la queue (TL)', measurement.tl),
            ('Longueur oreille (EL)', measurement.el),
        ]
        
        for name, value in measurements:
            writer.writerow([name, f"{value:.1f}" if value is not None else 'N/A'])
        
        return response
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get measurement statistics for user"""
        measurements = self.get_queryset()
        
        stats = {
            'total_measurements': measurements.count(),
            'completed_measurements': measurements.filter(status='completed').count(),
            'processing_measurements': measurements.filter(status='processing').count(),
            'failed_measurements': measurements.filter(status='failed').count(),
            'average_confidence': measurements.filter(
                confidence_score__isnull=False
            ).aggregate(
                avg_confidence=models.Avg('confidence_score')
            )['avg_confidence']
        }
        
        return Response(stats)