"""OpenBao loader unit tests (no live server required)."""
import os
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from channel_manager.openbao.loader import (
    MANAGED_SECRET_KEYS,
    apply_openbao_secrets,
    base_secret_path,
    is_enabled,
)


class OpenBaoLoaderTests(SimpleTestCase):
    def setUp(self):
        # Reset loader module state
        import channel_manager.openbao.loader as loader
        loader._LOADED = False
        loader._CACHE.clear()
        loader._STATUS = {
            'enabled': False, 'loaded': False, 'addr': '', 'path': '',
            'keys': [], 'error': '', 'source': 'env',
        }

    def test_disabled_by_default(self):
        with patch.dict(os.environ, {'OPENBAO_ENABLED': 'false'}, clear=False):
            self.assertFalse(is_enabled())
            status = apply_openbao_secrets(force=True)
            self.assertFalse(status['loaded'])
            self.assertEqual(status['source'], 'env')

    def test_base_path_uses_environment(self):
        with patch.dict(os.environ, {
            'OPENBAO_SECRET_PATH': 'revnext/channel-manager',
            'OPENBAO_ENVIRONMENT': 'staging',
        }, clear=False):
            self.assertEqual(base_secret_path(), 'revnext/channel-manager/staging')

    @patch('channel_manager.openbao.loader.OpenBaoClient')
    def test_applies_managed_keys(self, mock_cls):
        from channel_manager.openbao.client import OpenBaoError

        client = MagicMock()
        mock_cls.return_value = client
        client.addr = 'http://openbao:8200'

        def read_side_effect(path):
            # Flat env path only
            if path.endswith('/development') or path == 'revnext/channel-manager/development':
                return {
                    'SECRET_KEY': 'from-bao',
                    'RAZORPAY_KEY_SECRET': 'rzp_sec',
                    'IGNORED_KEY': 'x',
                }
            raise OpenBaoError('missing')

        client.read_secret.side_effect = read_side_effect

        with patch.dict(os.environ, {
            'OPENBAO_ENABLED': 'true',
            'OPENBAO_OVERWRITE_ENV': 'true',
            'OPENBAO_ENVIRONMENT': 'development',
            'OPENBAO_SECRET_PATH': 'revnext/channel-manager',
            'SECRET_KEY': 'old',
        }, clear=False):
            status = apply_openbao_secrets(force=True)
            self.assertTrue(status['loaded'])
            self.assertEqual(os.environ.get('SECRET_KEY'), 'from-bao')
            self.assertEqual(os.environ.get('RAZORPAY_KEY_SECRET'), 'rzp_sec')
            self.assertIn('SECRET_KEY', status['keys'])
            self.assertNotIn('IGNORED_KEY', status['keys'])

    def test_managed_keys_include_billing(self):
        self.assertIn('RAZORPAY_KEY_SECRET', MANAGED_SECRET_KEYS)
        self.assertIn('PAYU_MERCHANT_SALT', MANAGED_SECRET_KEYS)
        self.assertIn('DB_PASSWORD', MANAGED_SECRET_KEYS)
