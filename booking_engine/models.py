"""
Booking Engine - Direct booking

One-page booking, multi-currency, Google Hotel Ads, commission-free direct revenue.
"""
from django.db import models
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from core.models import Property, RoomType, RatePlan, TimeStampedModel


class DirectBooking(TimeStampedModel):
    """Direct booking from booking engine (not from OTA)"""
    
    STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('CHECKED_IN', 'Checked In'),
        ('CHECKED_OUT', 'Checked Out'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='direct_bookings')
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='direct_bookings')
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_bookings')
    
    check_in = models.DateField()
    check_out = models.DateField()
    nights = models.PositiveIntegerField(default=1)
    
    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    
    total_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    currency = models.CharField(max_length=3, default='INR')
    
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    confirmation_code = models.CharField(max_length=50, unique=True, blank=True)
    
    # Source
    source = models.CharField(max_length=50, default='booking_engine')
    google_hotel_ads = models.BooleanField(default=False)
    
    # Link to reservation for unified view
    reservation = models.ForeignKey(
        'bookings.Reservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_booking'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.confirmation_code} - {self.guest_name}"


class BookingSession(TimeStampedModel):
    """Temporary session for multi-step booking flow"""
    id = models.BigAutoField(primary_key=True)
    session_key = models.CharField(max_length=100, db_index=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True)
    step = models.PositiveIntegerField(default=1)
    data = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
