from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from core.models import Property
from .models import GatewayConfig, TransactionLog
from .forms import GatewayConfigForm


@login_required
def gateways_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    configs = GatewayConfig.objects.filter(property__tenant=tenant) if tenant else []
    
    # Transaction list with filters
    txn_qs = TransactionLog.objects.filter(property__tenant=tenant).order_by('-created_at') if tenant else TransactionLog.objects.none()
    property_id = request.GET.get('property')
    status_filter = request.GET.get('status')
    gateway_filter = request.GET.get('gateway')
    if property_id:
        txn_qs = txn_qs.filter(property_id=property_id)
    if status_filter:
        txn_qs = txn_qs.filter(status=status_filter)
    if gateway_filter:
        txn_qs = txn_qs.filter(gateway=gateway_filter)
    recent_txns = txn_qs[:50]
    
    # Get distinct statuses and gateways for filter dropdowns
    statuses = TransactionLog.objects.filter(property__tenant=tenant).values_list('status', flat=True).distinct()[:10] if tenant else []
    gateways = TransactionLog.objects.filter(property__tenant=tenant).values_list('gateway', flat=True).distinct()[:10] if tenant else []
    
    context = {
        'page_title': 'Payment Gateways',
        'properties': properties,
        'configs': configs,
        'recent_txns': recent_txns,
        'statuses': statuses,
        'gateways': gateways,
    }
    return render(request, 'payment_gateways/dashboard.html', context)


@login_required
def test_transaction(request, config_id):
    """Test transaction flow (UI placeholder - creates a test log entry)"""
    tenant = getattr(request, 'tenant', None)
    config = get_object_or_404(GatewayConfig, id=config_id)
    if config.property_id and (not tenant or config.property.tenant_id != tenant.id):
        from django.http import Http404
        raise Http404()
    TransactionLog.objects.create(
        property=config.property,
        gateway=config.gateway_name,
        transaction_id=f'TEST-{config.id}-{__import__("time").time()}',
        amount=1.00,
        currency='INR',
        status='TEST',
        payment_method='test',
    )
    messages.success(request, 'Test transaction logged. Check transaction list.')
    return redirect('payment_gateways:dashboard')


@login_required
def config_create(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('payment_gateways:dashboard')
    if request.method == 'POST':
        form = GatewayConfigForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Gateway config created.')
            return redirect('payment_gateways:dashboard')
    else:
        form = GatewayConfigForm(tenant=tenant)
    return render(request, 'payment_gateways/config_form.html', {'form': form, 'page_title': 'New Gateway'})


@login_required
def config_edit(request, config_id):
    tenant = getattr(request, 'tenant', None)
    config = get_object_or_404(GatewayConfig, id=config_id)
    if config.property_id:
        if not tenant or config.property.tenant_id != tenant.id:
            from django.http import Http404
            raise Http404()
    if request.method == 'POST':
        form = GatewayConfigForm(request.POST, instance=config, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Config updated.')
            return redirect('payment_gateways:dashboard')
    else:
        form = GatewayConfigForm(instance=config, tenant=tenant)
    return render(request, 'payment_gateways/config_form.html', {'form': form, 'page_title': 'Edit Gateway', 'config': config})
