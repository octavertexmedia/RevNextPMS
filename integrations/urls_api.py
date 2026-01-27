"""
API URLs for Integrations
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    IntegrationPlatformViewSet,
    PropertyIntegrationViewSet,
    SyncLogViewSet
)

router = DefaultRouter()
router.register(r'platforms', IntegrationPlatformViewSet, basename='integration-platform')
router.register(r'integrations', PropertyIntegrationViewSet, basename='property-integration')
router.register(r'sync-logs', SyncLogViewSet, basename='sync-log')

urlpatterns = [
    path('', include(router.urls)),
]
