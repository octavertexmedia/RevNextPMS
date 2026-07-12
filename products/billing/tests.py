"""Billing gateway unit tests (no live network)."""
from django.test import TestCase, override_settings

from products.billing.payu_gateway import PayUGateway
from products.billing.registry import (
    get_available_gateways,
    get_preferred_gateway_code,
    set_preferred_gateway,
)
from products.billing.razorpay_gateway import RazorpayGateway


class BillingRegistryTests(TestCase):
    @override_settings(BILLING_GATEWAY='payu')
    def test_preferred_from_settings(self):
        self.assertEqual(get_preferred_gateway_code(), 'payu')

    @override_settings(BILLING_GATEWAY='razorpay')
    def test_preferred_razorpay(self):
        self.assertEqual(get_preferred_gateway_code(), 'razorpay')

    def test_available_gateways_shape(self):
        items = get_available_gateways()
        codes = {i['code'] for i in items}
        self.assertEqual(codes, {'razorpay', 'payu'})
        for item in items:
            self.assertIn('configured', item)
            self.assertIn('preferred', item)


class PayUHashTests(TestCase):
    @override_settings(PAYU_MERCHANT_KEY='key', PAYU_MERCHANT_SALT='salt', PAYU_MODE='test')
    def test_verify_success_hash(self):
        gw = PayUGateway()
        data = {
            'status': 'success',
            'txnid': 'INV1T1',
            'amount': '2999.00',
            'productinfo': 'PMS Pro',
            'firstname': 'Test',
            'email': 'a@b.com',
            'udf1': '1',
            'udf2': '1',
            'udf3': 'pms_pro',
            'udf4': 'monthly',
            'udf5': '',
            'mihpayid': '999',
        }
        # Build reverse hash the same way verify does
        expected = gw._hash(
            'salt', 'success', '', '', '', '', '',
            '', 'monthly', 'pms_pro', '1', '1',
            'a@b.com', 'Test', 'PMS Pro', '2999.00', 'INV1T1', 'key',
        )
        data['hash'] = expected
        result = gw.verify_payment(data)
        self.assertTrue(result.success)
        self.assertEqual(result.transaction_id, '999')

    @override_settings(PAYU_MERCHANT_KEY='key', PAYU_MERCHANT_SALT='salt')
    def test_verify_bad_hash(self):
        gw = PayUGateway()
        result = gw.verify_payment({
            'status': 'success',
            'txnid': 'x',
            'amount': '1.00',
            'productinfo': 'p',
            'firstname': 'a',
            'email': 'a@b.com',
            'udf1': '', 'udf2': '', 'udf3': '', 'udf4': '', 'udf5': '',
            'hash': 'deadbeef',
        })
        self.assertFalse(result.success)


class RazorpayConfigTests(TestCase):
    @override_settings(RAZORPAY_KEY_ID='', RAZORPAY_KEY_SECRET='')
    def test_not_configured(self):
        self.assertFalse(RazorpayGateway().is_configured())

    @override_settings(RAZORPAY_KEY_ID='rzp_test', RAZORPAY_KEY_SECRET='secret')
    def test_configured(self):
        gw = RazorpayGateway()
        self.assertTrue(gw.is_configured())
        self.assertEqual(gw.public_config()['key_id'], 'rzp_test')
