"""
API URLs for Tenant Management
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    TenantViewSet, TenantUserViewSet,
    SubscriptionPlanViewSet, SubscriptionPaymentViewSet
)

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'users', TenantUserViewSet, basename='tenant-user')
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscription-plan')
router.register(r'payments', SubscriptionPaymentViewSet, basename='subscription-payment')

urlpatterns = [
    path('', include(router.urls)),
]
