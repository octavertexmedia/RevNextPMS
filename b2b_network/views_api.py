"""REST API for B2B Networks — staff (RBAC) + agent portal."""
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.db.models import Q

from core.mobile_api import tenant_from_user
from core.models import Property, RatePlan, RoomType
from products.services import has_product
from rbac.permissions import HasCapability
from tenants.permissions import IsTenantMember

from .models import (
    B2BAgent,
    B2BAllotment,
    B2BBooking,
    B2BRatePlan,
    CorporateAccount,
    agent_has_property_access,
    create_b2b_booking,
)
from .serializers import (
    B2BAgentSerializer,
    B2BAllotmentSerializer,
    B2BBookingSerializer,
    B2BRatePlanSerializer,
    PortalCreateBookingSerializer,
)


def _agents_for_user(user):
    qs = B2BAgent.objects.prefetch_related(
        'rate_plans__rate_plan', 'property_access__property',
    )
    if user.is_superuser:
        return qs
    tenant = tenant_from_user(user)
    if not tenant:
        return B2BAgent.objects.none()
    return qs.filter(
        Q(tenant=tenant) | Q(property_access__property__tenant=tenant)
    ).distinct()


class B2BAgentViewSet(viewsets.ModelViewSet):
    serializer_class = B2BAgentSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'b2b.view',
        'retrieve': 'b2b.view',
        'create': 'b2b.manage',
        'update': 'b2b.manage',
        'partial_update': 'b2b.manage',
        'destroy': 'b2b.manage',
        'set_active': 'b2b.manage',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['agent_type', 'is_active', 'portal_enabled']
    search_fields = ['company_name', 'contact_email', 'agent_code']
    ordering = ['company_name']

    def get_queryset(self):
        return _agents_for_user(self.request.user)

    def perform_create(self, serializer):
        tenant = tenant_from_user(self.request.user)
        property_ids = self.request.data.get('property_ids') or []
        agent = serializer.save(tenant=tenant)
        for pid in property_ids:
            prop = Property.objects.filter(id=pid, tenant=tenant).first()
            if prop:
                CorporateAccount.objects.get_or_create(
                    agent=agent, property=prop, defaults={'has_access': True},
                )

    def perform_update(self, serializer):
        agent = serializer.save()
        property_ids = self.request.data.get('property_ids')
        if property_ids is not None:
            tenant = tenant_from_user(self.request.user)
            CorporateAccount.objects.filter(agent=agent).delete()
            for pid in property_ids:
                prop = Property.objects.filter(id=pid, tenant=tenant).first()
                if prop:
                    CorporateAccount.objects.create(
                        agent=agent, property=prop, has_access=True,
                    )

    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        agent = self.get_object()
        is_active = request.data.get('is_active')
        if is_active is None:
            return Response({'detail': 'is_active is required.'}, status=status.HTTP_400_BAD_REQUEST)
        agent.is_active = bool(is_active)
        agent.save(update_fields=['is_active', 'updated_at'])
        return Response(B2BAgentSerializer(agent).data)


class B2BRatePlanViewSet(viewsets.ModelViewSet):
    serializer_class = B2BRatePlanSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'b2b.view',
        'retrieve': 'b2b.view',
        'create': 'b2b.manage',
        'update': 'b2b.manage',
        'partial_update': 'b2b.manage',
        'destroy': 'b2b.manage',
    }
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['agent', 'is_active', 'rate_plan']

    def get_queryset(self):
        qs = B2BRatePlan.objects.select_related('agent', 'rate_plan')
        user = self.request.user
        if user.is_superuser:
            return qs
        tenant = tenant_from_user(user)
        if not tenant:
            return B2BRatePlan.objects.none()
        return qs.filter(
            Q(agent__tenant=tenant) | Q(agent__property_access__property__tenant=tenant)
        ).distinct()


class B2BAllotmentViewSet(viewsets.ModelViewSet):
    serializer_class = B2BAllotmentSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'b2b.view',
        'retrieve': 'b2b.view',
        'create': 'b2b.manage',
        'update': 'b2b.manage',
        'partial_update': 'b2b.manage',
        'destroy': 'b2b.manage',
    }
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['agent', 'property', 'room_type', 'date']
    ordering = ['date']

    def get_queryset(self):
        qs = B2BAllotment.objects.select_related('agent', 'property', 'room_type')
        user = self.request.user
        if user.is_superuser:
            return qs
        tenant = tenant_from_user(user)
        if not tenant:
            return B2BAllotment.objects.none()
        return qs.filter(property__tenant=tenant)


