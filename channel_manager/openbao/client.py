"""OpenBao / Vault-compatible client (token or AppRole)."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class OpenBaoError(Exception):
    pass


class OpenBaoClient:
    """
    Thin wrapper around hvac for KV v2.

    Auth (first match):
      1. OPENBAO_TOKEN / BAO_TOKEN / VAULT_TOKEN
      2. AppRole OPENBAO_ROLE_ID + OPENBAO_SECRET_ID
    """

    def __init__(
        self,
        addr: Optional[str] = None,
        token: Optional[str] = None,
        mount_point: Optional[str] = None,
        namespace: Optional[str] = None,
        role_id: Optional[str] = None,
        secret_id: Optional[str] = None,
        timeout: int = 10,
        verify: Optional[bool] = None,
    ):
        self.addr = (
            addr
            or os.getenv('OPENBAO_ADDR')
            or os.getenv('BAO_ADDR')
            or os.getenv('VAULT_ADDR')
            or 'http://127.0.0.1:8200'
        ).rstrip('/')
        self.mount_point = (
            mount_point
            or os.getenv('OPENBAO_MOUNT_POINT')
            or os.getenv('BAO_MOUNT_POINT')
            or 'secret'
        )
        self.namespace = namespace or os.getenv('OPENBAO_NAMESPACE') or os.getenv('BAO_NAMESPACE') or ''
        self.timeout = int(os.getenv('OPENBAO_TIMEOUT', timeout))
        if verify is None:
            verify_env = os.getenv('OPENBAO_TLS_VERIFY', 'true').lower()
            self.verify = verify_env not in ('0', 'false', 'no')
        else:
            self.verify = verify

        self.token = (
            token
            or os.getenv('OPENBAO_TOKEN')
            or os.getenv('BAO_TOKEN')
            or os.getenv('VAULT_TOKEN')
            or ''
        )
        self.role_id = role_id or os.getenv('OPENBAO_ROLE_ID') or os.getenv('BAO_ROLE_ID') or ''
        self.secret_id = (
            secret_id or os.getenv('OPENBAO_SECRET_ID') or os.getenv('BAO_SECRET_ID') or ''
        )
        self._client = None

    def _build_client(self):
        try:
            import hvac
        except ImportError as exc:
            raise OpenBaoError(
                'hvac is not installed. Add hvac to requirements and pip install.'
            ) from exc

        client = hvac.Client(
            url=self.addr,
            token=self.token or None,
            namespace=self.namespace or None,
            timeout=self.timeout,
            verify=self.verify,
        )

        if not client.is_authenticated() and self.role_id and self.secret_id:
            resp = client.auth.approle.login(
                role_id=self.role_id,
                secret_id=self.secret_id,
            )
            self.token = resp['auth']['client_token']
            client.token = self.token

        if not client.is_authenticated():
            raise OpenBaoError(
                'OpenBao authentication failed. Set OPENBAO_TOKEN or AppRole credentials.'
            )
        return client

    @property
    def client(self):
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def is_reachable(self) -> bool:
        try:
            import hvac
            c = hvac.Client(url=self.addr, timeout=self.timeout, verify=self.verify)
            c.sys.read_health_status(method='GET')
            return True
        except Exception as exc:
            logger.debug('OpenBao health check failed: %s', exc)
            return False

    def ensure_kv_v2(self) -> None:
        """Enable KV v2 at mount_point if missing (requires elevated token)."""
        mounts = self.client.sys.list_mounted_secrets_engines()
        # hvac may return {'data': {...}} or flat dict
        data = mounts.get('data', mounts)
        path = f'{self.mount_point}/'
        if path in data:
            return
        self.client.sys.enable_secrets_engine(
            backend_type='kv',
            path=self.mount_point,
            options={'version': '2'},
        )

    def read_secret(self, path: str) -> dict[str, Any]:
        """Read KV v2 secret data dict at path (relative to mount)."""
        try:
            resp = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point,
            )
        except Exception as exc:
            raise OpenBaoError(f'Failed to read secret at {path}: {exc}') from exc
        return dict((resp.get('data') or {}).get('data') or {})

    def write_secret(self, path: str, data: dict[str, Any], *, merge: bool = True) -> None:
        """Create/update KV v2 secret. merge=True keeps existing keys."""
        payload = dict(data)
        if merge:
            try:
                existing = self.read_secret(path)
                existing.update(payload)
                payload = existing
            except OpenBaoError:
                pass
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=payload,
                mount_point=self.mount_point,
            )
        except Exception as exc:
            raise OpenBaoError(f'Failed to write secret at {path}: {exc}') from exc

    def delete_secret(self, path: str) -> None:
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=self.mount_point,
            )
        except Exception as exc:
            raise OpenBaoError(f'Failed to delete secret at {path}: {exc}') from exc

    def list_secrets(self, path: str = '') -> list[str]:
        try:
            resp = self.client.secrets.kv.v2.list_secrets(
                path=path or '/',
                mount_point=self.mount_point,
            )
            return list((resp.get('data') or {}).get('keys') or [])
        except Exception:
            return []
