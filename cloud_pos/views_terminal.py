"""Touch Billing POS terminal + waiter floor board."""
from __future__ import annotations

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from djmoney.money import Money

from core.models import Property

from .models import MenuCategory, MenuItem, POSOrder, POSOrderItem, POSTable
from .services import add_item_to_order, consume_inventory_for_order, recalculate_order_totals, sync_table_occupancy


def _tenant_properties(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return tenant, Property.objects.none()
    return tenant, Property.objects.filter(tenant=tenant, is_active=True)


@login_required
def billing_terminal(request):
    """Touch-style Billing POS — Dine In / Takeaway / Delivery."""
    tenant, properties = _tenant_properties(request)
    if not tenant:
        messages.error(request, 'No tenant on account.')
        return redirect('tenants:login')

    property_id = request.GET.get('property') or (str(properties.first().id) if properties.exists() else '')
    prop = None
    if property_id:
        prop = get_object_or_404(Property, id=property_id, tenant=tenant)

    categories = []
    tables = []
    open_folios = []
    if prop:
        categories = (
            MenuCategory.objects.filter(property=prop, is_active=True)
            .prefetch_related('items')
            .order_by('display_order', 'name')
        )
        tables = POSTable.objects.filter(property=prop).order_by('name')
        try:
            from cloud_pms.models import Folio
            open_folios = Folio.objects.filter(
                property=prop, status='OPEN'
            ).order_by('-created_at')[:50]
        except Exception:
            open_folios = []

    order_id = request.GET.get('order')
    active_order = None
    if order_id and prop:
        active_order = POSOrder.objects.filter(
            id=order_id, property=prop
        ).prefetch_related('items__menu_item').first()

    preselect_table = request.GET.get('table') or ''

    context = {
        'page_title': 'Billing POS',
        'properties': properties,
        'property': prop,
        'categories': categories,
        'tables': tables,
        'open_folios': open_folios,
        'active_order': active_order,
        'order_types': POSOrder.ORDER_TYPES,
        'preselect_table': preselect_table,
    }
    return render(request, 'cloud_pos/billing_terminal.html', context)


@login_required
@require_POST
def billing_api(request):
    """JSON API for the terminal (add item, pay, hold, new order)."""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        return JsonResponse({'error': 'no_tenant'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        payload = request.POST.dict()

    action = payload.get('action')
    property_id = payload.get('property_id')
    prop = get_object_or_404(Property, id=property_id, tenant=tenant)

    if action == 'create_order':
        order_type = payload.get('order_type') or 'DINE_IN'
        channel = payload.get('channel') or 'POS'
        table_id = payload.get('table_id') or None
        bill_to_room = bool(payload.get('bill_to_room'))
        folio_id = payload.get('folio_id') or None
        room_number = payload.get('room_number') or ''

        table = None
        if table_id:
            table = get_object_or_404(POSTable, id=table_id, property=prop)

        order = POSOrder.objects.create(
            property=prop,
            table=table,
            order_type=order_type,
            channel=channel,
            bill_to_room=bill_to_room,
            folio_id=folio_id if bill_to_room else None,
            room_number=room_number if bill_to_room else '',
            guest_name=payload.get('guest_name') or '',
            guest_phone=payload.get('guest_phone') or '',
            delivery_address=payload.get('delivery_address') or '',
            status='OPEN',
        )
        if table:
            sync_table_occupancy(table)
        return JsonResponse({'ok': True, 'order_id': order.id})

    order = get_object_or_404(POSOrder, id=payload.get('order_id'), property__tenant=tenant)

    if action == 'add_item':
        if order.status not in ('OPEN', 'SENT', 'SERVED', 'HELD'):
            return JsonResponse({'error': 'order_locked'}, status=400)
        menu_item = get_object_or_404(
            MenuItem, id=payload.get('menu_item_id'), category__property=prop, is_available=True
        )
        qty = int(payload.get('quantity') or 1)
        item = add_item_to_order(order, menu_item, qty, payload.get('notes') or '')
        order.refresh_from_db()
        return JsonResponse({
            'ok': True,
            'item_id': item.id,
            'subtotal': str(order.subtotal_amount.amount),
            'tax': str(order.tax_amount.amount),
            'total': str(order.total_amount.amount),
            'currency': str(order.total_amount.currency),
        })

    if action == 'remove_item':
        oi = get_object_or_404(POSOrderItem, id=payload.get('item_id'), order=order)
        oi.delete()
        recalculate_order_totals(order)
        order.refresh_from_db()
        return JsonResponse({
            'ok': True,
            'subtotal': str(order.subtotal_amount.amount),
            'tax': str(order.tax_amount.amount),
            'total': str(order.total_amount.amount),
        })

    if action == 'set_status':
        new_status = payload.get('status')
        # Allow Pay from OPEN in one hop (terminal Hold/Pay UX).
        allowed = {
            'OPEN': ['SENT', 'HELD', 'CANCELLED', 'PAID', 'BILLED'],
            'HELD': ['OPEN', 'CANCELLED', 'SENT', 'PAID'],
            'SENT': ['SERVED', 'BILLED', 'PAID'],
            'SERVED': ['BILLED', 'PAID'],
            'BILLED': ['PAID'],
        }
        if new_status not in allowed.get(order.status, []):
            return JsonResponse({'error': 'invalid_transition'}, status=400)
        order.status = new_status
        order.save(update_fields=['status'])
        if new_status in ('SENT', 'BILLED', 'PAID'):
            consume_inventory_for_order(order)
        if new_status in ('BILLED', 'PAID') and order.bill_to_room and order.folio_id:
            from cloud_pms.models import FolioLineItem
            from cloud_pms.views import _recalculate_folio_totals
            if not FolioLineItem.objects.filter(pos_order_id=str(order.id)).exists():
                FolioLineItem.objects.create(
                    folio=order.folio,
                    item_type='POS',
                    description=f'POS Order #{order.id} - F&B',
                    amount=order.total_amount,
                    quantity=1,
                    pos_order_id=str(order.id),
                )
                _recalculate_folio_totals(order.folio)
        if order.table_id:
            sync_table_occupancy(order.table)
        return JsonResponse({'ok': True, 'status': order.status})

    return JsonResponse({'error': 'unknown_action'}, status=400)


@login_required
def waiter_board(request):
    """Waiter app — table map + quick open order."""
    tenant, properties = _tenant_properties(request)
    property_id = request.GET.get('property') or (str(properties.first().id) if properties.exists() else '')
    prop = get_object_or_404(Property, id=property_id, tenant=tenant) if property_id else None
    tables = []
    if prop:
        tables = POSTable.objects.filter(property=prop).order_by('section', 'name')
    return render(request, 'cloud_pos/waiter_board.html', {
        'page_title': 'Waiter App',
        'properties': properties,
        'property': prop,
        'tables': tables,
    })
