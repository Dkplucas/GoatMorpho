from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Measurement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='measurements'
    )
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # File information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='measurements')
    image = models.ImageField(upload_to='measurements/')
    original_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=50)
    image_width = models.IntegerField(null=True, blank=True)
    image_height = models.IntegerField(null=True, blank=True)
    
    # Height measurements (in cm)
    wh = models.FloatField(null=True, blank=True, help_text="Hauteur au garrot (Withers Height)")
    bh = models.FloatField(null=True, blank=True, help_text="Hauteur au dos (Back Height)")
    sh = models.FloatField(null=True, blank=True, help_text="Hauteur au sternum (Sternum Height)")
    rh = models.FloatField(null=True, blank=True, help_text="Hauteur au Sacrum (Sacrum Height)")
    
    # Girth measurements (in cm)
    hg = models.FloatField(null=True, blank=True, help_text="Tour de poitrine (Chest Girth)")
    cc = models.FloatField(null=True, blank=True, help_text="Périmètre thoracique (Thoracic Circumference)")
    ag = models.FloatField(null=True, blank=True, help_text="Tour abdominal (Abdominal Girth)")
    ng = models.FloatField(null=True, blank=True, help_text="Tour du cou (Neck Girth)")
    
    # Width measurements (in cm)
    bd = models.FloatField(null=True, blank=True, help_text="Diamètre biscotal (Bi-iliac Diameter)")
    cw = models.FloatField(null=True, blank=True, help_text="Largeur poitrine (Chest Width)")
    rw = models.FloatField(null=True, blank=True, help_text="Largeur de Hanche (Hip Width)")
    hw = models.FloatField(null=True, blank=True, help_text="Largeur de la tête (Head Width)")
    
    # Length measurements (in cm)
    bl = models.FloatField(null=True, blank=True, help_text="Body Length")
    hl = models.FloatField(null=True, blank=True, help_text="Longueur de la tête (Head Length)")
    nl = models.FloatField(null=True, blank=True, help_text="Longueur du cou (Neck Length)")
    tl = models.FloatField(null=True, blank=True, help_text="Longueur de la queue (Tail Length)")
    
    # Special measurements (in cm)
    el = models.FloatField(null=True, blank=True, help_text="Longueur oreille (Ear Length)")
    
    # Analysis metadata
    confidence_score = models.FloatField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence score (0.0 to 1.0)"
    )
    processing_time = models.FloatField(null=True, blank=True, help_text="Processing time in seconds")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    error_message = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Measurement {self.id} - {self.original_name} ({self.status})"
    
    @property
    def measurement_count(self):
        """Count of non-null measurements"""
        measurements = [
            self.wh, self.bh, self.sh, self.rh,  # Heights
            self.hg, self.cc, self.ag, self.ng,  # Girths
            self.bd, self.cw, self.rw, self.hw,  # Widths
            self.bl, self.hl, self.nl, self.tl,  # Lengths
            self.el  # Special
        ]
        return sum(1 for m in measurements if m is not None)
    
    def get_measurements_dict(self):
        """Return measurements as a dictionary"""
        return {
            'height_measurements': {
                'wh': self.wh,
                'bh': self.bh,
                'sh': self.sh,
                'rh': self.rh,
            },
            'girth_measurements': {
                'hg': self.hg,
                'cc': self.cc,
                'ag': self.ag,
                'ng': self.ng,
            },
            'width_measurements': {
                'bd': self.bd,
                'cw': self.cw,
                'rw': self.rw,
                'hw': self.hw,
            },
            'length_measurements': {
                'bl': self.bl,
                'hl': self.hl,
                'nl': self.nl,
                'tl': self.tl,
            },
            'special_measurements': {
                'el': self.el,
            }
        }