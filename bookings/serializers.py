"""
Serializers for Bookings API
"""
from rest_framework import serializers
from .models import Reservation, Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payments"""
    reservation_id = serializers.IntegerField(source='reservation.id', read_only=True)
    amount_value = serializers.DecimalField(
        source='amount.amount',
        max_digits=14,
        decimal_places=2,
        read_only=True
    )
    currency = serializers.CharField(source='amount.currency', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'reservation', 'reservation_id',
            'amount', 'amount_value', 'currency',
            'payment_method', 'payment_status',
            'transaction_id', 'gateway_name',
            'paid_at', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ReservationSerializer(serializers.ModelSerializer):
    """Serializer for Reservations"""
    property_name = serializers.CharField(source='property.name', read_only=True)
    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    rate_plan_name = serializers.CharField(source='rate_plan.name', read_only=True)
    base_rate_amount = serializers.DecimalField(
        source='base_room_rate.amount',
        max_digits=14,
        decimal_places=2,
        read_only=True
    )
    total_amount_value = serializers.DecimalField(
        source='total_amount.amount',
        max_digits=14,
        decimal_places=2,
        read_only=True
    )
    payments = PaymentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'provider_name', 'provider_reservation_id', 'provider_confirmation_code',
            'property', 'property_name', 'room_type', 'room_type_name',
            'rate_plan', 'rate_plan_name',
            'check_in', 'check_out', 'nights',
            'guest_name', 'guest_email', 'guest_phone',
            'guest_address', 'guest_city', 'guest_state', 'guest_country', 'guest_gstin',
            'adults', 'children',
            'base_room_rate', 'base_rate_amount',
            'total_taxes_fees', 'total_amount', 'total_amount_value',
            'currency', 'cgst_amount', 'sgst_amount', 'igst_amount',
            'status', 'special_requests', 'reconciliation_notes',
            'last_reconciled_at', 'provider_specific_data',
            'payments',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
