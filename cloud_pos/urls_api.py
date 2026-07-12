"""API URLs for Cloud POS."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views_api import (
    MenuCategoryViewSet,
    MenuItemViewSet,
    POSOrderViewSet,
    POSTableViewSet,
)

router = DefaultRouter()
router.register(r'categories', MenuCategoryViewSet, basename='pos-category')
router.register(r'menu-items', MenuItemViewSet, basename='pos-menu-item')
router.register(r'tables', POSTableViewSet, basename='pos-table')
router.register(r'orders', POSOrderViewSet, basename='pos-order')

urlpatterns = [
    path('', include(router.urls)),
]
