"""
RBAC evaluation service.

Permission resolution is additive across effective UserRoleAssignment rows.
Legacy TenantUser.role is used as a fallback until assignments are migrated.
"""
from __future__ import annotations

from typing import Iterable, Optional, Set

from django.db.models import Q, QuerySet
from django.utils import timezone

from .catalog import LEGACY_ROLE_MAP
from .models import AccessAuditLog, Role, UserRoleAssignment

# Used when seed_rbac has not been run yet — keeps the API usable.
_UNSEEDED_LEGACY_CAPS = {
    'owner': {'*'},
    'manager': {
        'properties.view', 'properties.create', 'properties.edit',
        'reservations.view', 'reservations.create', 'reservations.edit',
        'reservations.cancel', 'reservations.checkin', 'reservations.checkout',
        'rates.view', 'rates.edit', 'inventory.view', 'inventory.edit',
        'channel.view', 'channel.sync', 'channel.configure',
        'pms.view', 'pms.operate', 'pos.view', 'pos.operate',
        'housekeeping.view', 'housekeeping.update', 'housekeeping.manage',
        'reports.view', 'reports.export', 'users.view', 'roles.view',
        'finance.view', 'tenant.view', 'billing.view',
    },
    'staff': {
        'properties.view', 'reservations.view', 'reservations.create',
        'reservations.edit', 'reservations.checkin', 'reservations.checkout',
        'rates.view', 'inventory.view', 'pms.view', 'pms.operate',
        'housekeeping.view',
    },
    'viewer': {
        'tenant.view', 'properties.view', 'reservations.view', 'rates.view',
        'inventory.view', 'channel.view', 'pms.view', 'pos.view',
        'reports.view', 'housekeeping.view', 'finance.view', 'billing.view',
        'users.view', 'roles.view',
    },
}


def _effective_assignment_filter(now=None):
    now = now or timezone.now()
    return (
        Q(is_active=True)
        & (Q(starts_at__isnull=True) | Q(starts_at__lte=now))
        & (Q(ends_at__isnull=True) | Q(ends_at__gte=now))
    )


def get_effective_assignments(user) -> QuerySet:
    if not user or not getattr(user, 'is_authenticated', False):
        return UserRoleAssignment.objects.none()
    if user.is_superuser:
        return UserRoleAssignment.objects.none()
    return (
        UserRoleAssignment.objects.filter(user=user)
        .filter(_effective_assignment_filter())
        .select_related('role', 'property', 'tenant')
        .prefetch_related('role__capabilities')
    )


def _legacy_capability_codenames(user) -> Set[str]:
    """Fallback when user has no RBAC assignments yet."""
    legacy = getattr(user, 'role', None)
    if not legacy:
        return set()
    code = LEGACY_ROLE_MAP.get(legacy, legacy)
    try:
        role = Role.objects.prefetch_related('capabilities').get(
            code=code, is_system=True, is_active=True
        )
    except Role.DoesNotExist:
        fallback = _UNSEEDED_LEGACY_CAPS.get(legacy, set())
        if fallback == {'*'}:
            from .models import Capability
            seeded = set(Capability.objects.filter(is_active=True).values_list('codename', flat=True))
            return seeded or {'*'}
        return set(fallback)
    return set(role.capabilities.filter(is_active=True).values_list('codename', flat=True))


