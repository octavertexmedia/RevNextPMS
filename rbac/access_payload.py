"""
Shared RBAC payload for /api/auth/me/ and login responses.
"""
from __future__ import annotations

from .services import (
    accessible_property_ids,
    ensure_legacy_assignment,
    get_effective_assignments,
    get_user_capabilities,
)


def build_access_payload(user) -> dict:
    """
    Return permissions, roles, and property scope for the authenticated user.

    Ensures a legacy TenantUser.role assignment exists when RBAC rows are missing.
    """
    ensure_legacy_assignment(user)
    caps = sorted(get_user_capabilities(user))
    ids = accessible_property_ids(user)
    assignments = list(get_effective_assignments(user))
    roles = []
    for a in assignments:
        roles.append({
            'code': a.role.code,
            'name': a.role.name,
            'property_id': a.property_id,
        })
    if not roles and getattr(user, 'role', None):
        roles.append({
            'code': user.role,
            'name': user.role.replace('_', ' ').title(),
            'property_id': None,
        })
    return {
        'permissions': caps,
        'roles': roles,
        'rbac': {
            'capabilities': caps,
            'property_scope': 'all' if ids is None else 'restricted',
            'accessible_property_ids': None if ids is None else sorted(ids),
            'roles': roles,
        },
    }
