from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

router = DefaultRouter()
router.register(r'bookings', views_api.DirectBookingViewSet, basename='direct-booking')
router.register(r'configs', views_api.BookingEngineConfigViewSet, basename='booking-config')

urlpatterns = [
    path('public/property/<int:property_id>/', views_api.public_property_config, name='public-property'),
    path('public/availability/', views_api.public_availability, name='public-availability'),
    path('public/bookings/', views_api.public_create_booking, name='public-create-booking'),
    path(
        'public/bookings/<str:confirmation_code>/',
        views_api.public_lookup_booking,
        name='public-lookup-booking',
    ),
    path('', include(router.urls)),
]
