"""
Views for tenant registration and authentication
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, FormView, View
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

from .models import Tenant, TenantUser
from .forms import (
    TenantRegistrationForm, TenantLoginForm, PropertyForm,
    PropertyIntegrationForm, ReservationForm, RoomTypeForm
)
from core.models import Property, Inventory, RoomType, RatePlan, PricingRule
from integrations.models import PropertyIntegration, IntegrationPlatform, SyncLog
from bookings.models import Reservation, Payment
from reports.models import ReportTemplate, GeneratedReport, ScheduledReport
from core.pricing_engine import PricingEngine
from django.db import transaction


class TenantRegistrationView(CreateView):
    """View for hotel owners to register as tenants"""
    model = Tenant
    form_class = TenantRegistrationForm
    template_name = 'tenants/register.html'
    success_url = reverse_lazy('tenants:dashboard')
    
    @transaction.atomic
    def form_valid(self, form):
        """Create tenant and initial user account"""
        # Create tenant
        tenant = form.save(commit=False)
        if not tenant.slug:
            tenant.slug = slugify(tenant.name)
        
        # Start 14-day trial
        tenant.subscription_status = 'trial'
        tenant.trial_end_date = timezone.now().date() + timedelta(days=14)
        
        tenant.save()
        
        # Create owner user account
        user = TenantUser.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
            tenant=tenant,
            role='owner',
            first_name=form.cleaned_data.get('first_name', ''),
            last_name=form.cleaned_data.get('last_name', ''),
            is_staff=True,  # Allow access to admin
        )
        
        # Log in the user
        login(self.request, user)
        
        messages.success(
            self.request,
            f'Welcome! Your account for {tenant.name} has been created successfully.'
        )
        
        return redirect(self.success_url)


class TenantLoginView(FormView):
    """Custom login view for tenants"""
    form_class = TenantLoginForm
    template_name = 'tenants/login.html'
    success_url = reverse_lazy('tenants:dashboard')
    
    def form_valid(self, form):
        """Authenticate and log in user"""
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(self.request, user)
                messages.success(self.request, f'Welcome back, {user.get_full_name() or user.username}!')
                return redirect(self.success_url)
            else:
                messages.error(self.request, 'Your account is inactive.')
        else:
            messages.error(self.request, 'Invalid username or password.')
        
        return self.form_invalid(form)


class TenantLogoutView(View):
    """Custom logout view that accepts GET requests and redirects to landing page"""
    
    def get(self, request):
        """Handle GET request for logout"""
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'You have been successfully logged out.')
        return redirect('core:landing_page')
    
    def post(self, request):
        """Handle POST request for logout (for form submissions)"""
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, 'You have been successfully logged out.')
        return redirect('core:landing_page')


@login_required
def tenant_dashboard(request):
    """Tenant-specific dashboard showing their properties, integrations, and stats
    
    Access restricted to tenant users only (hoteliers, property owners, property managers)
    """
    user = request.user
    
    # Ensure user is a tenant user (not superuser)
    if user.is_superuser:
        messages.error(request, 'This dashboard is for hotel owners only. Superusers should use the admin panel.')
        return redirect('tenants:login')
    
    if not hasattr(user, 'tenant') or not user.tenant:
        messages.error(request, 'Access denied. You must be associated with a tenant (hotel/property) to access this dashboard.')
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # All data is tenant-specific only
    
    # Get tenant's properties (tenant-specific only)
    properties = Property.objects.filter(tenant=tenant, is_active=True)
    
    # Get property integrations (tenant-specific only)
    integrations = PropertyIntegration.objects.filter(property__tenant=tenant, is_active=True)
    
    # Get OTA platforms
    platforms = IntegrationPlatform.objects.filter(
        id__in=integrations.values_list('platform_id', flat=True).distinct()
    )
    
    # Get reservations (tenant-specific only)
    reservations = Reservation.objects.filter(property__tenant=tenant)
    
    # Calculate statistics
    today = timezone.now().date()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)
    
    # Property stats
    total_properties = properties.count()
    
    # Reservation stats
    total_reservations = reservations.count()
    confirmed_reservations = reservations.filter(status='CONFIRMED').count()
    today_reservations = reservations.filter(check_in=today).count()
    upcoming_reservations = reservations.filter(
        check_in__gte=today,
        status='CONFIRMED'
    ).count()
    
    # Revenue stats (tenant-specific only)
    payments = Payment.objects.filter(reservation__property__tenant=tenant, payment_status='COMPLETED')
    
    # Revenue stats - Sum returns Decimal for MoneyField
    total_revenue_result = payments.aggregate(total=Sum('amount'))['total']
    total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
    
    today_revenue_result = payments.filter(
        created_at__date=today
    ).aggregate(total=Sum('amount'))['total']
    today_revenue = float(today_revenue_result) if today_revenue_result else 0.0
    
    monthly_revenue_result = payments.filter(
        created_at__date__gte=last_30_days
    ).aggregate(total=Sum('amount'))['total']
    monthly_revenue = float(monthly_revenue_result) if monthly_revenue_result else 0.0
    
    # Integration stats
    total_integrations = integrations.count()
    active_syncs = SyncLog.objects.filter(
        property_integration__in=integrations,
        created_at__gte=last_7_days,
        status='SUCCESS'
    ).count()
    failed_syncs = SyncLog.objects.filter(
        property_integration__in=integrations,
        created_at__gte=last_7_days,
        status='FAILED'
    ).count()
    
    # Inventory stats (tenant-specific only)
    low_inventory = Inventory.objects.filter(
        room_type__property__tenant=tenant,
        date__gte=today,
        available_rooms__lt=5
    ).count()
    
    # Recent reservations
    recent_reservations = reservations.order_by('-created_at')[:5]
    
    # Recent sync logs
    recent_syncs = SyncLog.objects.filter(
        property_integration__in=integrations
    ).order_by('-created_at')[:5]
    
    context = {
        'tenant': tenant,
        'user': user,
        'properties': properties,
        'integrations': integrations,
        'platforms': platforms,
        'reservations': reservations,
        'total_properties': total_properties,
        'total_reservations': total_reservations,
        'confirmed_reservations': confirmed_reservations,
        'today_reservations': today_reservations,
        'upcoming_reservations': upcoming_reservations,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'total_integrations': total_integrations,
        'active_syncs': active_syncs,
        'failed_syncs': failed_syncs,
        'low_inventory': low_inventory,
        'recent_reservations': recent_reservations,
        'recent_syncs': recent_syncs,
    }
    
    return render(request, 'tenants/dashboard.html', context)


# Additional tenant views for sidebar navigation
@login_required
def tenant_properties(request):
    """List all properties for the tenant"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    properties = Property.objects.filter(tenant=tenant, is_active=True)
    
    context = {
        'tenant': tenant,
        'user': user,
        'properties': properties,
    }
    return render(request, 'tenants/properties.html', context)


