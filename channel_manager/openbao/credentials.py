"""
Resolve runtime credentials from OpenBao (preferred) or local DB/env fallback.

Path conventions (KV v2 under mount `secret`):
  Platform:
    revnext/channel-manager/{env}/django|database|billing|oidc|...

  Tenant property payment gateway:
    revnext/tenants/{tenant_id}/properties/{property_id}/gateways/{gateway}

  Tenant OTA integration:
    revnext/tenants/{tenant_id}/properties/{property_id}/integrations/{platform_code}
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from channel_manager.openbao.client import OpenBaoClient, OpenBaoError
from channel_manager.openbao.loader import get_secret, is_enabled

logger = logging.getLogger(__name__)


def openbao_path_for_gateway(tenant_id, property_id, gateway_name: str) -> str:
    prop = property_id or 'tenant'
    return f'revnext/tenants/{tenant_id}/properties/{prop}/gateways/{gateway_name}'


def openbao_path_for_integration(tenant_id, property_id, platform_code: str) -> str:
    return (
        f'revnext/tenants/{tenant_id}/properties/{property_id}/integrations/{platform_code}'
    )


def read_path(path: str) -> dict[str, Any]:
    if not is_enabled():
        return {}
    try:
        return OpenBaoClient().read_secret(path)
    except OpenBaoError as exc:
        logger.warning('OpenBao read failed for %s: %s', path, exc)
        return {}


def write_path(path: str, data: dict[str, Any], *, merge: bool = True) -> bool:
    if not is_enabled():
        return False
    try:
        OpenBaoClient().write_secret(path, data, merge=merge)
        return True
    except OpenBaoError as exc:
        logger.error('OpenBao write failed for %s: %s', path, exc)
        return False


def resolve_mapping(
    *,
    secret_ref: str = '',
    local: Optional[dict[str, Any]] = None,
    keys: Optional[list[str]] = None,
) -> dict[str, Any]:
    """
    Merge OpenBao secret_ref data over local DB fields.
    Empty OpenBao values do not wipe non-empty local fallbacks.
    """
    local = dict(local or {})
    remote: dict[str, Any] = {}
    if secret_ref and is_enabled():
        remote = read_path(secret_ref)

    merged = dict(local)
    for key, value in remote.items():
        if keys and key not in keys:
            continue
        if value is None or value == '':
            continue
        merged[key] = value
    return merged


def platform_secret(key: str, default: str = '') -> str:
    """Platform SaaS secret (billing, OIDC client, etc.)."""
    return get_secret(key, default) or default
