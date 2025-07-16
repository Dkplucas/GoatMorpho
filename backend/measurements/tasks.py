"""
Celery tasks for background processing
"""
import time
import random
from celery import shared_task
from django.utils import timezone
from .models import Measurement


@shared_task
def process_measurement_async(measurement_id):
    """
    Process measurement asynchronously
    This is a mock implementation - replace with actual computer vision processing
    """
    try:
        measurement = Measurement.objects.get(id=measurement_id)
        
        # Simulate processing time
        processing_time = 2 + random.random() * 3  # 2-5 seconds
        time.sleep(processing_time)
        
        # Mock measurement extraction (replace with actual CV processing)
        measurements = {
            'wh': 72.5 + (random.random() - 0.5) * 10,  # Hauteur au garrot
            'bh': 68.2 + (random.random() - 0.5) * 8,   # Hauteur au dos
            'sh': 35.8 + (random.random() - 0.5) * 6,   # Hauteur au sternum
            'rh': 74.1 + (random.random() - 0.5) * 9,   # Hauteur au Sacrum
            'hg': 84.3 + (random.random() - 0.5) * 12,  # Tour de poitrine
            'cc': 82.1 + (random.random() - 0.5) * 10,  # Périmètre thoracique
            'ag': 89.7 + (random.random() - 0.5) * 15,  # Tour abdominal
            'ng': 42.6 + (random.random() - 0.5) * 8,   # Tour du cou
            'bd': 28.4 + (random.random() - 0.5) * 5,   # Diamètre biscotal
            'cw': 22.1 + (random.random() - 0.5) * 4,   # Largeur poitrine
            'rw': 19.8 + (random.random() - 0.5) * 3,   # Largeur de Hanche
            'hw': 12.3 + (random.random() - 0.5) * 2,   # Largeur de la tête
            'bl': 78.9 + (random.random() - 0.5) * 12,  # Body length
            'hl': 21.5 + (random.random() - 0.5) * 4,   # Longueur de la tête
            'nl': 31.2 + (random.random() - 0.5) * 6,   # Longueur du cou
            'tl': 18.7 + (random.random() - 0.5) * 4,   # Longueur de la queue
            'el': 15.4 + (random.random() - 0.5) * 3,   # Longueur oreille
        }
        
        # Update measurement with results
        for field, value in measurements.items():
            setattr(measurement, field, value)
        
        measurement.confidence_score = 0.85 + random.random() * 0.15
        measurement.processing_time = processing_time
        measurement.status = 'completed'
        measurement.save()
        
        print(f"Processing completed for measurement {measurement_id}")
        
    except Measurement.DoesNotExist:
        print(f"Measurement {measurement_id} not found")
    except Exception as e:
        print(f"Processing failed for measurement {measurement_id}: {e}")
        
        # Update measurement with error
        try:
            measurement = Measurement.objects.get(id=measurement_id)
            measurement.status = 'failed'
            measurement.error_message = str(e)
            measurement.save()
        except Measurement.DoesNotExist:
            pass