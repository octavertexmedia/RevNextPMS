"""
Django Unfold Admin Configuration for Core Models
"""
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.template.response import TemplateResponse
from django.utils import timezone
from datetime import timedelta
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from simple_history.admin import SimpleHistoryAdmin
from djangoql.admin import DjangoQLSearchMixin

from .models import (
    Property, RoomType, MealPlan, Policy, RatePlan,
    Inventory, Restrictions, TaxFee, Promotion, PricingRule
)
from tenants.mixins import TenantFilterMixin


# Override admin index to add KPIs and restrict access
original_index = admin.site.index

def custom_index(request, extra_context=None):
    """Custom admin index with KPIs - superuser only"""
    # Restrict admin access to superusers only
    if not request.user.is_superuser:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'Access denied. Admin panel is only accessible to superusers.')
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return redirect('/tenants/dashboard/')
        return redirect('/tenants/login/')
    """Custom admin index with KPIs"""
    extra_context = extra_context or {}
    
    try:
        from bookings.models import Reservation, Payment
        from integrations.models import PropertyIntegration, SyncLog
        
        # Calculate KPIs
        today = timezone.now().date()
        last_7_days = today - timedelta(days=7)
        
        # Total counts
        total_properties = Property.objects.filter(is_active=True).count()
        total_integrations = PropertyIntegration.objects.filter(is_active=True).count()
        
        # Reservation statistics (filtered by tenant)
        reservation_filter = {}
        if hasattr(request.user, 'tenant') and request.user.tenant:
            reservation_filter = {'property__tenant': request.user.tenant}
        
        confirmed_reservations = Reservation.objects.filter(status='CONFIRMED', **reservation_filter).count()
        pending_reservations = Reservation.objects.filter(status='PENDING', **reservation_filter).count()
        today_reservations = Reservation.objects.filter(
            check_in__lte=today,
            check_out__gte=today,
            **reservation_filter
        ).count()
        upcoming_reservations = Reservation.objects.filter(
            check_in__gt=today,
            check_in__lte=today + timedelta(days=7),
            **reservation_filter
        ).count()
        
        # Revenue statistics (filtered by tenant)
        payment_filter = {}
        if hasattr(request.user, 'tenant') and request.user.tenant:
            payment_filter = {'reservation__property__tenant': request.user.tenant}
        
        try:
            completed_payments = Payment.objects.filter(payment_status='COMPLETED', **payment_filter)[:1000]
            total_revenue = sum(float(p.amount.amount) for p in completed_payments if p.amount)
        except:
            total_revenue = 0
        
        # Sync statistics (filtered by tenant)
        sync_filter = {'created_at__gte': last_7_days}
        if hasattr(request.user, 'tenant') and request.user.tenant:
            sync_filter['property_integration__property__tenant'] = request.user.tenant
        
        recent_syncs = SyncLog.objects.filter(**sync_filter).count()
        successful_syncs = SyncLog.objects.filter(
            status='SUCCESS',
            **sync_filter
        ).count()
        sync_success_rate = (successful_syncs / recent_syncs * 100) if recent_syncs > 0 else 0
        
        # Create KPI cards
        kpis = [
            {
                'title': 'Properties',
                'value': total_properties,
                'icon': '🏨',
                'color': 'primary',
                'link': reverse('admin:core_property_changelist'),
            },
            {
                'title': 'Active Reservations',
                'value': confirmed_reservations,
                'icon': '📅',
                'color': 'success',
                'link': reverse('admin:bookings_reservation_changelist') + '?status__exact=CONFIRMED',
            },
            {
                'title': "Today's Check-ins",
                'value': today_reservations,
                'icon': '🚪',
                'color': 'info',
                'link': reverse('admin:bookings_reservation_changelist'),
            },
            {
                'title': 'Active Integrations',
                'value': total_integrations,
                'icon': '🔗',
                'color': 'warning',
                'link': reverse('admin:integrations_propertyintegration_changelist'),
            },
            {
                'title': 'Total Revenue',
                'value': f'₹{total_revenue:,.0f}' if total_revenue > 0 else '₹0',
                'icon': '💰',
                'color': 'success',
                'link': reverse('admin:bookings_payment_changelist') + '?payment_status__exact=COMPLETED',
            },
            {
                'title': 'Pending Reservations',
                'value': pending_reservations,
                'icon': '⏳',
                'color': 'warning',
                'link': reverse('admin:bookings_reservation_changelist') + '?status__exact=PENDING',
            },
            {
                'title': 'Upcoming (7 days)',
                'value': upcoming_reservations,
                'icon': '📆',
                'color': 'info',
                'link': reverse('admin:bookings_reservation_changelist'),
            },
            {
                'title': 'Sync Success Rate',
                'value': f'{sync_success_rate:.1f}%' if recent_syncs > 0 else 'N/A',
                'icon': '🔄',
                'color': 'success' if sync_success_rate > 90 else 'warning' if recent_syncs > 0 else 'secondary',
                'link': reverse('admin:integrations_synclog_changelist'),
            },
        ]
        
        # Create Quick Links for common actions
        quick_links = [
            {
                'title': 'Add New Property',
                'icon': '🏨',
                'link': reverse('admin:core_property_add'),
                'description': 'Register a new hotel property',
            },
            {
                'title': 'System Health',
                'icon': '💚',
                'link': reverse('core:admin_system_health'),
                'description': 'Monitor system health and status',
            },
            {
                'title': 'Backup Management',
                'icon': '💾',
                'link': reverse('core:admin_backup_management'),
                'description': 'Manage database backups',
            },
            {
                'title': 'Connect OTA Platform',
                'icon': '🔌',
                'link': reverse('admin:integrations_propertyintegration_add'),
                'description': 'Integrate Booking.com, Expedia, etc.',
            },
            {
                'title': 'View All Reservations',
                'icon': '📋',
                'link': reverse('admin:bookings_reservation_changelist'),
                'description': 'Manage all bookings',
            },
            {
                'title': 'Sync Status',
                'icon': '🔄',
                'link': reverse('admin:integrations_synclog_changelist'),
                'description': 'Check synchronization status',
            },
            {
                'title': 'Manage Inventory',
                'icon': '📦',
                'link': reverse('admin:core_inventory_changelist'),
                'description': 'Update room availability',
            },
            {
                'title': 'Rate Plans',
                'icon': '💵',
                'link': reverse('admin:core_rateplan_changelist'),
                'description': 'Configure pricing',
            },
            {
                'title': 'Room Types',
                'icon': '🛏️',
                'link': reverse('admin:core_roomtype_changelist'),
                'description': 'Manage room categories',
            },
            {
                'title': 'Integration Platforms',
                'icon': '🌐',
                'link': reverse('admin:integrations_integrationplatform_changelist'),
                'description': 'Configure OTA connections',
            },
            {
                'title': 'Payments',
                'icon': '💳',
                'link': reverse('admin:bookings_payment_changelist'),
                'description': 'View payment records',
            },
            {
                'title': 'Settings',
                'icon': '⚙️',
                'link': reverse('admin:constance_config_changelist'),
                'description': 'System configuration',
            },
        ]
        
        extra_context['kpis'] = kpis
        extra_context['quick_links'] = quick_links
        
    except Exception as e:
        extra_context['kpis'] = []
        extra_context['quick_links'] = []
        extra_context['error'] = str(e)
    
    # Call original_index to get proper Unfold structure, then add our KPIs
    response = original_index(request, extra_context)
    return response