@login_required
def tenant_property_add(request):
    """Add a new property"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # Check subscription limits
    if not tenant.can_add_property():
        messages.error(request, f'You have reached your property limit ({tenant.subscription_plan.max_properties if tenant.subscription_plan else 0}). Please upgrade your plan.')
        return redirect('tenants:properties')
    
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.tenant = tenant
            property_obj.save()
            messages.success(request, f'Property "{property_obj.name}" has been added successfully!')
            return redirect('tenants:properties')
    else:
        form = PropertyForm()
    
    context = {
        'tenant': tenant,
        'user': user,
        'form': form,
    }
    return render(request, 'tenants/property_add.html', context)


@login_required
def tenant_reservations(request):
    """List all reservations for the tenant"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    reservations = Reservation.objects.filter(property__tenant=tenant).order_by('-created_at')
    
    context = {
        'tenant': tenant,
        'user': user,
        'reservations': reservations,
    }
    return render(request, 'tenants/reservations.html', context)


@login_required
def tenant_reservation_add(request):
    """Create a new reservation"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    if request.method == 'POST':
        form = ReservationForm(request.POST, tenant=tenant)
        if form.is_valid():
            reservation = form.save(commit=False)
            # Ensure the property belongs to the tenant
            if reservation.property.tenant != tenant:
                messages.error(request, 'Invalid property selected.')
                return redirect('tenants:reservation_add')
            
            # Set currency and provider info for manual reservations
            reservation.currency = 'INR'
            reservation.provider_name = 'manual'
            reservation.provider_reservation_id = f"MANUAL-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Calculate nights
            if reservation.check_in and reservation.check_out:
                reservation.nights = (reservation.check_out - reservation.check_in).days
            
            reservation.save()
            messages.success(request, f'Reservation for {reservation.guest_name} has been created successfully!')
            return redirect('tenants:reservations')
    else:
        form = ReservationForm(tenant=tenant)
    
    properties = Property.objects.filter(tenant=tenant, is_active=True)
    
    context = {
        'tenant': tenant,
        'user': user,
        'form': form,
        'properties': properties,
    }
    return render(request, 'tenants/reservation_add.html', context)


@login_required
def tenant_integrations(request):
    """List all OTA integrations for the tenant"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    integrations = PropertyIntegration.objects.filter(property__tenant=tenant, is_active=True)
    
    context = {
        'tenant': tenant,
        'user': user,
        'integrations': integrations,
    }
    return render(request, 'tenants/integrations.html', context)


