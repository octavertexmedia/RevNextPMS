"""
API Views for Bookings
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from .models import Reservation, Payment
from .serializers import ReservationSerializer, PaymentSerializer
from tenants.permissions import IsTenantMember


class ReservationViewSet(viewsets.ModelViewSet):
    """ViewSet for Reservations"""
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property', 'status', 'provider_name', 'check_in', 'check_out']
    search_fields = ['guest_name', 'guest_email', 'provider_reservation_id', 'provider_confirmation_code']
    ordering_fields = ['check_in', 'check_out', 'created_at']
    ordering = ['-check_in']
    
    def get_queryset(self):
        """Filter reservations by tenant"""
        user = self.request.user
        if user.is_superuser:
            return Reservation.objects.all()
        elif hasattr(user, 'tenant') and user.tenant:
            return Reservation.objects.filter(property__tenant=user.tenant)
        return Reservation.objects.none()
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming reservations"""
        queryset = self.get_queryset().filter(
            check_in__gte=timezone.now().date(),
            status='CONFIRMED'
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's check-ins"""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(
            check_in=today,
            status='CONFIRMED'
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a reservation"""
        reservation = self.get_object()
        reservation.status = 'CANCELLED'
        reservation.save()
        serializer = self.get_serializer(reservation)
        return Response({
            'message': 'Reservation cancelled',
            'reservation': serializer.data,
        })


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Payments (read-only)"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['reservation', 'payment_status', 'payment_method', 'gateway_name']
    ordering_fields = ['paid_at', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter payments by tenant"""
        user = self.request.user
        if user.is_superuser:
            return Payment.objects.all()
        elif hasattr(user, 'tenant') and user.tenant:
            return Payment.objects.filter(reservation__property__tenant=user.tenant)
        return Payment.objects.none()
