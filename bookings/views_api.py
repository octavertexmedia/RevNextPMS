"""
API Views for Bookings
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from djmoney.money import Money

from .models import Reservation, Payment
from .serializers import ReservationSerializer, PaymentSerializer
from tenants.permissions import IsTenantMember
from rbac.permissions import HasCapability
from rbac.services import filter_by_property_fk


class ReservationViewSet(viewsets.ModelViewSet):
    """ViewSet for Reservations"""
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property', 'status', 'provider_name', 'check_in', 'check_out']
    search_fields = ['guest_name', 'guest_email', 'provider_reservation_id', 'provider_confirmation_code']
    ordering_fields = ['check_in', 'check_out', 'created_at']
    ordering = ['-check_in']
    capability_map = {
        'list': 'reservations.view',
        'retrieve': 'reservations.view',
        'create': 'reservations.create',
        'update': 'reservations.edit',
        'partial_update': 'reservations.edit',
        'destroy': 'reservations.cancel',
        'upcoming': 'reservations.view',
        'today': 'reservations.view',
        'departures': 'reservations.view',
        'in_house': 'reservations.view',
        'cancel': 'reservations.cancel',
        'check_in': 'reservations.checkin',
        'check_out': 'reservations.checkout',
    }

    def get_queryset(self):
        """Filter reservations by tenant + RBAC property scope"""
        qs = Reservation.objects.select_related(
            'property', 'room_type', 'rate_plan'
        ).prefetch_related('payments')
        return filter_by_property_fk(qs, self.request.user)

    def _property_filter(self, queryset):
        property_id = self.request.query_params.get('property')
        if property_id:
            queryset = queryset.filter(property_id=property_id)
        return queryset

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming reservations"""
        queryset = self._property_filter(self.get_queryset()).filter(
            check_in__gte=timezone.now().date(),
            status='CONFIRMED',
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's arrivals (confirmed check-ins)"""
        today = timezone.now().date()
        queryset = self._property_filter(self.get_queryset()).filter(
            check_in=today,
            status='CONFIRMED',
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def departures(self, request):
        """Get today's departures (in-house guests checking out today)"""
        today = timezone.now().date()
        queryset = self._property_filter(self.get_queryset()).filter(
            check_out=today,
            status='CHECKED_IN',
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def in_house(self, request):
        """Get currently in-house guests"""
        queryset = self._property_filter(self.get_queryset()).filter(status='CHECKED_IN')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a reservation"""
        reservation = self.get_object()
        if reservation.status in ('CHECKED_OUT', 'CANCELLED'):
            return Response(
                {'detail': f'Cannot cancel a reservation with status {reservation.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reservation.status = 'CANCELLED'
        reservation.save(update_fields=['status', 'updated_at'])
        serializer = self.get_serializer(reservation)
        return Response({
            'message': 'Reservation cancelled',
            'reservation': serializer.data,
        })

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        """
        Check in a guest.
        Optionally pass room_number to stamp on the auto-created folio.
        """
        reservation = self.get_object()
        if reservation.status not in ('CONFIRMED', 'PENDING', 'MODIFIED'):
            return Response(
                {'detail': f'Cannot check in a reservation with status {reservation.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.status = 'CHECKED_IN'
        reservation.save(update_fields=['status', 'updated_at'])

        folio = None
        try:
            from cloud_pms.models import Folio
            room_number = (request.data.get('room_number') or '').strip()
            folio, created = Folio.objects.get_or_create(
                reservation=reservation,
                defaults={
                    'property': reservation.property,
                    'guest_name': reservation.guest_name,
                    'guest_email': reservation.guest_email or '',
                    'room_number': room_number,
                    'status': 'OPEN',
                    'total_charges': Money(0, reservation.currency or 'INR'),
                    'total_payments': Money(0, reservation.currency or 'INR'),
                    'balance': Money(0, reservation.currency or 'INR'),
                },
            )
            if not created and room_number and not folio.room_number:
                folio.room_number = room_number
                folio.save(update_fields=['room_number', 'updated_at'])
        except Exception:
            folio = None

        try:
            from tenants.push import notify_tenant_staff
            notify_tenant_staff(
                getattr(reservation.property, 'tenant', None),
                title='Guest checked in',
                body=f'{reservation.guest_name} · {reservation.property.name}',
                data={'type': 'check_in', 'reservation_id': str(reservation.id)},
            )
        except Exception:
            pass

        serializer = self.get_serializer(reservation)
        payload = {
            'message': 'Guest checked in',
            'reservation': serializer.data,
        }
        if folio is not None:
            payload['folio_id'] = folio.id
        return Response(payload)

    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        """
        Check out a guest.
        Closes linked open folios when balance is zero or force=true.
        """
        reservation = self.get_object()
        if reservation.status != 'CHECKED_IN':
            return Response(
                {'detail': f'Cannot check out a reservation with status {reservation.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        force = bool(request.data.get('force', False))
        closed_folios = []

        try:
            from cloud_pms.models import Folio
            open_folios = Folio.objects.filter(
                reservation=reservation,
                status__in=('OPEN', 'PENDING', 'PAID'),
            )
            for folio in open_folios:
                balance_amount = float(folio.balance.amount) if folio.balance else 0
                if balance_amount > 0 and not force:
                    return Response(
                        {
                            'detail': 'Folio has an outstanding balance. Settle or pass force=true.',
                            'folio_id': folio.id,
                            'balance': str(folio.balance.amount),
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                folio.status = 'CLOSED'
                folio.closed_at = timezone.now()
                folio.save(update_fields=['status', 'closed_at', 'updated_at'])
                closed_folios.append(folio.id)
        except Exception:
            pass

        reservation.status = 'CHECKED_OUT'
        reservation.save(update_fields=['status', 'updated_at'])

        # Create departure housekeeping task when a room number is known
        try:
            from cloud_pms.models import Folio, HousekeepingTask
            room_number = ''
            folio = Folio.objects.filter(reservation=reservation).order_by('-created_at').first()
            if folio:
                room_number = folio.room_number or ''
            if room_number:
                HousekeepingTask.objects.create(
                    property=reservation.property,
                    room_number=room_number,
                    room_type=reservation.room_type,
                    task_type='Checkout Cleaning',
                    description=f'Checkout cleaning for {reservation.guest_name}',
                    status='PENDING',
                    priority='HIGH',
                    due_date=timezone.now().date(),
                    reservation=reservation,
                )
        except Exception:
            pass

        serializer = self.get_serializer(reservation)
        return Response({
            'message': 'Guest checked out',
            'reservation': serializer.data,
            'closed_folios': closed_folios,
        })


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Payments (read-only)"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['reservation', 'payment_status', 'payment_method', 'gateway_name']
    ordering_fields = ['paid_at', 'created_at']
    ordering = ['-created_at']
    capability_map = {
        'list': 'finance.view',
        'retrieve': 'finance.view',
    }

    def get_queryset(self):
        """Filter payments by tenant + RBAC property scope"""
        return filter_by_property_fk(
            Payment.objects.all(),
            self.request.user,
            property_field='reservation__property',
        )
