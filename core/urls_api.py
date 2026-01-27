"""
API URLs for Core Models
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    PropertyViewSet, RoomTypeViewSet,
    RatePlanViewSet, InventoryViewSet, PromotionViewSet
)

router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'room-types', RoomTypeViewSet, basename='room-type')
router.register(r'rate-plans', RatePlanViewSet, basename='rate-plan')
router.register(r'inventory', InventoryViewSet, basename='inventory')
router.register(r'promotions', PromotionViewSet, basename='promotion')

urlpatterns = [
    path('', include(router.urls)),
]