@login_required
def tenant_integration_add(request):
    """Add a new OTA integration"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    if request.method == 'POST':
        form = PropertyIntegrationForm(request.POST, tenant=tenant)
        if form.is_valid():
            integration = form.save(commit=False)
            # Ensure the property belongs to the tenant
            if integration.property.tenant != tenant:
                messages.error(request, 'Invalid property selected.')
                return redirect('tenants:integration_add')
            
            # Check subscription limits
            if not tenant.can_add_integration(integration.property):
                messages.error(request, f'You have reached your integration limit for this property. Please upgrade your plan.')
                return redirect('tenants:integrations')
            
            integration.save()
            messages.success(request, f'Successfully connected {integration.platform.name} for {integration.property.name}')
            return redirect('tenants:integrations')
    else:
        form = PropertyIntegrationForm(tenant=tenant)
    
    # Get available platforms
    platforms = IntegrationPlatform.objects.filter(is_active=True).order_by('display_name')
    properties = Property.objects.filter(tenant=tenant, is_active=True)
    
    context = {
        'tenant': tenant,
        'user': user,
        'form': form,
        'platforms': platforms,
        'properties': properties,
    }
    return render(request, 'tenants/integration_add.html', context)


@login_required
def tenant_inventory(request):
    """Manage inventory for the tenant with filters and date range"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    from core.models import Property, RoomType
    from datetime import datetime
    
    today = timezone.now().date()
    
    # Get filter parameters
    property_id = request.GET.get('property')
    room_type_id = request.GET.get('room_type')
    start_date = request.GET.get('start_date', today.strftime('%Y-%m-%d'))
    end_date = request.GET.get('end_date', (today + timedelta(days=30)).strftime('%Y-%m-%d'))
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        start_date_obj = today
        end_date_obj = today + timedelta(days=30)
    
    # Build query
    inventory = Inventory.objects.filter(
        property__tenant=tenant,
        date__gte=start_date_obj,
        date__lte=end_date_obj
    )
    
    if property_id:
        inventory = inventory.filter(property_id=property_id)
    
    if room_type_id:
        inventory = inventory.filter(room_type_id=room_type_id)
    
    inventory = inventory.order_by('date', 'property__name', 'room_type__name')
    
    # Add occupied_rooms property to each inventory item
    for item in inventory:
        item.occupied_rooms = item.total_rooms - item.available_rooms - item.blocked_rooms
    
    # Get filter options
    properties = Property.objects.filter(tenant=tenant, is_active=True).order_by('name')
    room_types = RoomType.objects.filter(property__tenant=tenant, is_active=True).order_by('property__name', 'name')
    
    # Calculate summary statistics
    total_rooms = inventory.aggregate(
        total=Sum('total_rooms'),
        available=Sum('available_rooms'),
        blocked=Sum('blocked_rooms')
    )
    
    context = {
        'tenant': tenant,
        'user': user,
        'inventory': inventory,
        'properties': properties,
        'room_types': room_types,
        'selected_property': property_id,
        'selected_room_type': room_type_id,
        'start_date': start_date_obj.strftime('%Y-%m-%d'),
        'end_date': end_date_obj.strftime('%Y-%m-%d'),
        'summary': total_rooms,
    }
    return render(request, 'tenants/inventory.html', context)


