"""
Serializers for Cloud PMS API
"""
from rest_framework import serializers
from core.models import RoomType
from .models import Folio, FolioLineItem, HousekeepingTask, LinkedRoomUnit


class FolioLineItemSerializer(serializers.ModelSerializer):
    amount_value = serializers.DecimalField(
        source='amount.amount', max_digits=14, decimal_places=2, read_only=True
    )
    currency = serializers.CharField(source='amount.currency', read_only=True)

    class Meta:
        model = FolioLineItem
        fields = [
            'id', 'folio', 'item_type', 'description',
            'amount', 'amount_value', 'currency', 'quantity',
            'pos_order_id', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FolioSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    reservation_id = serializers.IntegerField(source='reservation.id', read_only=True, allow_null=True)
    total_charges_value = serializers.DecimalField(
        source='total_charges.amount', max_digits=14, decimal_places=2, read_only=True
    )
    total_payments_value = serializers.DecimalField(
        source='total_payments.amount', max_digits=14, decimal_places=2, read_only=True
    )
    balance_value = serializers.DecimalField(
        source='balance.amount', max_digits=14, decimal_places=2, read_only=True
    )
    line_items = FolioLineItemSerializer(many=True, read_only=True)

    class Meta:
        model = Folio
        fields = [
            'id', 'property', 'property_name', 'reservation', 'reservation_id',
            'guest_name', 'guest_email', 'room_number',
            'total_charges', 'total_charges_value',
            'total_payments', 'total_payments_value',
            'balance', 'balance_value',
            'status', 'closed_at', 'line_items',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'total_charges', 'total_payments', 'balance',
            'closed_at', 'created_at', 'updated_at',
        ]


class HousekeepingTaskSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True, allow_null=True)
    reservation_id = serializers.IntegerField(source='reservation.id', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = HousekeepingTask
        fields = [
            'id', 'property', 'property_name',
            'room_number', 'room_type', 'room_type_name',
            'task_type', 'description',
            'status', 'status_display', 'priority', 'priority_display',
            'assigned_to', 'due_date', 'completed_at',
            'reservation', 'reservation_id',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'completed_at', 'created_at', 'updated_at']


class LinkedRoomUnitSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    room_type_ids = serializers.PrimaryKeyRelatedField(
        source='room_types',
        many=True,
        queryset=RoomType.objects.all(),
        required=False,
    )

    class Meta:
        model = LinkedRoomUnit
        fields = [
            'id', 'property', 'property_name', 'name',
            'room_type_ids', 'total_rooms',
            'sell_as_whole', 'whole_unit_price_multiplier',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
