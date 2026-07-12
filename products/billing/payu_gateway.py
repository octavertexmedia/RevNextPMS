"""PayU hosted checkout + reverse-hash verification for SaaS invoices."""
from __future__ import annotations

import hashlib
import logging
from decimal import Decimal
from typing import Optional
from urllib.parse import urljoin

from django.conf import settings

from .base import BillingGateway, CheckoutSession, PaymentResult

logger = logging.getLogger(__name__)


class PayUGateway(BillingGateway):
    code = 'payu'
    display_name = 'PayU'
    TEST_URL = 'https://test.payu.in/_payment'
    LIVE_URL = 'https://secure.payu.in/_payment'

    def __init__(self):
        from channel_manager.openbao.credentials import platform_secret
        from django.conf import settings
        self.merchant_key = platform_secret('PAYU_MERCHANT_KEY', getattr(settings, 'PAYU_MERCHANT_KEY', ''))
        self.merchant_salt = platform_secret('PAYU_MERCHANT_SALT', getattr(settings, 'PAYU_MERCHANT_SALT', ''))
        self.mode = (platform_secret('PAYU_MODE', getattr(settings, 'PAYU_MODE', 'test')) or 'test').lower()

    def is_configured(self) -> bool:
        return bool(self.merchant_key and self.merchant_salt)

    def public_config(self) -> dict:
        cfg = super().public_config()
        cfg['mode'] = self.mode
        return cfg

    @property
    def payment_url(self) -> str:
        return self.LIVE_URL if self.mode == 'live' else self.TEST_URL

    def _hash(self, *parts: str) -> str:
        raw = '|'.join(parts)
        return hashlib.sha512(raw.encode('utf-8')).hexdigest().lower()

    def create_checkout(self, invoice, *, customer: Optional[dict] = None, callback_url: str = '') -> CheckoutSession:
        if not self.is_configured():
            raise RuntimeError('PayU is not configured. Set PAYU_MERCHANT_KEY and PAYU_MERCHANT_SALT.')

        customer = customer or {}
        amount = f'{Decimal(invoice.amount.amount):.2f}'
        txnid = f'INV{invoice.id}T{invoice.tenant_id}'[:40]
        productinfo = invoice.plan.display_name[:100]
        firstname = (customer.get('name') or customer.get('firstname') or 'Customer').split()[0][:60]
        email = (customer.get('email') or f'tenant{invoice.tenant_id}@revnext.in')[:50]
        phone = (customer.get('phone') or '9999999999')[:20]

        # key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5||||||SALT
        udf1 = str(invoice.id)
        udf2 = str(invoice.tenant_id)
        udf3 = invoice.plan.code
        udf4 = invoice.billing_cycle
        udf5 = ''
        payment_hash = self._hash(
            self.merchant_key, txnid, amount, productinfo, firstname, email,
            udf1, udf2, udf3, udf4, udf5, '', '', '', '', '', self.merchant_salt,
        )

        site = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
        surl = callback_url or f'{site}/api/products/billing/payu/return/'
        furl = callback_url or f'{site}/api/products/billing/payu/return/'

        fields = {
            'key': self.merchant_key,
            'txnid': txnid,
            'amount': amount,
            'productinfo': productinfo,
            'firstname': firstname,
            'email': email,
            'phone': phone,
            'surl': surl,
            'furl': furl,
            'hash': payment_hash,
            'udf1': udf1,
            'udf2': udf2,
            'udf3': udf3,
            'udf4': udf4,
            'udf5': udf5,
            'service_provider': 'payu_paisa',
        }

        meta = dict(invoice.meta or {})
        meta['payu_txnid'] = txnid
        invoice.meta = meta
        invoice.payment_gateway = self.code
        invoice.transaction_id = invoice.transaction_id or txnid
        invoice.save(update_fields=['meta', 'payment_gateway', 'transaction_id', 'updated_at'])

        return CheckoutSession(
            gateway=self.code,
            invoice_id=invoice.id,
            amount=Decimal(invoice.amount.amount),
            currency=str(invoice.amount.currency),
            gateway_order_id=txnid,
            payload={
                'action': self.payment_url,
                'method': 'POST',
                'fields': fields,
            },
        )

    def verify_payment(self, data: dict) -> PaymentResult:
        """
        Verify PayU reverse hash from callback / webhook body.

        reverse hash:
        SALT|status||||||udf5|udf4|udf3|udf2|udf1|email|firstname|productinfo|amount|txnid|key
        """
        status_val = (data.get('status') or '').lower()
        txnid = data.get('txnid', '')
        amount = data.get('amount', '')
        productinfo = data.get('productinfo', '')
        firstname = data.get('firstname', '')
        email = data.get('email', '')
        udf1 = data.get('udf1', '')
        udf2 = data.get('udf2', '')
        udf3 = data.get('udf3', '')
        udf4 = data.get('udf4', '')
        udf5 = data.get('udf5', '')
        received_hash = (data.get('hash') or '').lower()
        mihpayid = data.get('mihpayid', '')

        if not received_hash or not txnid:
            return PaymentResult(success=False, gateway=self.code, error='Missing PayU hash/txnid')

        expected = self._hash(
            self.merchant_salt, status_val, '', '', '', '', '',
            udf5, udf4, udf3, udf2, udf1,
            email, firstname, productinfo, amount, txnid, self.merchant_key,
        )

        if not hmac_compare(expected, received_hash):
            return PaymentResult(
                success=False,
                gateway=self.code,
                gateway_order_id=txnid,
                transaction_id=mihpayid or txnid,
                error='Invalid PayU hash',
                raw=data,
            )

        ok = status_val in ('success', 'captured')
        return PaymentResult(
            success=ok,
            gateway=self.code,
            gateway_order_id=txnid,
            transaction_id=mihpayid or txnid,
            payment_method=data.get('mode', 'payu'),
            raw=data,
            error='' if ok else f'PayU status={status_val}',
        )


def hmac_compare(a: str, b: str) -> bool:
    import hmac
    return hmac.compare_digest(a, b)
