"""
Shared decorators for tenant isolation and permission checks.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def tenant_required(view_func):
    """Ensure request has a tenant. Redirect with error if not."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant = getattr(request, 'tenant', None)
        if not tenant:
            messages.error(request, 'No tenant selected. Please log in with a tenant account.')
            return redirect('tenants:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
