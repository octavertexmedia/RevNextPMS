"""
OIDC relying-party helpers for auth.revnext.in IdP.

Each product host (booking.revnext.in, networks.revnext.in, …) can use its own
client_id/secret from env / OpenBao while sharing the same issuer.

Keycloak issuer format:
  https://auth.revnext.in/realms/revnext
Endpoints resolve via discovery or /protocol/openid-connect/{auth,token,userinfo,logout}.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional
from urllib.parse import urlencode
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_http_methods

from channel_manager.domains import oidc_callback_url
from products.catalog import EXTERNAL_PRODUCT_RUNTIME, HOST_ALIASES, OIDC_PRODUCT_CLIENTS
from products.services import get_product_by_host

logger = logging.getLogger(__name__)

_discovery_cache: dict[str, dict] = {}


def product_code_for_request(request) -> Optional[str]:
    product = getattr(request, 'product', None)
    if product:
        return product.code
    host = request.get_host().split(':')[0].lower()
    return HOST_ALIASES.get(host)


def oidc_client_for_product(product_code: Optional[str]) -> dict:
    """
    Resolve OIDC client credentials for a product.

    Falls back to global OIDC_RP_* when per-product keys are unset.
    """
    client_id = getattr(settings, 'OIDC_RP_CLIENT_ID', '') or ''
    client_secret = getattr(settings, 'OIDC_RP_CLIENT_SECRET', '') or ''
    env_key = OIDC_PRODUCT_CLIENTS.get(product_code or '')
    if env_key:
        pid = os.getenv(f'{env_key}_ID') or os.getenv(env_key, '')
        psecret = os.getenv(f'{env_key}_SECRET', '')
        if pid:
            client_id = pid
        if psecret:
            client_secret = psecret
    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'issuer': getattr(settings, 'OIDC_OP_ISSUER', 'https://auth.revnext.in/realms/revnext'),
        'scopes': getattr(settings, 'OIDC_RP_SCOPES', 'openid profile email'),
        'product_code': product_code,
    }


def _normalize_issuer(issuer: str) -> str:
    issuer = (issuer or '').rstrip('/')
    # Flat auth.revnext.in without realm → Keycloak default realm path
    if issuer in ('https://auth.revnext.in', 'http://auth.revnext.in', 'https://auth.revnext.in/', 'http://localhost:8080'):
        if 'localhost' in issuer:
            return f'{issuer.rstrip("/")}/realms/revnext'
        return 'https://auth.revnext.in/realms/revnext'
    return issuer


def _oidc_endpoints(issuer: str) -> dict:
    """
    Resolve authorize/token/userinfo/end_session from discovery, with Keycloak fallbacks.
    """
    issuer = _normalize_issuer(issuer)
    if issuer in _discovery_cache:
        return _discovery_cache[issuer]

    discovery_url = f'{issuer}/.well-known/openid-configuration'
    try:
        req = urlrequest.Request(discovery_url)
        with urlrequest.urlopen(req, timeout=10) as resp:
            doc = json.loads(resp.read().decode())
            endpoints = {
                'issuer': doc.get('issuer', issuer),
                'authorization_endpoint': doc['authorization_endpoint'],
                'token_endpoint': doc['token_endpoint'],
                'userinfo_endpoint': doc.get('userinfo_endpoint', f'{issuer}/protocol/openid-connect/userinfo'),
                'end_session_endpoint': doc.get(
                    'end_session_endpoint',
                    f'{issuer}/protocol/openid-connect/logout',
                ),
            }
            _discovery_cache[issuer] = endpoints
            return endpoints
    except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
        logger.info('OIDC discovery failed for %s (%s); using Keycloak path fallbacks', issuer, exc)

    # Keycloak path convention
    base = f'{issuer}/protocol/openid-connect'
    endpoints = {
        'issuer': issuer,
        'authorization_endpoint': f'{base}/auth',
        'token_endpoint': f'{base}/token',
        'userinfo_endpoint': f'{base}/userinfo',
        'end_session_endpoint': f'{base}/logout',
    }
    # Also support flat OIDC providers that expose /authorize on the issuer
    if not issuer.endswith('/realms/revnext') and '/realms/' not in issuer:
        endpoints = {
            'issuer': issuer,
            'authorization_endpoint': f'{issuer}/authorize',
            'token_endpoint': f'{issuer}/token',
            'userinfo_endpoint': f'{issuer}/userinfo',
            'end_session_endpoint': f'{issuer}/logout',
        }
    _discovery_cache[issuer] = endpoints
    return endpoints


def login_redirect_for_product(product_code: Optional[str]) -> str:
    # External CMS → RevNextCMS owner portal (absolute URL)
    if product_code == 'cms':
        try:
            from products.models import Product
            product = Product.objects.filter(code='cms', is_active=True).first()
            if product and product.is_externally_served:
                return product.launch_url(with_oidc=True)
        except Exception:
            pass
        ext = EXTERNAL_PRODUCT_RUNTIME.get('cms', {})
        base = (ext.get('runtime_url') or 'https://app.revnext.in').rstrip('/')
        path = ext.get('launch_path') or '/dashboard/'
        from urllib.parse import quote
        return f'{base}/oidc/authenticate/?next={quote(path)}'

    homes = {
        'channel_manager': '/tenants/dashboard/',
        'pms': '/pms/',
        'pos': '/pos/',
        'booking': '/booking/',
        'aggregator': '/hotels/',
        'networks': '/b2b/',
        'tours': '/tours/',
    }
    return homes.get(product_code or '', getattr(settings, 'LOGIN_REDIRECT_URL', '/tenants/dashboard/'))


@require_GET
def oidc_login(request):
    """
    Start OIDC authorization code flow against auth.revnext.in.

    When OIDC_ENABLED is false, fall back to local tenant login.
    """
    if not getattr(settings, 'OIDC_ENABLED', False):
        next_url = request.GET.get('next') or login_redirect_for_product(product_code_for_request(request))
        # Absolute external URLs (CMS) — send browser there directly when OIDC off
        if next_url.startswith('http://') or next_url.startswith('https://'):
            return redirect(next_url)
        return redirect(f'/tenants/login/?next={next_url}')

    product_code = product_code_for_request(request)
    # CMS is not served here — bounce to RevNextCMS OIDC
    if product_code == 'cms':
        return redirect(login_redirect_for_product('cms'))

    client = oidc_client_for_product(product_code)
    if not client['client_id']:
        logger.warning('OIDC login attempted without client_id for product=%s', product_code)
        return HttpResponseBadRequest('OIDC client not configured for this product host')

    host = request.get_host().split(':')[0]
    callback = oidc_callback_url(host)
    next_url = request.GET.get('next') or login_redirect_for_product(product_code)
    request.session['oidc_next'] = next_url
    request.session['oidc_product'] = product_code or ''

    endpoints = _oidc_endpoints(client['issuer'])
    params = {
        'response_type': 'code',
        'client_id': client['client_id'],
        'redirect_uri': callback,
        'scope': client['scopes'],
        'state': request.session.session_key or 'anon',
    }
    return HttpResponseRedirect(f'{endpoints["authorization_endpoint"]}?{urlencode(params)}')


@require_http_methods(['GET'])
def oidc_callback(request):
    """
    Handle IdP callback.

    Full token exchange against auth.revnext.in is enabled when OIDC_ENABLED
    and client credentials are present.
    """
    if not getattr(settings, 'OIDC_ENABLED', False):
        return redirect('/tenants/login/')

    error = request.GET.get('error')
    if error:
        logger.info('OIDC error: %s %s', error, request.GET.get('error_description'))
        return HttpResponseBadRequest(f'OIDC error: {error}')

    code = request.GET.get('code')
    if not code:
        return HttpResponseBadRequest('Missing authorization code')

    product_code = request.session.get('oidc_product') or product_code_for_request(request)
    client = oidc_client_for_product(product_code)
    next_url = request.session.pop('oidc_next', None) or login_redirect_for_product(product_code)

    try:
        user = _exchange_code_and_resolve_user(request, code, client)
    except Exception as exc:
        logger.exception('OIDC token exchange failed: %s', exc)
        return HttpResponseBadRequest(f'OIDC token exchange failed: {exc}')

    if not user:
        return HttpResponseBadRequest('Could not resolve user from IdP claims')

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect(next_url)


def _exchange_code_and_resolve_user(request, code: str, client: dict):
    """
    Exchange authorization code for tokens and map `email` claim → TenantUser.
    """
    host = request.get_host().split(':')[0]
    endpoints = _oidc_endpoints(client['issuer'])
    body = urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': oidc_callback_url(host),
        'client_id': client['client_id'],
        'client_secret': client['client_secret'],
    }).encode()

    req = urlrequest.Request(endpoints['token_endpoint'], data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urlrequest.urlopen(req, timeout=15) as resp:
            token_payload = json.loads(resp.read().decode())
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc)) from exc

    access_token = token_payload.get('access_token')
    email = None
    if access_token:
        ureq = urlrequest.Request(endpoints['userinfo_endpoint'])
        ureq.add_header('Authorization', f'Bearer {access_token}')
        try:
            with urlrequest.urlopen(ureq, timeout=15) as resp:
                claims = json.loads(resp.read().decode())
                email = claims.get('email') or claims.get('preferred_username')
        except (HTTPError, URLError, TimeoutError):
            pass

    if not email:
        raise RuntimeError('IdP did not return an email claim')

    from tenants.models import TenantUser
    user = TenantUser.objects.filter(email__iexact=email).first()
    if not user:
        raise RuntimeError(f'No local user for IdP email {email}')
    return user


@require_GET
def oidc_logout(request):
    from django.contrib.auth import logout
    logout(request)
    issuer = _normalize_issuer(getattr(settings, 'OIDC_OP_ISSUER', 'https://auth.revnext.in/realms/revnext'))
    endpoints = _oidc_endpoints(issuer)
    post_logout = request.build_absolute_uri('/')
    if getattr(settings, 'OIDC_ENABLED', False):
        return HttpResponseRedirect(
            f'{endpoints["end_session_endpoint"]}?{urlencode({"post_logout_redirect_uri": post_logout})}'
        )
    return redirect('/')


@require_GET
def oidc_metadata(request):
    """Lightweight discovery for product hosts (points at shared IdP)."""
    from django.http import JsonResponse
    issuer = _normalize_issuer(getattr(settings, 'OIDC_OP_ISSUER', 'https://auth.revnext.in/realms/revnext'))
    endpoints = _oidc_endpoints(issuer)
    product = get_product_by_host(request.get_host())
    return JsonResponse({
        'issuer': endpoints['issuer'],
        'authorization_endpoint': endpoints['authorization_endpoint'],
        'token_endpoint': endpoints['token_endpoint'],
        'userinfo_endpoint': endpoints['userinfo_endpoint'],
        'end_session_endpoint': endpoints['end_session_endpoint'],
        'product': product.code if product else None,
        'product_host': request.get_host().split(':')[0],
        'callback': oidc_callback_url(request.get_host().split(':')[0]),
        'enabled': bool(getattr(settings, 'OIDC_ENABLED', False)),
    })
