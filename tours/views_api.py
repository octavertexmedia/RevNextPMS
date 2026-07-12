"""REST API for Tours — staff (RBAC) + public storefront + agent portal."""
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.mobile_api import tenant_from_user
from products.services import has_product
from rbac.permissions import HasCapability
from tenants.permissions import IsTenantMember

from .models import (
    Departure,
    ItineraryDay,
    TourAgent,
    TourBooking,
    TourPackage,
    ToursConfig,
    check_departure_availability,
    create_tour_booking,
)
from .serializers import (
    DepartureSerializer,
    ItineraryDaySerializer,
    PublicCreateTourBookingSerializer,
    PublicTourSearchSerializer,
    TourAgentSerializer,
    TourBookingSerializer,
    TourPackageSerializer,
    ToursConfigSerializer,
)


class ToursConfigViewSet(viewsets.ModelViewSet):
    serializer_class = ToursConfigSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'tours.view', 'retrieve': 'tours.view',
        'create': 'tours.manage', 'update': 'tours.manage',
        'partial_update': 'tours.manage', 'destroy': 'tours.manage',
    }
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']

    def get_queryset(self):
        tenant = tenant_from_user(self.request.user)
        if self.request.user.is_superuser:
            return ToursConfig.objects.all()
        if not tenant:
            return ToursConfig.objects.none()
        return ToursConfig.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=tenant_from_user(self.request.user))


class TourPackageViewSet(viewsets.ModelViewSet):
    serializer_class = TourPackageSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'tours.view', 'retrieve': 'tours.view',
        'create': 'tours.manage', 'update': 'tours.manage',
        'partial_update': 'tours.manage', 'destroy': 'tours.manage',
        'publish': 'tours.manage',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_published', 'category', 'property']
    search_fields = ['name', 'slug', 'description']
    ordering = ['name']

    def get_queryset(self):
        qs = TourPackage.objects.prefetch_related('itinerary_days', 'departures')
        if self.request.user.is_superuser:
            return qs
        tenant = tenant_from_user(self.request.user)
        return qs.filter(tenant=tenant) if tenant else qs.none()

    def perform_create(self, serializer):
        serializer.save(tenant=tenant_from_user(self.request.user))

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        pkg = self.get_object()
        pkg.is_published = bool(request.data.get('is_published', True))
        pkg.save(update_fields=['is_published', 'updated_at'])
        return Response(TourPackageSerializer(pkg).data)


class ItineraryDayViewSet(viewsets.ModelViewSet):
    serializer_class = ItineraryDaySerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'tours.view', 'retrieve': 'tours.view',
        'create': 'tours.manage', 'update': 'tours.manage',
        'partial_update': 'tours.manage', 'destroy': 'tours.manage',
    }
    filterset_fields = ['package']

    def get_queryset(self):
        qs = ItineraryDay.objects.select_related('package')
        if self.request.user.is_superuser:
            return qs
        tenant = tenant_from_user(self.request.user)
        return qs.filter(package__tenant=tenant) if tenant else qs.none()


class DepartureViewSet(viewsets.ModelViewSet):
    serializer_class = DepartureSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'tours.view', 'retrieve': 'tours.view',
        'create': 'tours.inventory', 'update': 'tours.inventory',
        'partial_update': 'tours.inventory', 'destroy': 'tours.inventory',
    }
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['package', 'status', 'start_date']
    ordering = ['start_date']

    def get_queryset(self):
        qs = Departure.objects.select_related('package')
        if self.request.user.is_superuser:
            return qs
        tenant = tenant_from_user(self.request.user)
        return qs.filter(package__tenant=tenant) if tenant else qs.none()


class TourBookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TourBookingSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'tours.view', 'retrieve': 'tours.view',
        'cancel': 'tours.bookings',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'package', 'departure']
    search_fields = ['guest_name', 'guest_email', 'confirmation_code']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = TourBooking.objects.select_related('package', 'departure', 'agent')
        if self.request.user.is_superuser:
            return qs
        tenant = tenant_from_user(self.request.user)
        return qs.filter(tenant=tenant) if tenant else qs.none()

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status == 'CANCELLED':
            return Response({'detail': 'Already cancelled'}, status=400)
        with transaction.atomic():
            booking.status = 'CANCELLED'
            booking.save(update_fields=['status', 'updated_at'])
            dep = Departure.objects.select_for_update().get(pk=booking.departure_id)
            dep.booked_seats = max(0, dep.booked_seats - booking.total_pax)
            if dep.status == 'FULL' and dep.seats_remaining > 0:
                dep.status = 'OPEN'
            dep.save(update_fields=['booked_seats', 'status', 'updated_at'])
        return Response(TourBookingSerializer(booking).data)


class TourAgentViewSet(viewsets.ModelViewSet):
    serializer_class = TourAgentSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'tours.view', 'retrieve': 'tours.view',
        'create': 'tours.agents', 'update': 'tours.agents',
        'partial_update': 'tours.agents', 'destroy': 'tours.agents',
    }
    filterset_fields = ['is_active', 'portal_enabled']
    search_fields = ['company_name', 'contact_email']

    def get_queryset(self):
        if self.request.user.is_superuser:
            return TourAgent.objects.all()
        tenant = tenant_from_user(self.request.user)
        return TourAgent.objects.filter(tenant=tenant) if tenant else TourAgent.objects.none()

    def perform_create(self, serializer):
        serializer.save(tenant=tenant_from_user(self.request.user))


# ─── Public storefront (tours.revnext.in) ───────────────────────────────────

