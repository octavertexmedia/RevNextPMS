"""
RBAC helpers for other apps.

Usage on a viewset:
    from rbac.mixins import RbacQuerysetMixin, RbacCapabilityMixin

    class ReservationViewSet(RbacCapabilityMixin, RbacQuerysetMixin, viewsets.ModelViewSet):
        property_fk = 'property'
        capability_map = {
            'list': 'reservations.view',
            'create': 'reservations.create',
            ...
        }
"""
from rbac.permissions import HasCapability
from rbac.services import filter_by_property_fk, filter_properties_for_user


class RbacCapabilityMixin:
    """Adds HasCapability to permission_classes if not already present."""

    def get_permissions(self):
        perms = super().get_permissions()
        if not any(isinstance(p, HasCapability) for p in perms):
            perms.append(HasCapability())
        return perms


class RbacQuerysetMixin:
    """
    Filters queryset by RBAC property scope.

    Set property_fk = 'property' (default) or property_fk = None for Property model itself.
    """
    property_fk = 'property'

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if self.property_fk is None:
            return filter_properties_for_user(qs, user)
        return filter_by_property_fk(qs, user, property_field=self.property_fk)
