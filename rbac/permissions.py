"""
DRF permission classes for capability-based and property-scoped access.
"""
from rest_framework import permissions

from .services import accessible_property_ids, user_has_capability, user_has_any_capability


def _property_id_from_request(request, view) -> int | None:
    """Resolve property id from view kwargs, query params, or body."""
    for key in ('property_id', 'property'):
        if hasattr(view, 'kwargs') and view.kwargs.get(key) is not None:
            try:
                return int(view.kwargs[key])
            except (TypeError, ValueError):
                pass
        raw = request.query_params.get(key) if hasattr(request, 'query_params') else None
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
    if hasattr(request, 'data') and isinstance(request.data, dict):
        raw = request.data.get('property') or request.data.get('property_id')
        if raw is not None:
            try:
                return int(raw)
            except (TypeError, ValueError):
                pass
    # Optional hook on viewsets
    getter = getattr(view, 'get_rbac_property_id', None)
    if callable(getter):
        return getter()
    return None


class HasCapability(permissions.BasePermission):
    """
    Require one or more capability codenames.

    On the viewset set:
      required_capabilities = ['reservations.view']
      required_capabilities_any = True   # default: all must match if False... wait
    """

    message = 'You do not have permission to perform this action.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        required = getattr(view, 'required_capabilities', None)
        if not required:
            # Fallback: action map
            action_map = getattr(view, 'capability_map', {}) or {}
            action = getattr(view, 'action', None)
            required = action_map.get(action) or action_map.get(request.method.lower())

        if not required:
            return True  # no capability declared → defer to other permission classes

        if isinstance(required, str):
            required = [required]

        property_id = _property_id_from_request(request, view)
        require_any = getattr(view, 'required_capabilities_any', False)

        if require_any:
            ok = user_has_any_capability(user, required, property_id=property_id)
        else:
            ok = all(
                user_has_capability(user, cap, property_id=property_id) for cap in required
            )

        if not ok:
            user_has_capability(
                user,
                required[0],
                property_id=property_id,
                log_denial=True,
                request=request,
            )
        return ok

    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False
        user = request.user
        if user.is_superuser:
            return True

        property_id = None
        if hasattr(obj, 'property_id'):
            property_id = obj.property_id
        elif obj.__class__.__name__ == 'Property':
            property_id = obj.pk
        elif hasattr(obj, 'id') and hasattr(obj, 'tenant_id') and hasattr(obj, 'name'):
            # duck-type Property
            from core.models import Property
            if isinstance(obj, Property):
                property_id = obj.pk

        if property_id is None:
            return True

        ids = accessible_property_ids(user)
        if ids is None:
            return getattr(user, 'tenant_id', None) == getattr(obj, 'tenant_id', user.tenant_id) or True
        return property_id in ids


class IsReadOnlyOrHasCapability(permissions.BasePermission):
    """SAFE methods always allowed for tenant members; writes need capability."""

    write_capability = None

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        capability = getattr(view, 'write_capability', None) or self.write_capability
        if not capability:
            return False
        property_id = _property_id_from_request(request, view)
        return user_has_capability(request.user, capability, property_id=property_id)


class HasPropertyAccess(permissions.BasePermission):
    """Ensure the requested property is within the user's assignment scope."""

    message = 'You do not have access to this property.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        property_id = _property_id_from_request(request, view)
        if property_id is None:
            return True

        ids = accessible_property_ids(user)
        if ids is None:
            return True
        return property_id in ids
