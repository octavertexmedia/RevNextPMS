from rest_framework import serializers

from .models import Capability, Role, UserRoleAssignment
from .services import get_user_capabilities, accessible_property_ids, get_effective_assignments


class CapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Capability
        fields = [
            'id', 'codename', 'module', 'action', 'label',
            'description', 'is_active',
        ]


class RoleSerializer(serializers.ModelSerializer):
    capabilities = CapabilitySerializer(many=True, read_only=True)
    capability_codenames = serializers.SerializerMethodField()
    capability_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Capability.objects.filter(is_active=True),
        source='capabilities',
        write_only=True,
        required=False,
    )

    class Meta:
        model = Role
        fields = [
            'id', 'code', 'name', 'description', 'department',
            'default_scope', 'tenant', 'is_system', 'is_active',
            'sort_order', 'parent', 'capabilities', 'capability_codenames',
            'capability_ids', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'is_system', 'created_at', 'updated_at']

    def get_capability_codenames(self, obj):
        return obj.capability_codenames()

    def validate(self, attrs):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if self.instance and self.instance.is_system:
            raise serializers.ValidationError('System roles cannot be modified via API.')
        if not self.instance:
            attrs['is_system'] = False
            if user and getattr(user, 'tenant_id', None):
                attrs['tenant'] = user.tenant
            if not attrs.get('tenant'):
                raise serializers.ValidationError('Custom roles require a tenant.')
        return attrs

    def create(self, validated_data):
        caps = validated_data.pop('capabilities', [])
        role = Role.objects.create(**validated_data)
        if caps:
            role.capabilities.set(caps)
        return role

    def update(self, instance, validated_data):
        caps = validated_data.pop('capabilities', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if caps is not None:
            instance.capabilities.set(caps)
        return instance


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    role_detail = RoleSerializer(source='role', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    property_name = serializers.CharField(source='property.name', read_only=True, default=None)
    is_effective = serializers.SerializerMethodField()

    class Meta:
        model = UserRoleAssignment
        fields = [
            'id', 'user', 'user_username', 'role', 'role_detail',
            'tenant', 'property', 'property_name',
            'is_active', 'starts_at', 'ends_at',
            'assigned_by', 'notes', 'is_effective',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'tenant', 'assigned_by', 'created_at', 'updated_at']

    def get_is_effective(self, obj):
        return obj.is_currently_effective()

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        validated_data['tenant'] = user.tenant
        validated_data['assigned_by'] = user
        assignment = UserRoleAssignment(**validated_data)
        assignment.full_clean()
        assignment.save()
        return assignment


class MyAccessSerializer(serializers.Serializer):
    """Payload for /api/rbac/me/ — capabilities + assignments for the current user."""

    legacy_role = serializers.CharField()
    capabilities = serializers.ListField(child=serializers.CharField())
    property_scope = serializers.CharField()
    accessible_property_ids = serializers.ListField(child=serializers.IntegerField(), allow_null=True)
    assignments = UserRoleAssignmentSerializer(many=True)

    @classmethod
    def from_user(cls, user):
        ids = accessible_property_ids(user)
        return {
            'legacy_role': getattr(user, 'role', None),
            'capabilities': sorted(get_user_capabilities(user)),
            'property_scope': 'all' if ids is None else 'restricted',
            'accessible_property_ids': None if ids is None else sorted(ids),
            'assignments': get_effective_assignments(user),
        }
