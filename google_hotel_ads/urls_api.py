from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import HotelAdsConfigViewSet

router = DefaultRouter()
router.register(r'configs', HotelAdsConfigViewSet, basename='hotel-ads-config')

urlpatterns = [path('', include(router.urls))]
