from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, debug_views
from django.shortcuts import redirect

app_name = 'measurements'

# API URL patterns
urlpatterns = [
    # Home page (public landing page)
    path('', views.home_view, name='home'),
    
    # Debug endpoints
    path('api/test-cv/', debug_views.test_cv_setup, name='test_cv'),
    path('api/test-upload/', debug_views.test_image_upload, name='test_upload'),
    path('api/test-samples/', debug_views.test_sample_images, name='test_samples'),
    
    # API endpoints
    path('api/upload/', views.upload_and_process_image, name='upload_and_process'),
    path('api/goats/', views.list_goats, name='list_goats'),
    path('api/goats/create/', views.create_goat, name='create_goat'),
    path('api/goats/<uuid:goat_id>/measurements/', views.get_goat_measurements, name='goat_measurements'),
    path('api/measurements/<uuid:measurement_id>/', views.get_measurement_detail, name='measurement_detail'),
    path('api/measurements/<uuid:measurement_id>/update/', views.update_measurement, name='update_measurement'),
    path('api/statistics/', views.measurement_statistics, name='measurement_statistics'),
    
    # AI/ML Enhanced API endpoints
    path('api/ai/predict-measurements/', views.predict_measurements, name='ai_predict_measurements'),
    path('api/ai/analyze-trends/', views.analyze_measurement_trends, name='ai_analyze_trends'),
    path('api/ai/insights/', views.get_ai_insights, name='ai_insights'),
    path('api/ai/train-model/', views.train_user_specific_model, name='ai_train_model'),
    
    # Web interface views
    path('dashboard/', views.measurement_dashboard, name='dashboard'),
    path('upload/', views.upload_image_view, name='upload_image'),
    path('batch-upload/', views.batch_upload_view, name='batch_upload'),
    path('batch-status/<uuid:session_id>/', views.batch_status_view, name='batch_status'),
    path('batch-sessions/', views.batch_sessions_view, name='batch_sessions'),
    
    # Batch processing API endpoints
    path('api/batch-status/<uuid:session_id>/', views.batch_status_api, name='batch_status_api'),
    path('api/retry-failed/<uuid:session_id>/', views.retry_failed_images, name='retry_failed_images'),
    
    path('logout-confirm/', views.confirm_logout_view, name='logout_confirm'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('export-options/', views.export_options_view, name='export_options'),
    path('export-excel/', views.export_measurements_excel, name='export_excel'),
    path('test-404/', views.test_404_view, name='test_404'),  # Temporary test endpoint
]
