"""
Custom permissions for tenant management
"""
from rest_framework import permissions


class IsTenantOwner(permissions.BasePermission):
    """Check if user is tenant owner"""
    
    def has_permission(self, request, view):
        """Check if user has permission"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is tenant owner
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return request.user.role == 'owner' or request.user.is_superuser
        
        return False


class IsTenantMember(permissions.BasePermission):
    """Check if user is member of tenant"""
    
    def has_permission(self, request, view):
        """Check if user has permission"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user has tenant
        return hasattr(request.user, 'tenant') and request.user.tenant is not None


class IsTenantManager(permissions.BasePermission):
    """Check if user is tenant owner or manager"""
    
    def has_permission(self, request, view):
        """Check if user has permission"""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is owner or manager
        if hasattr(request.user, 'tenant') and request.user.tenant:
            return request.user.role in ['owner', 'manager']
        
        return False
