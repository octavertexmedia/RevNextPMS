from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from core.models import Property
from integrations.models import PropertyIntegration, IntegrationPlatform
from .models import ListingProject
from .forms import ListingProjectForm


@login_required
def ota_listing_dashboard(request):
    tenant = getattr(request, 'tenant', None)
    properties = Property.objects.filter(tenant=tenant, is_active=True) if tenant else []
    
    projects = ListingProject.objects.filter(property__tenant=tenant).select_related('property', 'platform') if tenant else []
    
    context = {
        'page_title': 'OTA Listing Service',
        'properties': properties,
        'projects': projects,
    }
    return render(request, 'ota_listing/dashboard.html', context)


@login_required
def project_create(request):
    tenant = getattr(request, 'tenant', None)
    if not tenant:
        messages.error(request, 'No tenant selected.')
        return redirect('ota_listing:dashboard')
    if request.method == 'POST':
        form = ListingProjectForm(request.POST, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Listing project created.')
            return redirect('ota_listing:dashboard')
    else:
        form = ListingProjectForm(tenant=tenant)
    return render(request, 'ota_listing/project_form.html', {'form': form, 'page_title': 'New Listing Project'})


@login_required
def project_detail(request, project_id):
    tenant = getattr(request, 'tenant', None)
    project = get_object_or_404(ListingProject, id=project_id, property__tenant=tenant)
    context = {'page_title': f'{project.property.name} - {project.platform.display_name}', 'project': project}
    return render(request, 'ota_listing/project_detail.html', context)


@login_required
def project_edit(request, project_id):
    tenant = getattr(request, 'tenant', None)
    project = get_object_or_404(ListingProject, id=project_id, property__tenant=tenant)
    if request.method == 'POST':
        form = ListingProjectForm(request.POST, instance=project, tenant=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated.')
            return redirect('ota_listing:project_detail', project_id=project.id)
    else:
        form = ListingProjectForm(instance=project, tenant=tenant)
    return render(request, 'ota_listing/project_form.html', {
        'form': form, 'page_title': 'Edit Project', 'project': project
    })


@login_required
def project_status_update(request, project_id):
    tenant = getattr(request, 'tenant', None)
    project = get_object_or_404(ListingProject, id=project_id, property__tenant=tenant)
    new_status = request.POST.get('status')
    valid = [c[0] for c in ListingProject.STATUS]
    if new_status in valid:
        project.status = new_status
        if new_status in ('LIVE', 'OPTIMIZED'):
            project.completed_at = timezone.now()
        project.save()
        messages.success(request, f'Status updated to {project.get_status_display()}.')
    return redirect('ota_listing:project_detail', project_id=project.id)


OPTIMIZATION_CHECKLIST = [
    {'id': 'photos', 'title': 'High-quality photos', 'desc': 'Minimum 20 photos, 1200x800px'},
    {'id': 'description', 'title': 'Property description', 'desc': 'Compelling copy, 200+ words'},
    {'id': 'amenities', 'title': 'Amenities listed', 'desc': 'All amenities with icons'},
    {'id': 'policies', 'title': 'Policies', 'desc': 'Cancellation, check-in/out, house rules'},
    {'id': 'rates', 'title': 'Competitive rates', 'desc': 'Rates synced and competitive'},
    {'id': 'availability', 'title': 'Availability', 'desc': 'Inventory updated daily'},
    {'id': 'reviews', 'title': 'Reviews', 'desc': 'Respond to all guest reviews'},
]


@login_required
def project_optimization_checklist(request, project_id):
    tenant = getattr(request, 'tenant', None)
    project = get_object_or_404(ListingProject, id=project_id, property__tenant=tenant)
    # In a full impl, we'd store checklist progress in DB. For now show static list.
    context = {
        'page_title': f'Optimization - {project.property.name}',
        'project': project,
        'checklist': OPTIMIZATION_CHECKLIST,
    }
    return render(request, 'ota_listing/optimization_checklist.html', context)
