"""Auth API URLs for mobile / token clients."""
from django.urls import path

from .views_auth import LoginView, LogoutView, MeView
from .views_devices import DeviceListView, DeviceRegisterView, DeviceUnregisterView

urlpatterns = [
    path('login/', LoginView.as_view(), name='api-auth-login'),
    path('logout/', LogoutView.as_view(), name='api-auth-logout'),
    path('me/', MeView.as_view(), name='api-auth-me'),
    path('devices/', DeviceListView.as_view(), name='api-auth-devices'),
    path('devices/register/', DeviceRegisterView.as_view(), name='api-auth-devices-register'),
    path('devices/unregister/', DeviceUnregisterView.as_view(), name='api-auth-devices-unregister'),
]
