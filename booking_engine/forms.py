"""
Booking Engine Forms
"""
from django import forms
from datetime import date, timedelta


CURRENCY_CHOICES = [('INR', 'INR (₹)'), ('USD', 'USD ($)'), ('EUR', 'EUR (€)'), ('GBP', 'GBP (£)')]


class AvailabilityForm(forms.Form):
    """Check availability - property, dates"""
    property = forms.ModelChoiceField(
        queryset=None,
        empty_label='Select property',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    check_in = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )
    check_out = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'})
    )
    adults = forms.IntegerField(min_value=1, max_value=10, initial=1, widget=forms.NumberInput(attrs={'class': 'form-input'}))
    children = forms.IntegerField(min_value=0, max_value=10, initial=0, widget=forms.NumberInput(attrs={'class': 'form-input'}))
    display_currency = forms.ChoiceField(choices=CURRENCY_CHOICES, initial='INR', widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            from core.models import Property
            self.fields['property'].queryset = Property.objects.filter(tenant=tenant, is_active=True)

    def clean(self):
        data = super().clean()
        ci = data.get('check_in')
        co = data.get('check_out')
        if ci and co:
            if co <= ci:
                self.add_error('check_out', 'Check-out must be after check-in.')
            elif ci < date.today():
                self.add_error('check_in', 'Check-in cannot be in the past.')
        return data


class GuestDetailsForm(forms.Form):
    """Guest details for booking"""
    guest_name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full name'}))
    guest_email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@example.com'}))
    guest_phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone'}))
