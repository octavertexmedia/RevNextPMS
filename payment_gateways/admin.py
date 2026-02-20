from django.contrib import admin
from .models import GatewayConfig, TransactionLog


@admin.register(GatewayConfig)
class GatewayConfigAdmin(admin.ModelAdmin):
    list_display = ['property', 'gateway_name', 'is_active', 'pci_compliant']


@admin.register(TransactionLog)
class TransactionLogAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'property', 'gateway', 'amount', 'currency', 'status', 'created_at']
