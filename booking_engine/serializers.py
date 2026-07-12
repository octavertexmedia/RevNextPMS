"""Serializers for Booking Engine (staff + public APIs)."""
from rest_framework import serializers

from .models import BookingEngineConfig, DirectBooking


class BookingEngineConfigSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)

    class Meta:
        model = BookingEngineConfig
        fields = [
            'id', 'property', 'property_name', 'is_enabled', 'default_currency',
            'supported_currencies', 'allow_children', 'min_nights', 'max_nights',
            'deposit_percent', 'require_phone', 'google_hotel_ads_enabled',
            'widget_primary_color', 'confirmation_email_enabled', 'terms_url',
            'success_message', 'allowed_embed_origins', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'property_name', 'created_at', 'updated_at']


class DirectBookingSerializer(serializers.ModelSerializer):
    property_name = serializers.CharField(source='property.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    total_amount_value = serializers.DecimalField(
        source='total_amount.amount', max_digits=14, decimal_places=2, read_only=True
    )
    currency_code = serializers.CharField(source='total_amount.currency', read_only=True)
    deposit_amount_value = serializers.DecimalField(
        source='deposit_amount.amount', max_digits=14, decimal_places=2,
        read_only=True, allow_null=True,
    )
    reservation_id = serializers.IntegerField(
        source='reservation.id', read_only=True, allow_null=True
    )

    class Meta:
        model = DirectBooking
        fields = [
            'id', 'property', 'property_name', 'room_type', 'room_type_name',
            'rate_plan', 'check_in', 'check_out', 'nights',
            'guest_name', 'guest_email', 'guest_phone', 'adults', 'children',
            'total_amount_value', 'currency_code', 'currency', 'deposit_amount_value',
            'status', 'confirmation_code', 'source', 'google_hotel_ads',
            'channel_host', 'reservation_id', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class PublicAvailabilitySerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)


class PublicCreateBookingSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    room_type_id = serializers.IntegerField()
    rate_plan_id = serializers.IntegerField(required=False, allow_null=True)
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guest_name = serializers.CharField(max_length=255)
    guest_email = serializers.EmailField()
    guest_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)
    google_hotel_ads = serializers.BooleanField(default=False)
    source = serializers.CharField(max_length=50, required=False, default='booking_engine')
