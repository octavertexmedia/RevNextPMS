from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Property
from .models import POSOrder, POSOrderItem, MenuCategory, MenuItem, POSTable
from .forms import MenuCategoryForm, MenuItemForm, POSTableForm, POSOrderForm, POSOrderItemForm
from .services import recalculate_order_totals, consume_inventory_for_order, sync_table_occupancy


def _recalculate_order_total(order):
    return recalculate_order_totals(order)

@login_required
def pos_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    orders = POSOrder.objects.filter(property__tenant=tenant).order_by('-created_at')[:20] if tenant else []
    open_orders = POSOrder.objects.filter(property__tenant=tenant, status__in=['OPEN', 'SENT', 'SERVED']).count() if tenant else 0
    
    context = {
        'page_title': 'Cloud POS Dashboard',
        'properties': properties,
        'orders': orders,
        'open_orders': open_orders,
    }
    return render(request, 'cloud_pos/dashboard.html', context)


@login_required
def pos_orders(request):
    tenant = getattr(request, 'tenant', None)
    property_id = request.GET.get('property')
    
    orders = POSOrder.objects.filter(property__tenant=tenant, property__is_active=True)
    if property_id:
        orders = orders.filter(property_id=property_id)
    orders = orders.order_by('-created_at')[:50]
    
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    context = {'page_title': 'POS Orders', 'orders': orders, 'properties': properties}
    return render(request, 'cloud_pos/orders_list.html', context)


@login_required
def pos_menu(request):
    tenant = getattr(request, 'tenant', None)
    property_id = request.GET.get('property')
    
    categories = MenuCategory.objects.filter(property__tenant=tenant, property__is_active=True, is_active=True)
    if property_id:
        categories = categories.filter(property_id=property_id)
    categories = categories.prefetch_related('items').order_by('display_order', 'name')
    
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    context = {'page_title': 'Menu', 'categories': categories, 'properties': properties}
    return render(request, 'cloud_pos/menu_list.html', context)


