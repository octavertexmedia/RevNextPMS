"""Inventory + Swiggy/Zomato online order inbox."""
from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from djmoney.money import Money

from core.models import Property

from .models import DeliveryPartnerOrder, MenuItem, POSOrder
from .services import adjust_stock, add_item_to_order


@login_required
def inventory_list(request):
    tenant = getattr(request, 'tenant', None)
    property_id = request.GET.get('property')
    items = MenuItem.objects.filter(category__property__tenant=tenant).select_related('category', 'category__property')
    if property_id:
        items = items.filter(category__property_id=property_id)
    items = items.order_by('category__property__name', 'category__name', 'name')
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    return render(request, 'cloud_pos/inventory_list.html', {
        'page_title': 'Inventory',
        'items': items,
        'properties': properties,
    })


@login_required
def inventory_adjust(request, item_id):
    tenant = getattr(request, 'tenant', None)
    item = get_object_or_404(MenuItem, id=item_id, category__property__tenant=tenant)
    if request.method == 'POST':
        try:
            delta = Decimal(request.POST.get('delta') or '0')
        except Exception:
            messages.error(request, 'Invalid quantity.')
            return redirect('cloud_pos:inventory')
        reason = request.POST.get('reason') or 'ADJUST'
        note = request.POST.get('note') or ''
        adjust_stock(item, delta, reason=reason, note=note)
        messages.success(request, f'Stock updated for {item.name}.')
        return redirect('cloud_pos:inventory')
    return render(request, 'cloud_pos/inventory_adjust.html', {
        'page_title': f'Adjust · {item.name}',
        'item': item,
    })


@login_required
def delivery_inbox(request):
    tenant = getattr(request, 'tenant', None)
    property_id = request.GET.get('property')
    orders = DeliveryPartnerOrder.objects.filter(property__tenant=tenant)
    if property_id:
        orders = orders.filter(property_id=property_id)
    orders = orders.order_by('-created_at')[:100]
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    return render(request, 'cloud_pos/delivery_inbox.html', {
        'page_title': 'Swiggy & Zomato',
        'orders': orders,
        'properties': properties,
    })


@login_required
def delivery_create(request):
    """Manual capture of an aggregator order (API webhook can reuse this logic later)."""
    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    if request.method == 'POST':
        prop = get_object_or_404(Property, id=request.POST.get('property_id'), tenant=tenant)
        partner = request.POST.get('partner') or 'SWIGGY'
        partner_order_id = (request.POST.get('partner_order_id') or '').strip()
        if not partner_order_id:
            messages.error(request, 'Partner order id is required.')
            return redirect('cloud_pos:delivery_create')
        total = Money(request.POST.get('total') or '0', 'INR')
        dpo = DeliveryPartnerOrder.objects.create(
            property=prop,
            partner=partner,
            partner_order_id=partner_order_id,
            customer_name=request.POST.get('customer_name') or '',
            customer_phone=request.POST.get('customer_phone') or '',
            items_json=[{'name': line.strip()} for line in (request.POST.get('items') or '').splitlines() if line.strip()],
            total_amount=total,
            status='NEW',
        )
        messages.success(request, f'{dpo.get_partner_display()} order captured.')
        return redirect('cloud_pos:delivery_inbox')
    return render(request, 'cloud_pos/delivery_form.html', {
        'page_title': 'Capture online order',
        'properties': properties,
    })


@login_required
def delivery_accept(request, order_id):
    tenant = getattr(request, 'tenant', None)
    dpo = get_object_or_404(DeliveryPartnerOrder, id=order_id, property__tenant=tenant)
    if dpo.pos_order_id:
        messages.info(request, 'Already linked to a POS order.')
        return redirect('cloud_pos:delivery_inbox')
    pos = POSOrder.objects.create(
        property=dpo.property,
        order_type='AGGREGATOR',
        channel=dpo.partner,
        guest_name=dpo.customer_name,
        guest_phone=dpo.customer_phone,
        external_order_id=dpo.partner_order_id,
        status='OPEN',
        total_amount=dpo.total_amount,
        subtotal_amount=dpo.total_amount,
    )
    # Best-effort: match menu items by name from items_json
    for row in dpo.items_json or []:
        name = (row.get('name') if isinstance(row, dict) else str(row)) or ''
        mi = MenuItem.objects.filter(
            category__property=dpo.property, name__iexact=name.strip(), is_available=True
        ).first()
        if mi:
            add_item_to_order(pos, mi, int(row.get('qty', 1)) if isinstance(row, dict) else 1)
    dpo.pos_order = pos
    dpo.status = 'ACCEPTED'
    dpo.save(update_fields=['pos_order', 'status'])
    messages.success(request, f'Accepted — POS order #{pos.id} created.')
    return redirect('cloud_pos:order_detail', order_id=pos.id)
