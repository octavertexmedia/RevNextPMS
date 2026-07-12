"""
Payment Gateways - PCI-DSS compliant

PayPal, Razorpay, PayU, iPay88, Airpay, PaySwiff, Ingenico.
Secrets prefer OpenBao (`secret_ref`); DB fields are local fallback only.
"""
from django.db import models
from core.models import Property, TimeStampedModel


class GatewayConfig(TimeStampedModel):
    """Payment gateway configuration per property/tenant"""

    GATEWAYS = [
        ('razorpay', 'Razorpay'),
        ('payu', 'PayU'),
        ('paypal', 'PayPal'),
        ('ipay88', 'iPay88'),
        ('airpay', 'Airpay'),
        ('payswiff', 'PaySwiff'),
        ('ingenico', 'Ingenico'),
    ]

    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name='gateway_configs', null=True, blank=True,
    )

    gateway_name = models.CharField(max_length=50, choices=GATEWAYS)
    is_active = models.BooleanField(default=True)

    # Local fallback credentials (prefer OpenBao via secret_ref)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    merchant_id = models.CharField(max_length=100, blank=True)

    secret_ref = models.CharField(
        max_length=255,
        blank=True,
        help_text='OpenBao KV path, e.g. revnext/tenants/1/properties/2/gateways/razorpay',
    )

    config = models.JSONField(default=dict, blank=True)
    pci_compliant = models.BooleanField(default=True)

    class Meta:
        unique_together = ['property', 'gateway_name']

    def ensure_secret_ref(self):
        if self.secret_ref or not self.property_id:
            return self.secret_ref
        tenant_id = self.property.tenant_id
        if not tenant_id:
            return ''
        from channel_manager.openbao.credentials import openbao_path_for_gateway
        self.secret_ref = openbao_path_for_gateway(tenant_id, self.property_id, self.gateway_name)
        return self.secret_ref

    def resolved_credentials(self) -> dict:
        """Credentials with OpenBao overlay when enabled."""
        from channel_manager.openbao.credentials import resolve_mapping
        self.ensure_secret_ref()
        return resolve_mapping(
            secret_ref=self.secret_ref,
            local={
                'api_key': self.api_key,
                'api_secret': self.api_secret,
                'merchant_id': self.merchant_id,
                **(self.config or {}),
            },
            keys=['api_key', 'api_secret', 'merchant_id', 'webhook_secret', 'key_id', 'salt'],
        )

    def sync_secrets_to_openbao(self, *, clear_local: bool = False) -> bool:
        """Push local credentials to OpenBao; optionally blank local copies."""
        from channel_manager.openbao.credentials import write_path
        from channel_manager.openbao.loader import is_enabled
        if not is_enabled():
            return False
        path = self.ensure_secret_ref()
        if not path:
            return False
        payload = {
            'api_key': self.api_key,
            'api_secret': self.api_secret,
            'merchant_id': self.merchant_id,
        }
        ok = write_path(path, {k: v for k, v in payload.items() if v}, merge=True)
        if ok and clear_local:
            self.api_key = ''
            self.api_secret = ''
            self.merchant_id = ''
            self.save(update_fields=['api_key', 'api_secret', 'merchant_id', 'secret_ref', 'updated_at'])
        elif ok and self.secret_ref:
            self.save(update_fields=['secret_ref', 'updated_at'])
        return ok


class TransactionLog(TimeStampedModel):
    """Payment transaction log"""
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(
        Property, on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transactions',
    )

    gateway = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255, db_index=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')

    status = models.CharField(max_length=50)
    payment_method = models.CharField(max_length=50, blank=True)

    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
