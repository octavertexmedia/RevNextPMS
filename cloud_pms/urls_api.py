"""
API URLs for Cloud PMS
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import (
    FolioViewSet,
    HousekeepingTaskViewSet,
    LinkedRoomUnitViewSet,
    pms_dashboard_api,
)

router = DefaultRouter()
router.register(r'folios', FolioViewSet, basename='pms-folio')
router.register(r'housekeeping', HousekeepingTaskViewSet, basename='pms-housekeeping')
router.register(r'linked-rooms', LinkedRoomUnitViewSet, basename='pms-linked-room')

urlpatterns = [
    path('dashboard/', pms_dashboard_api, name='pms-dashboard-api'),
    path('', include(router.urls)),
]
