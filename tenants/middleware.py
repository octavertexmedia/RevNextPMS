"""
Middleware for tenant and subscription management
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.utils import timezone


class TenantMiddleware(MiddlewareMixin):
    """Add tenant context to request"""
    
    def process_request(self, request):
        """Add tenant to request if user is authenticated"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'tenant') and request.user.tenant:
                request.tenant = request.user.tenant
            else:
                request.tenant = None
        else:
            request.tenant = None
        return None


class SubscriptionMiddleware(MiddlewareMixin):
    """Enforce subscription limits"""
    
    # URLs that don't require subscription check
    EXEMPT_URLS = [
        '/admin/',
        '/api/docs/',
        '/api/redoc/',
        '/api/swagger/',
        '/tenants/register/',
        '/tenants/login/',
        '/health/',
        '/',
    ]
    
    # API endpoints that require subscription
    API_ENDPOINTS = [
        '/api/properties/',
        '/api/integrations/',
        '/api/reservations/',
        '/api/inventory/',
        '/api/rates/',
    ]
    
    def process_request(self, request):
        """Check subscription status for API requests"""
        # Skip check for exempt URLs
        if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
            return None
        
        # Only check API endpoints
        if not any(request.path.startswith(url) for url in self.API_ENDPOINTS):
            return None
        
        # Skip for superusers
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
            return None
        
        # Check if user has active tenant
        if not hasattr(request, 'tenant') or not request.tenant:
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'No tenant associated with user',
                    'detail': 'Please ensure your account is associated with a tenant.'
                }, status=403)
            return None
        
        tenant = request.tenant
        
        # Check subscription status
        if not tenant.is_subscription_active:
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Subscription expired',
                    'detail': f'Your subscription has expired. Please renew to continue using the service.',
                    'subscription_status': tenant.subscription_status,
                    'days_until_expiry': tenant.days_until_expiry,
                }, status=403)
            return None
        
        # Record API call for API endpoints
        if request.path.startswith('/api/') and request.method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            if not tenant.can_make_api_call():
                return JsonResponse({
                    'error': 'API rate limit exceeded',
                    'detail': f'You have exceeded your monthly API call limit of {tenant.max_api_calls_per_month}. Please upgrade your plan.',
                    'api_calls_this_month': tenant.api_calls_this_month,
                    'max_api_calls_per_month': tenant.max_api_calls_per_month,
                }, status=429)
            tenant.record_api_call()
        
        return None
