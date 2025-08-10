from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
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
        # Fixed circular import issue
        self.total_measurements = MorphometricMeasurement.objects.filter(
            goat__owner=self.user
        ).count()
        self.save()
        
    def clean(self):
        """Model validation"""
        if self.total_measurements < 0:
            raise ValidationError('Total measurements cannot be negative')


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
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                   validators=[MinValueValidator(0.1), MaxValueValidator(200.0)])
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goats')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', '-created_at']),
            models.Index(fields=['breed']),
        ]

    def clean(self):
        """Model validation"""
        if self.age_months and self.age_months > 300:  # 25 years max
            raise ValidationError('Age seems unrealistic for a goat')
        if self.weight_kg and self.age_months:
            if self.age_months < 6 and self.weight_kg > 50:  # Young goat weight check
                raise ValidationError('Weight seems too high for a young goat')

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
                                         help_text="AI confidence score (0-1)",
                                         validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    measurement_date = models.DateTimeField(auto_now_add=True)
    measured_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Reference object for scale (optional)
    reference_object_length_cm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                                   help_text="Known length of reference object in image",
                                                   validators=[MinValueValidator(0.1)])
    
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-measurement_date']
        indexes = [
            models.Index(fields=['measurement_date']),
            models.Index(fields=['goat', 'measurement_date']),
            models.Index(fields=['measured_by']),
            models.Index(fields=['measurement_method']),
        ]

    def clean(self):
        """Model validation for anatomical consistency"""
        # Basic anatomical relationship checks
        if self.body_length and self.hauteur_au_garrot:
            if self.body_length < self.hauteur_au_garrot * 0.3:
                raise ValidationError('Body length seems too small relative to height')
            if self.body_length > self.hauteur_au_garrot * 2.5:
                raise ValidationError('Body length seems too large relative to height')
        
        # Confidence score validation
        if self.confidence_score is not None:
            if self.confidence_score < 0 or self.confidence_score > 1:
                raise ValidationError('Confidence score must be between 0 and 1')

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
    goat = models.ForeignKey(Goat, on_delete=models.CASCADE, null=True, blank=True)
    total_images = models.PositiveIntegerField(default=0)
    processed_images = models.PositiveIntegerField(default=0)
    failed_images = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('PARTIAL', 'Partially Completed')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.session_name} - {self.user.username}"

    @property
    def progress_percentage(self):
        """Calculate processing progress as percentage"""
        if self.total_images == 0:
            return 0
        return (self.processed_images + self.failed_images) / self.total_images * 100

    @property
    def success_rate(self):
        """Calculate success rate as percentage"""
        total_processed = self.processed_images + self.failed_images
        if total_processed == 0:
            return 0
        return self.processed_images / total_processed * 100


class BatchImageUpload(models.Model):
    """Model to track individual images in a batch upload session"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(MeasurementSession, on_delete=models.CASCADE, related_name='batch_images')
    original_filename = models.CharField(max_length=255)
    image_file = models.ImageField(upload_to='goat_images/batch/')
    order_index = models.PositiveIntegerField(default=0, help_text="Order in which image was uploaded")
    
    # Processing status
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ], default='PENDING')
    
    # Result if processed successfully
    measurement = models.OneToOneField(
        'MorphometricMeasurement', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='batch_upload'
    )
    
    # Error information if failed
    error_message = models.TextField(blank=True, null=True)
    
    # Processing metadata
    processing_time_seconds = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['session', 'order_index']
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} in {self.session.session_name}"
