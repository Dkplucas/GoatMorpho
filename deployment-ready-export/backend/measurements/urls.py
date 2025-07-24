from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.MeasurementViewSet, basename='measurement')

urlpatterns = [
    path('', include(router.urls)),
]