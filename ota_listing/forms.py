"""
OTA Listing Forms
"""
from django import forms
from .models import ListingProject


class ListingProjectForm(forms.ModelForm):
    """Listing project create/edit"""
    class Meta:
        model = ListingProject
        fields = ['property', 'platform', 'status', 'provider_property_id', 'listing_score', 'optimization_notes']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'provider_property_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'OTA property ID'}),
            'listing_score': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'max': 100}),
            'optimization_notes': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            from core.models import Property
            from integrations.models import IntegrationPlatform
            self.fields['property'].queryset = Property.objects.filter(tenant=tenant, is_active=True)
            self.fields['platform'].queryset = IntegrationPlatform.objects.filter(is_active=True)
