from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

router = DefaultRouter()
router.register(r'agents', views_api.B2BAgentViewSet, basename='b2b-agent')
router.register(r'rates', views_api.B2BRatePlanViewSet, basename='b2b-rate')
router.register(r'allotments', views_api.B2BAllotmentViewSet, basename='b2b-allotment')
router.register(r'bookings', views_api.B2BBookingViewSet, basename='b2b-booking')

urlpatterns = [
    path('portal/me/', views_api.portal_me, name='portal-me'),
    path('portal/properties/', views_api.portal_properties, name='portal-properties'),
    path('portal/rates/', views_api.portal_rates, name='portal-rates'),
    path('portal/allotments/', views_api.portal_allotments, name='portal-allotments'),
    path('portal/bookings/', views_api.portal_bookings, name='portal-bookings'),
    path('portal/bookings/create/', views_api.portal_create_booking, name='portal-create-booking'),
    path('', include(router.urls)),
]
