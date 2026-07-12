from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views_api

router = DefaultRouter()
router.register(r'listings', views_api.AggregatorListingViewSet, basename='hotel-listing')
router.register(r'claims', views_api.ListingClaimViewSet, basename='hotel-claim')
router.register(r'feeds', views_api.MetasearchFeedJobViewSet, basename='hotel-feed')

urlpatterns = [
    path('public/search/', views_api.public_search, name='public-search'),
    path('public/cities/', views_api.public_cities, name='public-cities'),
    path('public/listings/<slug:slug>/', views_api.public_listing_detail, name='public-listing'),
    path('public/claims/', views_api.public_submit_claim, name='public-claim'),
    path('', include(router.urls)),
]
