"""
Forms for tenant registration and authentication
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.text import slugify

from .models import Tenant, TenantUser
from core.models import Property, RoomType, RatePlan
from integrations.models import PropertyIntegration, IntegrationPlatform
from bookings.models import Reservation


class TenantRegistrationForm(forms.ModelForm):
    """Form for tenant registration"""
    
    # User account fields
    username = forms.CharField(
        max_length=150,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = forms.EmailField(required=True)
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        help_text="Your password must contain at least 8 characters."
    )
    password2 = forms.CharField(
        label="Password confirmation",
        widget=forms.PasswordInput,
        help_text="Enter the same password as before, for verification."
    )
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    
    class Meta:
        model = Tenant
        fields = ['name', 'business_name', 'email', 'phone', 'address', 'city', 'state', 'country', 'postal_code', 'gstin']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if TenantUser.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        if Tenant.objects.filter(email=email).exists():
            raise ValidationError("A tenant with this email already exists.")
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if TenantUser.objects.filter(username=username).exists():
            raise ValidationError("A user with this username already exists.")
        return username
    
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")
        if len(password1) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return password2
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        slug = slugify(name)
        if Tenant.objects.filter(slug=slug).exists():
            raise ValidationError("A tenant with a similar name already exists. Please choose a different name.")
        return name


class TenantLoginForm(forms.Form):
    """Form for tenant login"""
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'placeholder': 'Password'})


class PropertyForm(forms.ModelForm):
    """Form for adding/editing properties"""
    
    class Meta:
        model = Property
        fields = [
            'name', 'legal_name', 'property_type', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'phone', 'email', 'website',
            'timezone', 'currency', 'gstin', 'pan'
        ]
        widgets = {
            'address_line1': forms.TextInput(attrs={'class': 'form-input'}),
            'address_line2': forms.TextInput(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'legal_name': forms.TextInput(attrs={'class': 'form-input'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'state': forms.TextInput(attrs={'class': 'form-input'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'website': forms.URLInput(attrs={'class': 'form-input'}),
            'gstin': forms.TextInput(attrs={'class': 'form-input'}),
            'pan': forms.TextInput(attrs={'class': 'form-input'}),
            'property_type': forms.Select(attrs={'class': 'form-select'}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
            'timezone': forms.TextInput(attrs={'class': 'form-input'}),
            'currency': forms.TextInput(attrs={'class': 'form-input'}),
        }


class PropertyIntegrationForm(forms.ModelForm):
    """Form for adding OTA integrations"""
    
    class Meta:
        model = PropertyIntegration
        fields = [
            'property', 'platform', 'provider_property_id',
            'sync_availability', 'sync_rates', 'sync_inventory', 'sync_reservations',
            'availability_sync_interval', 'rates_sync_interval',
            'inventory_sync_interval', 'reservations_sync_interval',
            'is_active'
        ]
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'provider_property_id': forms.TextInput(attrs={'class': 'form-input'}),
            'sync_availability': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'sync_rates': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'sync_inventory': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'sync_reservations': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'availability_sync_interval': forms.NumberInput(attrs={'class': 'form-input'}),
            'rates_sync_interval': forms.NumberInput(attrs={'class': 'form-input'}),
            'inventory_sync_interval': forms.NumberInput(attrs={'class': 'form-input'}),
            'reservations_sync_interval': forms.NumberInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['property'].queryset = Property.objects.filter(tenant=tenant, is_active=True)
        self.fields['platform'].queryset = IntegrationPlatform.objects.filter(is_active=True)


class ReservationForm(forms.ModelForm):
    """Form for creating reservations"""
    
    class Meta:
        model = Reservation
        fields = [
            'property', 'room_type', 'rate_plan', 'guest_name', 'guest_email',
            'guest_phone', 'check_in', 'check_out', 'adults', 'children',
            'base_room_rate', 'total_amount', 'status', 'special_requests'
        ]
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'rate_plan': forms.Select(attrs={'class': 'form-select'}),
            'guest_name': forms.TextInput(attrs={'class': 'form-input'}),
            'guest_email': forms.EmailInput(attrs={'class': 'form-input'}),
            'guest_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'check_in': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'check_out': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'adults': forms.NumberInput(attrs={'class': 'form-input'}),
            'children': forms.NumberInput(attrs={'class': 'form-input'}),
            'base_room_rate': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'special_requests': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['property'].queryset = Property.objects.filter(tenant=tenant, is_active=True)
            # Room types and rate plans will be filtered dynamically via JavaScript or we can filter here
            self.fields['room_type'].queryset = RoomType.objects.filter(property__tenant=tenant, is_active=True)
            self.fields['rate_plan'].queryset = RatePlan.objects.filter(property__tenant=tenant, is_active=True)


class RoomTypeForm(forms.ModelForm):
    """Form for adding/editing room types"""
    
    class Meta:
        model = RoomType
        fields = [
            'property', 'name', 'description', 'max_occupancy', 'base_occupancy',
            'max_adults', 'max_children', 'size_sqm', 'bed_type', 'amenities', 'is_active'
        ]
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea'}),
            'max_occupancy': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'base_occupancy': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'max_adults': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'max_children': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'size_sqm': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': 0}),
            'bed_type': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., King, Queen, Twin'}),
            'amenities': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea', 'placeholder': 'Enter amenities separated by commas (e.g., wifi, ac, tv, minibar)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['property'].queryset = Property.objects.filter(tenant=tenant, is_active=True)
    
    def clean_amenities(self):
        """Convert comma-separated amenities string to list"""
        amenities = self.cleaned_data.get('amenities')
        if isinstance(amenities, str):
            # Split by comma and clean up
            amenities_list = [a.strip() for a in amenities.split(',') if a.strip()]
            return amenities_list
        return amenities or []
