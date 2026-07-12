"""
API Views for Core Models
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone

from .models import Property, RoomType, RatePlan, Inventory, Promotion
from .serializers import (
    PropertySerializer, RoomTypeSerializer,
    RatePlanSerializer, InventorySerializer, PromotionSerializer
)
from tenants.permissions import IsTenantMember
from rbac.permissions import HasCapability
from rbac.services import filter_properties_for_user, filter_by_property_fk


class PropertyViewSet(viewsets.ModelViewSet):
    """ViewSet for Properties"""
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property_type', 'city', 'state', 'country', 'is_active']
    search_fields = ['name', 'legal_name', 'city', 'gstin']
    ordering_fields = ['name', 'created_at']
    ordering = ['-created_at']
    capability_map = {
        'list': 'properties.view',
        'retrieve': 'properties.view',
        'create': 'properties.create',
        'update': 'properties.edit',
        'partial_update': 'properties.edit',
        'destroy': 'properties.delete',
        'inventory': 'inventory.view',
        'stats': 'properties.view',
    }
    
    def get_queryset(self):
        """Filter properties by tenant + RBAC property assignments"""
        return filter_properties_for_user(Property.objects.all(), self.request.user)
    
    def perform_create(self, serializer):
        """Set tenant when creating property"""
        user = self.request.user
        if hasattr(user, 'tenant') and user.tenant:
            # Check if tenant can add property
            if not user.tenant.can_add_property():
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'error': 'Property limit reached',
                    'detail': f'You have reached your maximum of {user.tenant.max_properties} properties. Please upgrade your plan.'
                })
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get inventory for a property"""
        property_obj = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = Inventory.objects.filter(property=property_obj)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        serializer = InventorySerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get property statistics"""
        property_obj = self.get_object()
        
        from bookings.models import Reservation
        from integrations.models import PropertyIntegration
        
        stats = {
            'room_types': property_obj.room_types.filter(is_active=True).count(),
            'rate_plans': property_obj.rate_plans.filter(is_active=True).count(),
            'integrations': PropertyIntegration.objects.filter(
                property=property_obj,
                is_active=True
            ).count(),
            'reservations': {
                'total': Reservation.objects.filter(property=property_obj).count(),
                'confirmed': Reservation.objects.filter(
                    property=property_obj,
                    status='CONFIRMED'
                ).count(),
                'upcoming': Reservation.objects.filter(
                    property=property_obj,
                    status='CONFIRMED',
                    check_in__gte=timezone.now().date()
                ).count(),
            },
        }
        
        return Response(stats)


class RoomTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for Room Types"""
    serializer_class = RoomTypeSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property', 'is_active']
    search_fields = ['name', 'description']
    capability_map = {
        'list': 'properties.view',
        'retrieve': 'properties.view',
        'create': 'properties.edit',
        'update': 'properties.edit',
        'partial_update': 'properties.edit',
        'destroy': 'properties.edit',
    }
    
    def get_queryset(self):
        return filter_by_property_fk(RoomType.objects.all(), self.request.user)


class RatePlanViewSet(viewsets.ModelViewSet):
    """ViewSet for Rate Plans"""
    serializer_class = RatePlanSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property', 'room_type', 'is_active']
    search_fields = ['name', 'description']
    capability_map = {
        'list': 'rates.view',
        'retrieve': 'rates.view',
        'create': 'rates.edit',
        'update': 'rates.edit',
        'partial_update': 'rates.edit',
        'destroy': 'rates.edit',
    }
    
    def get_queryset(self):
        return filter_by_property_fk(RatePlan.objects.all(), self.request.user)


class InventoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Inventory"""
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['property', 'room_type', 'date']
    ordering_fields = ['date']
    ordering = ['date']
    capability_map = {
        'list': 'inventory.view',
        'retrieve': 'inventory.view',
        'create': 'inventory.edit',
        'update': 'inventory.edit',
        'partial_update': 'inventory.edit',
        'destroy': 'inventory.edit',
    }
    
    def get_queryset(self):
        return filter_by_property_fk(Inventory.objects.all(), self.request.user)


class PromotionViewSet(viewsets.ModelViewSet):
    """ViewSet for Promotions"""
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['property', 'promotion_type', 'is_active']
    search_fields = ['name', 'description']
    capability_map = {
        'list': 'rates.view',
        'retrieve': 'rates.view',
        'create': 'rates.edit',
        'update': 'rates.edit',
        'partial_update': 'rates.edit',
        'destroy': 'rates.edit',
    }
    
    def get_queryset(self):
        return filter_by_property_fk(Promotion.objects.all(), self.request.user)