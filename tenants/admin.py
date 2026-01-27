"""
Admin configuration for Tenant models
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import display
from django.utils.html import format_html
from django.urls import reverse

from .models import Tenant, TenantUser, SubscriptionPlan, SubscriptionPayment


@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = [
        'name',
        'slug',
        'email',
        'subscription_plan',
        'property_count_display',
        'is_subscription_active_display',
        'is_active',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'subscription_plan',
        'country',
        'created_at',
    ]
    
    search_fields = ['name', 'email', 'business_name', 'gstin', 'slug']
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login', 'property_count_display', 'is_subscription_active_display']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Business Details', {
            'fields': ('business_name', 'gstin', 'pan', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Subscription', {
            'fields': (
                'subscription_plan',
                'subscription_status',
                'subscription_start_date',
                'subscription_end_date',
                'trial_end_date',
                'is_subscription_active_display',
                'billing_cycle',
                'auto_renew',
                'payment_method',
            )
        }),
        ('Usage', {
            'fields': (
                'api_calls_this_month',
                'max_api_calls_per_month',
                'api_calls_reset_date',
            ),
            'classes': ('collapse',)
        }),
        ('Limits', {
            'fields': ('max_properties', 'max_integrations_per_property', 'property_count_display')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    @display(description='Properties', ordering='property_count')
    def property_count_display(self, obj):
        count = obj.property_count
        max_count = obj.max_properties
        color = 'success' if count < max_count else 'warning'
        return format_html(
            '<span class="badge badge-{}">{}/{}</span>',
            color, count, max_count
        )
    
    @display(description='Subscription Active')
    def is_subscription_active_display(self, obj):
        is_active = obj.is_subscription_active
        color = 'success' if is_active else 'danger'
        text = 'Active' if is_active else 'Expired'
        return format_html('<span class="badge badge-{}">{}</span>', color, text)


@admin.register(TenantUser)
class TenantUserAdmin(BaseUserAdmin, ModelAdmin):
    list_display = [
        'username',
        'email',
        'tenant',
        'role',
        'is_active',
        'last_login',
    ]
    
    list_filter = [
        'tenant',
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
    ]
    
    search_fields = ['username', 'email', 'first_name', 'last_name', 'tenant__name']
    
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login', 'last_activity']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Tenant Information', {
            'fields': ('tenant', 'role')
        }),
        ('Profile', {
            'fields': ('phone', 'avatar', 'timezone', 'language')
        }),
        ('Activity', {
            'fields': ('last_activity',),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Tenant Information', {
            'fields': ('tenant', 'role', 'email')
        }),
    )
    
    filter_horizontal = BaseUserAdmin.filter_horizontal


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = [
        'display_name',
        'name',
        'monthly_price',
        'yearly_price',
        'max_properties',
        'max_integrations_per_property',
        'max_users',
        'max_api_calls_per_month',
        'is_active',
        'is_visible',
    ]
    
    list_filter = [
        'is_active',
        'is_visible',
    ]
    
    search_fields = ['name', 'display_name', 'description']
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'display_name', 'description', 'is_active', 'is_visible')
        }),
        ('Pricing', {
            'fields': ('monthly_price', 'yearly_price')
        }),
        ('Limits', {
            'fields': (
                'max_properties',
                'max_integrations_per_property',
                'max_users',
                'max_api_calls_per_month',
            )
        }),
        ('Features', {
            'fields': ('features',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(ModelAdmin):
    list_display = [
        'tenant',
        'subscription_plan',
        'amount',
        'billing_cycle',
        'payment_status',
        'payment_date',
        'period_start',
        'period_end',
        'created_at',
    ]
    
    list_filter = [
        'payment_status',
        'billing_cycle',
        'payment_gateway',
        'created_at',
    ]
    
    search_fields = [
        'tenant__name',
        'transaction_id',
        'subscription_plan__display_name',
    ]
    
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'tenant', 'subscription_plan')
        }),
        ('Payment Details', {
            'fields': (
                'amount', 'billing_cycle', 'payment_status',
                'transaction_id', 'payment_gateway', 'payment_method',
                'payment_date',
            )
        }),
        ('Period', {
            'fields': ('period_start', 'period_end')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
