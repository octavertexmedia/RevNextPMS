"""
Reservation and Booking Models
"""
from django.db import models
from django.core.validators import MinValueValidator
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from simple_history.models import HistoricalRecords
from core.models import Property, RoomType, RatePlan, TimeStampedModel


class Reservation(TimeStampedModel):
    """Reservation/Booking entity - core booking model"""
    
    RESERVATION_STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('MODIFIED', 'Modified'),
        ('CANCELLED', 'Cancelled'),
        ('CHECKED_IN', 'Checked In'),
        ('CHECKED_OUT', 'Checked Out'),
        ('NO_SHOW', 'No Show'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    
    # Provider Information
    provider_name = models.CharField(max_length=100, help_text="OTA/Platform name, e.g., 'booking.com', 'expedia'")
    provider_reservation_id = models.CharField(max_length=255, db_index=True, help_text="Reservation ID from provider")
    provider_confirmation_code = models.CharField(max_length=255, blank=True)
    
    # Property and Room Details
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name='reservations')
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='reservations')
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations')
    
    # Dates
    check_in = models.DateField()
    check_out = models.DateField()
    nights = models.PositiveIntegerField(help_text="Number of nights")
    
    # Guest Information
    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20, blank=True)
    guest_address = models.TextField(blank=True)
    guest_city = models.CharField(max_length=100, blank=True)
    guest_state = models.CharField(max_length=100, blank=True)
    guest_country = models.CharField(max_length=100, blank=True)
    guest_gstin = models.CharField(max_length=15, blank=True, help_text="Guest GSTIN for B2B transactions")
    
    # Occupancy
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    
    # Pricing Breakdown
    base_room_rate = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    total_taxes_fees = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    total_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    currency = models.CharField(max_length=3, default='INR')
    
    # GST Breakdown (India-specific)
    cgst_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    sgst_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    igst_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    
    # Status
    status = models.CharField(max_length=20, choices=RESERVATION_STATUS, default='PENDING')
    
    # Special Requests
    special_requests = models.TextField(blank=True)
    
    # Provider-specific data
    provider_specific_data = models.JSONField(default=dict, blank=True)
    
    # Reconciliation
    last_reconciled_at = models.DateTimeField(null=True, blank=True)
    reconciliation_notes = models.TextField(blank=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-check_in', '-created_at']
        indexes = [
            models.Index(fields=['provider_name', 'provider_reservation_id']),
            models.Index(fields=['property', 'check_in', 'check_out']),
            models.Index(fields=['status']),
        ]
        unique_together = ['provider_name', 'provider_reservation_id']

    def __str__(self):
        return f"{self.provider_name} - {self.provider_reservation_id} - {self.guest_name}"

    def save(self, *args, **kwargs):
        # Auto-calculate nights
        if self.check_in and self.check_out:
            from datetime import timedelta
            self.nights = (self.check_out - self.check_in).days
        super().save(*args, **kwargs)


class Payment(TimeStampedModel):
    """Payment records for reservations"""
    
    PAYMENT_METHODS = [
        ('CREDIT_CARD', 'Credit Card'),
        ('DEBIT_CARD', 'Debit Card'),
        ('UPI', 'UPI'),
        ('NET_BANKING', 'Net Banking'),
        ('WALLET', 'Wallet'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CASH', 'Cash'),
        ('COD', 'Cash on Delivery'),
    ]
    
    PAYMENT_STATUS = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='payments')
    
    # Payment Details
    amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    currency = models.CharField(max_length=3, default='INR')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='PENDING')
    
    # Transaction Details
    transaction_id = models.CharField(max_length=255, blank=True, db_index=True)
    gateway_transaction_id = models.CharField(max_length=255, blank=True)
    gateway_name = models.CharField(max_length=100, blank=True, help_text="Payment gateway name, e.g., 'razorpay', 'stripe'")
    
    # Timestamps
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Provider-specific data
    provider_specific_data = models.JSONField(default=dict, blank=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reservation} - {self.amount} ({self.get_payment_status_display()})"


class ReservationModification(TimeStampedModel):
    """Track modifications to reservations"""
    
    MODIFICATION_TYPES = [
        ('DATE_CHANGE', 'Date Change'),
        ('ROOM_CHANGE', 'Room Type Change'),
        ('GUEST_CHANGE', 'Guest Details Change'),
        ('PRICE_CHANGE', 'Price Change'),
        ('CANCELLATION', 'Cancellation'),
        ('OTHER', 'Other'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='modifications')
    modification_type = models.CharField(max_length=20, choices=MODIFICATION_TYPES)
    
    # Change Details
    old_value = models.JSONField(default=dict, help_text="Previous values")
    new_value = models.JSONField(default=dict, help_text="New values")
    
    # Source
    modified_by = models.CharField(max_length=100, blank=True, help_text="Who made the change (provider/system/user)")
    notes = models.TextField(blank=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reservation} - {self.get_modification_type_display()}"

