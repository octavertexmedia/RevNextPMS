from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Product, ProductInvoice, ProductPlan, TenantProductSubscription


class ProductPlanInline(TabularInline):
    model = ProductPlan
    fk_name = 'product'
    extra = 0
    fields = [
        'code', 'display_name', 'tier', 'monthly_price', 'yearly_price',
        'is_active', 'is_visible', 'sort_order',
    ]
    show_change_link = True


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = [
        'short_name', 'code', 'primary_host', 'is_billable', 'is_active', 'sort_order',
    ]
    list_filter = ['is_active', 'is_billable']
    search_fields = ['code', 'name', 'short_name', 'primary_host']
    inlines = [ProductPlanInline]


@admin.register(ProductPlan)
class ProductPlanAdmin(ModelAdmin):
    list_display = [
        'display_name', 'code', 'product', 'is_package', 'tier',
        'monthly_price', 'yearly_price', 'is_visible', 'is_active',
    ]
    list_filter = ['is_package', 'tier', 'is_active', 'is_visible', 'product']
    search_fields = ['code', 'display_name']
    filter_horizontal = ['package_products']
    autocomplete_fields = ['product']


@admin.register(TenantProductSubscription)
class TenantProductSubscriptionAdmin(ModelAdmin):
    list_display = [
        'tenant', 'plan', 'product', 'status', 'billing_cycle',
        'starts_at', 'ends_at', 'auto_renew', 'created_at',
    ]
    list_filter = ['status', 'billing_cycle', 'plan__is_package', 'product']
    search_fields = ['tenant__name', 'tenant__email', 'plan__code']
    autocomplete_fields = ['tenant', 'plan', 'product']
    readonly_fields = ['created_at', 'updated_at', 'limits_snapshot', 'features_snapshot']


@admin.register(ProductInvoice)
class ProductInvoiceAdmin(ModelAdmin):
    list_display = [
        'id', 'tenant', 'plan', 'amount', 'billing_cycle', 'status',
        'period_start', 'period_end', 'paid_at', 'created_at',
    ]
    list_filter = ['status', 'billing_cycle', 'payment_gateway']
    search_fields = ['tenant__name', 'transaction_id', 'plan__code']
    autocomplete_fields = ['tenant', 'subscription', 'plan']
    readonly_fields = ['created_at', 'updated_at']
