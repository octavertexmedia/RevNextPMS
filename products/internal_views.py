"""
Internal S2S entitlements API for RevNextCMS (and other external runtimes).

Auth: Authorization: Bearer <ENTITLEMENTS_SERVICE_TOKEN>
   or: X-RevNext-Entitlements-Token: <token>
"""
from __future__ import annotations

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from products.services import (
    active_subscriptions,
    has_product,
    tenant_entitlements_summary,
)


def _token_ok(request) -> bool:
    expected = getattr(settings, 'ENTITLEMENTS_SERVICE_TOKEN', '') or ''
    if not expected:
        return False
    auth = request.headers.get('Authorization') or ''
    if auth.lower().startswith('bearer '):
        provided = auth[7:].strip()
    else:
        provided = request.headers.get('X-RevNext-Entitlements-Token') or ''
    return bool(provided) and provided == expected


def _resolve_tenant(*, email: str = '', tenant_slug: str = ''):
    from tenants.models import Tenant, TenantUser

    if tenant_slug:
        return Tenant.objects.filter(slug=tenant_slug, is_active=True).first()
    if email:
        user = TenantUser.objects.filter(email__iexact=email).select_related('tenant').first()
        if user and user.tenant_id:
            return user.tenant
    return None


@require_GET
def internal_entitlements(request):
    """
    GET /api/internal/entitlements/?email=… | ?tenant_slug=…
    Optional: ?product=cms  (defaults to checking cms)

    Returns entitled product codes, cms entitlement flag, limits, and launch_urls.
    """
    if not _token_ok(request):
        return JsonResponse({'error': 'unauthorized'}, status=401)

    email = (request.GET.get('email') or '').strip()
    tenant_slug = (request.GET.get('tenant_slug') or '').strip()
    product = (request.GET.get('product') or 'cms').strip() or 'cms'

    if not email and not tenant_slug:
        return JsonResponse(
            {'error': 'email_or_tenant_slug_required'},
            status=400,
        )

    tenant = _resolve_tenant(email=email, tenant_slug=tenant_slug)
    if not tenant:
        return JsonResponse({
            'entitled': False,
            'product': product,
            'products': [],
            'tenant_slug': tenant_slug or None,
            'email': email or None,
            'limits': {},
            'features': [],
            'launch_urls': {},
            'detail': 'tenant_not_found',
        })

    summary = tenant_entitlements_summary(tenant)
    entitled = has_product(tenant, product)

    # Roll up limits/features from active subs that entitle `product`
    limits: dict = {}
    features: list = []
    for sub in active_subscriptions(tenant):
        if product in sub.entitled_product_codes():
            for key, val in (sub.limits_snapshot or {}).items():
                if isinstance(val, int):
                    limits[key] = max(limits.get(key, 0), val)
                elif key not in limits:
                    limits[key] = val
            for feat in sub.features_snapshot or []:
                if feat not in features:
                    features.append(feat)

    return JsonResponse({
        'entitled': entitled,
        'product': product,
        'products': summary['products'],
        'tenant_slug': tenant.slug,
        'tenant_name': tenant.name,
        'email': email or None,
        'limits': limits,
        'features': features,
        'launch_urls': summary.get('launch_urls', {}),
        'subscriptions': summary.get('subscriptions', []),
    })