@login_required
def tenant_rate_plans(request):
    """List all rate plans for the tenant with filters and search"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    from core.models import RatePlan, Property, RoomType
    
    # Get filter parameters
    property_id = request.GET.get('property')
    room_type_id = request.GET.get('room_type')
    search_query = request.GET.get('search', '')
    
    # Build query
    rate_plans = RatePlan.objects.filter(property__tenant=tenant, is_active=True)
    
    if property_id:
        rate_plans = rate_plans.filter(property_id=property_id)
    
    if room_type_id:
        rate_plans = rate_plans.filter(room_type_id=room_type_id)
    
    if search_query:
        rate_plans = rate_plans.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(property__name__icontains=search_query) |
            Q(room_type__name__icontains=search_query)
        )
    
    rate_plans = rate_plans.order_by('property__name', 'room_type__name', 'name')
    
    # Get filter options
    properties = Property.objects.filter(tenant=tenant, is_active=True).order_by('name')
    room_types = RoomType.objects.filter(property__tenant=tenant, is_active=True).order_by('property__name', 'name')
    
    context = {
        'tenant': tenant,
        'user': user,
        'rate_plans': rate_plans,
        'properties': properties,
        'room_types': room_types,
        'selected_property': property_id,
        'selected_room_type': room_type_id,
        'search_query': search_query,
    }
    return render(request, 'tenants/rate_plans.html', context)


@login_required
def tenant_room_types(request):
    """List all room types for the tenant with filters and search"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # Get filter parameters
    property_id = request.GET.get('property')
    search_query = request.GET.get('search', '')
    
    # Build query
    room_types = RoomType.objects.filter(property__tenant=tenant, is_active=True)
    
    if property_id:
        room_types = room_types.filter(property_id=property_id)
    
    if search_query:
        room_types = room_types.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(property__name__icontains=search_query) |
            Q(bed_type__icontains=search_query)
        )
    
    room_types = room_types.order_by('property__name', 'name')
    
    # Get filter options
    properties = Property.objects.filter(tenant=tenant, is_active=True).order_by('name')
    
    context = {
        'tenant': tenant,
        'user': user,
        'room_types': room_types,
        'properties': properties,
        'selected_property': property_id,
        'search_query': search_query,
    }
    return render(request, 'tenants/room_types.html', context)


@login_required
def tenant_room_type_add(request):
    """Add a new room type"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    if request.method == 'POST':
        form = RoomTypeForm(request.POST, tenant=tenant)
        if form.is_valid():
            room_type = form.save(commit=False)
            # Ensure the property belongs to the tenant
            if room_type.property.tenant != tenant:
                messages.error(request, 'Invalid property selected.')
                return redirect('tenants:room_type_add')
            
            room_type.save()
            messages.success(request, f'Successfully created room type: {room_type.name}')
            return redirect('tenants:room_types')
    else:
        form = RoomTypeForm(tenant=tenant)
    
    context = {
        'tenant': tenant,
        'user': user,
        'form': form,
    }
    return render(request, 'tenants/room_type_add.html', context)


@login_required
def tenant_payments(request):
    """List all payments for the tenant"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    payments = Payment.objects.filter(reservation__property__tenant=tenant).order_by('-created_at')
    
    context = {
        'tenant': tenant,
        'user': user,
        'payments': payments,
    }
    return render(request, 'tenants/payments.html', context)


