from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class UserProfile(models.Model):
    """Extended user profile with additional information"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.CharField(max_length=100, blank=True, help_text="University, Farm, Research Institute")
    registration_date = models.DateTimeField(auto_now_add=True)
    total_measurements = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.organization}"

    def update_measurement_count(self):
        """Update the total measurement count"""
        from .models import MorphometricMeasurement  # Avoid circular import
        self.total_measurements = MorphometricMeasurement.objects.filter(
            goat__owner=self.user
        ).count()
        self.save()


class Goat(models.Model):
    """Model to store goat information"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True, null=True)
    breed = models.CharField(max_length=100, blank=True, null=True)
    age_months = models.PositiveIntegerField(blank=True, null=True)
    sex = models.CharField(max_length=10, choices=[
        ('M', 'Male'),
        ('F', 'Female')
    ], blank=True, null=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name or 'Unnamed Goat'} - {self.id}"


class MorphometricMeasurement(models.Model):
    """Model to store morphometric measurements for goats"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goat = models.ForeignKey(Goat, on_delete=models.CASCADE, related_name='measurements')
    
    # Original image and processed data
    original_image = models.ImageField(upload_to='goat_images/original/')
    processed_image = models.ImageField(upload_to='goat_images/processed/', blank=True, null=True)
    
    # Morphometric measurements (in centimeters)
    # Heights
    hauteur_au_garrot = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, 
                                           help_text="Wither Height (WH) - cm")
    hauteur_au_dos = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                        help_text="Back Height (BH) - cm")
    hauteur_au_sternum = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                           help_text="Sternum Height (SH) - cm")
    hauteur_au_sacrum = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                          help_text="Rump Height (RH) - cm")
    
    # Circumferences
    tour_de_poitrine = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                         help_text="Heart Girth (HG) - cm")
    perimetre_thoracique = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                             help_text="Chest Circumference (CC) - cm")
    tour_abdominal = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                       help_text="Abdominal Girth (AG) - cm")
    tour_du_cou = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                    help_text="Neck Girth (NG) - cm")
    
    # Widths and Diameters
    diametre_biscotal = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                          help_text="Bi-costal Diameter (BD) - cm")
    largeur_poitrine = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                         help_text="Chest Width (CW) - cm")
    largeur_hanche = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                       help_text="Rump Width (RW) - cm")
    largeur_tete = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                     help_text="Head Width (HW) - cm")
    
    # Lengths
    body_length = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                    help_text="Body Length (BL) - cm")
    longueur_oreille = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                         help_text="Ear Length (EL) - cm")
    longueur_tete = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                      help_text="Head Length (HL) - cm")
    longueur_cou = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                     help_text="Neck Length (NL) - cm")
    longueur_queue = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                       help_text="Tail Length (TL) - cm")
    
    # Measurement metadata
    measurement_method = models.CharField(max_length=20, choices=[
        ('AUTO', 'Automatic AI Detection'),
        ('MANUAL', 'Manual Input'),
        ('HYBRID', 'AI-Assisted with Manual Correction')
    ], default='AUTO')
    
    confidence_score = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True,
                                         help_text="AI confidence score (0-1)")
    measurement_date = models.DateTimeField(auto_now_add=True)
    measured_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Reference object for scale (optional)
    reference_object_length_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                                   help_text="Known length of reference object in image")
    
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-measurement_date']

    def __str__(self):
        return f"Measurements for {self.goat.name or self.goat.id} - {self.measurement_date.strftime('%Y-%m-%d')}"


class KeyPoint(models.Model):
    """Model to store detected keypoints on goat images"""
    measurement = models.ForeignKey(MorphometricMeasurement, on_delete=models.CASCADE, related_name='keypoints')
    
    # Keypoint identification
    name = models.CharField(max_length=50, help_text="Name of the keypoint (e.g., 'wither', 'sternum', etc.)")
    
    # Coordinates in the image
    x_coordinate = models.DecimalField(max_digits=8, decimal_places=2)
    y_coordinate = models.DecimalField(max_digits=8, decimal_places=2)
    
    # Detection confidence
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True, blank=True)
    
    # Whether this keypoint was manually adjusted
    manually_adjusted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} at ({self.x_coordinate}, {self.y_coordinate})"


class MeasurementSession(models.Model):
    """Model to track measurement sessions for batch processing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.session_name} - {self.user.username}"