def get_user_capabilities(user, property_id: Optional[int] = None) -> Set[str]:
    """
    Resolve capability codenames for a user.

    If property_id is provided, only tenant-wide assignments and assignments
    for that property contribute. If omitted, all assignment capabilities
    are unioned (useful for Me / navigation).
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return set()
    if user.is_superuser:
        from .models import Capability
        seeded = set(Capability.objects.filter(is_active=True).values_list('codename', flat=True))
        return seeded or {'*'}

    assignments = get_effective_assignments(user)
    if property_id is not None:
        assignments = assignments.filter(Q(property__isnull=True) | Q(property_id=property_id))

    if not assignments.exists():
        return _legacy_capability_codenames(user)

    caps: Set[str] = set()
    for assignment in assignments:
        caps.update(
            assignment.role.capabilities.filter(is_active=True).values_list('codename', flat=True)
        )
    return caps


def user_has_capability(
    user,
    capability: str,
    property_id: Optional[int] = None,
    *,
    log_denial: bool = False,
    request=None,
) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if user.is_superuser:
        return True

    caps = get_user_capabilities(user, property_id=property_id)
    allowed = capability in caps or '*' in caps
    if not allowed and log_denial:
        AccessAuditLog.objects.create(
            tenant=getattr(user, 'tenant', None),
            actor=user,
            subject_user=user,
            event_type='permission_denied',
            capability=capability,
            property_id_snapshot=property_id,
            detail={'path': getattr(request, 'path', '') if request else ''},
            ip_address=_client_ip(request) if request else None,
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:255] if request else ''),
        )
    return allowed


def user_has_any_capability(user, capabilities: Iterable[str], property_id: Optional[int] = None) -> bool:
    caps = get_user_capabilities(user, property_id=property_id)
    if '*' in caps:
        return True
    return any(c in caps for c in capabilities)


def user_has_all_capabilities(user, capabilities: Iterable[str], property_id: Optional[int] = None) -> bool:
    caps = get_user_capabilities(user, property_id=property_id)
    if '*' in caps:
        return True
    return all(c in caps for c in capabilities)


def accessible_property_ids(user) -> Optional[Set[int]]:
    """
    Return property IDs the user may access.

    None means unrestricted within the tenant (tenant-wide role / owner / superuser).
    Empty set means no property access.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return set()
    if user.is_superuser:
        return None

    assignments = list(get_effective_assignments(user))
    if not assignments:
        # Legacy: owners/managers/viewers see all tenant properties; staff too (current behavior)
        if getattr(user, 'tenant_id', None):
            return None
        return set()

    if any(a.property_id is None for a in assignments):
        return None  # tenant-wide

    return {a.property_id for a in assignments if a.property_id}


def filter_properties_for_user(queryset, user):
    """Apply property-scope filter to a Property queryset."""
    if not user or not getattr(user, 'is_authenticated', False):
        return queryset.none()
    if user.is_superuser:
        return queryset

    ids = accessible_property_ids(user)
    if ids is None:
        if getattr(user, 'tenant_id', None):
            return queryset.filter(tenant_id=user.tenant_id)
        return queryset.none()
    return queryset.filter(id__in=ids, tenant_id=user.tenant_id)


def filter_by_property_fk(queryset, user, property_field: str = 'property'):
    """Filter any queryset that has a FK to Property."""
    if not user or not getattr(user, 'is_authenticated', False):
        return queryset.none()
    if user.is_superuser:
        return queryset

    ids = accessible_property_ids(user)
    tenant_filter = {f'{property_field}__tenant_id': user.tenant_id}
    if ids is None:
        if getattr(user, 'tenant_id', None):
            return queryset.filter(**tenant_filter)
        return queryset.none()
    return queryset.filter(**{f'{property_field}_id__in': ids, **tenant_filter})


def ensure_legacy_assignment(user, assigned_by=None) -> Optional[UserRoleAssignment]:
    """
    Create a tenant-wide RBAC assignment from TenantUser.role if missing.
    Safe to call repeatedly (idempotent).
    """
    if not user or not user.tenant_id or user.is_superuser:
        return None
    if get_effective_assignments(user).exists():
        return None

    code = LEGACY_ROLE_MAP.get(user.role, user.role)
    try:
        role = Role.objects.get(code=code, is_system=True, is_active=True)
    except Role.DoesNotExist:
        return None

    assignment, created = UserRoleAssignment.objects.get_or_create(
        user=user,
        role=role,
        tenant_id=user.tenant_id,
        property=None,
        defaults={
            'assigned_by': assigned_by,
            'notes': 'Auto-migrated from legacy TenantUser.role',
        },
    )
    if created:
        AccessAuditLog.objects.create(
            tenant_id=user.tenant_id,
            actor=assigned_by or user,
            subject_user=user,
            event_type='legacy_migrated',
            detail={'legacy_role': user.role, 'rbac_role': role.code},
        )
    return assignment


def _client_ip(request):
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