@login_required
def tenant_sync_logs(request):
    """List sync logs for the tenant with export functionality"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    from django.http import HttpResponse
    import csv
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="sync_logs_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Platform', 'Property', 'Type', 'Status', 'Records Processed', 'Records Succeeded', 'Records Failed', 'Duration (seconds)', 'Date'])
        
        integrations = PropertyIntegration.objects.filter(property__tenant=tenant, is_active=True)
        sync_logs = SyncLog.objects.filter(property_integration__in=integrations).order_by('-created_at')
        
        for log in sync_logs:
            writer.writerow([
                log.property_integration.platform.name if log.property_integration else (log.platform.name if log.platform else 'N/A'),
                log.property_integration.property.name if log.property_integration else 'N/A',
                log.get_sync_type_display(),
                log.get_status_display(),
                log.records_processed,
                log.records_succeeded,
                log.records_failed,
                log.duration_seconds or 0,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    # Regular view with filters
    integrations = PropertyIntegration.objects.filter(property__tenant=tenant, is_active=True)
    sync_logs = SyncLog.objects.filter(property_integration__in=integrations).order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        sync_logs = sync_logs.filter(status=status_filter)
    
    # Filter by platform if provided
    platform_filter = request.GET.get('platform')
    if platform_filter:
        sync_logs = sync_logs.filter(
            Q(property_integration__platform_id=platform_filter) |
            Q(platform_id=platform_filter)
        )
    
    # Limit to 100 most recent
    sync_logs = sync_logs[:100]
    
    # Get filter options
    platforms = IntegrationPlatform.objects.filter(
        property_integrations__property__tenant=tenant
    ).distinct().order_by('display_name')
    
    context = {
        'tenant': tenant,
        'user': user,
        'sync_logs': sync_logs,
        'platforms': platforms,
        'status_filter': status_filter,
        'platform_filter': platform_filter,
    }
    return render(request, 'tenants/sync_logs.html', context)


@login_required
def tenant_subscription(request):
    """View and manage subscription with payment history and upgrade options"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    # Get payment history
    from tenants.models import SubscriptionPayment, SubscriptionPlan
    payment_history = SubscriptionPayment.objects.filter(
        tenant=tenant
    ).order_by('-created_at')[:10]
    
    # Get all available plans for upgrade
    available_plans = SubscriptionPlan.objects.filter(
        is_active=True,
        is_visible=True
    ).order_by('monthly_price')
    
    # Calculate usage statistics
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # API usage trend (last 6 months) - simplified for now
    api_usage_trend = []
    for i in range(5, -1, -1):
        month_date = current_month_start - timedelta(days=30*i)
        api_usage_trend.append({
            'month': month_date.strftime('%b %Y'),
            'calls': tenant.api_calls_this_month if i == 0 else 0
        })
    
    context = {
        'tenant': tenant,
        'user': user,
        'payment_history': payment_history,
        'available_plans': available_plans,
        'api_usage_trend': api_usage_trend,
    }
    return render(request, 'tenants/subscription.html', context)


