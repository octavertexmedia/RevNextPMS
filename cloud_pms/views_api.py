"""
REST API views for Cloud PMS (mobile / front-desk clients).
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from bookings.models import Reservation
from core.models import Property
from tenants.permissions import IsTenantMember
from rbac.permissions import HasCapability
from rbac.services import filter_by_property_fk, filter_properties_for_user, user_has_capability

from .models import Folio, FolioLineItem, HousekeepingTask, LinkedRoomUnit
from .serializers import (
    FolioSerializer,
    FolioLineItemSerializer,
    HousekeepingTaskSerializer,
    LinkedRoomUnitSerializer,
)
from djmoney.money import Money


def _tenant_from_user(user):
    if user.is_superuser:
        return None
    return getattr(user, 'tenant', None)


def _property_qs(user):
    return filter_properties_for_user(Property.objects.filter(is_active=True), user)


def _recalculate_folio_totals(folio):
    currency = str(folio.total_charges.currency)
    charges = Money(0, currency)
    payments = Money(0, currency)
    for item in folio.line_items.all():
        line_total = float(item.amount.amount) * item.quantity
        if item.item_type == 'PAYMENT':
            payments += Money(line_total, currency)
        else:
            charges += Money(line_total, currency)
    folio.total_charges = charges
    folio.total_payments = payments
    folio.balance = charges - payments
    folio.save(update_fields=['total_charges', 'total_payments', 'balance', 'updated_at'])


class FolioViewSet(viewsets.ModelViewSet):
    """Folio list/detail with line-item and close actions."""
    serializer_class = FolioSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property', 'status', 'reservation']
    search_fields = ['guest_name', 'guest_email', 'room_number']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    capability_map = {
        'list': 'finance.view',
        'retrieve': 'finance.view',
        'create': 'pms.operate',
        'update': 'finance.manage',
        'partial_update': 'finance.manage',
        'add_line_item': 'finance.manage',
        'remove_line_item': 'finance.manage',
        'close': 'finance.manage',
    }

    def get_queryset(self):
        qs = Folio.objects.select_related('property', 'reservation').prefetch_related('line_items')
        return filter_by_property_fk(qs, self.request.user)

    def perform_create(self, serializer):
        prop = serializer.validated_data['property']
        user = self.request.user
        if not user.is_superuser:
            tenant = _tenant_from_user(user)
            if not tenant or prop.tenant_id != tenant.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Property does not belong to your tenant.')
        serializer.save()

    @action(detail=True, methods=['post'])
    def add_line_item(self, request, pk=None):
        folio = self.get_object()
        if folio.status == 'CLOSED':
            return Response(
                {'detail': 'Cannot add items to a closed folio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item_type = request.data.get('item_type')
        description = (request.data.get('description') or '').strip()
        quantity = int(request.data.get('quantity') or 1)
        try:
            amount_value = float(request.data.get('amount'))
        except (TypeError, ValueError):
            return Response({'detail': 'Valid amount is required.'}, status=status.HTTP_400_BAD_REQUEST)
        valid_types = [c[0] for c in FolioLineItem.TYPE]
        if item_type not in valid_types:
            return Response(
                {'detail': f'Invalid item_type. Choose from: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not description:
            return Response({'detail': 'Description is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity < 1:
            return Response({'detail': 'Quantity must be >= 1.'}, status=status.HTTP_400_BAD_REQUEST)

        currency = str(folio.total_charges.currency) if folio.total_charges else 'INR'
        FolioLineItem.objects.create(
            folio=folio,
            item_type=item_type,
            description=description,
            amount=Money(amount_value, currency),
            quantity=quantity,
            pos_order_id=(request.data.get('pos_order_id') or ''),
        )
        _recalculate_folio_totals(folio)
        folio.refresh_from_db()
        return Response(FolioSerializer(folio).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def remove_line_item(self, request, pk=None):
        folio = self.get_object()
        if folio.status == 'CLOSED':
            return Response(
                {'detail': 'Cannot remove items from a closed folio.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            line_item_id = int(request.data.get('line_item_id'))
        except (TypeError, ValueError):
            return Response(
                {'detail': 'line_item_id is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item = folio.line_items.filter(id=line_item_id).first()
        if item is None:
            return Response(
                {'detail': 'Line item not found on this folio.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.delete()
        _recalculate_folio_totals(folio)
        folio.refresh_from_db()
        return Response(FolioSerializer(folio).data)

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        folio = self.get_object()
        if folio.status == 'CLOSED':
            return Response({'detail': 'Folio is already closed.'}, status=status.HTTP_400_BAD_REQUEST)
        force = bool(request.data.get('force', False))
        balance = float(folio.balance.amount) if folio.balance else 0
        if balance > 0 and not force:
            return Response(
                {
                    'detail': 'Folio has an outstanding balance. Settle or pass force=true.',
                    'balance': str(folio.balance.amount),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        new_status = request.data.get('status', 'CLOSED')
        if new_status not in ('PAID', 'CLOSED'):
            new_status = 'CLOSED'
        folio.status = new_status
        if new_status == 'CLOSED':
            folio.closed_at = timezone.now()
            folio.save(update_fields=['status', 'closed_at', 'updated_at'])
        else:
            folio.save(update_fields=['status', 'updated_at'])
        return Response(FolioSerializer(folio).data)


class HousekeepingTaskViewSet(viewsets.ModelViewSet):
    """Housekeeping task CRUD + status updates."""
    serializer_class = HousekeepingTaskSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['property', 'status', 'priority', 'room_number']
    search_fields = ['room_number', 'task_type', 'assigned_to', 'description']
    ordering_fields = ['priority', 'due_date', 'created_at', 'status']
    ordering = ['-priority', 'due_date', 'created_at']
    capability_map = {
        'list': 'housekeeping.view',
        'retrieve': 'housekeeping.view',
        'create': 'housekeeping.manage',
        'update': 'housekeeping.update',
        'partial_update': 'housekeeping.update',
        'destroy': 'housekeeping.manage',
        'set_status': 'housekeeping.update',
    }

    def get_queryset(self):
        qs = HousekeepingTask.objects.select_related('property', 'room_type', 'reservation')
        return filter_by_property_fk(qs, self.request.user)

    def perform_create(self, serializer):
        prop = serializer.validated_data['property']
        user = self.request.user
        if not user.is_superuser:
            tenant = _tenant_from_user(user)
            if not tenant or prop.tenant_id != tenant.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Property does not belong to your tenant.')
        serializer.save()

    @action(detail=True, methods=['patch', 'post'])
    def set_status(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        valid = [c[0] for c in HousekeepingTask.STATUS]
        if new_status not in valid:
            return Response(
                {'detail': f'Invalid status. Choose from: {", ".join(valid)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        task.status = new_status
        update_fields = ['status', 'updated_at']
        if new_status == 'COMPLETED':
            task.completed_at = timezone.now()
            update_fields.append('completed_at')
        task.save(update_fields=update_fields)
        return Response(self.get_serializer(task).data)


class LinkedRoomUnitViewSet(viewsets.ModelViewSet):
    """Linked room units — list/create/update for mobile front desk."""
    serializer_class = LinkedRoomUnitSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    http_method_names = ['get', 'post', 'patch', 'put', 'head', 'options']
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['property', 'is_active']
    ordering = ['property', 'name']
    capability_map = {
        'list': 'pms.view',
        'retrieve': 'pms.view',
        'create': 'pms.operate',
        'update': 'pms.operate',
        'partial_update': 'pms.operate',
    }

    def get_queryset(self):
        qs = LinkedRoomUnit.objects.select_related('property').prefetch_related('room_types')
        return filter_by_property_fk(qs, self.request.user)

    def perform_create(self, serializer):
        prop = serializer.validated_data['property']
        user = self.request.user
        if not user.is_superuser:
            tenant = _tenant_from_user(user)
            if not tenant or prop.tenant_id != tenant.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Property does not belong to your tenant.')
        serializer.save()

    def perform_update(self, serializer):
        prop = serializer.validated_data.get('property', serializer.instance.property)
        user = self.request.user
        if not user.is_superuser:
            tenant = _tenant_from_user(user)
            if not tenant or prop.tenant_id != tenant.id:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Property does not belong to your tenant.')
        serializer.save()


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTenantMember])
def pms_dashboard_api(request):
    """
    Front-desk dashboard stats for the authenticated tenant.
    Optional query: ?property=<id>
    """
    user = request.user
    if not user.is_superuser and not user_has_capability(user, 'pms.view'):
        return Response({'detail': 'You do not have permission to perform this action.'}, status=status.HTTP_403_FORBIDDEN)

    property_id = request.query_params.get('property')
    today = timezone.now().date()

    props = _property_qs(user)
    if property_id:
        props = props.filter(id=property_id)

    prop_ids = list(props.values_list('id', flat=True))

    if user.is_superuser and not property_id:
        reservations = Reservation.objects.all()
        folios = Folio.objects.all()
        tasks = HousekeepingTask.objects.all()
    else:
        reservations = Reservation.objects.filter(property_id__in=prop_ids)
        folios = Folio.objects.filter(property_id__in=prop_ids)
        tasks = HousekeepingTask.objects.filter(property_id__in=prop_ids)

    data = {
        'date': today.isoformat(),
        'property_id': int(property_id) if property_id else None,
        'arrivals': reservations.filter(check_in=today, status='CONFIRMED').count(),
        'departures': reservations.filter(check_out=today, status='CHECKED_IN').count(),
        'in_house': reservations.filter(status='CHECKED_IN').count(),
        'pending_housekeeping': tasks.filter(status='PENDING').count(),
        'in_progress_housekeeping': tasks.filter(status='IN_PROGRESS').count(),
        'open_folios': folios.filter(status='OPEN').count(),
        'properties': [
            {'id': p.id, 'name': p.name}
            for p in props.order_by('name')
        ],
    }
    return Response(data)
