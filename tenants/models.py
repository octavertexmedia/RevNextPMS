"""
Multi-Tenant Models for Channel Manager

Each hotel owner/operator is a tenant with isolated data.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
from djmoney.models.fields import MoneyField
from djmoney.money import Money


class SubscriptionPlan(models.Model):
    """Predefined subscription plans"""
    
    PLAN_TYPES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=50, choices=PLAN_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Pricing
    monthly_price = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    yearly_price = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    
    # Limits
    max_properties = models.PositiveIntegerField(default=1)
    max_integrations_per_property = models.PositiveIntegerField(default=5)
    max_users = models.PositiveIntegerField(default=1)
    max_api_calls_per_month = models.PositiveIntegerField(default=1000)
    
    # Features
    features = models.JSONField(
        default=list,
        help_text="List of features, e.g., ['real_time_sync', 'api_access', 'priority_support']"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_visible = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'
        ordering = ['monthly_price']
    
    def __str__(self):
        return self.display_name


class Tenant(models.Model):
    """Hotel owner/operator - represents a tenant in the multi-tenant system"""
    
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Hotel owner/company name")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly identifier")
    
    # Contact Information
    email = models.EmailField(unique=True)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        blank=True
    )
    
    # Business Details
    business_name = models.CharField(max_length=255, blank=True)
    gstin = models.CharField(max_length=15, blank=True, help_text="GST Identification Number")
    pan = models.CharField(max_length=10, blank=True, help_text="Permanent Account Number")
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='India')
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Subscription & Status
    is_active = models.BooleanField(default=True)
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tenants',
        help_text="Current subscription plan"
    )
    subscription_start_date = models.DateField(null=True, blank=True)
    subscription_end_date = models.DateField(null=True, blank=True)
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('trial', 'Trial'),
            ('active', 'Active'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
            ('suspended', 'Suspended'),
        ],
        default='trial'
    )
    trial_end_date = models.DateField(null=True, blank=True, help_text="End date of trial period (14 days)")
    
    # Payment Information
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('credit_card', 'Credit Card'),
            ('debit_card', 'Debit Card'),
            ('upi', 'UPI'),
            ('net_banking', 'Net Banking'),
            ('bank_transfer', 'Bank Transfer'),
        ],
        blank=True
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )
    auto_renew = models.BooleanField(default=True, help_text="Automatically renew subscription")
    
    # Limits based on subscription (cached from plan)
    max_properties = models.PositiveIntegerField(default=1, help_text="Maximum number of properties allowed")
    max_integrations_per_property = models.PositiveIntegerField(default=5, help_text="Maximum OTA integrations per property")
    max_users = models.PositiveIntegerField(default=1, help_text="Maximum number of users")
    max_api_calls_per_month = models.PositiveIntegerField(default=1000, help_text="Maximum API calls per month")
    
    # Usage tracking
    api_calls_this_month = models.PositiveIntegerField(default=0)
    api_calls_reset_date = models.DateField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['subscription_status']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Update limits when subscription plan changes"""
        if self.subscription_plan:
            self.max_properties = self.subscription_plan.max_properties
            self.max_integrations_per_property = self.subscription_plan.max_integrations_per_property
            self.max_users = self.subscription_plan.max_users
            self.max_api_calls_per_month = self.subscription_plan.max_api_calls_per_month
        super().save(*args, **kwargs)
    
    @property
    def property_count(self):
        """Get the number of properties for this tenant"""
        return self.properties.filter(is_active=True).count()
    
    @property
    def user_count(self):
        """Get the number of users for this tenant"""
        return self.users.filter(is_active=True).count()
    
    @property
    def is_subscription_active(self):
        """Check if subscription is currently active"""
        if self.subscription_status == 'trial':
            if self.trial_end_date:
                return timezone.now().date() <= self.trial_end_date
            return True
        elif self.subscription_status == 'active':
            if not self.subscription_end_date:
                return True
            return timezone.now().date() <= self.subscription_end_date
        return False
    
    @property
    def days_until_expiry(self):
        """Get days until subscription expires"""
        if self.subscription_status == 'trial' and self.trial_end_date:
            delta = self.trial_end_date - timezone.now().date()
            return max(0, delta.days)
        elif self.subscription_end_date:
            delta = self.subscription_end_date - timezone.now().date()
            return max(0, delta.days)
        return None
    
    def can_add_property(self):
        """Check if tenant can add more properties"""
        if not self.is_subscription_active:
            return False
        return self.property_count < self.max_properties
    
    def can_add_user(self):
        """Check if tenant can add more users"""
        if not self.is_subscription_active:
            return False
        return self.user_count < self.max_users
    
    def can_add_integration(self, property_obj):
        """Check if tenant can add more integrations to a property"""
        if not self.is_subscription_active:
            return False
        from integrations.models import PropertyIntegration
        integration_count = PropertyIntegration.objects.filter(
            property=property_obj,
            property__tenant=self,
            is_active=True
        ).count()
        return integration_count < self.max_integrations_per_property
    
    def can_make_api_call(self):
        """Check if tenant can make API calls"""
        if not self.is_subscription_active:
            return False
        
        # Reset counter if new month
        today = timezone.now().date()
        if not self.api_calls_reset_date or self.api_calls_reset_date < today:
            self.api_calls_this_month = 0
            # Set reset date to first of next month
            if today.month == 12:
                self.api_calls_reset_date = today.replace(year=today.year + 1, month=1, day=1)
            else:
                self.api_calls_reset_date = today.replace(month=today.month + 1, day=1)
            self.save(update_fields=['api_calls_reset_date', 'api_calls_this_month'])
        
        return self.api_calls_this_month < self.max_api_calls_per_month
    
    def record_api_call(self):
        """Record an API call"""
        if self.can_make_api_call():
            self.api_calls_this_month += 1
            self.save(update_fields=['api_calls_this_month'])
            return True
        return False
    
    def start_trial(self, days=14):
        """Start a trial period"""
        self.subscription_status = 'trial'
        self.trial_end_date = timezone.now().date() + timedelta(days=days)
        self.save(update_fields=['subscription_status', 'trial_end_date'])
    
    def upgrade_subscription(self, plan, billing_cycle='monthly'):
        """Upgrade to a subscription plan"""
        self.subscription_plan = plan
        self.billing_cycle = billing_cycle
        self.subscription_status = 'active'
        self.subscription_start_date = timezone.now().date()
        
        if billing_cycle == 'monthly':
            self.subscription_end_date = timezone.now().date() + timedelta(days=30)
        else:
            self.subscription_end_date = timezone.now().date() + timedelta(days=365)
        
        # Update limits from plan
        self.max_properties = plan.max_properties
        self.max_integrations_per_property = plan.max_integrations_per_property
        self.max_users = plan.max_users
        self.max_api_calls_per_month = plan.max_api_calls_per_month
        
        self.save()
    
    def cancel_subscription(self):
        """Cancel subscription"""
        self.subscription_status = 'cancelled'
        self.auto_renew = False
        self.save(update_fields=['subscription_status', 'auto_renew'])


