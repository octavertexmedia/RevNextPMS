"""
API Views for Integrations
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import IntegrationPlatform, PropertyIntegration, SyncLog
from .serializers import (
    IntegrationPlatformSerializer,
    PropertyIntegrationSerializer,
    SyncLogSerializer
)
from tenants.permissions import IsTenantMember


class IntegrationPlatformViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Integration Platforms (read-only)"""
    queryset = IntegrationPlatform.objects.filter(is_active=True)
    serializer_class = IntegrationPlatformSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['platform_type', 'is_active']
    search_fields = ['name', 'display_name']


class PropertyIntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet for Property Integrations"""
    serializer_class = PropertyIntegrationSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property', 'platform', 'is_active']
    search_fields = ['property__name', 'platform__name']
    
    def get_queryset(self):
        """Filter integrations by tenant"""
        user = self.request.user
        if user.is_superuser:
            return PropertyIntegration.objects.all()
        elif hasattr(user, 'tenant') and user.tenant:
            return PropertyIntegration.objects.filter(property__tenant=user.tenant)
        return PropertyIntegration.objects.none()
    
    def perform_create(self, serializer):
        """Check subscription limits when creating integration"""
        property_obj = serializer.validated_data.get('property')
        user = self.request.user
        
        if hasattr(user, 'tenant') and user.tenant:
            if not user.tenant.can_add_integration(property_obj):
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'error': 'Integration limit reached',
                    'detail': f'You have reached your maximum of {user.tenant.max_integrations_per_property} integrations per property. Please upgrade your plan.'
                })
        
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Trigger manual sync for an integration"""
        integration = self.get_object()
        sync_type = request.data.get('sync_type', 'FULL')
        
        from .tasks import sync_availability, sync_rates, sync_reservations
        
        if sync_type == 'AVAILABILITY':
            sync_availability.delay(str(integration.id))
        elif sync_type == 'RATES':
            sync_rates.delay(str(integration.id))
        elif sync_type == 'RESERVATIONS':
            sync_reservations.delay(str(integration.id))
        else:
            # Sync all
            sync_availability.delay(str(integration.id))
            sync_rates.delay(str(integration.id))
            sync_reservations.delay(str(integration.id))
        
        return Response({
            'message': f'Sync triggered for {sync_type}',
            'integration_id': integration.id,
        })


class SyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Sync Logs (read-only)"""
    serializer_class = SyncLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['platform', 'property_integration', 'sync_type', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter sync logs by tenant"""
        user = self.request.user
        if user.is_superuser:
            return SyncLog.objects.all()
        elif hasattr(user, 'tenant') and user.tenant:
            return SyncLog.objects.filter(
                property_integration__property__tenant=user.tenant
            )
        return SyncLog.objects.none()
