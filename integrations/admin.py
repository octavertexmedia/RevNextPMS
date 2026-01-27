"""
Django Unfold Admin Configuration for Integrations
"""
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from simple_history.admin import SimpleHistoryAdmin
from djangoql.admin import DjangoQLSearchMixin

from .models import IntegrationPlatform, PropertyIntegration, SyncLog, RoomTypeMapping, RatePlanMapping


class PropertyIntegrationInline(TabularInline):
    model = PropertyIntegration
    extra = 0
    fields = ('property', 'provider_property_id', 'is_active', 'last_reservations_sync')
    readonly_fields = ['last_reservations_sync']
    show_change_link = True
    autocomplete_fields = ['property']


@admin.register(IntegrationPlatform)
class IntegrationPlatformAdmin(DjangoQLSearchMixin, SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'display_name',
        'name',
        'platform_type',
        'is_active',
        'is_connected',
        'last_sync_at',
        'sync_status',
    ]
    
    list_filter = [
        'platform_type',
        'is_active',
        'is_connected',
        'supports_webhooks',
        'supports_polling',
    ]
    
    search_fields = ['name', 'display_name', 'api_base_url']
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_sync_at',
        'credentials_display',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'display_name', 'platform_type', 'is_active', 'is_connected')
        }),
        ('API Configuration', {
            'fields': ('api_base_url', 'api_version', 'auth_type')
        }),
        ('Credentials', {
            'fields': ('api_key', 'api_secret', 'additional_credentials', 'credentials_display'),
            'classes': ('collapse',)
        }),
        ('Rate Limiting', {
            'fields': ('rate_limit_rpm', 'rate_limit_rps')
        }),
        ('Features', {
            'fields': ('supports_webhooks', 'supports_polling', 'supports_batch_updates')
        }),
        ('Status', {
            'fields': ('last_sync_at',)
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [PropertyIntegrationInline]
    
    @display(description='Sync Status')
    def sync_status(self, obj):
        if obj.is_connected:
            if obj.last_sync_at:
                from django.utils import timezone
                from datetime import timedelta
                time_diff = timezone.now() - obj.last_sync_at
                if time_diff < timedelta(minutes=30):
                    return format_html('<span class="badge badge-success">Recent</span>')
                elif time_diff < timedelta(hours=2):
                    return format_html('<span class="badge badge-warning">Stale</span>')
                else:
                    return format_html('<span class="badge badge-danger">Old</span>')
            return format_html('<span class="badge badge-secondary">Never</span>')
        return format_html('<span class="badge badge-danger">Disconnected</span>')
    
    @display(description='Credentials')
    def credentials_display(self, obj):
        if obj.api_key:
            masked_key = obj.api_key[:8] + '...' if len(obj.api_key) > 8 else '***'
            return format_html('<code>{}</code>', masked_key)
        return '-'


class RoomTypeMappingInline(TabularInline):
    model = RoomTypeMapping
    extra = 0
    fields = ('room_type', 'provider_room_type_id', 'provider_room_name', 'is_active', 'ordering')
    autocomplete_fields = ['room_type']


class RatePlanMappingInline(TabularInline):
    model = RatePlanMapping
    extra = 0
    fields = ('rate_plan', 'provider_rate_plan_id', 'pricing_mode', 'pricing_value', 'is_active')
    autocomplete_fields = ['rate_plan']


@admin.register(PropertyIntegration)
class PropertyIntegrationAdmin(DjangoQLSearchMixin, SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'property',
        'platform',
        'provider_property_id',
        'sync_status',
        'is_active',
        'last_reservations_sync',
        'error_count',
    ]
    
    list_filter = [
        'platform',
        'is_active',
        'sync_availability',
        'sync_rates',
        'sync_inventory',
        'sync_reservations',
    ]
    
    search_fields = [
        'property__name',
        'platform__name',
        'provider_property_id',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_availability_sync',
        'last_rates_sync',
        'last_inventory_sync',
        'last_reservations_sync',
        'last_error_at',
    ]
    
    autocomplete_fields = ['property', 'platform']
    
    inlines = [RoomTypeMappingInline, RatePlanMappingInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'property', 'platform', 'provider_property_id', 'is_active')
        }),
        ('Mappings', {
            'fields': ('provider_room_type_mappings', 'provider_rate_plan_mappings'),
            'classes': ('collapse',),
            'description': 'Legacy JSON mappings (Deprecated in favor of explicit mapping tables below)'
        }),
        ('Sync Settings', {
            'fields': (
                'sync_availability',
                'sync_rates',
                'sync_inventory',
                'sync_reservations',
            )
        }),
        ('Sync Intervals (minutes)', {
            'fields': (
                'availability_sync_interval',
                'rates_sync_interval',
                'inventory_sync_interval',
                'reservations_sync_interval',
            )
        }),
        ('Last Sync Times', {
            'fields': (
                'last_availability_sync',
                'last_rates_sync',
                'last_inventory_sync',
                'last_reservations_sync',
            ),
            'classes': ('collapse',)
        }),
        ('Error Tracking', {
            'fields': ('last_error', 'error_count', 'last_error_at'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('config',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Sync Status')
    def sync_status(self, obj):
        if obj.is_active:
            if obj.error_count > 10:
                return format_html('<span class="badge badge-danger">Errors</span>')
            elif obj.last_reservations_sync:
                from django.utils import timezone
                from datetime import timedelta
                time_diff = timezone.now() - obj.last_reservations_sync
                if time_diff < timedelta(minutes=30):
                    return format_html('<span class="badge badge-success">Active</span>')
                else:
                    return format_html('<span class="badge badge-warning">Stale</span>')
            return format_html('<span class="badge badge-secondary">Never Synced</span>')
        return format_html('<span class="badge badge-secondary">Inactive</span>')


@admin.register(SyncLog)
class SyncLogAdmin(DjangoQLSearchMixin, ModelAdmin):
    list_display = [
        'platform',
        'property_integration',
        'sync_type',
        'status_badge',
        'records_processed',
        'records_succeeded',
        'records_failed',
        'duration_seconds',
        'created_at',
    ]
    
    list_filter = [
        'platform',
        'sync_type',
        'status',
        'created_at',
    ]
    
    search_fields = [
        'platform__name',
        'property_integration__property__name',
        'error_message',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'duration_seconds',
        'error_details_display',
    ]
    
    autocomplete_fields = ['property_integration', 'platform']
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'platform', 'property_integration', 'sync_type', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_seconds')
        }),
        ('Results', {
            'fields': ('records_processed', 'records_succeeded', 'records_failed')
        }),
        ('Error Details', {
            'fields': ('error_message', 'error_details', 'error_details_display'),
            'classes': ('collapse',)
        }),
        ('Request/Response', {
            'fields': ('request_data', 'response_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Status')
    def status_badge(self, obj):
        colors = {
            'SUCCESS': 'success',
            'FAILED': 'danger',
            'IN_PROGRESS': 'info',
            'PARTIAL': 'warning',
            'PENDING': 'secondary',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @display(description='Error Details')
    def error_details_display(self, obj):
        if obj.error_details:
            return format_html('<pre>{}</pre>', str(obj.error_details))
        return '-'


@admin.register(RoomTypeMapping)
class RoomTypeMappingAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'property_integration',
        'room_type',
        'provider_room_type_id',
        'is_active',
    ]
    search_fields = [
        'property_integration__property__name',
        'room_type__name',
        'provider_room_type_id',
        'provider_room_name'
    ]
    autocomplete_fields = ['property_integration', 'room_type']
    list_filter = ['is_active', 'property_integration__platform']


@admin.register(RatePlanMapping)
class RatePlanMappingAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = [
        'property_integration',
        'rate_plan',
        'provider_rate_plan_id',
        'pricing_mode',
        'pricing_value',
        'is_active',
    ]
    search_fields = [
        'property_integration__property__name',
        'rate_plan__name',
        'provider_rate_plan_id',
        'provider_rate_plan_name'
    ]
    autocomplete_fields = ['property_integration', 'rate_plan']
    list_filter = ['is_active', 'property_integration__platform', 'pricing_mode']

