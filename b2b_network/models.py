"""
Stay B2B Network - Corporate/Agent portals

Secure logins, role-based access, special rate management. Dedicated B2B sales channel.
"""
from django.db import models
from django.conf import settings
from djmoney.models.fields import MoneyField
from core.models import Property, RatePlan, TimeStampedModel


class B2BAgent(TimeStampedModel):
    """Corporate partner or travel agent"""
    
    AGENT_TYPES = [
        ('CORPORATE', 'Corporate'),
        ('TRAVEL_AGENT', 'Travel Agent'),
        ('WHOLESALER', 'Wholesaler'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='b2b_agent', null=True, blank=True)
    
    company_name = models.CharField(max_length=255)
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    credit_limit = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


class B2BRatePlan(TimeStampedModel):
    """Special B2B rate for a rate plan"""
    id = models.BigAutoField(primary_key=True)
    agent = models.ForeignKey(B2BAgent, on_delete=models.CASCADE, related_name='rate_plans')
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name='b2b_rates')
    
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    net_rate = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['agent', 'rate_plan']


class CorporateAccount(TimeStampedModel):
    """Corporate account linked to properties"""
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='corporate_accounts')
    agent = models.ForeignKey(B2BAgent, on_delete=models.CASCADE, related_name='property_access')
    has_access = models.BooleanField(default=True)

    class Meta:
        unique_together = ['property', 'agent']