# Replace the index method
admin.site.index = custom_index


# Inline Admin Classes
class RoomTypeInline(TabularInline):
    model = RoomType
    extra = 1
    fields = ('name', 'max_occupancy', 'base_occupancy', 'is_active')
    show_change_link = True


class RatePlanInline(TabularInline):
    model = RatePlan
    extra = 1
    fields = ('name', 'room_type', 'base_rate', 'meal_plan', 'is_active')
    show_change_link = True
    autocomplete_fields = ['room_type']


class InventoryInline(TabularInline):
    model = Inventory
    extra = 0
    fields = ('room_type', 'date', 'available_rooms', 'total_rooms', 'blocked_rooms')
    readonly_fields = ('version',)
    autocomplete_fields = ['room_type']


# Resource Classes for Import/Export
class PropertyResource(resources.ModelResource):
    class Meta:
        model = Property
        fields = ('id', 'name', 'legal_name', 'property_type', 'city', 'state', 'country', 'gstin', 'is_active')
        import_id_fields = ['id']


# Admin Classes
@admin.register(Property)
class PropertyAdmin(TenantFilterMixin, DjangoQLSearchMixin, ImportExportModelAdmin, SimpleHistoryAdmin, ModelAdmin):
    resource_class = PropertyResource
    
    list_display = [
        'id',
        'name',
        'property_type',
        'city',
        'state',
        'gstin_display',
        'provider_count',
        'is_active',
        'created_at',
    ]
    
    list_filter = [
        'property_type',
        'country',
        'state',
        'is_active',
        'created_at',
    ]
    
    search_fields = ['name', 'legal_name', 'city', 'gstin', 'pan']
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'provider_mappings_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'name', 'legal_name', 'property_type', 'is_active')
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country', 'location')
        }),
        ('Contact', {
            'fields': ('phone', 'email', 'website')
        }),
        ('Business Details', {
            'fields': ('timezone', 'currency', 'gstin', 'pan')
        }),
        ('Provider Mappings', {
            'fields': ('provider_mappings', 'provider_mappings_display'),
            'classes': ('collapse',)
        }),
        ('Provider Specific Data', {
            'fields': ('provider_specific_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RoomTypeInline, RatePlanInline]
    
    autocomplete_fields = []
    
    @display(description='GSTIN', ordering='gstin')
    def gstin_display(self, obj):
        if obj.gstin:
            return format_html('<code>{}</code>', obj.gstin)
        return '-'
    
    @display(description='Providers')
    def provider_count(self, obj):
        count = len(obj.provider_mappings) if obj.provider_mappings else 0
        if count > 0:
            return format_html('<span class="badge badge-success">{}</span>', count)
        return format_html('<span class="badge badge-secondary">0</span>')
    
    @display(description='Provider Mappings')
    def provider_mappings_display(self, obj):
        if not obj.provider_mappings:
            return '-'
        html = '<ul>'
        for provider, provider_id in obj.provider_mappings.items():
            html += f'<li><strong>{provider}:</strong> {provider_id}</li>'
        html += '</ul>'
        return mark_safe(html)


@admin.register(RoomType)
class RoomTypeAdmin(DjangoQLSearchMixin, SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'name',
        'property',
        'max_occupancy',
        'base_occupancy',
        'amenities_count',
        'is_active',
    ]
    
    list_filter = [
        'property',
        'max_occupancy',
        'is_active',
    ]
    
    search_fields = ['name', 'description', 'property__name']
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    autocomplete_fields = ['property']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'property', 'name', 'description', 'is_active')
        }),
        ('Capacity', {
            'fields': ('max_occupancy', 'base_occupancy', 'max_adults', 'max_children')
        }),
        ('Physical Attributes', {
            'fields': ('size_sqm', 'bed_type', 'amenities')
        }),
        ('Provider Mappings', {
            'fields': ('provider_mappings', 'provider_specific_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Amenities')
    def amenities_count(self, obj):
        count = len(obj.amenities) if obj.amenities else 0
        return format_html('<span class="badge badge-info">{}</span>', count)


@admin.register(MealPlan)
class MealPlanAdmin(ModelAdmin):
    list_display = ['code', 'name', 'description']
    search_fields = ['code', 'name']


@admin.register(Policy)
class PolicyAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ['name', 'policy_type', 'details_preview', 'created_at']
    
    list_filter = ['policy_type', 'created_at']
    
    search_fields = ['name', 'description']
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'policy_type', 'description')
        }),
        ('Policy Details', {
            'fields': ('details',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Details')
    def details_preview(self, obj):
        if obj.details:
            preview = str(obj.details)[:100]
            return format_html('<code>{}</code>', preview)
        return '-'


@admin.register(RatePlan)
class RatePlanAdmin(DjangoQLSearchMixin, SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'name',
        'property',
        'room_type',
        'base_rate',
        'meal_plan',
        'is_derived',
        'is_active',
    ]
    
    list_filter = [
        'property',
        'meal_plan',
        'is_derived',
        'is_active',
    ]
    
    search_fields = ['name', 'description', 'property__name', 'room_type__name']
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    autocomplete_fields = ['property', 'room_type', 'parent_rate_plan']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'property', 'room_type', 'name', 'description', 'is_active')
        }),
        ('Meal Plan & Inclusions', {
            'fields': ('meal_plan', 'inclusions')
        }),
        ('Pricing', {
            'fields': ('base_rate', 'base_occupancy', 'extra_adult_charge', 'extra_child_charge')
        }),
        ('Length of Stay Pricing', {
            'fields': ('los_based_rates',),
            'classes': ('collapse',)
        }),
        ('Derived Rates', {
            'fields': ('is_derived', 'parent_rate_plan', 'derivation_rule'),
            'classes': ('collapse',)
        }),
        ('Policies', {
            'fields': ('cancellation_policy', 'prepayment_policy', 'no_show_policy')
        }),
        ('Provider Mappings', {
            'fields': ('provider_mappings', 'provider_specific_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Inventory)
class InventoryAdmin(DjangoQLSearchMixin, SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'property',
        'room_type',
        'date',
        'available_rooms',
        'total_rooms',
        'blocked_rooms',
        'occupancy_percentage',
        'version',
    ]
    
    list_filter = [
        'property',
        'date',
    ]
    
    search_fields = ['property__name', 'room_type__name']
    
    readonly_fields = ['id', 'version', 'created_at', 'updated_at']
    
    autocomplete_fields = ['property', 'room_type']
    
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'property', 'room_type', 'date')
        }),
        ('Availability', {
            'fields': ('total_rooms', 'available_rooms', 'blocked_rooms', 'version')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Occupancy %', ordering='available_rooms')
    def occupancy_percentage(self, obj):
        if obj.total_rooms > 0:
            percentage = (obj.available_rooms / obj.total_rooms) * 100
            color = 'success' if percentage > 50 else 'warning' if percentage > 20 else 'danger'
            return format_html(
                '<div class="progress" style="width: 100px;"><div class="progress-bar bg-{}" style="width: {}%"></div></div>',
                color, percentage
            )
        return '-'


@admin.register(Restrictions)
class RestrictionsAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'property',
        'rate_plan',
        'date',
        'min_los',
        'max_los',
        'closed_to_arrival',
        'closed_to_departure',
    ]
    
    list_filter = [
        'property',
        'closed_to_arrival',
        'closed_to_departure',
    ]
    
    search_fields = ['property__name', 'rate_plan__name']
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    autocomplete_fields = ['property', 'rate_plan', 'room_type']
    
    date_hierarchy = 'date'


@admin.register(TaxFee)
class TaxFeeAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'name',
        'property',
        'tax_type',
        'value',
        'gst_component',
        'is_inclusive',
    ]
    
    list_filter = [
        'tax_type',
        'gst_component',
        'is_inclusive',
    ]
    
    search_fields = ['name', 'description', 'property__name']
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    autocomplete_fields = ['property']


