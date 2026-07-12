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
    '/api/internal/',
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
    '/website-builder/',  # legacy stub → redirected to RevNextCMS
)


CMS_RUNTIME_FALLBACK = 'https://app.revnext.in/oidc/authenticate/?next=%2Fdashboard%2F'


def _cms_launch_url() -> str:
    try:
        from .models import Product
        product = Product.objects.filter(code='cms', is_active=True).first()
        if product:
            return product.launch_url(with_oidc=True)
    except Exception:
        pass
    return CMS_RUNTIME_FALLBACK


class ProductHostMiddleware(MiddlewareMixin):
    """
    Resolve request.product from Host header.

    Also attaches request.product_host and request.is_product_host.
    Redirects legacy /website-builder/ to RevNextCMS.
    """

    def process_request(self, request):
        # Legacy website_builder stub → external RevNextCMS
        if request.path.startswith('/website-builder/') or request.path.startswith('/api/website-builder/'):
            return HttpResponseRedirect(_cms_launch_url())

        host = request.get_host()
        product = get_product_by_host(host)
        request.product = product
        request.product_host = host.split(':')[0].lower()
        request.is_product_host = product is not None

        # External products are never served on this process — send home to runtime
        if (
            product
            and getattr(product, 'is_externally_served', False)
            and request.path == '/'
        ):
            return HttpResponseRedirect(product.launch_url(with_oidc=True))

        # If on a product subdomain and hitting bare /, send authenticated users
        # to the product app. Guests see the product-specific landing (core.landing_page).
        if product and request.path == '/':
            homes = {
                'channel_manager': '/tenants/dashboard/',
                'pms': '/pms/',
                'pos': '/pos/',
                'booking': '/booking/',
                'aggregator': '/hotels/',
                'networks': '/b2b/',
                'tours': '/tours/',
            }
            target = homes.get(product.code)
            # Suite marketing homepage only on apex (Vercel or local)
            apex_hosts = {'revnext.in', 'www.revnext.in', 'revnext.localhost', 'www.localhost'}
            host_only = request.product_host
            if product.code == 'aggregator' and host_only in apex_hosts:
                return None
            if target and request.user.is_authenticated:
                return HttpResponseRedirect(target)
        return None


class ProductEntitlementMiddleware(MiddlewareMixin):
    """
    Block access to product web/API surfaces unless the tenant is entitled.

    Superusers bypass. Unauthenticated users hitting product apps are redirected
    to login (web) or 401 (API). Missing entitlement → 402 Payment Required.
    Externally served products are not gated on local paths (they live elsewhere).
    """

    PRODUCT_WEB_PREFIXES = (
        '/pms/', '/pos/', '/booking/',
        '/ota-listing/', '/google-hotel-ads/', '/hotels/', '/b2b/', '/tours/',
        '/tenants/dashboard/', '/tenants/properties/',
    )
    PRODUCT_API_PREFIXES = (
        '/api/pms/', '/api/pos/', '/api/booking-engine/',
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

        # External products are enforced on their own VPS, not here
        if getattr(product, 'is_externally_served', False):
            return None

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
                'launch_url': (
                    product.launch_url(with_oidc=True)
                    if getattr(product, 'is_externally_served', False)
                    else ''
                ),
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
