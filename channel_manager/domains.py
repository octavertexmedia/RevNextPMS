"""
Canonical RevNext platform + product host map.

Infrastructure (not billable Django product apps):
  secrets.revnext.in  → OpenBao
  auth.revnext.in     → OIDC IdP (SSO for all product hosts)

Marketing / suite apex:
  revnext.in / www.revnext.in

Billable product hosts:
  channel-manager.revnext.in
  pms.revnext.in
  pos.revnext.in
  cms.revnext.in
  booking.revnext.in
  hotels.revnext.in
  networks.revnext.in
  tours.revnext.in
"""

BASE_DOMAIN = 'revnext.in'

INFRA_HOSTS = {
    'secrets': {
        'host': 'secrets.revnext.in',
        'service': 'openbao',
        'default_addr': 'https://secrets.revnext.in',
        'description': 'OpenBao secrets manager',
    },
    'auth': {
        'host': 'auth.revnext.in',
        'service': 'oidc',
        'issuer': 'https://auth.revnext.in',
        'description': 'OIDC identity provider (SSO across products)',
    },
}

ALL_PUBLIC_HOSTS = [
    'localhost',
    '127.0.0.1',
    'revnext.in',
    'www.revnext.in',
    'hotels.revnext.in',
    'channel-manager.revnext.in',
    'pms.revnext.in',
    'pos.revnext.in',
    'cms.revnext.in',
    'booking.revnext.in',
    'networks.revnext.in',
    'tours.revnext.in',
    'secrets.revnext.in',
    'auth.revnext.in',
    'channel-manager.localhost',
    'pms.localhost',
    'pos.localhost',
    'cms.localhost',
    'booking.localhost',
    'networks.localhost',
    'tours.localhost',
    'hotels.localhost',
    'secrets.localhost',
    'auth.localhost',
]


def default_allowed_hosts() -> list[str]:
    return list(ALL_PUBLIC_HOSTS)


def csrf_trusted_origins(scheme: str = 'https') -> list[str]:
    origins = []
    for host in ALL_PUBLIC_HOSTS:
        if host in ('localhost', '127.0.0.1') or host.endswith('.localhost'):
            origins.append(f'http://{host}')
            origins.append(f'http://{host}:8000')
            origins.append(f'http://{host}:8001')
        else:
            origins.append(f'{scheme}://{host}')
    return origins


def oidc_callback_url(product_host: str) -> str:
    """Per-product OIDC callback on auth-aware product hosts."""
    if product_host.endswith('.localhost') or product_host in ('localhost', '127.0.0.1'):
        return f'http://{product_host}:8000/oidc/callback/'
    return f'https://{product_host}/oidc/callback/'


PRODUCT_OIDC_REDIRECT_URIS = [
    oidc_callback_url(h) for h in ALL_PUBLIC_HOSTS
    if h not in ('localhost', '127.0.0.1', 'secrets.revnext.in', 'auth.revnext.in',
                 'secrets.localhost', 'auth.localhost')
    and not h.startswith('secrets.') and not h.startswith('auth.')
]

# Production apex hosts (no .localhost) — for env.example / deploy.sh
PRODUCTION_HOSTS = [
    h for h in ALL_PUBLIC_HOSTS
    if h not in ('localhost', '127.0.0.1') and not h.endswith('.localhost')
]

# Nginx / app product hosts (exclude infra secrets/auth which may be separate services)
NGINX_APP_HOSTS = [
    h for h in PRODUCTION_HOSTS
    if h not in ('secrets.revnext.in', 'auth.revnext.in')
]


def production_allowed_hosts_csv(extra: list[str] | None = None) -> str:
    hosts = list(PRODUCTION_HOSTS)
    for h in (extra or []):
        if h and h not in hosts:
            hosts.append(h)
    return ','.join(hosts)


def production_csrf_origins_csv() -> str:
    return ','.join(f'https://{h}' for h in PRODUCTION_HOSTS)


def production_cors_origins_csv() -> str:
    """Browser SPA / widget origins for product hosts + common local."""
    origins = [f'https://{h}' for h in NGINX_APP_HOSTS]
    origins.extend([
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:8080',
        'http://127.0.0.1:8080',
    ])
    return ','.join(origins)