@admin.register(PricingRule)
class PricingRuleAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ['name', 'property', 'rate_plan', 'rule_type', 'adjustment_type', 'adjustment_value', 'priority', 'is_active', 'is_automatic', 'last_applied_at']
    list_filter = ['rule_type', 'adjustment_type', 'is_active', 'is_automatic', 'property']
    search_fields = ['name', 'description', 'property__name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_applied_at', 'times_applied']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'property', 'rate_plan', 'rule_type', 'description')
        }),
        ('Adjustment Configuration', {
            'fields': ('adjustment_type', 'adjustment_value', 'min_price', 'max_price')
        }),
        ('Conditions', {
            'fields': ('conditions', 'occupancy_threshold')
        }),
        ('Seasonal Configuration', {
            'fields': ('start_date', 'end_date', 'recurrence')
        }),
        ('Status', {
            'fields': ('priority', 'is_active', 'is_automatic', 'last_applied_at', 'times_applied')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Promotion)
class PromotionAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'name',
        'property',
        'promotion_type',
        'discount_value',
        'start_date',
        'end_date',
        'is_active',
    ]
    
    list_filter = [
        'promotion_type',
        'is_active',
        'start_date',
        'end_date',
    ]
    
    search_fields = ['name', 'description', 'property__name']
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    autocomplete_fields = ['property']
    
    date_hierarchy = 'start_date'


# Import Constance admin configuration
from . import constance_admin
