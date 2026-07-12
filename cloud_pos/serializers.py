"""
Serializers for Cloud POS mobile API.
"""
from rest_framework import serializers
from djmoney.money import Money

from .models import MenuCategory, MenuItem, POSOrder, POSOrderItem, POSTable


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    property = serializers.IntegerField(source='category.property_id', read_only=True)
    price_value = serializers.DecimalField(
        source='price.amount', max_digits=14, decimal_places=2, read_only=True
    )
    currency = serializers.CharField(source='price.currency', read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_name', 'property',
            'name', 'description', 'price', 'price_value', 'currency',
            'image_url', 'is_available', 'track_inventory', 'stock_qty', 'low_stock_at',
        ]
        read_only_fields = fields


class MenuCategorySerializer(serializers.ModelSerializer):
    items = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = MenuCategory
        fields = [
            'id', 'property', 'name', 'icon', 'display_order', 'is_active', 'items',
        ]
        read_only_fields = fields


class POSTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSTable
        fields = ['id', 'property', 'name', 'capacity', 'section', 'is_occupied', 'qr_token']
        read_only_fields = fields


class POSOrderItemSerializer(serializers.ModelSerializer):
    menu_item_name = serializers.CharField(source='menu_item.name', read_only=True)
    unit_price_value = serializers.DecimalField(
        source='unit_price.amount', max_digits=14, decimal_places=2, read_only=True
    )
    line_total_value = serializers.DecimalField(
        source='line_total.amount', max_digits=14, decimal_places=2, read_only=True
    )
    currency = serializers.CharField(source='unit_price.currency', read_only=True)

    class Meta:
        model = POSOrderItem
        fields = [
            'id', 'menu_item', 'menu_item_name', 'quantity',
            'unit_price_value', 'line_total_value', 'currency', 'notes',
        ]
        read_only_fields = fields


class POSOrderSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    table_name = serializers.CharField(source='table.name', read_only=True, allow_null=True)
    total_amount_value = serializers.DecimalField(
        source='total_amount.amount', max_digits=14, decimal_places=2, read_only=True
    )
    subtotal_amount_value = serializers.DecimalField(
        source='subtotal_amount.amount', max_digits=14, decimal_places=2, read_only=True
    )
    tax_amount_value = serializers.DecimalField(
        source='tax_amount.amount', max_digits=14, decimal_places=2, read_only=True
    )
    currency = serializers.CharField(source='total_amount.currency', read_only=True)
    items = POSOrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    order_type_display = serializers.CharField(source='get_order_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)

    class Meta:
        model = POSOrder
        fields = [
            'id', 'property', 'property_name',
            'table', 'table_name',
            'order_type', 'order_type_display', 'channel', 'channel_display',
            'guest_name', 'guest_phone', 'delivery_address', 'external_order_id', 'notes',
            'bill_to_room', 'folio', 'room_number',
            'status', 'status_display',
            'subtotal_amount_value', 'tax_amount_value', 'total_amount_value', 'tax_rate',
            'currency', 'items', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'subtotal_amount_value', 'tax_amount_value',
            'total_amount_value', 'currency',
            'items', 'created_at', 'updated_at', 'status_display',
            'order_type_display', 'channel_display',
            'property_name', 'table_name',
        ]
