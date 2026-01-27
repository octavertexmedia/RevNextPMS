"""
URLs for tenant registration and authentication
"""
from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    TenantRegistrationView, TenantLoginView, TenantLogoutView, tenant_dashboard,
    tenant_properties, tenant_property_add, tenant_reservations, tenant_reservation_add,
    tenant_integrations, tenant_integration_add,
    tenant_inventory, tenant_rate_plans, tenant_room_types, tenant_room_type_add,
    tenant_payments, tenant_sync_logs, tenant_subscription, tenant_profile,
    tenant_analytics,
    tenant_reports_list, tenant_report_create, tenant_report_detail, tenant_report_download,
    tenant_pricing_rules, tenant_pricing_rule_add, tenant_rate_optimization,
)

app_name = 'tenants'

urlpatterns = [
    path('', tenant_dashboard, name='index'),  # Redirect /tenants/ to dashboard
    path('register/', TenantRegistrationView.as_view(), name='register'),
    path('login/', TenantLoginView.as_view(), name='login'),
    path('logout/', TenantLogoutView.as_view(), name='logout'),
    path('dashboard/', tenant_dashboard, name='dashboard'),
    
        # Properties
        path('properties/', tenant_properties, name='properties'),
        path('properties/add/', tenant_property_add, name='property_add'),
        path('room-types/', tenant_room_types, name='room_types'),
        path('room-types/add/', tenant_room_type_add, name='room_type_add'),
    
    # Reservations
    path('reservations/', tenant_reservations, name='reservations'),
    path('reservations/add/', tenant_reservation_add, name='reservation_add'),
    path('payments/', tenant_payments, name='payments'),
    
    # Integrations
    path('integrations/', tenant_integrations, name='integrations'),
    path('integrations/add/', tenant_integration_add, name='integration_add'),
    path('sync-logs/', tenant_sync_logs, name='sync_logs'),
    
    # Inventory & Rates
    path('inventory/', tenant_inventory, name='inventory'),
    path('rate-plans/', tenant_rate_plans, name='rate_plans'),
    
    # Analytics
    path('analytics/', tenant_analytics, name='analytics'),
    
    # Reports
    path('reports/', tenant_reports_list, name='reports_list'),
    path('reports/create/', tenant_report_create, name='report_create'),
    path('reports/<int:report_id>/', tenant_report_detail, name='report_detail'),
    path('reports/<int:report_id>/download/', tenant_report_download, name='report_download'),
    
    # Pricing Rules
    path('pricing-rules/', tenant_pricing_rules, name='pricing_rules'),
    path('pricing-rules/add/', tenant_pricing_rule_add, name='pricing_rule_add'),
    path('pricing-rules/<int:rule_id>/edit/', tenant_pricing_rule_add, name='pricing_rule_edit'),
    path('rate-optimization/', tenant_rate_optimization, name='rate_optimization'),
    
    # Settings
    path('subscription/', tenant_subscription, name='subscription'),
    path('profile/', tenant_profile, name='profile'),
]
