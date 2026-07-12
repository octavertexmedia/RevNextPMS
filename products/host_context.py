"""
Resolve marketing + auth chrome for product hosts (pms.revnext.in, etc.).
"""
from __future__ import annotations

from typing import Any, Optional

from django.conf import settings


def _host_from_request(request) -> str:
    return (
        getattr(request, 'product_host', None)
        or request.get_host().split(':')[0]
    ).lower().strip()


def resolve_product_code(request) -> Optional[str]:
    from .catalog import HOST_ALIASES

    product = getattr(request, 'product', None)
    if product is not None:
        return product.code
    return HOST_ALIASES.get(_host_from_request(request))


def product_host_context(request, *, product_code: Optional[str] = None) -> dict[str, Any]:
    """
    Context for product-host landings and auth pages.

    Empty dict when not on a known product subdomain (suite / apex / infra).
    """
    from .catalog import HOST_ALIASES, PRODUCT_CATALOG, PRODUCT_HOST_LANDING
    from core.solutions_data import get_solution

    host = _host_from_request(request)
    apex = {
        'revnext.in', 'www.revnext.in', 'revnext.localhost', 'www.localhost',
        'localhost', '127.0.0.1',
    }
    code = product_code or resolve_product_code(request)
    if not code or code not in PRODUCT_HOST_LANDING or host in apex:
        return {'product_host_mode': False}

    meta = PRODUCT_HOST_LANDING[code]
    solution = get_solution(meta['solution_slug']) or {}
    product = getattr(request, 'product', None)
    if product:
        product_name = product.short_name or product.name
    else:
        product_name = next(
            (row[2] for row in PRODUCT_CATALOG if row[0] == code),
            solution.get('eyebrow', 'RevNext'),
        )

    app_home = meta['app_home']
    next_url = request.GET.get('next') or app_home
    # Always use product-branded tenants auth pages on product hosts.
    # OIDC (if enabled) remains available at /oidc/login/ as an SSO option.
    login_url = f'/tenants/login/?next={next_url}'
    register_url = f'/tenants/register/?product={code}&next={next_url}'
    oidc_login_url = ''
    if getattr(settings, 'OIDC_ENABLED', False):
        oidc_login_url = f'/oidc/login/?next={next_url}'

    return {
        'product_host_mode': True,
        'product_code': code,
        'product_name': product_name,
        'solution': solution,
        'solution_slug': solution.get('slug', meta['solution_slug']),
        'solution_title': solution.get('title', product_name),
        'solution_description': solution.get('lead', ''),
        'solution_features': solution.get('features', []),
        'app_home': app_home,
        'login_url': login_url,
        'login_label': meta.get('login_label', 'Sign in'),
        'register_url': register_url,
        'oidc_login_url': oidc_login_url,
        'cta_label': meta.get('cta_label', 'Start free trial'),
        'guest_cta': meta.get('guest_cta'),
        'auth_eyebrow': meta.get('auth_eyebrow') or solution.get('eyebrow', product_name),
        'auth_title': meta.get('auth_title') or solution.get('title', product_name),
        'auth_lead': meta.get('auth_lead') or solution.get('lead', ''),
        'auth_stats': meta.get('auth_stats') or [],
        'auth_bullets': meta.get('auth_bullets') or solution.get('features', [])[:3],
        'welcome_title': meta.get('welcome_title', 'Welcome back'),
        'welcome_lead': meta.get('welcome_lead', f'Sign in to {product_name}'),
        'register_title': meta.get('register_title', f'Create your {product_name} account'),
        'register_lead': meta.get(
            'register_lead',
            f'Start your 14-day trial for {product_name}',
        ),
        'page_title': f"{solution.get('eyebrow', product_name)} | RevNext",
        'meta_description': solution.get('meta', ''),
    }
