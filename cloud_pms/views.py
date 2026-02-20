"""
Cloud PMS - Property Management System

Front desk, housekeeping, billing, Linked Room dashboards.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from core.models import Property
from .models import Folio, FolioLineItem, HousekeepingTask, LinkedRoomUnit
from .forms import FolioForm, FolioLineItemForm, HousekeepingTaskForm, LinkedRoomUnitForm
from djmoney.money import Money


def _recalculate_folio_totals(folio):
    """Recalculate folio total_charges and balance from line items"""
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
    folio.save(update_fields=['total_charges', 'total_payments', 'balance'])


@login_required
def pms_dashboard(request):
    """Main PMS dashboard - overview of all modules"""
    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    # Stats
    open_folios = Folio.objects.filter(property__tenant=tenant, status='OPEN').count() if tenant else 0
    pending_tasks = HousekeepingTask.objects.filter(property__tenant=tenant, status='PENDING').count() if tenant else 0
    linked_units = LinkedRoomUnit.objects.filter(property__tenant=tenant, is_active=True).count() if tenant else 0
    
    context = {
        'page_title': 'Cloud PMS Dashboard',
        'properties': properties,
        'open_folios': open_folios,
        'pending_tasks': pending_tasks,
        'linked_units': linked_units,
    }
    return render(request, 'cloud_pms/dashboard.html', context)


@login_required
def pms_dashboard_property(request, property_id):
    """PMS dashboard for a specific property"""
    tenant = getattr(request, 'tenant', None)
    property_obj = get_object_or_404(Property, id=property_id, tenant=tenant)
    
    folios = Folio.objects.filter(property=property_obj).order_by('-created_at')[:20]
    tasks = HousekeepingTask.objects.filter(property=property_obj).order_by('-created_at')[:20]
    linked_units = LinkedRoomUnit.objects.filter(property=property_obj, is_active=True)
    
    context = {
        'page_title': f'PMS - {property_obj.name}',
        'property': property_obj,
        'folios': folios,
        'tasks': tasks,
        'linked_units': linked_units,
    }
    return render(request, 'cloud_pms/dashboard_property.html', context)


@login_required
def housekeeping_list(request):
    """Housekeeping task list"""
    tenant = getattr(request, 'tenant', None)
    property_id = request.GET.get('property')
    
    tasks = HousekeepingTask.objects.filter(property__tenant=tenant, property__is_active=True)
    if property_id:
        tasks = tasks.filter(property_id=property_id)
    tasks = tasks.order_by('-priority', 'due_date', 'created_at')[:50]
    
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    context = {
        'page_title': 'Housekeeping',
        'tasks': tasks,
        'properties': properties,
        'task_status_choices': HousekeepingTask.STATUS,
    }
    return render(request, 'cloud_pms/housekeeping_list.html', context)


@login_required
def folios_list(request):
    """Guest folios list"""
    tenant = getattr(request, 'tenant', None)
    property_id = request.GET.get('property')
    
    folios = Folio.objects.filter(property__tenant=tenant, property__is_active=True)
    if property_id:
        folios = folios.filter(property_id=property_id)
    folios = folios.order_by('-created_at')[:50]
    
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    context = {
        'page_title': 'Folios & Billing',
        'folios': folios,
        'properties': properties,
    }
    return render(request, 'cloud_pms/folios_list.html', context)


@login_required
def linked_rooms_list(request):
    """Linked Room units (villas/apartments)"""
    tenant = getattr(request, 'tenant', None)
    
    units = LinkedRoomUnit.objects.filter(property__tenant=tenant, property__is_active=True, is_active=True)
    units = units.select_related('property').prefetch_related('room_types')
    
    context = {
        'page_title': 'Linked Room Units',
        'units': units,
    }
    return render(request, 'cloud_pms/linked_rooms_list.html', context)


# --- Task 1: Folio Create ---
@login_required
def folio_create(request):
    """Create new guest folio"""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('cloud_pms:folios')
    
    if request.method == 'POST':
        form = FolioForm(request.POST, tenant=tenant)
        if form.is_valid():
            folio = form.save(commit=False)
            folio.status = 'OPEN'
            folio.save()
            messages.success(request, f'Folio created for {folio.guest_name}.')
            return redirect('cloud_pms:folio_detail', folio_id=folio.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FolioForm(tenant=tenant)
    
    properties = Property.objects.filter(tenant=tenant, is_active=True)
    context = {'page_title': 'New Folio', 'form': form, 'properties': properties}
    return render(request, 'cloud_pms/folio_form.html', context)


# --- Task 2: Folio detail view ---
@login_required
def folio_detail(request, folio_id):
    """Folio detail with line items"""
    tenant = getattr(request, 'tenant', None)
    folio = get_object_or_404(Folio, id=folio_id, property__tenant=tenant)
    line_items = folio.line_items.all().order_by('created_at')
    
    context = {
        'page_title': f'Folio #{folio.id}',
        'folio': folio,
        'line_items': line_items,
    }
    return render(request, 'cloud_pms/folio_detail.html', context)


# --- Task 3: Folio line item add ---
@login_required
def folio_line_item_add(request, folio_id):
    """Add line item to folio"""
    tenant = getattr(request, 'tenant', None)
    folio = get_object_or_404(Folio, id=folio_id, property__tenant=tenant)
    
    if request.method == 'POST':
        form = FolioLineItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.folio = folio
            item.save()
            # Recalculate folio totals from line items
            _recalculate_folio_totals(folio)
            messages.success(request, 'Line item added.')
            return redirect('cloud_pms:folio_detail', folio_id=folio.id)
    else:
        from djmoney.money import Money
        form = FolioLineItemForm(initial={'amount': Money(0, folio.total_charges.currency)})
    
    context = {'form': form, 'folio': folio}
    return render(request, 'cloud_pms/folio_line_item_form.html', context)


@login_required
def folio_line_item_delete(request, folio_id, line_item_id):
    """Remove line item from folio"""
    tenant = getattr(request, 'tenant', None)
    folio = get_object_or_404(Folio, id=folio_id, property__tenant=tenant)
    item = get_object_or_404(FolioLineItem, id=line_item_id, folio=folio)
    item.delete()
    _recalculate_folio_totals(folio)
    messages.success(request, 'Line item removed.')
    return redirect('cloud_pms:folio_detail', folio_id=folio.id)


# --- Task 4: Housekeeping task create ---
@login_required
def housekeeping_task_create(request):
    """Create housekeeping task"""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('cloud_pms:housekeeping')
    
    if request.method == 'POST':
        form = HousekeepingTaskForm(request.POST, tenant=tenant)
        if form.is_valid():
            task = form.save()
            messages.success(request, f'Task created for room {task.room_number}.')
            return redirect('cloud_pms:housekeeping')
    else:
        form = HousekeepingTaskForm(tenant=tenant)
    
    context = {'page_title': 'New Housekeeping Task', 'form': form}
    return render(request, 'cloud_pms/housekeeping_task_form.html', context)


# --- Task 5: Linked Room Unit create ---
@login_required
def linked_room_create(request):
    """Create linked room unit"""
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('cloud_pms:linked_rooms')
    
    if request.method == 'POST':
        form = LinkedRoomUnitForm(request.POST, tenant=tenant)
        if form.is_valid():
            unit = form.save()
            messages.success(request, f'Linked unit "{unit.name}" created.')
            return redirect('cloud_pms:linked_rooms')
    else:
        form = LinkedRoomUnitForm(tenant=tenant)
    
    context = {'page_title': 'New Linked Room Unit', 'form': form}
    return render(request, 'cloud_pms/linked_room_form.html', context)


# --- Task 6: Housekeeping task Edit/status update ---
@login_required
def housekeeping_task_edit(request, task_id):
    tenant = getattr(request, 'tenant', None)
    task = get_object_or_404(HousekeepingTask, id=task_id, property__tenant=tenant)
    if request.method == 'POST':
        form = HousekeepingTaskForm(request.POST, instance=task, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated.')
            return redirect('cloud_pms:housekeeping')
    else:
        form = HousekeepingTaskForm(instance=task, tenant=tenant)
    return render(request, 'cloud_pms/housekeeping_task_form.html', {'form': form, 'page_title': 'Edit Task'})


@login_required
def housekeeping_task_status_update(request, task_id):
    tenant = getattr(request, 'tenant', None)
    task = get_object_or_404(HousekeepingTask, id=task_id, property__tenant=tenant)
    new_status = request.POST.get('status')
    valid = [c[0] for c in HousekeepingTask.STATUS]
    if new_status in valid:
        task.status = new_status
        task.save(update_fields=['status'])
        messages.success(request, f'Status updated to {task.get_status_display()}.')
    return redirect('cloud_pms:housekeeping')


# --- Task 7: Linked Room Unit Edit ---
@login_required
def linked_room_edit(request, unit_id):
    tenant = getattr(request, 'tenant', None)
    unit = get_object_or_404(LinkedRoomUnit, id=unit_id, property__tenant=tenant)
    if request.method == 'POST':
        form = LinkedRoomUnitForm(request.POST, instance=unit, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Linked unit updated.')
            return redirect('cloud_pms:linked_rooms')
    else:
        form = LinkedRoomUnitForm(instance=unit, tenant=tenant)
    return render(request, 'cloud_pms/linked_room_form.html', {'form': form, 'page_title': 'Edit Linked Unit'})


# --- Task 8: Folio close/settle ---
@login_required
def folio_close(request, folio_id):
    tenant = getattr(request, 'tenant', None)
    folio = get_object_or_404(Folio, id=folio_id, property__tenant=tenant)
    if folio.status == 'CLOSED':
        messages.warning(request, 'Folio is already closed.')
        return redirect('cloud_pms:folio_detail', folio_id=folio.id)
    new_status = request.POST.get('status', 'CLOSED')
    if new_status in ('PAID', 'CLOSED'):
        folio.status = new_status
        if new_status == 'CLOSED':
            folio.closed_at = timezone.now()
            folio.save(update_fields=['status', 'closed_at'])
        else:
            folio.save(update_fields=['status'])
        messages.success(request, f'Folio marked as {folio.get_status_display()}.')
    return redirect('cloud_pms:folio_detail', folio_id=folio.id)
