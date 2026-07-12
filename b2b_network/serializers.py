from rest_framework import serializers

from .models import B2BAgent, B2BAllotment, B2BBooking, B2BRatePlan, CorporateAccount


class B2BRatePlanSerializer(serializers.ModelSerializer):
    rate_plan_name = serializers.CharField(source='rate_plan.name', read_only=True)
    net_rate_value = serializers.DecimalField(
        source='net_rate.amount', max_digits=14, decimal_places=2,
        read_only=True, allow_null=True,
    )

    class Meta:
        model = B2BRatePlan
        fields = [
            'id', 'agent', 'rate_plan', 'rate_plan_name', 'discount_percent',
            'net_rate_value', 'is_active', 'valid_from', 'valid_to',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'rate_plan_name', 'net_rate_value', 'created_at', 'updated_at']


class CorporateAccountSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)

    class Meta:
        model = CorporateAccount
        fields = ['id', 'property', 'property_name', 'agent', 'has_access', 'created_at']
        read_only_fields = ['id', 'property_name', 'created_at']


class B2BAllotmentSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = B2BAllotment
        fields = [
            'id', 'agent', 'property', 'property_name', 'room_type', 'room_type_name',
            'date', 'allocated_rooms', 'used_rooms', 'remaining', 'release_days',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'property_name', 'room_type_name', 'remaining', 'used_rooms',
                            'created_at', 'updated_at']


class B2BBookingSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    agent_name = serializers.CharField(source='agent.company_name', read_only=True)
    total_amount_value = serializers.DecimalField(
        source='total_amount.amount', max_digits=14, decimal_places=2, read_only=True,
    )
    commission_amount_value = serializers.DecimalField(
        source='commission_amount.amount', max_digits=14, decimal_places=2,
        read_only=True, allow_null=True,
    )
    reservation_id = serializers.IntegerField(
        source='reservation.id', read_only=True, allow_null=True,
    )

    class Meta:
        model = B2BBooking
        fields = [
            'id', 'agent', 'agent_name', 'property', 'property_name',
            'room_type', 'room_type_name', 'rate_plan', 'b2b_rate',
            'check_in', 'check_out', 'nights',
            'guest_name', 'guest_email', 'guest_phone', 'adults', 'children',
            'total_amount_value', 'commission_amount_value', 'currency',
            'status', 'confirmation_code', 'channel_host', 'special_requests',
            'reservation_id', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class B2BAgentSerializer(serializers.ModelSerializer):
    rate_plans = B2BRatePlanSerializer(many=True, read_only=True)
    property_access = CorporateAccountSerializer(many=True, read_only=True)
    credit_limit_value = serializers.DecimalField(
        source='credit_limit.amount', max_digits=14, decimal_places=2,
        read_only=True, allow_null=True,
    )
    property_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False,
    )

    class Meta:
        model = B2BAgent
        fields = [
            'id', 'tenant', 'company_name', 'agent_code', 'agent_type',
            'contact_email', 'contact_phone', 'commission_percent',
            'credit_limit_value', 'is_active', 'portal_enabled', 'notes',
            'rate_plans', 'property_access', 'property_ids',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'tenant', 'credit_limit_value', 'rate_plans', 'property_access',
            'created_at', 'updated_at',
        ]


class PortalCreateBookingSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    room_type_id = serializers.IntegerField()
    rate_plan_id = serializers.IntegerField(required=False, allow_null=True)
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guest_name = serializers.CharField(max_length=255)
    guest_email = serializers.EmailField(required=False, allow_blank=True)
    guest_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)
    special_requests = serializers.CharField(required=False, allow_blank=True)
