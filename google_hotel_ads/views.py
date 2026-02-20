from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from core.models import Property
from .models import HotelAdsConfig, FeedSubmission
from .forms import HotelAdsConfigForm


@login_required
def hotel_ads_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    configs = HotelAdsConfig.objects.filter(property__tenant=tenant) if tenant else []
    recent_feeds = FeedSubmission.objects.filter(property__tenant=tenant).order_by('-submitted_at')[:10] if tenant else []
    
    context = {
        'page_title': 'Google Hotel Ads',
        'properties': properties,
        'configs': configs,
        'recent_feeds': recent_feeds,
    }
    return render(request, 'google_hotel_ads/dashboard.html', context)


@login_required
def config_create(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('google_hotel_ads:dashboard')
    if request.method == 'POST':
        form = HotelAdsConfigForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Google Hotel Ads config created.')
            return redirect('google_hotel_ads:dashboard')
    else:
        form = HotelAdsConfigForm(tenant=tenant)
    return render(request, 'google_hotel_ads/config_form.html', {'form': form, 'page_title': 'New Config'})


@login_required
def config_edit(request, config_id):
    tenant = getattr(request, 'tenant', None)
    config = get_object_or_404(HotelAdsConfig, id=config_id, property__tenant=tenant)
    if request.method == 'POST':
        form = HotelAdsConfigForm(request.POST, instance=config, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Config updated.')
            return redirect('google_hotel_ads:dashboard')
    else:
        form = HotelAdsConfigForm(instance=config, tenant=tenant)
    return render(request, 'google_hotel_ads/config_form.html', {'form': form, 'page_title': 'Edit Config', 'config': config})


@login_required
def feed_submit(request, config_id):
    """Trigger feed submission (UI placeholder - actual submission would be async)"""
    tenant = getattr(request, 'tenant', None)
    config = get_object_or_404(HotelAdsConfig, id=config_id, property__tenant=tenant)
    FeedSubmission.objects.create(
        property=config.property,
        status='SUBMITTED',
        rooms_count=0,
        rates_count=0,
    )
    config.last_feed_submitted = timezone.now()
    config.feed_status = 'SUBMITTED'
    config.save(update_fields=['last_feed_submitted', 'feed_status'])
    messages.success(request, 'Feed submission triggered.')
    return redirect('google_hotel_ads:dashboard')
