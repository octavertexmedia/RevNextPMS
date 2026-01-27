"""
Serializers for Core API
"""
from rest_framework import serializers
from .models import Property, RoomType, RatePlan, Inventory, Promotion


class RoomTypeSerializer(serializers.ModelSerializer):
    """Serializer for Room Types"""
    
    class Meta:
        model = RoomType
        fields = [
            'id', 'property', 'name', 'description',
            'max_occupancy', 'base_occupancy',
            'max_adults', 'max_children',
            'size_sqm', 'bed_type', 'amenities',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RatePlanSerializer(serializers.ModelSerializer):
    """Serializer for Rate Plans"""
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    meal_plan_name = serializers.CharField(source='meal_plan.name', read_only=True)
    base_rate_amount = serializers.DecimalField(
        source='base_rate.amount',
        max_digits=14,
        decimal_places=2,
        read_only=True
    )
    base_rate_currency = serializers.CharField(source='base_rate.currency', read_only=True)
    
    class Meta:
        model = RatePlan
        fields = [
            'id', 'property', 'room_type', 'room_type_name',
            'name', 'description', 'meal_plan', 'meal_plan_name',
            'inclusions', 'base_rate', 'base_rate_amount', 'base_rate_currency',
            'base_occupancy', 'extra_adult_charge', 'extra_child_charge',
            'los_based_rates', 'is_derived', 'parent_rate_plan',
            'cancellation_policy', 'prepayment_policy', 'no_show_policy',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PropertySerializer(serializers.ModelSerializer):
    """Serializer for Properties"""
    room_types = RoomTypeSerializer(many=True, read_only=True)
    rate_plans = RatePlanSerializer(many=True, read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = Property
        fields = [
            'id', 'tenant', 'tenant_name', 'name', 'legal_name',
            'property_type', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'location',
            'phone', 'email', 'website', 'timezone', 'currency',
            'gstin', 'pan', 'is_active',
            'room_types', 'rate_plans',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InventorySerializer(serializers.ModelSerializer):
    """Serializer for Inventory"""
    property_name = serializers.CharField(source='property.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    occupancy_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = [
            'id', 'property', 'property_name',
            'room_type', 'room_type_name',
            'date', 'available_rooms', 'total_rooms',
            'blocked_rooms', 'version', 'occupancy_percentage',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'version', 'created_at', 'updated_at']
    
    def get_occupancy_percentage(self, obj):
        """Calculate occupancy percentage"""
        if obj.total_rooms > 0:
            return round((obj.available_rooms / obj.total_rooms) * 100, 2)
        return 0


class PromotionSerializer(serializers.ModelSerializer):
    """Serializer for Promotions"""
    property_name = serializers.CharField(source='property.name', read_only=True)
    
    class Meta:
        model = Promotion
        fields = [
            'id', 'property', 'property_name',
            'name', 'promotion_type', 'discount_value',
            'start_date', 'end_date', 'eligibility_rules',
            'description', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
