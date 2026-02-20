"""
Google Hotel Ads Forms
"""
from django import forms
from .models import HotelAdsConfig


class HotelAdsConfigForm(forms.ModelForm):
    """Google Hotel Ads config create/edit"""
    class Meta:
        model = HotelAdsConfig
        fields = ['property', 'google_hotel_id', 'partner_hotel_id', 'is_enabled', 'commission_model']
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'google_hotel_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Google Hotel ID'}),
            'partner_hotel_id': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Partner Hotel ID'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-checkbox h-4 w-4 text-indigo-600'}),
            'commission_model': forms.Select(attrs={'class': 'form-select'}, choices=[('pay_per_conversion', 'Pay Per Conversion'), ('cpc', 'Cost Per Click')]),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            from core.models import Property
            qs = Property.objects.filter(tenant=tenant, is_active=True)
            if not (self.instance and self.instance.pk):
                existing = HotelAdsConfig.objects.filter(property__tenant=tenant).values_list('property_id', flat=True)
                qs = qs.exclude(id__in=existing)
            self.fields['property'].queryset = qs
