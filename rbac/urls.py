from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CapabilityViewSet,
    MyAccessView,
    RoleViewSet,
    SeedStatusView,
    UserRoleAssignmentViewSet,
)

router = DefaultRouter()
router.register(r'capabilities', CapabilityViewSet, basename='rbac-capability')
router.register(r'roles', RoleViewSet, basename='rbac-role')
router.register(r'assignments', UserRoleAssignmentViewSet, basename='rbac-assignment')

urlpatterns = [
    path('me/', MyAccessView.as_view(), name='rbac-me'),
    path('status/', SeedStatusView.as_view(), name='rbac-status'),
    path('', include(router.urls)),
]
