from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Goat, MorphometricMeasurement, KeyPoint, MeasurementSession, UserProfile


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(UserAdmin):
    """Extended User admin with profile"""
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_organization')
    
    def get_organization(self, obj):
        try:
            return obj.userprofile.organization or 'Not specified'
        except UserProfile.DoesNotExist:
            return 'No profile'
    get_organization.short_description = 'Organization'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Goat)
class GoatAdmin(admin.ModelAdmin):
    list_display = ['name', 'breed', 'sex', 'age_months', 'weight_kg', 'owner', 'created_at']
    list_filter = ['sex', 'breed', 'created_at']
    search_fields = ['name', 'breed', 'owner__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'breed', 'owner')
        }),
        ('Physical Attributes', {
            'fields': ('sex', 'age_months', 'weight_kg')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class KeyPointInline(admin.TabularInline):
    model = KeyPoint
    extra = 0
    readonly_fields = ['confidence']


@admin.register(MorphometricMeasurement)
class MorphometricMeasurementAdmin(admin.ModelAdmin):
    list_display = [
        'goat', 'measurement_date', 'measurement_method', 
        'confidence_score', 'hauteur_au_garrot', 'body_length'
    ]
    list_filter = ['measurement_method', 'measurement_date', 'goat__sex']
    search_fields = ['goat__name', 'measured_by__username']
    readonly_fields = ['id', 'measurement_date', 'confidence_score']
    inlines = [KeyPointInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'goat', 'measured_by', 'measurement_date', 'measurement_method')
        }),
        ('Images', {
            'fields': ('original_image', 'processed_image')
        }),
        ('Height Measurements (cm)', {
            'fields': ('hauteur_au_garrot', 'hauteur_au_dos', 'hauteur_au_sternum', 'hauteur_au_sacrum')
        }),
        ('Circumference Measurements (cm)', {
            'fields': ('tour_de_poitrine', 'perimetre_thoracique', 'tour_abdominal', 'tour_du_cou')
        }),
        ('Width and Diameter Measurements (cm)', {
            'fields': ('diametre_biscotal', 'largeur_poitrine', 'largeur_hanche', 'largeur_tete')
        }),
        ('Length Measurements (cm)', {
            'fields': ('body_length', 'longueur_oreille', 'longueur_tete', 'longueur_cou', 'longueur_queue')
        }),
        ('Metadata', {
            'fields': ('confidence_score', 'reference_object_length_cm', 'notes')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('goat', 'measured_by')


@admin.register(KeyPoint)
class KeyPointAdmin(admin.ModelAdmin):
    list_display = ['measurement', 'name', 'x_coordinate', 'y_coordinate', 'confidence', 'manually_adjusted']
    list_filter = ['name', 'manually_adjusted', 'measurement__measurement_date']
    search_fields = ['measurement__goat__name', 'name']
    readonly_fields = ['confidence']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('measurement', 'measurement__goat')


@admin.register(MeasurementSession)
class MeasurementSessionAdmin(admin.ModelAdmin):
    list_display = ['session_name', 'user', 'created_at', 'completed_at']
    list_filter = ['created_at', 'completed_at']
    search_fields = ['session_name', 'user__username']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('id', 'session_name', 'user')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at')
        }),
    )
