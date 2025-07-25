from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Goat, MorphometricMeasurement, KeyPoint, MeasurementSession


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class GoatSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    measurements_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Goat
        fields = [
            'id', 'name', 'breed', 'age_months', 'sex', 'weight_kg',
            'owner', 'created_at', 'updated_at', 'measurements_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_measurements_count(self, obj):
        return obj.measurements.count()


class KeyPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyPoint
        fields = [
            'id', 'name', 'x_coordinate', 'y_coordinate', 
            'confidence', 'manually_adjusted'
        ]


class MorphometricMeasurementSerializer(serializers.ModelSerializer):
    goat = GoatSerializer(read_only=True)
    measured_by = UserSerializer(read_only=True)
    keypoints = KeyPointSerializer(many=True, read_only=True)
    keypoints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MorphometricMeasurement
        fields = [
            'id', 'goat', 'original_image', 'processed_image',
            # Height measurements
            'hauteur_au_garrot', 'hauteur_au_dos', 'hauteur_au_sternum', 'hauteur_au_sacrum',
            # Circumference measurements
            'tour_de_poitrine', 'perimetre_thoracique', 'tour_abdominal', 'tour_du_cou',
            # Width and diameter measurements
            'diametre_biscotal', 'largeur_poitrine', 'largeur_hanche', 'largeur_tete',
            # Length measurements
            'body_length', 'longueur_oreille', 'longueur_tete', 'longueur_cou', 'longueur_queue',
            # Metadata
            'measurement_method', 'confidence_score', 'measurement_date', 
            'measured_by', 'reference_object_length_cm', 'notes',
            'keypoints', 'keypoints_count'
        ]
        read_only_fields = ['id', 'measurement_date', 'keypoints', 'keypoints_count']
    
    def get_keypoints_count(self, obj):
        return obj.keypoints.count()


class MeasurementSessionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    measurements_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MeasurementSession
        fields = [
            'id', 'user', 'session_name', 'created_at', 
            'completed_at', 'measurements_count'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_measurements_count(self, obj):
        # This would need to be implemented based on how you link measurements to sessions
        return 0


class GoatCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating new goats"""
    
    class Meta:
        model = Goat
        fields = ['name', 'breed', 'age_months', 'sex', 'weight_kg']


class MeasurementUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating measurement values"""
    
    class Meta:
        model = MorphometricMeasurement
        fields = [
            'hauteur_au_garrot', 'hauteur_au_dos', 'hauteur_au_sternum', 'hauteur_au_sacrum',
            'tour_de_poitrine', 'perimetre_thoracique', 'tour_abdominal', 'tour_du_cou',
            'diametre_biscotal', 'largeur_poitrine', 'largeur_hanche', 'largeur_tete',
            'body_length', 'longueur_oreille', 'longueur_tete', 'longueur_cou', 'longueur_queue',
            'notes'
        ]


class MeasurementSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for measurement summaries"""
    goat_name = serializers.CharField(source='goat.name', read_only=True)
    
    class Meta:
        model = MorphometricMeasurement
        fields = [
            'id', 'goat_name', 'measurement_date', 'confidence_score',
            'measurement_method', 'hauteur_au_garrot', 'body_length'
        ]
