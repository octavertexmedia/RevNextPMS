"""
Payment Gateways Forms
"""
from django import forms
from .models import GatewayConfig


class GatewayConfigForm(forms.ModelForm):
    """Payment gateway config create/edit"""
    class Meta:
        model = GatewayConfig
        fields = [
            'property', 'gateway_name', 'is_active',
            'api_key', 'api_secret', 'merchant_id', 'secret_ref', 'pci_compliant',
        ]
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'gateway_name': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox h-4 w-4 text-indigo-600'}),
            'api_key': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'API Key (fallback)', 'type': 'password', 'autocomplete': 'off'}),
            'api_secret': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'API Secret (fallback)', 'type': 'password', 'autocomplete': 'off'}),
            'merchant_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Merchant ID'}),
            'secret_ref': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'OpenBao path e.g. revnext/tenants/1/properties/2/gateways/razorpay',
            }),
            'pci_compliant': forms.CheckboxInput(attrs={'class': 'form-checkbox h-4 w-4 text-indigo-600'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            from core.models import Property
            self.fields['property'].queryset = Property.objects.filter(tenant=tenant, is_active=True)
        self.fields['property'].required = False
