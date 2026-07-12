from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

router = DefaultRouter()
router.register(r'configs', views_api.ToursConfigViewSet, basename='tours-config')
router.register(r'packages', views_api.TourPackageViewSet, basename='tour-package')
router.register(r'itinerary', views_api.ItineraryDayViewSet, basename='tour-itinerary')
router.register(r'departures', views_api.DepartureViewSet, basename='tour-departure')
router.register(r'bookings', views_api.TourBookingViewSet, basename='tour-booking')
router.register(r'agents', views_api.TourAgentViewSet, basename='tour-agent')

urlpatterns = [
    path('public/packages/', views_api.public_search_packages, name='public-packages'),
    path('public/packages/<slug:slug>/', views_api.public_package_detail, name='public-package-detail'),
    path('public/departures/<int:departure_id>/availability/', views_api.public_departure_availability, name='public-departure-avail'),
    path('public/bookings/', views_api.public_create_booking, name='public-create-booking'),
    path('public/bookings/<str:confirmation_code>/', views_api.public_lookup_booking, name='public-lookup-booking'),
    path('portal/me/', views_api.portal_me, name='portal-me'),
    path('portal/packages/', views_api.portal_packages, name='portal-packages'),
    path('portal/bookings/', views_api.portal_bookings, name='portal-bookings'),
    path('portal/bookings/create/', views_api.portal_create_booking, name='portal-create-booking'),
    path('', include(router.urls)),
]