def _tenant_entitled_tours(tenant) -> bool:
    return bool(tenant and has_product(tenant, 'tours'))


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def public_search_packages(request):
    """Search published tour packages across entitled operators."""
    if request.method == 'POST':
        ser = PublicTourSearchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
    else:
        ser = PublicTourSearchSerializer(data=request.query_params)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

    qs = TourPackage.objects.filter(is_active=True, is_published=True).prefetch_related('departures')
    # Only packages whose tenant has tours entitlement
    entitled_ids = []
    for tid in qs.values_list('tenant_id', flat=True).distinct():
        from tenants.models import Tenant
        t = Tenant.objects.filter(id=tid).first()
        if _tenant_entitled_tours(t):
            entitled_ids.append(tid)
    qs = qs.filter(tenant_id__in=entitled_ids)

    if data.get('destination'):
        qs = qs.filter(destinations__icontains=data['destination'])
    if data.get('category'):
        qs = qs.filter(category=data['category'])
    if data.get('min_days'):
        qs = qs.filter(duration_days__gte=data['min_days'])
    if data.get('max_days'):
        qs = qs.filter(duration_days__lte=data['max_days'])

    start_from = data.get('start_from')
    start_to = data.get('start_to')
    if start_from or start_to:
        dep_q = Q(departures__status__in=('OPEN', 'GUARANTEED'))
        if start_from:
            dep_q &= Q(departures__start_date__gte=start_from)
        if start_to:
            dep_q &= Q(departures__start_date__lte=start_to)
        qs = qs.filter(dep_q).distinct()

    return Response({
        'count': qs.count(),
        'results': TourPackageSerializer(qs[:50], many=True).data,
        'host': 'tours.revnext.in',
        'product': 'tours',
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def public_package_detail(request, slug):
    pkg = get_object_or_404(
        TourPackage.objects.prefetch_related('itinerary_days', 'departures'),
        slug=slug, is_active=True, is_published=True,
    )
    if not _tenant_entitled_tours(pkg.tenant):
        return Response({'error': 'product_entitlement_required', 'product': 'tours'}, status=402)
    return Response(TourPackageSerializer(pkg).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_departure_availability(request, departure_id):
    dep = get_object_or_404(Departure.objects.select_related('package'), id=departure_id)
    if not _tenant_entitled_tours(dep.package.tenant):
        return Response({'error': 'product_entitlement_required', 'product': 'tours'}, status=402)
    pax = int(request.query_params.get('pax', 1))
    ok, remaining, msg = check_departure_availability(dep, pax)
    return Response({
        'departure': DepartureSerializer(dep).data,
        'available': ok,
        'seats_remaining': remaining,
        'message': msg,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def public_create_booking(request):
    ser = PublicCreateTourBookingSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    dep = get_object_or_404(Departure.objects.select_related('package'), id=data['departure_id'])
    if not _tenant_entitled_tours(dep.package.tenant):
        return Response({'error': 'product_entitlement_required', 'product': 'tours'}, status=402)
    host = request.get_host().split(':')[0]
    try:
        booking = create_tour_booking(
            departure=dep,
            guest_name=data['guest_name'],
            guest_email=data['guest_email'],
            guest_phone=data.get('guest_phone') or '',
            adults=data['adults'],
            children=data['children'],
            special_requests=data.get('special_requests') or '',
            channel_host=host,
            source='tours_public',
            require_published=True,
        )
    except ValueError as exc:
        return Response({'error': str(exc)}, status=400)
    return Response(TourBookingSerializer(booking).data, status=201)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_lookup_booking(request, confirmation_code):
    email = (request.query_params.get('email') or '').strip().lower()
    if not email:
        return Response({'error': 'email query param required'}, status=400)
    booking = TourBooking.objects.filter(
        confirmation_code__iexact=confirmation_code,
        guest_email__iexact=email,
    ).select_related('package', 'departure').first()
    if not booking:
        return Response({'error': 'Booking not found'}, status=404)
    return Response(TourBookingSerializer(booking).data)


# ─── Agent portal ───────────────────────────────────────────────────────────

def _portal_tour_agent(request):
    agent = getattr(request.user, 'tour_agent', None)
    if agent and agent.is_active and agent.portal_enabled:
        return agent
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_me(request):
    agent = _portal_tour_agent(request)
    if not agent:
        return Response({'error': 'Not a tours portal agent'}, status=403)
    if not has_product(agent.tenant, 'tours'):
        return Response({'error': 'product_entitlement_required', 'product': 'tours'}, status=402)
    return Response({
        'agent': TourAgentSerializer(agent).data,
        'host': 'tours.revnext.in',
        'product': 'tours',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_packages(request):
    agent = _portal_tour_agent(request)
    if not agent:
        return Response({'error': 'Not a tours portal agent'}, status=403)
    qs = TourPackage.objects.filter(tenant=agent.tenant, is_active=True)
    return Response(TourPackageSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def portal_create_booking(request):
    agent = _portal_tour_agent(request)
    if not agent:
        return Response({'error': 'Not a tours portal agent'}, status=403)
    if not has_product(agent.tenant, 'tours'):
        return Response({'error': 'product_entitlement_required', 'product': 'tours'}, status=402)
    ser = PublicCreateTourBookingSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data
    dep = get_object_or_404(
        Departure.objects.select_related('package'),
        id=data['departure_id'], package__tenant=agent.tenant,
    )
    host = request.get_host().split(':')[0]
    try:
        booking = create_tour_booking(
            departure=dep,
            guest_name=data['guest_name'],
            guest_email=data['guest_email'],
            guest_phone=data.get('guest_phone') or '',
            adults=data['adults'],
            children=data['children'],
            special_requests=data.get('special_requests') or '',
            agent=agent,
            channel_host=host,
            source='tours_agent_portal',
            require_published=False,
        )
    except ValueError as exc:
        return Response({'error': str(exc)}, status=400)
    return Response(TourBookingSerializer(booking).data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_bookings(request):
    agent = _portal_tour_agent(request)
    if not agent:
        return Response({'error': 'Not a tours portal agent'}, status=403)
    qs = TourBooking.objects.filter(agent=agent).select_related('package', 'departure')[:100]
    return Response(TourBookingSerializer(qs, many=True).data)
