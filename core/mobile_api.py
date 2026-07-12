"""Shared helpers for tenant-scoped mobile APIs."""


def tenant_from_user(user):
    if getattr(user, 'is_superuser', False):
        return None
    return getattr(user, 'tenant', None)


def property_tenant_qs(qs, user, property_field='property'):
    """Filter a queryset that has a FK to Property by the user's tenant."""
    if user.is_superuser:
        return qs
    tenant = tenant_from_user(user)
    if not tenant:
        return qs.none()
    return qs.filter(**{f'{property_field}__tenant': tenant})
