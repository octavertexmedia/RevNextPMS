"""
API Views for Tenant Management
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.utils import timezone
from datetime import timedelta

from .models import Tenant, TenantUser, SubscriptionPlan, SubscriptionPayment
from .serializers import (
    TenantSerializer, TenantUserSerializer,
    SubscriptionPlanSerializer, SubscriptionPaymentSerializer
)
from .permissions import IsTenantOwner, IsTenantMember


class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Subscription Plans (read-only for tenants)"""
    queryset = SubscriptionPlan.objects.filter(is_active=True, is_visible=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return visible plans"""
        return SubscriptionPlan.objects.filter(is_active=True, is_visible=True).order_by('monthly_price')


class TenantViewSet(viewsets.ModelViewSet):
    """ViewSet for Tenant Management"""
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter tenants based on user permissions"""
        user = self.request.user
        if user.is_superuser:
            return Tenant.objects.all()
        elif hasattr(user, 'tenant') and user.tenant:
            return Tenant.objects.filter(id=user.tenant.id)
        return Tenant.objects.none()
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]  # Only admins can modify tenants
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get tenant statistics"""
        tenant = self.get_object()
        
        from core.models import Property
        from bookings.models import Reservation, Payment
        from integrations.models import PropertyIntegration
        
        stats = {
            'properties': {
                'total': tenant.property_count,
                'max': tenant.max_properties,
                'can_add': tenant.can_add_property(),
            },
            'users': {
                'total': tenant.user_count,
                'max': tenant.max_users,
                'can_add': tenant.can_add_user(),
            },
            'reservations': {
                'total': Reservation.objects.filter(property__tenant=tenant).count(),
                'confirmed': Reservation.objects.filter(
                    property__tenant=tenant,
                    status='CONFIRMED'
                ).count(),
                'pending': Reservation.objects.filter(
                    property__tenant=tenant,
                    status='PENDING'
                ).count(),
            },
            'integrations': {
                'total': PropertyIntegration.objects.filter(
                    property__tenant=tenant,
                    is_active=True
                ).count(),
            },
            'api_usage': {
                'calls_this_month': tenant.api_calls_this_month,
                'max_per_month': tenant.max_api_calls_per_month,
                'reset_date': tenant.api_calls_reset_date,
            },
            'subscription': {
                'status': tenant.subscription_status,
                'is_active': tenant.is_subscription_active,
                'days_until_expiry': tenant.days_until_expiry,
                'plan': tenant.subscription_plan.display_name if tenant.subscription_plan else None,
            },
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def upgrade_subscription(self, request, pk=None):
        """Upgrade tenant subscription"""
        tenant = self.get_object()
        
        plan_id = request.data.get('plan_id')
        billing_cycle = request.data.get('billing_cycle', 'monthly')
        
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'Invalid subscription plan'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tenant.upgrade_subscription(plan, billing_cycle)
        
        # Create payment record
        amount = plan.monthly_price if billing_cycle == 'monthly' else plan.yearly_price
        payment = SubscriptionPayment.objects.create(
            tenant=tenant,
            subscription_plan=plan,
            amount=amount,
            billing_cycle=billing_cycle,
            payment_status='pending',
            period_start=timezone.now().date(),
            period_end=tenant.subscription_end_date,
        )
        
        serializer = self.get_serializer(tenant)
        return Response({
            'message': 'Subscription upgraded successfully',
            'tenant': serializer.data,
            'payment_id': payment.id,
        })


class TenantUserViewSet(viewsets.ModelViewSet):
    """ViewSet for Tenant User Management"""
    serializer_class = TenantUserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter users based on tenant"""
        user = self.request.user
        if user.is_superuser:
            return TenantUser.objects.all()
        elif hasattr(user, 'tenant') and user.tenant:
            return TenantUser.objects.filter(tenant=user.tenant)
        return TenantUser.objects.none()
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsTenantOwner()]  # Only owners can manage users
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Set tenant when creating user"""
        user = self.request.user
        if hasattr(user, 'tenant') and user.tenant:
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()


class SubscriptionPaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Subscription Payments (read-only)"""
    serializer_class = SubscriptionPaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter payments based on tenant"""
        user = self.request.user
        if user.is_superuser:
            return SubscriptionPayment.objects.all()
        elif hasattr(user, 'tenant') and user.tenant:
            return SubscriptionPayment.objects.filter(tenant=user.tenant)
        return SubscriptionPayment.objects.none()
