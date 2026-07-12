"""
Entitlement & subscription service for multi-product billing.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Iterable, Optional, Set

from django.db import transaction
from django.utils import timezone
from djmoney.money import Money

from .models import Product, ProductInvoice, ProductPlan, TenantProductSubscription


ACTIVE_STATUSES = ('trial', 'active', 'past_due')


def get_product_by_host(host: str) -> Optional[Product]:
    from .catalog import HOST_ALIASES

    host = (host or '').split(':')[0].lower().strip()
    code = HOST_ALIASES.get(host)
    if code:
        try:
            return Product.objects.get(code=code, is_active=True)
        except Product.DoesNotExist:
            return None
    # Fall back to primary_host match
    try:
        return Product.objects.get(primary_host=host, is_active=True)
    except Product.DoesNotExist:
        return None


def get_product_for_path(path: str) -> Optional[Product]:
    for product in Product.objects.filter(is_active=True).order_by('sort_order'):
        if product.matches_path(path):
            return product
    return None


def active_subscriptions(tenant) -> Iterable[TenantProductSubscription]:
    if not tenant:
        return TenantProductSubscription.objects.none()
    today = timezone.now().date()
    qs = TenantProductSubscription.objects.filter(
        tenant=tenant,
        status__in=ACTIVE_STATUSES,
    ).select_related('plan', 'product').prefetch_related('plan__package_products')
    # Exclude ended
    return [
        s for s in qs
        if (s.status != 'trial' or not s.trial_end_date or s.trial_end_date >= today)
        and (not s.ends_at or s.ends_at >= today)
    ]


def entitled_product_codes(tenant) -> Set[str]:
    codes: Set[str] = set()
    for sub in active_subscriptions(tenant):
        codes.update(sub.entitled_product_codes())
    return codes


def has_product(tenant, product_code: str) -> bool:
    if not tenant:
        return False
    if product_code in entitled_product_codes(tenant):
        return True
    # Legacy bridge: active Channel Manager-era subscription unlocks CM
    if product_code == 'channel_manager' and getattr(tenant, 'is_subscription_active', False):
        return True
    return False


def tenant_entitlements_summary(tenant) -> dict:
    subs = active_subscriptions(tenant)
    return {
        'products': sorted(entitled_product_codes(tenant)),
        'subscriptions': [
            {
                'id': s.id,
                'plan': s.plan.code,
                'plan_name': s.plan.display_name,
                'is_package': s.plan.is_package,
                'product': s.product.code if s.product_id else None,
                'status': s.status,
                'billing_cycle': s.billing_cycle,
                'starts_at': s.starts_at,
                'ends_at': s.ends_at,
                'trial_end_date': s.trial_end_date,
                'entitles': s.entitled_product_codes(),
            }
            for s in subs
        ],
    }


@transaction.atomic
def start_product_trial(tenant, plan: ProductPlan, days: Optional[int] = None) -> TenantProductSubscription:
    days = days if days is not None else plan.trial_days
    today = timezone.now().date()
    product = None if plan.is_package else plan.product

    # Cancel overlapping à-la-carte for same product
    if product:
        TenantProductSubscription.objects.filter(
            tenant=tenant, product=product, status__in=ACTIVE_STATUSES,
        ).update(status='cancelled', auto_renew=False)

    sub = TenantProductSubscription.objects.create(
        tenant=tenant,
        plan=plan,
        product=product,
        status='trial',
        billing_cycle='monthly',
        trial_end_date=today + timedelta(days=days),
        starts_at=today,
        ends_at=today + timedelta(days=days),
        limits_snapshot=plan.limits or {},
        features_snapshot=plan.features or [],
        notes='Trial started',
    )
    _sync_legacy_tenant_limits(tenant)
    return sub


@transaction.atomic
def subscribe(
    tenant,
    plan: ProductPlan,
    billing_cycle: str = 'monthly',
    *,
    mark_paid: bool = False,
    payment_gateway: str = '',
    transaction_id: str = '',
    actor=None,
) -> tuple[TenantProductSubscription, ProductInvoice]:
    """
    Create/replace a product or suite subscription and draft an invoice.

    mark_paid=True completes the invoice immediately (admin / offline payment).
    """
    if billing_cycle not in ('monthly', 'yearly'):
        raise ValueError('billing_cycle must be monthly or yearly')

    today = timezone.now().date()
    period_days = 365 if billing_cycle == 'yearly' else 30
    ends = today + timedelta(days=period_days)
    product = None if plan.is_package else plan.product
    amount = plan.price_for(billing_cycle)

    if product:
        TenantProductSubscription.objects.filter(
            tenant=tenant, product=product, status__in=ACTIVE_STATUSES,
        ).update(status='cancelled', auto_renew=False)
    elif plan.is_package:
        # Suite replaces overlapping product subs optionally — keep them but suite covers all
        pass

    sub = TenantProductSubscription.objects.create(
        tenant=tenant,
        plan=plan,
        product=product,
        status='active' if mark_paid else 'pending_payment',
        billing_cycle=billing_cycle,
        auto_renew=True,
        starts_at=today,
        ends_at=ends,
        trial_end_date=None,
        limits_snapshot=plan.limits or {},
        features_snapshot=plan.features or [],
        notes=f'Subscribed by {getattr(actor, "username", "system")}' if actor else '',
    )

    invoice = ProductInvoice.objects.create(
        tenant=tenant,
        subscription=sub,
        plan=plan,
        amount=amount,
        billing_cycle=billing_cycle,
        status='paid' if mark_paid else 'pending',
        period_start=today,
        period_end=ends,
        payment_gateway=payment_gateway,
        transaction_id=transaction_id,
        paid_at=timezone.now() if mark_paid else None,
        meta={'actor_id': getattr(actor, 'id', None)},
    )

    # Keep legacy Tenant.subscription_* roughly in sync for Channel Manager primary
    if mark_paid:
        _sync_legacy_tenant_limits(tenant)
        if plan.is_package or (product and product.code == 'channel_manager'):
            _mirror_legacy_subscription(tenant, plan, billing_cycle, today, ends)

    return sub, invoice


def cancel_subscription(sub: TenantProductSubscription, *, at_period_end: bool = True) -> TenantProductSubscription:
    sub.auto_renew = False
    if at_period_end:
        sub.notes = (sub.notes + '\n' if sub.notes else '') + 'Cancel at period end'
        sub.save(update_fields=['auto_renew', 'notes', 'updated_at'])
    else:
        sub.status = 'cancelled'
        sub.save(update_fields=['status', 'auto_renew', 'updated_at'])
    return sub


def _sync_legacy_tenant_limits(tenant):
    """Roll up max limits from all active product subscriptions onto Tenant."""
    limits = {
        'max_properties': tenant.max_properties or 1,
        'max_integrations_per_property': tenant.max_integrations_per_property or 5,
        'max_users': tenant.max_users or 1,
        'max_api_calls_per_month': tenant.max_api_calls_per_month or 1000,
    }
    for sub in active_subscriptions(tenant):
        for key in limits:
            val = (sub.limits_snapshot or {}).get(key)
            if isinstance(val, int):
                limits[key] = max(limits[key], val)
    for key, val in limits.items():
        setattr(tenant, key, val)
    tenant.save(update_fields=list(limits.keys()) + ['updated_at'])


def _mirror_legacy_subscription(tenant, plan, billing_cycle, start, end):
    """Best-effort bridge to legacy SubscriptionPlan for CM-era middleware."""
    from tenants.models import SubscriptionPlan

    legacy_name = {
        'starter': 'basic',
        'growth': 'professional',
        'pro': 'professional',
        'scale': 'enterprise',
        'suite': 'enterprise',
        'partner': 'professional',
        'network': 'enterprise',
    }.get(plan.tier, 'basic')
    legacy = SubscriptionPlan.objects.filter(name=legacy_name, is_active=True).first()
    if not legacy:
        return
    tenant.subscription_plan = legacy
    tenant.billing_cycle = billing_cycle
    tenant.subscription_status = 'active'
    tenant.subscription_start_date = start
    tenant.subscription_end_date = end
    tenant.save(update_fields=[
        'subscription_plan', 'billing_cycle', 'subscription_status',
        'subscription_start_date', 'subscription_end_date', 'updated_at',
    ])
