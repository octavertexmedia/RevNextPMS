from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    AccessAuditLog,
    Capability,
    Role,
    RoleCapability,
    UserRoleAssignment,
)


class RoleCapabilityInline(TabularInline):
    model = RoleCapability
    extra = 0
    autocomplete_fields = ['capability']


@admin.register(Capability)
class CapabilityAdmin(ModelAdmin):
    list_display = ['codename', 'module', 'action', 'label', 'is_active']
    list_filter = ['module', 'is_active']
    search_fields = ['codename', 'label', 'description']
    ordering = ['module', 'action']


@admin.register(Role)
class RoleAdmin(ModelAdmin):
    list_display = [
        'name', 'code', 'department', 'default_scope',
        'is_system', 'tenant', 'is_active', 'sort_order',
    ]
    list_filter = ['is_system', 'department', 'default_scope', 'is_active']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['is_system']
    inlines = [RoleCapabilityInline]
    autocomplete_fields = ['tenant', 'parent']

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_system and not request.user.is_superuser:
            return ro + ['code', 'name', 'department', 'default_scope', 'tenant']
        return ro

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(ModelAdmin):
    list_display = [
        'user', 'role', 'tenant', 'property',
        'is_active', 'starts_at', 'ends_at', 'assigned_by', 'created_at',
    ]
    list_filter = ['is_active', 'role__department', 'tenant']
    search_fields = [
        'user__username', 'user__email', 'role__code', 'role__name', 'notes',
    ]
    autocomplete_fields = ['user', 'role', 'tenant', 'property', 'assigned_by']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AccessAuditLog)
class AccessAuditLogAdmin(ModelAdmin):
    list_display = [
        'created_at', 'event_type', 'tenant', 'actor',
        'subject_user', 'capability', 'property_id_snapshot',
    ]
    list_filter = ['event_type', 'tenant']
    search_fields = ['capability', 'actor__username', 'subject_user__username']
    readonly_fields = [
        'tenant', 'actor', 'subject_user', 'event_type', 'capability',
        'property_id_snapshot', 'detail', 'ip_address', 'user_agent',
        'created_at', 'updated_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
