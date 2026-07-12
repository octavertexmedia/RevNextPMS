"""
OpenBao secrets management for RevNext Channel Manager.

OpenBao (Apache-2.0 Vault fork) is API-compatible with Vault; we use `hvac`.
Secrets load into os.environ before Django settings are evaluated, with
graceful fallback to .env when OpenBao is disabled or unreachable.
"""
from .client import OpenBaoClient, OpenBaoError
from .loader import apply_openbao_secrets, get_secret, secret_status
from .credentials import (
    openbao_path_for_gateway,
    openbao_path_for_integration,
    platform_secret,
    resolve_mapping,
)

__all__ = [
    'OpenBaoClient',
    'OpenBaoError',
    'apply_openbao_secrets',
    'get_secret',
    'secret_status',
    'openbao_path_for_gateway',
    'openbao_path_for_integration',
    'platform_secret',
    'resolve_mapping',
]
