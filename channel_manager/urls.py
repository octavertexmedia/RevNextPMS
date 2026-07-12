"""
URL configuration for channel_manager project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Configure admin site titles
admin.site.site_title = "RevNext Admin Management"
admin.site.site_header = "RevNext Admin Management"
admin.site.index_title = "RevNext Admin Management"

# Swagger/OpenAPI Schema View
schema_view = get_schema_view(
    openapi.Info(
        title="RevNext Channel Manager API",
        default_version='v1',
        description="""RevNext Channel Manager API

Complete REST API for managing hotel properties, OTA integrations, reservations, and subscriptions.

Features:
- Multi-tenant SaaS: Each hotel owner has isolated data
- Subscription Management: Flexible plans with usage limits
- OTA Integration: Connect to 75+ booking platforms
- Real-time Sync: Keep inventory and rates synchronized
- GST Compliance: Built for Indian hotels with automatic tax calculation

Authentication:
The API supports multiple authentication methods:
1. Token Authentication: Use Token <your-token> in the Authorization header
2. Session Authentication: Use Django session cookies (for browser-based access)

Rate Limiting:
- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- API calls are tracked per tenant subscription plan

Subscription Plans:
- Free: 1 property, 5 integrations/property, 1,000 API calls/month
- Basic: 5 properties, 10 integrations/property, 10,000 API calls/month
- Professional: 25 properties, 25 integrations/property, 100,000 API calls/month
- Enterprise: 100 properties, unlimited integrations, unlimited API calls

Support:
For API support, contact: support@revnext.in
        """,
        terms_of_service="https://www.revnext.in/terms/",
        contact=openapi.Contact(
            name="RevNext Support",
            email="support@revnext.in",
            url="https://www.revnext.in",
        ),
        license=openapi.License(name="Proprietary License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=[
        path('api/auth/', include('tenants.urls_auth')),
        path('api/', include('tenants.urls_api')),
        path('api/rbac/', include('rbac.urls')),
        path('api/products/', include('products.urls')),
        path('api/core/', include('core.urls_api')),
        path('api/integrations/', include('integrations.urls_api')),
        path('api/bookings/', include('bookings.urls_api')),
        path('api/pms/', include('cloud_pms.urls_api')),
        path('api/pos/', include('cloud_pos.urls_api')),
        path('api/booking-engine/', include('booking_engine.urls_api')),
        path('api/website-builder/', include('website_builder.urls_api')),
        path('api/b2b/', include('b2b_network.urls_api')),
        path('api/ota-listing/', include('ota_listing.urls_api')),
        path('api/google-hotel-ads/', include('google_hotel_ads.urls_api')),
        path('api/reports/', include('reports.urls')),
        path('api/tours/', include('tours.urls_api')),
        path('api/hotels/', include('hotels.urls_api')),
    ],
)

urlpatterns = [
    # Admin (superuser only - access control in core/admin.py)
    path('admin/', admin.site.urls),
    
    # Public pages
    path('', include('core.urls')),  # Landing page and core URLs
    path('tenants/', include('tenants.urls')),  # Tenant registration and login
    
    # Solution apps (require login, tenant context)
    path('pms/', include('cloud_pms.urls')),
    path('pos/', include('cloud_pos.urls')),
    path('booking/', include('booking_engine.urls')),
    path('website-builder/', include('website_builder.urls')),
    path('b2b/', include('b2b_network.urls')),
    path('ota-listing/', include('ota_listing.urls')),
    path('google-hotel-ads/', include('google_hotel_ads.urls')),
    path('payment-gateways/', include('payment_gateways.urls')),
    path('tours/', include('tours.urls')),
    path('hotels/', include('hotels.urls')),

    # OIDC RP → auth.revnext.in (SSO across product hosts)
    path('oidc/', include('channel_manager.oidc_urls')),
    
    # Health check
    path('health/', include(('core.urls', 'core'), namespace='health')),
    
    # API Documentation
    re_path(r'^api/schema(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^api/docs(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json-alt'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui-alt'),
    
    # API Endpoints
    path('api/auth/', include('tenants.urls_auth')),
    path('api/', include('tenants.urls_api')),  # Tenant and subscription APIs
    path('api/rbac/', include('rbac.urls')),  # Enterprise hospitality RBAC
    path('api/products/', include('products.urls')),  # Multi-product catalog & billing
    path('api/core/', include('core.urls_api')),
    path('api/integrations/', include('integrations.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/pms/', include('cloud_pms.urls_api')),
    path('api/pos/', include('cloud_pos.urls_api')),
    path('api/booking-engine/', include('booking_engine.urls_api')),
    path('api/website-builder/', include('website_builder.urls_api')),
    path('api/b2b/', include('b2b_network.urls_api')),
    path('api/ota-listing/', include('ota_listing.urls_api')),
    path('api/google-hotel-ads/', include('google_hotel_ads.urls_api')),
    path('api/reports/', include('reports.urls')),  # Reports API
    path('api/tours/', include('tours.urls_api')),
    path('api/hotels/', include('hotels.urls_api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
