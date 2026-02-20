"""
Payment Gateways - PCI-DSS compliant

PayPal, Razorpay, iPay88, Airpay, PaySwiff, Ingenico. Secure payment processing.
"""
from django.db import models
from core.models import Property, TimeStampedModel


class GatewayConfig(TimeStampedModel):
    """Payment gateway configuration per property/tenant"""
    
    GATEWAYS = [
        ('razorpay', 'Razorpay'),
        ('paypal', 'PayPal'),
        ('ipay88', 'iPay88'),
        ('airpay', 'Airpay'),
        ('payswiff', 'PaySwiff'),
        ('ingenico', 'Ingenico'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='gateway_configs', null=True, blank=True)
    
    gateway_name = models.CharField(max_length=50, choices=GATEWAYS)
    is_active = models.BooleanField(default=True)
    
    # Credentials (encrypted in production)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    merchant_id = models.CharField(max_length=100, blank=True)
    
    # Config
    config = models.JSONField(default=dict, blank=True)
    
    # PCI-DSS
    pci_compliant = models.BooleanField(default=True)

    class Meta:
        unique_together = ['property', 'gateway_name']


class TransactionLog(TimeStampedModel):
    """Payment transaction log"""
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transactions')
    
    gateway = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    status = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50, blank=True)
    
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
