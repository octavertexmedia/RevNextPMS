"""
Product catalog, commercial plans, packages, and tenant entitlements.
"""
from datetime import timedelta

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from djmoney.models.fields import MoneyField
from djmoney.money import Money


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(TimeStampedModel):
    """A billable RevNext product with its own branded host."""

    code = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    short_name = models.CharField(max_length=80)
    tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    subdomain = models.CharField(
        max_length=80, blank=True,
        help_text="Subdomain label, e.g. pms → pms.revnext.in",
    )
    primary_host = models.CharField(
        max_length=255, unique=True,
        help_text="Canonical public host, e.g. pms.revnext.in",
    )
    path_prefixes = models.JSONField(
        default=list, blank=True,
        help_text="Web URL prefixes owned by this product",
    )
    api_prefixes = models.JSONField(
        default=list, blank=True,
        help_text="API URL prefixes owned by this product",
    )
    app_label = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    is_billable = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    marketing_url = models.URLField(blank=True)

    class Meta:
        db_table = 'products'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return f'{self.short_name} ({self.primary_host})'

    def matches_path(self, path: str) -> bool:
        prefixes = list(self.path_prefixes or []) + list(self.api_prefixes or [])
        return any(path.startswith(p) for p in prefixes)


class ProductPlan(TimeStampedModel):
    """Monthly/yearly SKU for a single product (or suite package)."""

    TIER_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('growth', 'Growth'),
        ('pro', 'Pro'),
        ('scale', 'Scale'),
        ('partner', 'Partner'),
        ('network', 'Network'),
        ('suite', 'Suite Package'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='plans',
        null=True,
        blank=True,
        help_text='Null when this is a multi-product suite package',
    )
    code = models.SlugField(max_length=80, unique=True)
    display_name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='starter')

    monthly_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'),
    )
    yearly_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'),
    )

    is_package = models.BooleanField(
        default=False,
        help_text='If true, entitles all products in package_products',
    )
    package_products = models.ManyToManyField(
        Product,
        blank=True,
        related_name='packages',
        help_text='Products included when is_package=True',
    )

    limits = models.JSONField(default=dict, blank=True)
    features = models.JSONField(default=list, blank=True)

    trial_days = models.PositiveIntegerField(default=14)
    is_active = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)

    class Meta:
        db_table = 'product_plans'
        ordering = ['sort_order', 'monthly_price']

    def __str__(self):
        kind = 'package' if self.is_package else (self.product.code if self.product_id else 'orphan')
        return f'{self.display_name} [{kind}]'

    def clean(self):
        if self.is_package and self.product_id:
            raise ValidationError('Suite packages must not point at a single product FK.')
        if not self.is_package and not self.product_id:
            raise ValidationError('Non-package plans require a product.')

    def price_for(self, billing_cycle: str) -> Money:
        return self.yearly_price if billing_cycle == 'yearly' else self.monthly_price

    def entitled_product_codes(self):
        if self.is_package:
            return list(self.package_products.values_list('code', flat=True))
        if self.product_id:
            return [self.product.code]
        return []


class TenantProductSubscription(TimeStampedModel):
    """
    A tenant's paid (or trial) entitlement to a product or suite package.

    A suite subscription grants all package products via services.has_product().
    À-la-carte subscriptions grant a single product.
    """

    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('pending_payment', 'Pending payment'),
        ('active', 'Active'),
        ('past_due', 'Past due'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('suspended', 'Suspended'),
    ]
    CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='product_subscriptions',
    )
    plan = models.ForeignKey(
        ProductPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
    )
    # Denormalized product for à-la-carte; null for suite packages
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        null=True,
        blank=True,
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    billing_cycle = models.CharField(max_length=20, choices=CYCLE_CHOICES, default='monthly')
    auto_renew = models.BooleanField(default=True)

    trial_end_date = models.DateField(null=True, blank=True)
    starts_at = models.DateField(null=True, blank=True)
    ends_at = models.DateField(null=True, blank=True)

    limits_snapshot = models.JSONField(default=dict, blank=True)
    features_snapshot = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = 'tenant_product_subscriptions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['product', 'status']),
            models.Index(fields=['ends_at']),
        ]
        constraints = [
            # One active/trial/pending à-la-carte sub per tenant+product
            models.UniqueConstraint(
                fields=['tenant', 'product'],
                condition=models.Q(
                    product__isnull=False,
                    status__in=['trial', 'active', 'past_due', 'pending_payment'],
                ),
                name='uniq_active_tenant_product_sub',
            ),
        ]

    def __str__(self):
        target = self.product.code if self.product_id else self.plan.code
        return f'{self.tenant} → {target} ({self.status})'

    @property
    def is_active_now(self) -> bool:
        if self.status not in ('trial', 'active', 'past_due'):
            return False
        today = timezone.now().date()
        if self.status == 'trial' and self.trial_end_date:
            return today <= self.trial_end_date
        if self.ends_at and today > self.ends_at:
            return False
        return True

    def entitled_product_codes(self):
        return self.plan.entitled_product_codes()


class ProductInvoice(TimeStampedModel):
    """Invoice / payment record for a product or suite subscription."""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('void', 'Void'),
    ]

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='product_invoices',
    )
    subscription = models.ForeignKey(
        TenantProductSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
    )
    plan = models.ForeignKey(ProductPlan, on_delete=models.PROTECT, related_name='invoices')

    amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    billing_cycle = models.CharField(max_length=20, choices=TenantProductSubscription.CYCLE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)

    transaction_id = models.CharField(max_length=255, blank=True, db_index=True)
    payment_gateway = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    meta = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'product_invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f'Invoice {self.id} — {self.tenant} — {self.amount} ({self.status})'
