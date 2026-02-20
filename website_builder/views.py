from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from core.models import Property
from .models import SiteTemplate, PropertyWebsite
from .forms import PropertyWebsiteForm


@login_required
def website_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    templates = SiteTemplate.objects.filter(is_active=True)[:12]
    
    websites = PropertyWebsite.objects.filter(property__tenant=tenant) if tenant else []
    
    context = {
        'page_title': 'Website Builder',
        'properties': properties,
        'templates': templates,
        'websites': websites,
    }
    return render(request, 'website_builder/dashboard.html', context)


@login_required
def website_editor(request, property_id):
    tenant = getattr(request, 'tenant', None)
    property_obj = get_object_or_404(Property, id=property_id, tenant=tenant)
    website, _ = PropertyWebsite.objects.get_or_create(property=property_obj, defaults={})
    
    if request.method == 'POST':
        form = PropertyWebsiteForm(request.POST, instance=website)
        if form.is_valid():
            inst = form.save(commit=False)
            if inst.is_published and not inst.published_at:
                inst.published_at = timezone.now()
            inst.save()
            messages.success(request, 'Website settings saved.')
            return redirect('website_builder:editor', property_id=property_obj.id)
    else:
        form = PropertyWebsiteForm(instance=website)
    
    context = {
        'page_title': f'Edit - {property_obj.name}',
        'property': property_obj,
        'website': website,
        'form': form,
    }
    return render(request, 'website_builder/editor.html', context)


@login_required
def website_preview(request, property_id):
    """Preview property website"""
    tenant = getattr(request, 'tenant', None)
    property_obj = get_object_or_404(Property, id=property_id, tenant=tenant)
    website = get_object_or_404(PropertyWebsite, property=property_obj)
    context = {'property': property_obj, 'website': website}
    return render(request, 'website_builder/preview.html', context)
