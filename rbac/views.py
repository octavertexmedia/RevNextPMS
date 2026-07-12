from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.permissions import IsTenantMember, IsTenantOwner

from .models import AccessAuditLog, Capability, Role, UserRoleAssignment
from .permissions import HasCapability
from .serializers import (
    CapabilitySerializer,
    MyAccessSerializer,
    RoleSerializer,
    UserRoleAssignmentSerializer,
)
from .services import ensure_legacy_assignment


class CapabilityViewSet(viewsets.ReadOnlyModelViewSet):
    """List the global capability catalog."""
    serializer_class = CapabilitySerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    queryset = Capability.objects.filter(is_active=True)
    search_fields = ['codename', 'label', 'module']
    filterset_fields = ['module', 'action']


class RoleViewSet(viewsets.ModelViewSet):
    """
    System + tenant-custom roles.

    Tenants can create custom roles; system roles are read-only.
    """
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    search_fields = ['code', 'name', 'department']
    filterset_fields = ['department', 'is_system', 'default_scope', 'is_active']
    capability_map = {
        'list': 'roles.view',
        'retrieve': 'roles.view',
        'create': 'roles.manage',
        'update': 'roles.manage',
        'partial_update': 'roles.manage',
        'destroy': 'roles.manage',
    }

    def get_queryset(self):
        user = self.request.user
        qs = Role.objects.filter(is_active=True).prefetch_related('capabilities')
        if user.is_superuser:
            return qs
        return qs.filter(Q(is_system=True) | Q(tenant_id=user.tenant_id))

    def perform_destroy(self, instance):
        if instance.is_system:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('System roles cannot be deleted.')
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])


class UserRoleAssignmentViewSet(viewsets.ModelViewSet):
    """Assign / revoke roles for staff (owner / users.manage)."""
    serializer_class = UserRoleAssignmentSerializer
    permission_classes = [IsAuthenticated, IsTenantMember, HasCapability]
    filterset_fields = ['user', 'role', 'property', 'is_active']
    capability_map = {
        'list': 'users.view',
        'retrieve': 'users.view',
        'create': 'users.manage',
        'update': 'users.manage',
        'partial_update': 'users.manage',
        'destroy': 'users.manage',
        'revoke': 'users.manage',
    }

    def get_queryset(self):
        user = self.request.user
        qs = UserRoleAssignment.objects.select_related(
            'user', 'role', 'property', 'tenant', 'assigned_by'
        ).prefetch_related('role__capabilities')
        if user.is_superuser:
            return qs
        return qs.filter(tenant_id=user.tenant_id)

    def perform_create(self, serializer):
        assignment = serializer.save()
        AccessAuditLog.objects.create(
            tenant=assignment.tenant,
            actor=self.request.user,
            subject_user=assignment.user,
            event_type='role_assigned',
            property_id_snapshot=assignment.property_id,
            detail={
                'role': assignment.role.code,
                'property': assignment.property_id,
            },
        )

    def perform_destroy(self, instance):
        AccessAuditLog.objects.create(
            tenant=instance.tenant,
            actor=self.request.user,
            subject_user=instance.user,
            event_type='role_revoked',
            property_id_snapshot=instance.property_id,
            detail={'role': instance.role.code},
        )
        instance.is_active = False
        instance.ends_at = timezone.now()
        instance.save(update_fields=['is_active', 'ends_at', 'updated_at'])

    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        assignment = self.get_object()
        self.perform_destroy(assignment)
        return Response({'detail': 'Assignment revoked.'})


class MyAccessView(APIView):
    """Current user's resolved capabilities, property scope, and assignments."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_legacy_assignment(request.user)
        payload = MyAccessSerializer.from_user(request.user)
        data = {
            'legacy_role': payload['legacy_role'],
            'capabilities': payload['capabilities'],
            'property_scope': payload['property_scope'],
            'accessible_property_ids': payload['accessible_property_ids'],
            'assignments': UserRoleAssignmentSerializer(
                payload['assignments'], many=True
            ).data,
        }
        return Response(data)


class SeedStatusView(APIView):
    """Quick diagnostic for owners — whether system RBAC catalog is loaded."""
    permission_classes = [IsAuthenticated, IsTenantOwner]

    def get(self, request):
        return Response({
            'capabilities': Capability.objects.filter(is_active=True).count(),
            'system_roles': Role.objects.filter(is_system=True, is_active=True).count(),
            'tenant_assignments': UserRoleAssignment.objects.filter(
                tenant=request.user.tenant, is_active=True
            ).count() if request.user.tenant_id else 0,
        })
