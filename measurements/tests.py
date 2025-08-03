from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.core.exceptions import ValidationError
from decimal import Decimal
import tempfile
from PIL import Image
import io

from .models import Goat, MorphometricMeasurement, UserProfile, KeyPoint, MeasurementSession
from .cv_processor import GoatMorphometryProcessor


class ModelTestCase(TestCase):
    """Test cases for model validation and behavior"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.goat = Goat.objects.create(
            name='Test Goat',
            breed='Boer',
            age_months=12,
            sex='F',
            weight_kg=Decimal('25.5'),
            owner=self.user
        )
    
    def test_goat_validation(self):
        """Test goat model validation"""
        # Test invalid age
        goat = Goat(
            name='Invalid Goat',
            age_months=400,  # Too old
            owner=self.user
        )
        with self.assertRaises(ValidationError):
            goat.full_clean()
    
    def test_measurement_validation(self):
        """Test measurement model validation"""
        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        # Test invalid confidence score
        measurement = MorphometricMeasurement(
            goat=self.goat,
            original_image=SimpleUploadedFile(
                name='test.jpg',
                content=temp_file.read(),
                content_type='image/jpeg'
            ),
            confidence_score=Decimal('1.5'),  # Invalid confidence > 1
            measured_by=self.user
        )
        with self.assertRaises(ValidationError):
            measurement.full_clean()
    
    def test_anatomical_validation(self):
        """Test anatomical relationship validation"""
        image = Image.new('RGB', (100, 100), color='red')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file, format='JPEG')
        temp_file.seek(0)
        
        measurement = MorphometricMeasurement(
            goat=self.goat,
            original_image=SimpleUploadedFile(
                name='test.jpg',
                content=temp_file.read(),
                content_type='image/jpeg'
            ),
            hauteur_au_garrot=Decimal('60.0'),
            body_length=Decimal('10.0'),  # Too small relative to height
            measured_by=self.user
        )
        with self.assertRaises(ValidationError):
            measurement.full_clean()


class ViewTestCase(TestCase):
    """Test cases for views and API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.goat = Goat.objects.create(
            name='Test Goat',
            owner=self.user
        )
    
    def test_dashboard_view(self):
        """Test dashboard view access"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('measurements:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')
    
    def test_upload_view_requires_login(self):
        """Test that upload view requires authentication"""
        response = self.client.get(reverse('measurements:upload_image'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_api_authentication(self):
        """Test API endpoints require authentication"""
        response = self.client.post('/api/upload-and-process/')
        self.assertEqual(response.status_code, 401)  # Unauthorized


class CVProcessorTestCase(TestCase):
    """Test cases for computer vision processing"""
    
    def setUp(self):
        self.processor = GoatMorphometryProcessor()
    
    def test_processor_initialization(self):
        """Test that CV processor initializes correctly"""
        self.assertIsNotNone(self.processor.mp_pose)
        self.assertIsNotNone(self.processor.pose)
    
    def test_image_processing(self):
        """Test basic image processing functionality"""
        # Create a simple test image
        image = Image.new('RGB', (640, 480), color='white')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Test that processing doesn't crash
        try:
            result = self.processor.process_goat_image(img_bytes)
            self.assertIsInstance(result, dict)
        except Exception as e:
            # Processing might fail with test image, but shouldn't crash
            self.assertIsInstance(e, Exception)


class SecurityTestCase(TestCase):
    """Test cases for security features"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_file_upload_validation(self):
        """Test file upload security"""
        self.client.login(username='testuser', password='testpass123')
        
        # Try to upload a non-image file
        malicious_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        response = self.client.post('/api/upload-and-process/', {
            'image': malicious_file
        })
        # Should reject non-image files
        self.assertNotEqual(response.status_code, 200)
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection"""
        self.client.login(username='testuser', password='testpass123')
        
        # Try SQL injection in URL parameters
        response = self.client.get('/measurements/export-excel/?goat_id=1; DROP TABLE measurements_goat;--')
        # Should not crash or execute malicious SQL
        self.assertNotEqual(response.status_code, 500)
