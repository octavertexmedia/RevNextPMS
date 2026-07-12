from django.urls import path

from .internal_views import internal_entitlements

urlpatterns = [
    path('entitlements/', internal_entitlements, name='internal-entitlements'),
]
