"""
Cloud POS Forms
"""
from django import forms
from .models import MenuCategory, MenuItem, POSTable, POSOrder, POSOrderItem


class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ['property', 'name', 'icon', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Starters'}),
            'icon': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'burgers'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-input', 'value': 0}),
            'property': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['property'].queryset = self.fields['property'].queryset.filter(tenant=tenant, is_active=True)


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'category', 'name', 'description', 'price', 'image_url',
            'is_available', 'track_inventory', 'stock_qty', 'low_stock_at',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 2}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'image_url': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://…'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'stock_qty': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'low_stock_at': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['category'].queryset = MenuCategory.objects.filter(property__tenant=tenant)


class POSTableForm(forms.ModelForm):
    class Meta:
        model = POSTable
        fields = ['property', 'name', 'capacity', 'section']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Table 1'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-input', 'value': 4}),
            'section': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Main hall'}),
            'property': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['property'].queryset = self.fields['property'].queryset.filter(tenant=tenant, is_active=True)


class POSOrderForm(forms.ModelForm):
    class Meta:
        model = POSOrder
        fields = [
            'property', 'table', 'order_type', 'channel',
            'guest_name', 'guest_phone', 'delivery_address',
            'bill_to_room', 'room_number', 'folio',
        ]
        widgets = {
            'property': forms.Select(attrs={'class': 'form-select'}),
            'table': forms.Select(attrs={'class': 'form-select'}),
            'order_type': forms.Select(attrs={'class': 'form-select'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'guest_name': forms.TextInput(attrs={'class': 'form-input'}),
            'guest_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-input form-textarea', 'rows': 2}),
            'bill_to_room': forms.CheckboxInput(attrs={'class': 'form-checkbox h-4 w-4 text-indigo-600'}),
            'room_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '101'}),
            'folio': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        tenant = kwargs.pop('tenant', None)
        property_id = kwargs.pop('property_id', None)
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields['property'].queryset = self.fields['property'].queryset.filter(tenant=tenant, is_active=True)
            self.fields['table'].queryset = POSTable.objects.filter(property__tenant=tenant)
            from cloud_pms.models import Folio
            self.fields['folio'].queryset = Folio.objects.filter(property__tenant=tenant, status='OPEN')
        if property_id:
            self.fields['property'].initial = property_id
            self.fields['table'].queryset = self.fields['table'].queryset.filter(property_id=property_id)
        self.fields['table'].required = False
        self.fields['folio'].required = False
        self.fields['room_number'].required = False
    
    def clean(self):
        data = super().clean()
        bill_to_room = data.get('bill_to_room')
        order_type = data.get('order_type') or 'DINE_IN'
        if bill_to_room:
            if not data.get('folio'):
                self.add_error('folio', 'Select a folio when billing to room.')
        elif order_type == 'DINE_IN' and not data.get('table'):
            self.add_error('table', 'Select a table for dine-in orders.')
        return data


class POSOrderItemForm(forms.ModelForm):
    class Meta:
        model = POSOrderItem
        fields = ['menu_item', 'quantity']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'value': 1}),
        }
    
    def __init__(self, *args, **kwargs):
        order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        if order and order.property_id:
            self.fields['menu_item'].queryset = MenuItem.objects.filter(
                category__property_id=order.property_id, is_available=True
            ).select_related('category').order_by('category__display_order', 'name')
