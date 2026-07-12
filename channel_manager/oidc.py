"""
OIDC relying-party helpers for auth.revnext.in IdP.

Each product host (booking.revnext.in, networks.revnext.in, …) can use its own
client_id/secret from env / OpenBao while sharing the same issuer.
"""
from __future__ import annotations

import logging
import os
from typing import Optional
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_http_methods

from channel_manager.domains import oidc_callback_url
from products.catalog import HOST_ALIASES, OIDC_PRODUCT_CLIENTS
from products.services import get_product_by_host

logger = logging.getLogger(__name__)


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
        # Prefer OIDC_CLIENT_<PRODUCT>_ID / _SECRET, else single env with JSON-ish not used —
        # we use parallel env vars: OIDC_CLIENT_BOOKING_ID + OIDC_CLIENT_BOOKING_SECRET
        pid = os.getenv(f'{env_key}_ID') or os.getenv(env_key, '')
        psecret = os.getenv(f'{env_key}_SECRET', '')
        if pid:
            client_id = pid
        if psecret:
            client_secret = psecret
    return {
        'client_id': client_id,
        'client_secret': client_secret,
        'issuer': getattr(settings, 'OIDC_OP_ISSUER', 'https://auth.revnext.in'),
        'scopes': getattr(settings, 'OIDC_RP_SCOPES', 'openid profile email'),
        'product_code': product_code,
    }


def login_redirect_for_product(product_code: Optional[str]) -> str:
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
    return homes.get(product_code or '', getattr(settings, 'LOGIN_REDIRECT_URL', '/tenants/dashboard/'))


@require_GET
def oidc_login(request):
    """
    Start OIDC authorization code flow against auth.revnext.in.

    When OIDC_ENABLED is false, fall back to local tenant login.
    """
    if not getattr(settings, 'OIDC_ENABLED', False):
        next_url = request.GET.get('next') or login_redirect_for_product(product_code_for_request(request))
        return redirect(f'/tenants/login/?next={next_url}')

    product_code = product_code_for_request(request)
    client = oidc_client_for_product(product_code)
    if not client['client_id']:
        logger.warning('OIDC login attempted without client_id for product=%s', product_code)
        return HttpResponseBadRequest('OIDC client not configured for this product host')

    host = request.get_host().split(':')[0]
    callback = oidc_callback_url(host)
    next_url = request.GET.get('next') or login_redirect_for_product(product_code)
    request.session['oidc_next'] = next_url
    request.session['oidc_product'] = product_code or ''

    # Authorization endpoint (standard OIDC discovery path)
    authorize_url = f"{client['issuer'].rstrip('/')}/authorize"
    params = {
        'response_type': 'code',
        'client_id': client['client_id'],
        'redirect_uri': callback,
        'scope': client['scopes'],
        'state': request.session.session_key or 'anon',
    }
    return HttpResponseRedirect(f'{authorize_url}?{urlencode(params)}')


@require_http_methods(['GET'])
def oidc_callback(request):
    """
    Handle IdP callback.

    Full token exchange against auth.revnext.in is enabled when OIDC_ENABLED
    and client credentials are present. Until the IdP issues codes in this
    environment, we surface a clear error rather than silently failing.
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

    # Token exchange — optional httpx/requests; keep dependency-light with urllib
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

    Uses stdlib urllib to avoid a hard dependency on python-jose / mozilla-django-oidc.
    """
    import json
    from urllib import request as urlrequest
    from urllib.error import HTTPError, URLError

    host = request.get_host().split(':')[0]
    token_url = f"{client['issuer'].rstrip('/')}/token"
    body = urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': oidc_callback_url(host),
        'client_id': client['client_id'],
        'client_secret': client['client_secret'],
    }).encode()

    req = urlrequest.Request(token_url, data=body, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urlrequest.urlopen(req, timeout=15) as resp:
            token_payload = json.loads(resp.read().decode())
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(str(exc)) from exc

    # Prefer userinfo endpoint for email
    access_token = token_payload.get('access_token')
    email = None
    if access_token:
        userinfo_url = f"{client['issuer'].rstrip('/')}/userinfo"
        ureq = urlrequest.Request(userinfo_url)
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
    end_session = f"{getattr(settings, 'OIDC_OP_ISSUER', 'https://auth.revnext.in').rstrip('/')}/logout"
    post_logout = request.build_absolute_uri('/')
    if getattr(settings, 'OIDC_ENABLED', False):
        return HttpResponseRedirect(f'{end_session}?{urlencode({"post_logout_redirect_uri": post_logout})}')
    return redirect('/')


@require_GET
def oidc_metadata(request):
    """Lightweight discovery for product hosts (points at shared IdP)."""
    from django.http import JsonResponse
    issuer = getattr(settings, 'OIDC_OP_ISSUER', 'https://auth.revnext.in')
    product = get_product_by_host(request.get_host())
    return JsonResponse({
        'issuer': issuer,
        'authorization_endpoint': f'{issuer.rstrip("/")}/authorize',
        'token_endpoint': f'{issuer.rstrip("/")}/token',
        'userinfo_endpoint': f'{issuer.rstrip("/")}/userinfo',
        'end_session_endpoint': f'{issuer.rstrip("/")}/logout',
        'product': product.code if product else None,
        'product_host': request.get_host().split(':')[0],
        'callback': oidc_callback_url(request.get_host().split(':')[0]),
        'enabled': bool(getattr(settings, 'OIDC_ENABLED', False)),
    })
