"""
Host-based product context + entitlement enforcement.
"""
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.deprecation import MiddlewareMixin

from .services import get_product_by_host, get_product_for_path, has_product


# Public / auth / docs paths never gated by product entitlement
EXEMPT_PREFIXES = (
    '/admin/',
    '/api/docs/',
    '/api/redoc/',
    '/api/swagger/',
    '/api/schema',
    '/api/auth/',
    '/api/rbac/',
    '/api/products/',
    '/tenants/login/',
    '/tenants/register/',
    '/tenants/logout/',
    '/health/',
    '/static/',
    '/media/',
    '/pricing/',
    '/about/',
    '/contact/',
    '/solutions/',
    '/integrations/',  # marketing integrations page (landing)
    '/blog/',
    '/docs/',
    '/guides/',
    '/help/',
    '/api/',  # product gate applied selectively below for API
    '/privacy/',
    '/terms/',
    '/careers/',
)


# Public guest / agent surfaces (entitlement checked against property tenant inside views)
PUBLIC_PRODUCT_EXEMPT = (
    '/booking/widget/',
    '/api/booking-engine/public/',
    '/b2b/portal/',
    '/api/b2b/portal/',
    '/tours/catalog/',
    '/api/tours/public/',
    '/api/tours/portal/',
    '/hotels/search/',
    '/api/hotels/public/',
    '/oidc/',
)


class ProductHostMiddleware(MiddlewareMixin):
    """
    Resolve request.product from Host header.

    Also attaches request.product_host and request.is_product_host.
    """

    def process_request(self, request):
        host = request.get_host()
        product = get_product_by_host(host)
        request.product = product
        request.product_host = host.split(':')[0].lower()
        request.is_product_host = product is not None

        # If on a product subdomain and hitting bare /, send to product home
        if product and request.path == '/':
            homes = {
                'channel_manager': '/tenants/dashboard/',
                'pms': '/pms/',
                'pos': '/pos/',
                'cms': '/website-builder/',
                'booking': '/booking/',
                'aggregator': '/hotels/',
                'networks': '/b2b/',
                'tours': '/tours/',
            }
            target = homes.get(product.code)
            # Aggregator keeps marketing homepage only on apex revnext.in / www
            apex_hosts = {'revnext.in', 'www.revnext.in', 'revnext.localhost', 'www.localhost'}
            host_only = request.product_host
            if product.code == 'aggregator' and host_only in apex_hosts:
                return None
            if target and target != '/' and request.user.is_authenticated:
                return HttpResponseRedirect(target)
            if target and target != '/' and product.code in ('booking', 'networks', 'tours', 'aggregator'):
                if not request.user.is_authenticated:
                    # Guest storefronts for tours / hotels
                    if product.code == 'tours':
                        return HttpResponseRedirect('/tours/catalog/')
                    if product.code == 'aggregator':
                        return HttpResponseRedirect('/hotels/search/')
                    from django.conf import settings as dj_settings
                    if getattr(dj_settings, 'OIDC_ENABLED', False):
                        return HttpResponseRedirect(f'/oidc/login/?next={target}')
                    from django.contrib.auth.views import redirect_to_login
                    return redirect_to_login(target)
                return HttpResponseRedirect(target)
        return None


class ProductEntitlementMiddleware(MiddlewareMixin):
    """
    Block access to product web/API surfaces unless the tenant is entitled.

    Superusers bypass. Unauthenticated users hitting product apps are redirected
    to login (web) or 401 (API). Missing entitlement → 402 Payment Required.
    """

    PRODUCT_WEB_PREFIXES = (
        '/pms/', '/pos/', '/website-builder/', '/booking/',
        '/ota-listing/', '/google-hotel-ads/', '/hotels/', '/b2b/', '/tours/',
        '/tenants/dashboard/', '/tenants/properties/',
    )
    PRODUCT_API_PREFIXES = (
        '/api/pms/', '/api/pos/', '/api/website-builder/', '/api/booking-engine/',
        '/api/ota-listing/', '/api/google-hotel-ads/', '/api/hotels/', '/api/b2b/', '/api/tours/',
        '/api/core/', '/api/integrations/', '/api/bookings/',
    )

    def process_request(self, request):
        path = request.path

        if any(path.startswith(p) for p in PUBLIC_PRODUCT_EXEMPT):
            return None

        # Always allow true public marketing on apex / known public pages
        if path == '/' or any(path.startswith(p) for p in EXEMPT_PREFIXES if p not in ('/api/',)):
            # Still gate protected API product prefixes
            if not path.startswith('/api/'):
                return None

        needs_check = (
            any(path.startswith(p) for p in self.PRODUCT_WEB_PREFIXES)
            or any(path.startswith(p) for p in self.PRODUCT_API_PREFIXES)
        )
        if not needs_check:
            return None

        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            if path.startswith('/api/'):
                return JsonResponse({'error': 'Authentication required'}, status=401)
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(path)

        if user.is_superuser:
            return None

        tenant = getattr(request, 'tenant', None) or getattr(user, 'tenant', None)
        if not tenant:
            return self._deny(request, 'No tenant on account', status=403)

        product = getattr(request, 'product', None) or get_product_for_path(path)
        if not product:
            return None  # path not mapped to a billable product

        if not product.is_billable:
            return None

        if has_product(tenant, product.code):
            return None

        return self._deny(
            request,
            f'Subscription required for {product.short_name}',
            status=402,
            extra={
                'product': product.code,
                'host': product.primary_host,
                'subscribe_url': f'/api/products/plans/?product={product.code}',
                'suite_code': 'revnext_suite',
            },
        )

    def _deny(self, request, detail, status=402, extra=None):
        payload = {'error': 'product_entitlement_required', 'detail': detail}
        if extra:
            payload.update(extra)
        if request.path.startswith('/api/'):
            return JsonResponse(payload, status=status)
        # Web: send to pricing with product hint
        from django.shortcuts import redirect
        product = (extra or {}).get('product', '')
        return redirect(f'/pricing/?product={product}&reason=subscribe')