class B2BBookingViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = B2BBookingSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    capability_map = {
        'list': 'b2b.view',
        'retrieve': 'b2b.view',
        'cancel': 'b2b.manage',
    }
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['agent', 'property', 'status']
    search_fields = ['guest_name', 'confirmation_code', 'guest_email']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = B2BBooking.objects.select_related(
            'agent', 'property', 'room_type', 'rate_plan', 'reservation',
        )
        user = self.request.user
        if user.is_superuser:
            return qs
        tenant = tenant_from_user(user)
        if not tenant:
            return B2BBooking.objects.none()
        return qs.filter(property__tenant=tenant)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status == 'CANCELLED':
            return Response({'detail': 'Already cancelled'}, status=400)
        booking.status = 'CANCELLED'
        booking.save(update_fields=['status', 'updated_at'])
        if booking.reservation_id:
            booking.reservation.status = 'CANCELLED'
            booking.reservation.save(update_fields=['status', 'updated_at'])
        return Response(B2BBookingSerializer(booking).data)


# ─── Agent portal (networks.revnext.in/b2b/portal + /api/b2b/portal) ────────

def _portal_agent(request):
    """Resolve authenticated user → B2BAgent."""
    user = request.user
    agent = getattr(user, 'b2b_agent', None)
    if agent and agent.is_active and agent.portal_enabled:
        return agent
    return None


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_me(request):
    agent = _portal_agent(request)
    if not agent:
        return Response({'error': 'Not a B2B portal user'}, status=403)
    tenant = agent.tenant
    if tenant and not has_product(tenant, 'networks'):
        return Response(
            {'error': 'product_entitlement_required', 'product': 'networks'},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )
    return Response({
        'agent': B2BAgentSerializer(agent).data,
        'host': 'networks.revnext.in',
        'product': 'networks',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_properties(request):
    agent = _portal_agent(request)
    if not agent:
        return Response({'error': 'Not a B2B portal user'}, status=403)
    access = CorporateAccount.objects.filter(
        agent=agent, has_access=True,
    ).select_related('property')
    return Response([
        {
            'id': ca.property_id,
            'name': ca.property.name,
            'city': getattr(ca.property, 'city', '') or '',
        }
        for ca in access
    ])


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_rates(request):
    agent = _portal_agent(request)
    if not agent:
        return Response({'error': 'Not a B2B portal user'}, status=403)
    rates = B2BRatePlan.objects.filter(agent=agent, is_active=True).select_related('rate_plan')
    return Response(B2BRatePlanSerializer(rates, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_allotments(request):
    agent = _portal_agent(request)
    if not agent:
        return Response({'error': 'Not a B2B portal user'}, status=403)
    qs = B2BAllotment.objects.filter(agent=agent).select_related('property', 'room_type')
    property_id = request.query_params.get('property')
    if property_id:
        qs = qs.filter(property_id=property_id)
    return Response(B2BAllotmentSerializer(qs[:200], many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def portal_bookings(request):
    agent = _portal_agent(request)
    if not agent:
        return Response({'error': 'Not a B2B portal user'}, status=403)
    qs = B2BBooking.objects.filter(agent=agent).select_related(
        'property', 'room_type',
    ).order_by('-created_at')[:100]
    return Response(B2BBookingSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def portal_create_booking(request):
    agent = _portal_agent(request)
    if not agent:
        return Response({'error': 'Not a B2B portal user'}, status=403)
    if agent.tenant and not has_product(agent.tenant, 'networks'):
        return Response(
            {'error': 'product_entitlement_required', 'product': 'networks'},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )

    ser = PortalCreateBookingSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    property_obj = get_object_or_404(Property, id=data['property_id'])
    if not agent_has_property_access(agent, property_obj):
        return Response({'error': 'No access to this property'}, status=403)

    room_type = get_object_or_404(RoomType, id=data['room_type_id'], property=property_obj)
    rate_plan = None
    if data.get('rate_plan_id'):
        rate_plan = get_object_or_404(RatePlan, id=data['rate_plan_id'])

    host = request.get_host().split(':')[0]
    try:
        booking = create_b2b_booking(
            agent=agent,
            property_obj=property_obj,
            room_type=room_type,
            check_in=data['check_in'],
            check_out=data['check_out'],
            guest_name=data['guest_name'],
            guest_email=data.get('guest_email') or '',
            guest_phone=data.get('guest_phone') or '',
            adults=data['adults'],
            children=data['children'],
            rate_plan=rate_plan,
            special_requests=data.get('special_requests') or '',
            channel_host=host,
        )
    except ValueError as exc:
        return Response({'error': str(exc)}, status=400)

    return Response(B2BBookingSerializer(booking).data, status=status.HTTP_201_CREATED)
