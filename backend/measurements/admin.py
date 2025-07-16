from django.contrib import admin
from .models import Measurement


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'original_name', 'status', 'measurement_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['original_name', 'user__username']
    readonly_fields = ['created_at', 'updated_at', 'measurement_count']
    
    fieldsets = (
        ('File Information', {
            'fields': ('user', 'image', 'original_name', 'file_size', 'mime_type', 'image_width', 'image_height')
        }),
        ('Height Measurements', {
            'fields': ('wh', 'bh', 'sh', 'rh'),
            'classes': ('collapse',)
        }),
        ('Girth Measurements', {
            'fields': ('hg', 'cc', 'ag', 'ng'),
            'classes': ('collapse',)
        }),
        ('Width Measurements', {
            'fields': ('bd', 'cw', 'rw', 'hw'),
            'classes': ('collapse',)
        }),
        ('Length Measurements', {
            'fields': ('bl', 'hl', 'nl', 'tl'),
            'classes': ('collapse',)
        }),
        ('Special Measurements', {
            'fields': ('el',),
            'classes': ('collapse',)
        }),
        ('Analysis Results', {
            'fields': ('confidence_score', 'processing_time', 'status', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )