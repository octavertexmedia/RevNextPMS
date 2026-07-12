"""
Enterprise RBAC models for hospitality multi-property operations.

Layers:
  Capability  → atomic permission (module.action)
  Role        → named job role with a capability set (system or tenant-custom)
  Assignment  → user ↔ role at tenant-wide or property scope
"""
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

from .catalog import DEPARTMENT_CHOICES


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Capability(TimeStampedModel):
    """Atomic permission used across system and custom roles."""

    codename = models.CharField(max_length=100, unique=True, db_index=True)
    module = models.CharField(max_length=50, db_index=True)
    action = models.CharField(max_length=50)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'rbac_capabilities'
        ordering = ['module', 'action']
        verbose_name_plural = 'Capabilities'
        indexes = [
            models.Index(fields=['module', 'action']),
        ]

    def __str__(self):
        return self.codename


class Role(TimeStampedModel):
    """
    Job role definition.

    System roles (is_system=True, tenant=NULL) are global hospitality templates.
    Custom roles belong to a tenant and can clone / extend the capability pool.
    """

    SCOPE_CHOICES = [
        ('tenant', 'Tenant-wide'),
        ('property', 'Property-scoped'),
    ]

    code = models.SlugField(max_length=80)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    department = models.CharField(
        max_length=40,
        choices=DEPARTMENT_CHOICES,
        default='other',
        db_index=True,
    )
    default_scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='property',
        help_text='Suggested assignment scope when granting this role',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='rbac_roles',
        null=True,
        blank=True,
        help_text='Null for system roles; set for tenant-custom roles',
    )
    is_system = models.BooleanField(
        default=False,
        help_text='System roles are seeded and not editable by tenants',
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=100)
    capabilities = models.ManyToManyField(
        Capability,
        through='RoleCapability',
        related_name='roles',
        blank=True,
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text='Optional parent role for inheritance display',
    )

    class Meta:
        db_table = 'rbac_roles'
        ordering = ['sort_order', 'name']
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=models.Q(tenant__isnull=True),
                name='rbac_role_unique_system_code',
            ),
            models.UniqueConstraint(
                fields=['tenant', 'code'],
                condition=models.Q(tenant__isnull=False),
                name='rbac_role_unique_tenant_code',
            ),
        ]
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['is_system', 'code']),
        ]

    def __str__(self):
        scope = 'system' if self.is_system else (self.tenant.name if self.tenant_id else 'custom')
        return f'{self.name} ({scope})'

    def clean(self):
        if self.is_system and self.tenant_id:
            raise ValidationError('System roles cannot belong to a tenant.')
        if not self.is_system and not self.tenant_id:
            raise ValidationError('Custom roles must belong to a tenant.')

    def capability_codenames(self):
        return list(
            self.capabilities.filter(is_active=True).values_list('codename', flat=True)
        )


class RoleCapability(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_capabilities')
    capability = models.ForeignKey(
        Capability, on_delete=models.CASCADE, related_name='capability_roles'
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'rbac_role_capabilities'
        unique_together = [('role', 'capability')]

    def __str__(self):
        return f'{self.role.code} → {self.capability.codename}'


class UserRoleAssignment(TimeStampedModel):
    """
    Grants a role to a user.

    - property=NULL  → tenant-wide grant (all current/future properties)
    - property set   → scoped to that property only
    Multiple assignments are unioned (additive permissions).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='role_assignments',
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name='assignments',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='role_assignments',
    )
    property = models.ForeignKey(
        'core.Property',
        on_delete=models.CASCADE,
        related_name='role_assignments',
        null=True,
        blank=True,
        help_text='Null = tenant-wide access for this role',
    )
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='roles_assigned',
    )
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'rbac_user_role_assignments'
        ordering = ['-created_at']
        constraints = [
            # Property-scoped uniqueness
            models.UniqueConstraint(
                fields=['user', 'role', 'tenant', 'property'],
                condition=models.Q(property__isnull=False),
                name='rbac_assignment_unique_user_role_property',
            ),
            # Tenant-wide uniqueness (property IS NULL)
            models.UniqueConstraint(
                fields=['user', 'role', 'tenant'],
                condition=models.Q(property__isnull=True),
                name='rbac_assignment_unique_user_role_tenantwide',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['property', 'is_active']),
        ]

    def __str__(self):
        prop = self.property.name if self.property_id else 'ALL'
        return f'{self.user} → {self.role.code} @ {prop}'

    def clean(self):
        if self.property_id and self.property.tenant_id != self.tenant_id:
            raise ValidationError('Property must belong to the same tenant as the assignment.')
        if self.user_id and self.user.tenant_id and self.user.tenant_id != self.tenant_id:
            raise ValidationError('User must belong to the assignment tenant.')
        if self.role.is_system is False and self.role.tenant_id != self.tenant_id:
            raise ValidationError('Custom role must belong to the same tenant.')

    def is_currently_effective(self):
        from django.utils import timezone
        if not self.is_active:
            return False
        now = timezone.now()
        if self.starts_at and now < self.starts_at:
            return False
        if self.ends_at and now > self.ends_at:
            return False
        return True


class AccessAuditLog(TimeStampedModel):
    """Immutable-ish audit trail for RBAC changes and denials."""

    EVENT_CHOICES = [
        ('role_assigned', 'Role assigned'),
        ('role_revoked', 'Role revoked'),
        ('role_updated', 'Role updated'),
        ('permission_denied', 'Permission denied'),
        ('capability_checked', 'Capability checked'),
        ('legacy_migrated', 'Legacy role migrated'),
    ]

    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rbac_audit_logs',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rbac_actions',
    )
    subject_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rbac_events',
    )
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES, db_index=True)
    capability = models.CharField(max_length=100, blank=True)
    property_id_snapshot = models.BigIntegerField(null=True, blank=True)
    detail = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'rbac_access_audit_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'event_type', 'created_at']),
        ]

    def __str__(self):
        return f'{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M}'
