"""
Load secrets from OpenBao into os.environ before Django settings bind.

Path layout (KV v2, mount=secret by default):
  revnext/channel-manager/{environment}

  Keys are env-var names, e.g.:
    SECRET_KEY, DB_PASSWORD, RAZORPAY_KEY_SECRET, PAYU_MERCHANT_SALT, ...

Optional nested paths (also merged when present):
  revnext/channel-manager/{environment}/django
  revnext/channel-manager/{environment}/database
  revnext/channel-manager/{environment}/billing
  revnext/channel-manager/{environment}/integrations
  revnext/channel-manager/{environment}/oidc
  …
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from .catalog import all_managed_secret_keys
from .client import OpenBaoClient, OpenBaoError

logger = logging.getLogger(__name__)

# Allowlist derived from SECRET_GROUPS — never overwrite OPENBAO_* bootstrap
MANAGED_SECRET_KEYS = all_managed_secret_keys()

NESTED_SUFFIXES = ('django', 'database', 'billing', 'integrations', 'email', 'cloud', 'oidc', 'celery')

_CACHE: dict[str, Any] = {}
_LOADED = False
_STATUS: dict[str, Any] = {
    'enabled': False,
    'loaded': False,
    'addr': '',
    'path': '',
    'keys': [],
    'error': '',
    'source': 'env',
}


def is_enabled() -> bool:
    return os.getenv('OPENBAO_ENABLED', 'false').lower() in ('1', 'true', 'yes')


def base_secret_path() -> str:
    env_name = (
        os.getenv('OPENBAO_ENVIRONMENT')
        or os.getenv('ENVIRONMENT')
        or ('production' if os.getenv('DEBUG', 'True') == 'False' else 'development')
    )
    root = os.getenv('OPENBAO_SECRET_PATH', 'revnext/channel-manager')
    return f'{root.rstrip("/")}/{env_name}'


def apply_openbao_secrets(*, force: bool = False) -> dict[str, Any]:
    """
    Fetch secrets and inject into os.environ.

    Returns status dict. Safe to call multiple times.
    """
    global _LOADED, _STATUS

    if _LOADED and not force:
        return dict(_STATUS)

    _STATUS = {
        'enabled': is_enabled(),
        'loaded': False,
        'addr': os.getenv('OPENBAO_ADDR', os.getenv('BAO_ADDR', '')),
        'path': base_secret_path(),
        'keys': [],
        'error': '',
        'source': 'env',
    }

    if not is_enabled():
        _LOADED = True
        return dict(_STATUS)

    required = os.getenv('OPENBAO_REQUIRED', 'false').lower() in ('1', 'true', 'yes')
    overwrite = os.getenv('OPENBAO_OVERWRITE_ENV', 'true').lower() in ('1', 'true', 'yes')

    try:
        client = OpenBaoClient()
        secrets = _collect_secrets(client)
        applied = []
        for key, value in secrets.items():
            if key.startswith('OPENBAO_') or key.startswith('BAO_'):
                continue
            if key not in MANAGED_SECRET_KEYS and not os.getenv('OPENBAO_ALLOW_ANY_KEY'):
                continue
            if value is None:
                continue
            str_val = str(value)
            if not overwrite and os.getenv(key):
                continue
            os.environ[key] = str_val
            _CACHE[key] = str_val
            applied.append(key)

        _STATUS.update({
            'loaded': True,
            'keys': sorted(applied),
            'source': 'openbao',
            'addr': client.addr,
        })
        logger.info(
            'OpenBao secrets loaded from %s (%d keys)',
            _STATUS['path'], len(applied),
        )
    except Exception as exc:
        _STATUS['error'] = str(exc)
        logger.warning('OpenBao secret load failed; using environment/.env: %s', exc)
        if required:
            raise OpenBaoError(
                f'OPENBAO_REQUIRED=true but secrets could not be loaded: {exc}'
            ) from exc

    _LOADED = True
    return dict(_STATUS)


def _collect_secrets(client: OpenBaoClient) -> dict[str, Any]:
    path = base_secret_path()
    merged: dict[str, Any] = {}

    try:
        merged.update(client.read_secret(path))
    except OpenBaoError:
        # Parent path may not exist; try nested only
        pass

    for suffix in NESTED_SUFFIXES:
        nested = f'{path}/{suffix}'
        try:
            merged.update(client.read_secret(nested))
        except OpenBaoError:
            continue

    if not merged:
        raise OpenBaoError(f'No secrets found at {path} (or nested children)')
    return merged


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Read a single secret (cache → OpenBao → env → default)."""
    if key in _CACHE:
        return _CACHE[key]
    if is_enabled() and not _LOADED:
        apply_openbao_secrets()
    if key in _CACHE:
        return _CACHE[key]
    return os.getenv(key, default)


def secret_status() -> dict[str, Any]:
    return dict(_STATUS)