# --- Task 6: Menu Category CRUD ---
@login_required
def menu_category_create(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('cloud_pos:menu')
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu category created.')
            return redirect('cloud_pos:menu')
    else:
        form = MenuCategoryForm(tenant=tenant)
    return render(request, 'cloud_pos/menu_category_form.html', {'form': form, 'page_title': 'New Category'})


@login_required
def menu_category_edit(request, category_id):
    tenant = getattr(request, 'tenant', None)
    cat = get_object_or_404(MenuCategory, id=category_id, property__tenant=tenant)
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST, instance=cat, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated.')
            return redirect('cloud_pos:menu')
    else:
        form = MenuCategoryForm(instance=cat, tenant=tenant)
    return render(request, 'cloud_pos/menu_category_form.html', {'form': form, 'page_title': 'Edit Category'})


# --- Task 7: Menu Item CRUD ---
@login_required
def menu_item_create(request):
    tenant = getattr(request, 'tenant', None)
    category_id = request.GET.get('category')
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('cloud_pos:menu')
    if request.method == 'POST':
        form = MenuItemForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item created.')
            return redirect('cloud_pos:menu')
    else:
        form = MenuItemForm(tenant=tenant)
        if category_id:
            form.fields['category'].initial = category_id
    return render(request, 'cloud_pos/menu_item_form.html', {'form': form, 'page_title': 'New Menu Item'})


@login_required
def menu_item_edit(request, item_id):
    tenant = getattr(request, 'tenant', None)
    item = get_object_or_404(MenuItem, id=item_id, category__property__tenant=tenant)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, instance=item, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated.')
            return redirect('cloud_pos:menu')
    else:
        form = MenuItemForm(instance=item, tenant=tenant)
    return render(request, 'cloud_pos/menu_item_form.html', {'form': form, 'page_title': 'Edit Menu Item'})


# --- Task 8: Order create ---
@login_required
def order_create(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('cloud_pos:orders')
    if request.method == 'POST':
        form = POSOrderForm(request.POST, tenant=tenant)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = 'OPEN'
            order.save()
            messages.success(request, f'Order #{order.id} created.')
            return redirect('cloud_pos:orders')
    else:
        form = POSOrderForm(tenant=tenant)
    return render(request, 'cloud_pos/order_form.html', {'form': form, 'page_title': 'New Order'})


# --- Task 10: Table management CRUD ---
@login_required
def pos_tables(request):
    tenant = getattr(request, 'tenant', None)
    property_id = request.GET.get('property')
    
    tables = POSTable.objects.filter(property__tenant=tenant, property__is_active=True)
    if property_id:
        tables = tables.filter(property_id=property_id)
    tables = tables.order_by('name')
    
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    context = {'page_title': 'Tables', 'tables': tables, 'properties': properties}
    return render(request, 'cloud_pos/tables_list.html', context)


@login_required
def table_create(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('cloud_pos:tables')
    if request.method == 'POST':
        form = POSTableForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Table created.')
            return redirect('cloud_pos:tables')
    else:
        form = POSTableForm(tenant=tenant)
    return render(request, 'cloud_pos/table_form.html', {'form': form, 'page_title': 'New Table'})


@login_required
def table_edit(request, table_id):
    tenant = getattr(request, 'tenant', None)
    table = get_object_or_404(POSTable, id=table_id, property__tenant=tenant)
    if request.method == 'POST':
        form = POSTableForm(request.POST, instance=table, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Table updated.')
            return redirect('cloud_pos:tables')
    else:
        form = POSTableForm(instance=table, tenant=tenant)
    return render(request, 'cloud_pos/table_form.html', {'form': form, 'page_title': 'Edit Table'})


# --- Task 11: Order add items ---
@login_required
def order_detail(request, order_id):
    tenant = getattr(request, 'tenant', None)
    order = get_object_or_404(POSOrder, id=order_id, property__tenant=tenant)
    order.items.all()  # prefetch
    context = {'page_title': f'Order #{order.id}', 'order': order}
    return render(request, 'cloud_pos/order_detail.html', context)


@login_required
def order_add_item(request, order_id):
    tenant = getattr(request, 'tenant', None)
    order = get_object_or_404(POSOrder, id=order_id, property__tenant=tenant)
    if order.status not in ('OPEN', 'SENT', 'SERVED'):
        messages.error(request, 'Cannot add items to a billed/paid order.')
        return redirect('cloud_pos:order_detail', order_id=order.id)
    if request.method == 'POST':
        form = POSOrderItemForm(request.POST, order=order)
        if form.is_valid():
            item = form.save(commit=False)
            item.order = order
            item.unit_price = item.menu_item.price
            item.line_total = item.unit_price * item.quantity
            item.save()
            _recalculate_order_total(order)
            messages.success(request, f'Added {item.menu_item.name} x{item.quantity}.')
            return redirect('cloud_pos:order_detail', order_id=order.id)
    else:
        form = POSOrderItemForm(order=order)
    return render(request, 'cloud_pos/order_item_form.html', {
        'form': form, 'order': order, 'page_title': f'Add Item to Order #{order.id}'
    })


@login_required
def order_item_delete(request, order_id, item_id):
    tenant = getattr(request, 'tenant', None)
    order = get_object_or_404(POSOrder, id=order_id, property__tenant=tenant)
    oi = get_object_or_404(POSOrderItem, id=item_id, order=order)
    if order.status not in ('OPEN', 'SENT', 'SERVED'):
        messages.error(request, 'Cannot remove items from a billed/paid order.')
        return redirect('cloud_pos:order_detail', order_id=order.id)
    oi.delete()
    _recalculate_order_total(order)
    messages.success(request, 'Item removed.')
    return redirect('cloud_pos:order_detail', order_id=order.id)


# --- Task 12: Order checkout/complete ---
@login_required
def order_status_update(request, order_id):
    tenant = getattr(request, 'tenant', None)
    order = get_object_or_404(POSOrder, id=order_id, property__tenant=tenant)
    new_status = request.POST.get('status')
    valid_transitions = {
        'OPEN': ['SENT'],
        'SENT': ['SERVED'],
        'SERVED': ['BILLED'],
        'BILLED': ['PAID'],
    }
    if not new_status or new_status not in valid_transitions.get(order.status, []):
        messages.error(request, 'Invalid status transition.')
        return redirect('cloud_pos:order_detail', order_id=order.id)
    order.status = new_status
    if new_status == 'SENT':
        consume_inventory_for_order(order)
    if new_status == 'BILLED' and order.bill_to_room and order.folio_id:
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
        messages.success(request, f'Order billed. Charges added to Folio #{order.folio.id}.')
    elif new_status == 'PAID':
        messages.success(request, 'Order marked as paid.')
    else:
        messages.success(request, f'Order status updated to {order.get_status_display()}.')
    order.save(update_fields=['status'])
    if order.table_id:
        sync_table_occupancy(order.table)
    return redirect('cloud_pos:order_detail', order_id=order.id)
