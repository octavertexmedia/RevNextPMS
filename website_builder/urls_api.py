from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import PropertyWebsiteViewSet, SiteTemplateViewSet

router = DefaultRouter()
router.register(r'templates', SiteTemplateViewSet, basename='site-template')
router.register(r'websites', PropertyWebsiteViewSet, basename='property-website')

urlpatterns = [path('', include(router.urls))]
