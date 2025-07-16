from rest_framework import serializers
from .models import Measurement


class MeasurementSerializer(serializers.ModelSerializer):
    """Serializer for Measurement model"""
    
    measurement_count = serializers.ReadOnlyField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Measurement
        fields = [
            'id', 'user', 'image', 'image_url', 'original_name', 
            'file_size', 'mime_type', 'image_width', 'image_height',
            'wh', 'bh', 'sh', 'rh',  # Heights
            'hg', 'cc', 'ag', 'ng',  # Girths
            'bd', 'cw', 'rw', 'hw',  # Widths
            'bl', 'hl', 'nl', 'tl',  # Lengths
            'el',  # Special
            'confidence_score', 'processing_time', 'status', 'error_message',
            'measurement_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_image_url(self, obj):
        """Get the full URL for the image"""
        if obj.image:
            return obj.image.url
        return None


class MeasurementCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating measurements"""
    
    class Meta:
        model = Measurement
        fields = [
            'image', 'original_name', 'file_size', 'mime_type'
        ]
    
    def validate_image(self, value):
        """Validate uploaded image"""
        if value.size > 10 * 1024 * 1024:  # 10MB
            raise serializers.ValidationError("Image size must be less than 10MB")
        
        if not value.content_type.startswith('image/'):
            raise serializers.ValidationError("File must be an image")
        
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only JPG, PNG, and WebP images are allowed")
        
        return value


class MeasurementUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating measurement results"""
    
    class Meta:
        model = Measurement
        fields = [
            'image_width', 'image_height',
            'wh', 'bh', 'sh', 'rh',  # Heights
            'hg', 'cc', 'ag', 'ng',  # Girths
            'bd', 'cw', 'rw', 'hw',  # Widths
            'bl', 'hl', 'nl', 'tl',  # Lengths
            'el',  # Special
            'confidence_score', 'processing_time', 'status', 'error_message'
        ]