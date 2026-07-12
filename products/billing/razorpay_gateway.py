"""Razorpay Orders + signature verification for SaaS invoices."""
from __future__ import annotations

import hashlib
import hmac
import logging
from decimal import Decimal
from typing import Optional

import requests
from django.conf import settings

from .base import BillingGateway, CheckoutSession, PaymentResult

logger = logging.getLogger(__name__)


class RazorpayGateway(BillingGateway):
    code = 'razorpay'
    display_name = 'Razorpay'
    API_BASE = 'https://api.razorpay.com/v1'

    def __init__(self):
        from channel_manager.openbao.credentials import platform_secret
        from django.conf import settings
        self.key_id = platform_secret('RAZORPAY_KEY_ID', getattr(settings, 'RAZORPAY_KEY_ID', ''))
        self.key_secret = platform_secret('RAZORPAY_KEY_SECRET', getattr(settings, 'RAZORPAY_KEY_SECRET', ''))
        self.webhook_secret = platform_secret(
            'RAZORPAY_WEBHOOK_SECRET', getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', ''),
        )

    def is_configured(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def public_config(self) -> dict:
        cfg = super().public_config()
        cfg['key_id'] = self.key_id if self.is_configured() else ''
        return cfg

    def create_checkout(self, invoice, *, customer: Optional[dict] = None, callback_url: str = '') -> CheckoutSession:
        if not self.is_configured():
            raise RuntimeError('Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.')

        amount_paise = int(Decimal(invoice.amount.amount) * 100)
        if amount_paise < 100:
            raise ValueError('Amount must be at least ₹1.00 for Razorpay')

        receipt = f'inv_{invoice.id}'
        body = {
            'amount': amount_paise,
            'currency': str(invoice.amount.currency),
            'receipt': receipt[:40],
            'notes': {
                'invoice_id': str(invoice.id),
                'tenant_id': str(invoice.tenant_id),
                'plan_code': invoice.plan.code,
                'billing_cycle': invoice.billing_cycle,
            },
        }
        resp = requests.post(
            f'{self.API_BASE}/orders',
            json=body,
            auth=(self.key_id, self.key_secret),
            timeout=30,
        )
        if resp.status_code >= 400:
            logger.error('Razorpay order create failed: %s %s', resp.status_code, resp.text)
            raise RuntimeError(f'Razorpay order failed: {resp.text}')

        order = resp.json()
        order_id = order['id']

        meta = dict(invoice.meta or {})
        meta['razorpay_order_id'] = order_id
        invoice.meta = meta
        invoice.payment_gateway = self.code
        invoice.transaction_id = invoice.transaction_id or order_id
        invoice.save(update_fields=['meta', 'payment_gateway', 'transaction_id', 'updated_at'])

        customer = customer or {}
        return CheckoutSession(
            gateway=self.code,
            invoice_id=invoice.id,
            amount=Decimal(invoice.amount.amount),
            currency=str(invoice.amount.currency),
            gateway_order_id=order_id,
            payload={
                'key': self.key_id,
                'amount': amount_paise,
                'currency': str(invoice.amount.currency),
                'order_id': order_id,
                'name': 'RevNext Hospitality',
                'description': invoice.plan.display_name,
                'prefill': {
                    'name': customer.get('name', ''),
                    'email': customer.get('email', ''),
                    'contact': customer.get('phone', ''),
                },
                'notes': body['notes'],
                'callback_url': callback_url,
                'theme': {'color': '#1B3A4B'},
            },
        )

    def verify_payment(self, data: dict) -> PaymentResult:
        order_id = data.get('razorpay_order_id') or data.get('order_id', '')
        payment_id = data.get('razorpay_payment_id') or data.get('payment_id', '')
        signature = data.get('razorpay_signature') or data.get('signature', '')

        if not (order_id and payment_id and signature):
            return PaymentResult(
                success=False, gateway=self.code, error='Missing Razorpay payment fields',
            )

        expected = hmac.new(
            self.key_secret.encode('utf-8'),
            f'{order_id}|{payment_id}'.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return PaymentResult(
                success=False,
                gateway=self.code,
                gateway_order_id=order_id,
                transaction_id=payment_id,
                error='Invalid Razorpay signature',
            )

        return PaymentResult(
            success=True,
            gateway=self.code,
            gateway_order_id=order_id,
            transaction_id=payment_id,
            payment_method='razorpay',
            raw=data,
        )

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            return False
        expected = hmac.new(
            self.webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature or '')