class SubscriptionPayment(models.Model):
    """Track subscription payments"""
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    
    # Payment Details
    amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    billing_cycle = models.CharField(max_length=20, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')])
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Transaction Details
    transaction_id = models.CharField(max_length=255, unique=True, blank=True)
    payment_gateway = models.CharField(max_length=50, blank=True, help_text="e.g., razorpay, payu, stripe")
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Dates
    payment_date = models.DateTimeField(null=True, blank=True)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'subscription_payments'
        verbose_name = 'Subscription Payment'
        verbose_name_plural = 'Subscription Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'payment_status']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.amount} - {self.get_payment_status_display()}"


class TenantUser(AbstractUser):
    """Extended User model with tenant relationship"""
    
    # Use default AutoField for primary key (inherited from AbstractUser)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        help_text="The tenant/hotel owner this user belongs to"
    )
    
    # Additional user fields
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        blank=True
    )
    role = models.CharField(
        max_length=50,
        choices=[
            ('owner', 'Owner'),
            ('manager', 'Manager'),
            ('staff', 'Staff'),
            ('viewer', 'Viewer'),
        ],
        default='staff'
    )
    
    # Profile
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    timezone = models.CharField(max_length=50, default='Asia/Kolkata')
    language = models.CharField(max_length=10, default='en')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tenant_users'
        verbose_name = 'Tenant User'
        verbose_name_plural = 'Tenant Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        if self.tenant:
            return f"{self.username} ({self.tenant.name})"
        return self.username
    
    @property
    def is_owner(self):
        """Check if user is the tenant owner"""
        return self.role == 'owner'
    
    @property
    def is_manager(self):
        """Check if user is a manager"""
        return self.role in ['owner', 'manager']
    
    def has_tenant_access(self, tenant):
        """Check if user has access to a specific tenant"""
        return self.tenant == tenant or self.is_superuser