@login_required
def tenant_profile(request):
    """View and edit tenant profile"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    
    context = {
        'tenant': tenant,
        'user': user,
    }
    return render(request, 'tenants/profile.html', context)


@login_required
def tenant_analytics(request):
    """Advanced analytics dashboard with charts and insights"""
    user = request.user
    if user.is_superuser or not hasattr(user, 'tenant') or not user.tenant:
        return redirect('tenants:login')
    
    tenant = user.tenant
    from datetime import datetime, timedelta
    from django.http import JsonResponse
    
    # Handle AJAX requests for chart data
    if request.GET.get('format') == 'json':
        chart_type = request.GET.get('chart_type', 'revenue_trend')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not start_date or not end_date:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if chart_type == 'revenue_trend':
            # Daily revenue trend
            payments = Payment.objects.filter(
                reservation__property__tenant=tenant,
                payment_status='COMPLETED',
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).extra(
                select={'day': "DATE(created_at)"}
            ).values('day').annotate(
                revenue=Sum('amount')
            ).order_by('day')
            
            data = {
                'labels': [p['day'].strftime('%Y-%m-%d') for p in payments],
                'datasets': [{
                    'label': 'Revenue (₹)',
                    'data': [float(p['revenue']) for p in payments],
                    'borderColor': 'rgb(79, 70, 229)',
                    'backgroundColor': 'rgba(79, 70, 229, 0.1)',
                    'tension': 0.4,
                }]
            }
            return JsonResponse(data)
        
        elif chart_type == 'occupancy_trend':
            # Daily occupancy trend
            inventories = Inventory.objects.filter(
                property__tenant=tenant,
                date__gte=start_date,
                date__lte=end_date
            ).values('date').annotate(
                total_rooms=Sum('total_rooms'),
                occupied_rooms=Sum('total_rooms') - Sum('available_rooms') - Sum('blocked_rooms')
            ).order_by('date')
            
            data = {
                'labels': [str(inv['date']) for inv in inventories],
                'datasets': [{
                    'label': 'Occupancy Rate (%)',
                    'data': [
                        (inv['occupied_rooms'] / inv['total_rooms'] * 100) if inv['total_rooms'] > 0 else 0
                        for inv in inventories
                    ],
                    'borderColor': 'rgb(16, 185, 129)',
                    'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                    'tension': 0.4,
                }]
            }
            return JsonResponse(data)
        
        elif chart_type == 'channel_performance':
            # Channel performance pie chart
            reservations = Reservation.objects.filter(
                property__tenant=tenant,
                check_in__gte=start_date,
                check_in__lte=end_date
            )
            
            channel_data = {}
            for res in reservations:
                channel = res.provider_name
                if channel not in channel_data:
                    channel_data[channel] = {'bookings': 0, 'revenue': 0}
                channel_data[channel]['bookings'] += 1
                if res.status == 'CONFIRMED':
                    channel_data[channel]['revenue'] += float(res.total_amount.amount)
            
            colors = [
                'rgb(79, 70, 229)', 'rgb(16, 185, 129)', 'rgb(245, 158, 11)',
                'rgb(239, 68, 68)', 'rgb(59, 130, 246)', 'rgb(139, 92, 246)',
            ]
            
            data = {
                'labels': list(channel_data.keys()),
                'datasets': [{
                    'label': 'Bookings',
                    'data': [channel_data[ch]['bookings'] for ch in channel_data.keys()],
                    'backgroundColor': colors[:len(channel_data)],
                }]
            }
            return JsonResponse(data)
        
        elif chart_type == 'booking_insights':
            # Booking patterns (day of week, month)
            reservations = Reservation.objects.filter(
                property__tenant=tenant,
                check_in__gte=start_date,
                check_in__lte=end_date
            )
            
            # Day of week analysis
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            day_counts = {day: 0 for day in day_names}
            
            for res in reservations:
                day_name = day_names[res.check_in.weekday()]
                day_counts[day_name] += 1
            
            data = {
                'labels': day_names,
                'datasets': [{
                    'label': 'Bookings by Day of Week',
                    'data': [day_counts[day] for day in day_names],
                    'backgroundColor': 'rgba(79, 70, 229, 0.6)',
                }]
            }
            return JsonResponse(data)
    
    # Default view - render analytics page
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Calculate summary statistics
    payments = Payment.objects.filter(
        reservation__property__tenant=tenant,
        payment_status='COMPLETED',
        created_at__date__gte=last_30_days
    )
    
    total_revenue_30d = sum(p.amount.amount for p in payments)
    avg_daily_revenue = total_revenue_30d / 30 if payments.count() > 0 else 0
    
    reservations_30d = Reservation.objects.filter(
        property__tenant=tenant,
        check_in__gte=last_30_days
    )
    
    total_bookings_30d = reservations_30d.count()
    confirmed_bookings = reservations_30d.filter(status='CONFIRMED').count()
    cancellation_rate = ((total_bookings_30d - confirmed_bookings) / total_bookings_30d * 100) if total_bookings_30d > 0 else 0
    
    # Channel performance
    channel_stats = {}
    for res in reservations_30d:
        channel = res.provider_name
        if channel not in channel_stats:
            channel_stats[channel] = {'bookings': 0, 'revenue': 0}
        channel_stats[channel]['bookings'] += 1
        if res.status == 'CONFIRMED':
            channel_stats[channel]['revenue'] += float(res.total_amount.amount)
    
    # Top performing channels (calculate average booking value)
    top_channels = []
    for channel, stats in channel_stats.items():
        avg_booking_value = stats['revenue'] / stats['bookings'] if stats['bookings'] > 0 else 0
        top_channels.append((channel, {
            'bookings': stats['bookings'],
            'revenue': stats['revenue'],
            'avg_booking_value': avg_booking_value
        }))
    
    # Sort by revenue and take top 5
    top_channels = sorted(
        top_channels,
        key=lambda x: x[1]['revenue'],
        reverse=True
    )[:5]
    
    context = {
        'tenant': tenant,
        'user': user,
        'total_revenue_30d': total_revenue_30d,
        'avg_daily_revenue': avg_daily_revenue,
        'total_bookings_30d': total_bookings_30d,
        'confirmed_bookings': confirmed_bookings,
        'cancellation_rate': cancellation_rate,
        'top_channels': top_channels,
        'default_start_date': last_30_days.strftime('%Y-%m-%d'),
        'default_end_date': today.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'tenants/analytics.html', context)


# Import report and pricing views
from .views_reports import (
    tenant_reports_list,
    tenant_report_create,
    tenant_report_detail,
    tenant_report_download,
)
from .views_pricing import (
    tenant_pricing_rules,
    tenant_pricing_rule_add,
    tenant_rate_optimization,
)
