"""
Mixins for tenant-aware admin and views
"""
from django.contrib import admin
from django.core.exceptions import PermissionDenied


class TenantFilterMixin:
    """
    Mixin to automatically filter querysets by tenant
    """
    
    def get_queryset(self, request):
        """Filter queryset by tenant"""
        qs = super().get_queryset(request)
        
        # Superusers can see all
        if request.user.is_superuser:
            return qs
        
        # Filter by tenant if user has one
        if hasattr(request.user, 'tenant') and request.user.tenant:
            if hasattr(qs.model, 'tenant'):
                return qs.filter(tenant=request.user.tenant)
            elif hasattr(qs.model, 'property'):
                # For models related to Property, filter by property's tenant
                return qs.filter(property__tenant=request.user.tenant)
            elif hasattr(qs.model, 'reservation'):
                # For models related to Reservation, filter by reservation's property's tenant
                return qs.filter(reservation__property__tenant=request.user.tenant)
        
        # If no tenant, return empty queryset
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """Automatically set tenant when saving"""
        # Superusers can set tenant manually
        if request.user.is_superuser:
            super().save_model(request, obj, form, change)
            return
        
        # Auto-set tenant for non-superusers
        if hasattr(request.user, 'tenant') and request.user.tenant:
            if hasattr(obj, 'tenant') and not obj.tenant:
                obj.tenant = request.user.tenant
            elif hasattr(obj, 'property') and obj.property:
                # Ensure property belongs to user's tenant
                if obj.property.tenant != request.user.tenant:
                    raise PermissionDenied("You don't have permission to modify this property.")
        
        super().save_model(request, obj, form, change)
    
    def get_form(self, request, obj=None, **kwargs):
        """Filter form fields based on tenant"""
        form = super().get_form(request, obj, **kwargs)
        
        # For non-superusers, restrict tenant field
        if not request.user.is_superuser:
            if 'tenant' in form.base_fields:
                form.base_fields['tenant'].queryset = form.base_fields['tenant'].queryset.filter(
                    id=request.user.tenant.id
                ) if hasattr(request.user, 'tenant') and request.user.tenant else form.base_fields['tenant'].queryset.none()
                form.base_fields['tenant'].widget = admin.widgets.HiddenInput()
        
        return form
