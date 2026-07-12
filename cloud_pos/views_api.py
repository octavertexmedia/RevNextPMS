"""
REST API for Cloud POS (mobile front-desk).
"""
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from djmoney.money import Money

from tenants.permissions import IsTenantMember
from rbac.permissions import HasCapability
from rbac.services import filter_by_property_fk
from core.models import Property

from .models import MenuCategory, MenuItem, POSOrder, POSOrderItem, POSTable
from .serializers import (
    MenuCategorySerializer,
    MenuItemSerializer,
    POSOrderSerializer,
    POSTableSerializer,
)


def _tenant_from_user(user):
    if user.is_superuser:
        return None
    return getattr(user, 'tenant', None)


def _recalculate_order_total(order):
    currency = str(order.total_amount.currency) if order.total_amount else 'INR'
    total = Money(0, currency)
    for item in order.items.all():
        total += item.line_total
    order.total_amount = total
    order.save(update_fields=['total_amount', 'updated_at'])


class MenuCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MenuCategorySerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['property', 'is_active']
    ordering = ['display_order', 'name']
    capability_map = {
        'list': 'pos.view',
        'retrieve': 'pos.view',
    }

    def get_queryset(self):
        qs = MenuCategory.objects.select_related('property').prefetch_related('items')
        return filter_by_property_fk(qs, self.request.user)


class MenuItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description']
    ordering = ['category', 'name']
    capability_map = {
        'list': 'pos.view',
        'retrieve': 'pos.view',
    }

    def get_queryset(self):
        qs = MenuItem.objects.select_related('category', 'category__property')
        property_id = self.request.query_params.get('property')
        if property_id:
            qs = qs.filter(category__property_id=property_id)
        return filter_by_property_fk(qs, self.request.user, property_field='category__property')


class POSTableViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = POSTableSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['property', 'is_occupied']
    capability_map = {
        'list': 'pos.view',
        'retrieve': 'pos.view',
    }

    def get_queryset(self):
        qs = POSTable.objects.select_related('property')
        return filter_by_property_fk(qs, self.request.user)


class POSOrderViewSet(viewsets.ModelViewSet):
    serializer_class = POSOrderSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['property', 'status', 'bill_to_room']
    ordering = ['-created_at']
    capability_map = {
        'list': 'pos.view',
        'retrieve': 'pos.view',
        'create': 'pos.operate',
        'update': 'pos.operate',
        'partial_update': 'pos.operate',
        'add_item': 'pos.operate',
        'set_status': 'pos.operate',
    }

    def get_queryset(self):
        qs = POSOrder.objects.select_related(
            'property', 'table', 'folio'
        ).prefetch_related('items__menu_item')
        return filter_by_property_fk(qs, self.request.user)

    def create(self, request, *args, **kwargs):
        prop_id = request.data.get('property')
        try:
            prop = Property.objects.get(id=prop_id)
        except (Property.DoesNotExist, TypeError, ValueError):
            return Response({'detail': 'Valid property is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.is_superuser:
            tenant = _tenant_from_user(user)
            if not tenant or prop.tenant_id != tenant.id:
                return Response({'detail': 'Property does not belong to your tenant.'}, status=status.HTTP_403_FORBIDDEN)

        table = None
        table_id = request.data.get('table')
        if table_id:
            table = POSTable.objects.filter(id=table_id, property=prop).first()

        order = POSOrder.objects.create(
            property=prop,
            table=table,
            bill_to_room=bool(request.data.get('bill_to_room', False)),
            folio_id=request.data.get('folio') or None,
            room_number=(request.data.get('room_number') or '').strip(),
            status='OPEN',
            total_amount=Money(0, 'INR'),
        )
        return Response(POSOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        order = self.get_object()
        if order.status not in ('OPEN', 'SENT', 'SERVED'):
            return Response(
                {'detail': 'Cannot add items to a billed/paid order.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            menu_item_id = int(request.data.get('menu_item'))
            quantity = int(request.data.get('quantity') or 1)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'menu_item and quantity are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if quantity < 1:
            return Response({'detail': 'Quantity must be >= 1.'}, status=status.HTTP_400_BAD_REQUEST)

        menu_item = MenuItem.objects.filter(
            id=menu_item_id,
            category__property=order.property,
            is_available=True,
        ).first()
        if menu_item is None:
            return Response({'detail': 'Menu item not found.'}, status=status.HTTP_404_NOT_FOUND)

        unit_price = menu_item.price
        POSOrderItem.objects.create(
            order=order,
            menu_item=menu_item,
            quantity=quantity,
            unit_price=unit_price,
            line_total=unit_price * quantity,
        )
        _recalculate_order_total(order)
        order.refresh_from_db()
        return Response(POSOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        valid_transitions = {
            'OPEN': ['SENT'],
            'SENT': ['SERVED'],
            'SERVED': ['BILLED'],
            'BILLED': ['PAID'],
        }
        if new_status not in valid_transitions.get(order.status, []):
            return Response(
                {
                    'detail': f'Invalid transition from {order.status} to {new_status}.',
                    'allowed': valid_transitions.get(order.status, []),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        order.status = new_status
        if new_status == 'BILLED' and order.bill_to_room and order.folio_id:
            from cloud_pms.models import FolioLineItem
            from cloud_pms.views_api import _recalculate_folio_totals
            FolioLineItem.objects.create(
                folio=order.folio,
                item_type='POS',
                description=f'POS Order #{order.id} - F&B',
                amount=order.total_amount,
                quantity=1,
                pos_order_id=str(order.id),
            )
            _recalculate_folio_totals(order.folio)
        order.save(update_fields=['status', 'updated_at'])
        return Response(POSOrderSerializer(order).data)
