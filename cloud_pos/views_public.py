"""Public QR guest ordering (no login)."""
from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import MenuCategory, MenuItem, POSOrder, POSTable
from .services import add_item_to_order, consume_inventory_for_order


@require_http_methods(['GET', 'POST'])
def qr_order(request, token: str):
    table = get_object_or_404(POSTable, qr_token=token)
    prop = table.property
    categories = (
        MenuCategory.objects.filter(property=prop, is_active=True)
        .prefetch_related('items')
        .order_by('display_order', 'name')
    )

    order_id = request.session.get(f'qr_order_{table.id}')
    order = None
    if order_id:
        order = POSOrder.objects.filter(
            id=order_id, table=table, status__in=['OPEN', 'SENT']
        ).prefetch_related('items__menu_item').first()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            item = get_object_or_404(
                MenuItem, id=request.POST.get('menu_item_id'),
                category__property=prop, is_available=True,
            )
            if not order:
                order = POSOrder.objects.create(
                    property=prop,
                    table=table,
                    order_type='QR',
                    channel='QR',
                    guest_name=request.POST.get('guest_name') or '',
                    status='OPEN',
                )
                table.is_occupied = True
                table.save(update_fields=['is_occupied'])
                request.session[f'qr_order_{table.id}'] = order.id
            add_item_to_order(order, item, int(request.POST.get('quantity') or 1))
            messages.success(request, f'Added {item.name}')
            return redirect('cloud_pos:qr_order', token=token)

        if action == 'send' and order:
            order.status = 'SENT'
            order.save(update_fields=['status'])
            consume_inventory_for_order(order)
            messages.success(request, 'Order sent to the kitchen. Enjoy!')
            return redirect('cloud_pos:qr_order', token=token)

    return render(request, 'cloud_pos/qr_order.html', {
        'page_title': f'Order · Table {table.name}',
        'table': table,
        'property': prop,
        'categories': categories,
        'order': order,
    })
