"""
Cloud PMS Forms
"""
from django import forms
from .models import Folio, FolioLineItem, HousekeepingTask, LinkedRoomUnit


class FolioForm(forms.ModelForm):
    """Create/Edit Folio"""
    
    class Meta:
        model = Folio
        fields = ['property', 'guest_name', 'guest_email', 'room_number', 'reservation']
        widgets = {
            'guest_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Guest name'}),
            'guest_email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'guest@example.com'}),
            'room_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Room 101'}),
            'property': forms.Select(attrs={'class': 'form-select'}),
            'reservation': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['property'].queryset = self.fields['property'].queryset.filter(tenant=self.tenant, is_active=True)
            try:
                from bookings.models import Reservation
                self.fields['reservation'].queryset = Reservation.objects.filter(property__tenant=self.tenant).order_by('-check_in')[:100]
            except Exception:
                self.fields['reservation'].queryset = self.fields['reservation'].queryset.none()
        self.fields['reservation'].required = False
        self.fields['guest_email'].required = False


class FolioLineItemForm(forms.ModelForm):
    """Add line item to Folio"""
    
    class Meta:
        model = FolioLineItem
        fields = ['item_type', 'description', 'amount', 'quantity']
        widgets = {
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Description'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'value': 1}),
        }


class HousekeepingTaskForm(forms.ModelForm):
    """Create/Edit Housekeeping Task"""
    
    class Meta:
        model = HousekeepingTask
        fields = ['property', 'room_number', 'room_type', 'task_type', 'description', 'priority', 'assigned_to', 'due_date']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '101'}),
            'task_type': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Cleaning', 'value': 'Cleaning'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Optional notes'}),
            'assigned_to': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Staff name'}),
            'due_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'property': forms.Select(attrs={'class': 'form-select'}),
            'room_type': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['property'].queryset = self.fields['property'].queryset.filter(tenant=self.tenant, is_active=True)
            self.fields['room_type'].queryset = self.fields['room_type'].queryset.filter(property__tenant=self.tenant)
        self.fields['room_type'].required = False
        self.fields['due_date'].required = False


class LinkedRoomUnitForm(forms.ModelForm):
    """Create/Edit Linked Room Unit"""
    
    class Meta:
        model = LinkedRoomUnit
        fields = ['property', 'name', 'total_rooms', 'sell_as_whole', 'whole_unit_price_multiplier', 'room_types', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Villa A'}),
            'total_rooms': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'property': forms.Select(attrs={'class': 'form-select'}),
            'room_types': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if self.tenant:
            self.fields['property'].queryset = self.fields['property'].queryset.filter(tenant=self.tenant, is_active=True)
            self.fields['room_types'].queryset = self.fields['room_types'].queryset.filter(property__tenant=self.tenant)
