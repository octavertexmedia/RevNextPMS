"""Checkout + settle ProductInvoice through the active platform gateway."""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from products.models import ProductInvoice, TenantProductSubscription
from products.services import _mirror_legacy_subscription, _sync_legacy_tenant_limits

from .base import CheckoutSession, PaymentResult
from .registry import get_active_gateway


class BillingError(Exception):
    pass


def create_invoice_checkout(
    invoice: ProductInvoice,
    *,
    gateway_code: str | None = None,
    customer: dict | None = None,
    callback_url: str = '',
) -> CheckoutSession:
    if invoice.status == 'paid':
        raise BillingError('Invoice is already paid.')
    if invoice.status in ('void', 'refunded'):
        raise BillingError(f'Invoice cannot be paid (status={invoice.status}).')

    gateway = get_active_gateway(gateway_code)
    session = gateway.create_checkout(invoice, customer=customer, callback_url=callback_url)
    return session


@transaction.atomic
def mark_invoice_paid(
    invoice: ProductInvoice,
    result: PaymentResult,
) -> ProductInvoice:
    if invoice.status == 'paid':
        return invoice

    invoice.status = 'paid'
    invoice.payment_gateway = result.gateway
    invoice.transaction_id = result.transaction_id or invoice.transaction_id
    invoice.payment_method = result.payment_method or invoice.payment_method
    invoice.paid_at = timezone.now()
    meta = dict(invoice.meta or {})
    meta['payment_result'] = {
        'gateway_order_id': result.gateway_order_id,
        'transaction_id': result.transaction_id,
        'raw_keys': list((result.raw or {}).keys()),
    }
    invoice.meta = meta
    invoice.save()

    sub = invoice.subscription
    if sub and sub.status in ('pending_payment', 'past_due', 'suspended', 'trial'):
        sub.status = 'active'
        if not sub.starts_at:
            sub.starts_at = timezone.now().date()
        sub.save(update_fields=['status', 'starts_at', 'updated_at'])

        _sync_legacy_tenant_limits(sub.tenant)
        if sub.plan.is_package or (sub.product_id and sub.product.code == 'channel_manager'):
            _mirror_legacy_subscription(
                sub.tenant, sub.plan, sub.billing_cycle,
                sub.starts_at, sub.ends_at,
            )

    return invoice


@transaction.atomic
def verify_and_settle(
    invoice: ProductInvoice,
    data: dict,
    *,
    gateway_code: str | None = None,
) -> tuple[ProductInvoice, PaymentResult]:
    code = gateway_code or invoice.payment_gateway or None
    gateway = get_active_gateway(code)
    result = gateway.verify_payment(data)
    if not result.success:
        invoice.status = 'failed'
        meta = dict(invoice.meta or {})
        meta['last_error'] = result.error
        invoice.meta = meta
        invoice.payment_gateway = result.gateway
        invoice.save(update_fields=['status', 'meta', 'payment_gateway', 'updated_at'])
        return invoice, result

    invoice = mark_invoice_paid(invoice, result)
    return invoice, result


def find_invoice_for_razorpay_order(order_id: str) -> ProductInvoice | None:
    return (
        ProductInvoice.objects.filter(meta__razorpay_order_id=order_id)
        .select_related('subscription', 'plan', 'tenant')
        .first()
    )


def find_invoice_for_payu_txn(txnid: str = '', invoice_id: str = '') -> ProductInvoice | None:
    if invoice_id:
        try:
            return ProductInvoice.objects.select_related(
                'subscription', 'plan', 'tenant'
            ).get(pk=int(invoice_id))
        except (ProductInvoice.DoesNotExist, ValueError, TypeError):
            pass
    if txnid:
        return (
            ProductInvoice.objects.filter(meta__payu_txnid=txnid)
            .select_related('subscription', 'plan', 'tenant')
            .first()
        )
    return None
