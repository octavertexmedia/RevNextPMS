"""REST API for Booking Engine — staff (RBAC) + public guest checkout."""
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.mobile_api import property_tenant_qs, tenant_from_user
from core.models import Property, RatePlan, RoomType
from products.services import has_product
from rbac.permissions import HasCapability
from tenants.permissions import IsTenantMember

from .models import BookingEngineConfig, DirectBooking, check_availability, create_direct_booking
from .serializers import (
    BookingEngineConfigSerializer,
    DirectBookingSerializer,
    PublicAvailabilitySerializer,
    PublicCreateBookingSerializer,
)


def _tenant_entitled_for_booking(property_obj) -> bool:
    tenant = getattr(property_obj, 'tenant', None)
    if not tenant:
        return False
    return has_product(tenant, 'booking')


class DirectBookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DirectBookingSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'booking_engine.view',
        'retrieve': 'booking_engine.view',
        'cancel': 'booking_engine.configure',
        'confirm': 'booking_engine.configure',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property', 'status', 'source']
    search_fields = ['guest_name', 'guest_email', 'confirmation_code']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = DirectBooking.objects.select_related(
            'property', 'room_type', 'rate_plan', 'reservation',
        )
        return property_tenant_qs(qs, self.request.user)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status in ('CANCELLED', 'CHECKED_OUT'):
            return Response(
                {'detail': f'Cannot cancel booking with status {booking.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.status = 'CANCELLED'
        booking.save(update_fields=['status', 'updated_at'])
        if booking.reservation_id:
            booking.reservation.status = 'CANCELLED'
            booking.reservation.save(update_fields=['status', 'updated_at'])
        return Response(DirectBookingSerializer(booking).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        booking = self.get_object()
        if booking.status != 'PENDING':
            return Response(
                {'detail': 'Only PENDING bookings can be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        booking.status = 'CONFIRMED'
        booking.save(update_fields=['status', 'updated_at'])
        if booking.reservation_id:
            booking.reservation.status = 'CONFIRMED'
            booking.reservation.save(update_fields=['status', 'updated_at'])
        return Response(DirectBookingSerializer(booking).data)


class BookingEngineConfigViewSet(viewsets.ModelViewSet):
    serializer_class = BookingEngineConfigSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'booking_engine.view',
        'retrieve': 'booking_engine.view',
        'create': 'booking_engine.configure',
        'update': 'booking_engine.configure',
        'partial_update': 'booking_engine.configure',
        'destroy': 'booking_engine.configure',
    }
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property', 'is_enabled']

    def get_queryset(self):
        qs = BookingEngineConfig.objects.select_related('property')
        user = self.request.user
        if user.is_superuser:
            return qs
        tenant = tenant_from_user(user)
        if not tenant:
            return BookingEngineConfig.objects.none()
        return qs.filter(property__tenant=tenant)

    def perform_create(self, serializer):
        prop = serializer.validated_data['property']
        tenant = tenant_from_user(self.request.user)
        if not self.request.user.is_superuser and prop.tenant_id != getattr(tenant, 'id', None):
            raise PermissionError('Property not in your tenant')
        serializer.save()


# ─── Public guest API (booking.revnext.in widget / embed) ───────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def public_property_config(request, property_id):
    """Public widget bootstrap: branding + constraints for a property."""
    property_obj = get_object_or_404(Property, id=property_id, is_active=True)
    if not _tenant_entitled_for_booking(property_obj):
        return Response(
            {'error': 'product_entitlement_required', 'product': 'booking'},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )
    config, _ = BookingEngineConfig.objects.get_or_create(property=property_obj)
    if not config.is_enabled:
        return Response({'error': 'Booking engine disabled for this property'}, status=403)

    room_types = [
        {
            'id': rt.id,
            'name': rt.name,
            'max_occupancy': getattr(rt, 'max_occupancy', None) or getattr(rt, 'max_adults', 2),
        }
        for rt in RoomType.objects.filter(property=property_obj, is_active=True)
    ]
    return Response({
        'property': {
            'id': property_obj.id,
            'name': property_obj.name,
            'city': getattr(property_obj, 'city', '') or '',
            'country': getattr(property_obj, 'country', '') or '',
        },
        'config': BookingEngineConfigSerializer(config).data,
        'room_types': room_types,
        'host': 'booking.revnext.in',
        'product': 'booking',
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def public_availability(request):
    """Check room availability for public checkout."""
    ser = PublicAvailabilitySerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    property_obj = get_object_or_404(Property, id=data['property_id'], is_active=True)
    if not _tenant_entitled_for_booking(property_obj):
        return Response(
            {'error': 'product_entitlement_required', 'product': 'booking'},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )
    config = BookingEngineConfig.objects.filter(property=property_obj).first()
    if config and not config.is_enabled:
        return Response({'error': 'Booking engine disabled'}, status=403)

    check_in, check_out = data['check_in'], data['check_out']
    nights = (check_out - check_in).days
    if config:
        if nights < config.min_nights or nights > config.max_nights:
            return Response(
                {'error': f'Stay must be between {config.min_nights} and {config.max_nights} nights'},
                status=400,
            )
        if not config.allow_children and data['children'] > 0:
            return Response({'error': 'Children not allowed'}, status=400)

    results = []
    for rt in RoomType.objects.filter(property=property_obj, is_active=True):
        ok, available, msg = check_availability(property_obj, rt, check_in, check_out)
        if not ok:
            continue
        plans = []
        for rp in RatePlan.objects.filter(room_type=rt, is_active=True):
            total = rp.base_rate.amount * nights
            plans.append({
                'id': rp.id,
                'name': rp.name,
                'per_night': float(rp.base_rate.amount),
                'total': float(total),
                'currency': str(rp.base_rate.currency),
            })
        if plans:
            results.append({
                'room_type_id': rt.id,
                'room_type_name': rt.name,
                'available': available,
                'nights': nights,
                'rate_plans': plans,
            })
    return Response({
        'property_id': property_obj.id,
        'check_in': check_in,
        'check_out': check_out,
        'nights': nights,
        'results': results,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def public_create_booking(request):
    """Create a direct booking from the public widget / API."""
    ser = PublicCreateBookingSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    property_obj = get_object_or_404(Property, id=data['property_id'], is_active=True)
    if not _tenant_entitled_for_booking(property_obj):
        return Response(
            {'error': 'product_entitlement_required', 'product': 'booking'},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )
    config = BookingEngineConfig.objects.filter(property=property_obj).first()
    if config and not config.is_enabled:
        return Response({'error': 'Booking engine disabled'}, status=403)
    if config and config.require_phone and not data.get('guest_phone'):
        return Response({'error': 'Phone number is required'}, status=400)

    room_type = get_object_or_404(RoomType, id=data['room_type_id'], property=property_obj)
    rate_plan = None
    if data.get('rate_plan_id'):
        rate_plan = get_object_or_404(RatePlan, id=data['rate_plan_id'], room_type=room_type)

    host = request.get_host().split(':')[0]
    try:
        booking = create_direct_booking(
            property_obj=property_obj,
            room_type=room_type,
            rate_plan=rate_plan,
            check_in=data['check_in'],
            check_out=data['check_out'],
            guest_name=data['guest_name'],
            guest_email=data['guest_email'],
            guest_phone=data.get('guest_phone') or '',
            adults=data['adults'],
            children=data['children'],
            source=data.get('source') or 'booking_engine',
            google_hotel_ads=data.get('google_hotel_ads', False),
            channel_host=host,
            auto_confirm=True,
        )
    except ValueError as exc:
        return Response({'error': str(exc)}, status=400)

    return Response(DirectBookingSerializer(booking).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_lookup_booking(request, confirmation_code):
    """Guest confirmation lookup by code + email."""
    email = (request.query_params.get('email') or '').strip().lower()
    if not email:
        return Response({'error': 'email query param required'}, status=400)
    booking = DirectBooking.objects.filter(
        confirmation_code__iexact=confirmation_code,
        guest_email__iexact=email,
    ).select_related('property', 'room_type').first()
    if not booking:
        return Response({'error': 'Booking not found'}, status=404)
    return Response(DirectBookingSerializer(booking).data)
