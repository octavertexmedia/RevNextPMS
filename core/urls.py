from django.urls import path, include
from . import views
from . import views_admin

app_name = 'core'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('health/', views.health_check, name='health_check'),
    
    # Static pages
    path('about/', views.about_us, name='about'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('careers/', views.careers, name='careers'),
    path('contact/', views.contact, name='contact'),
    path('documentation/', views.documentation, name='documentation'),
    path('documentation/getting-started/', views.guide_getting_started, name='guide_getting_started'),
    path('documentation/property-management/', views.guide_property_management, name='guide_property_management'),
    path('documentation/ota-integration/', views.guide_ota_integration, name='guide_ota_integration'),
    path('documentation/inventory-management/', views.guide_inventory_management, name='guide_inventory_management'),
    path('documentation/rate-management/', views.guide_rate_management, name='guide_rate_management'),
    path('documentation/gst-invoicing/', views.guide_gst_invoicing, name='guide_gst_invoicing'),
    path('api-reference/', views.api_reference, name='api_reference'),
    path('help/', views.help_center, name='help_center'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('integrations/', views.integrations_page, name='integrations'),
    
    # API endpoints
    path('', include('core.urls_api')),  # API endpoints
    
    # Admin views
    path('admin/system-health/', views_admin.admin_system_health, name='admin_system_health'),
    path('admin/backup-management/', views_admin.admin_backup_management, name='admin_backup_management'),
]

