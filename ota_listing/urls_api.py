from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import ListingProjectViewSet

router = DefaultRouter()
router.register(r'projects', ListingProjectViewSet, basename='ota-listing-project')

urlpatterns = [path('', include(router.urls))]
