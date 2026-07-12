"""
Booking Engine - Direct booking product (booking.revnext.in)

One-page booking, multi-currency, Google Hotel Ads, commission-free direct revenue.
Standalone billable product — also included in the Hospitality Suite.
"""
import builtins
import secrets
import string
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from core.models import Property, RoomType, RatePlan, Inventory, TimeStampedModel


def generate_confirmation_code(prefix='RN'):
    alphabet = string.ascii_uppercase + string.digits
    return prefix + ''.join(secrets.choice(alphabet) for _ in range(8))


class BookingEngineConfig(TimeStampedModel):
    """Per-property booking engine configuration."""

    property = models.OneToOneField(
        Property, on_delete=models.CASCADE, related_name='booking_engine_config',
    )
    is_enabled = models.BooleanField(default=True)
    default_currency = models.CharField(max_length=3, default='INR')
    supported_currencies = models.JSONField(default=list, blank=True)
    allow_children = models.BooleanField(default=True)
    min_nights = models.PositiveIntegerField(default=1)
    max_nights = models.PositiveIntegerField(default=30)
    deposit_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    require_phone = models.BooleanField(default=False)
    google_hotel_ads_enabled = models.BooleanField(default=False)
    widget_primary_color = models.CharField(max_length=20, default='#1B3A4B')
    confirmation_email_enabled = models.BooleanField(default=True)
    terms_url = models.URLField(blank=True)
    success_message = models.CharField(
        max_length=255,
        blank=True,
        default='Thank you — your booking is confirmed.',
    )
    allowed_embed_origins = models.JSONField(
        default=list, blank=True,
        help_text='Origins allowed to embed the booking widget',
    )

    class Meta:
        db_table = 'booking_engine_configs'
        verbose_name = 'Booking Engine Config'

    def __str__(self):
        return f'Booking config — {self.property.name}'


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
    rate_plan = models.ForeignKey(
        RatePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_bookings',
    )

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
    deposit_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True,
    )

    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    confirmation_code = models.CharField(max_length=50, unique=True, blank=True)

    source = models.CharField(max_length=50, default='booking_engine')
    google_hotel_ads = models.BooleanField(default=False)
    channel_host = models.CharField(
        max_length=100, blank=True,
        help_text='Product host that created this booking, e.g. booking.revnext.in',
    )

    reservation = models.ForeignKey(
        'bookings.Reservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_booking',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['property', 'status']),
            models.Index(fields=['confirmation_code']),
            models.Index(fields=['guest_email']),
        ]

    def __str__(self):
        return f'{self.confirmation_code} - {self.guest_name}'

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = generate_confirmation_code()
        if self.check_in and self.check_out:
            self.nights = max(1, (self.check_out - self.check_in).days)
        super().save(*args, **kwargs)


class BookingSession(TimeStampedModel):
    """Temporary session for multi-step / public booking flow."""

    id = models.BigAutoField(primary_key=True)
    session_key = models.CharField(max_length=100, db_index=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True, blank=True)
    step = models.PositiveIntegerField(default=1)
    data = models.JSONField(default=dict)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [models.Index(fields=['session_key', 'expires_at'])]

    @classmethod
    def create_session(cls, property_obj=None, ttl_minutes=60, **data):
        return cls.objects.create(
            session_key=secrets.token_urlsafe(24),
            property=property_obj,
            data=data,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )

    @builtins.property
    def is_expired(self):
        return timezone.now() >= self.expires_at


def check_availability(property_obj, room_type, check_in, check_out):
    """Return (ok, available_count, message)."""
    nights = (check_out - check_in).days
    if nights < 1:
        return False, 0, 'Check-out must be after check-in'
    qs = Inventory.objects.filter(
        property=property_obj,
        room_type=room_type,
        date__gte=check_in,
        date__lt=check_out,
    )
    if qs.count() < nights:
        return False, 0, 'Inventory not fully configured for these dates'
    available = min((row.available_rooms for row in qs), default=0)
    if available < 1:
        return False, 0, 'No rooms available'
    return True, available, 'ok'


@transaction.atomic
def create_direct_booking(
    *,
    property_obj,
    room_type,
    rate_plan,
    check_in,
    check_out,
    guest_name,
    guest_email,
    guest_phone='',
    adults=1,
    children=0,
    total_amount=None,
    currency='INR',
    source='booking_engine',
    google_hotel_ads=False,
    channel_host='',
    auto_confirm=True,
):
    """Create DirectBooking + Reservation and decrement inventory."""
    from bookings.models import Reservation

    ok, _, msg = check_availability(property_obj, room_type, check_in, check_out)
    if not ok:
        raise ValueError(msg)

    nights = (check_out - check_in).days
    if total_amount is None:
        base = rate_plan.base_rate if rate_plan else Money(0, currency)
        total_amount = Money(base.amount * nights, base.currency)

    config = getattr(property_obj, 'booking_engine_config', None)
    deposit = None
    if config and config.deposit_percent and total_amount:
        deposit = Money(
            (total_amount.amount * config.deposit_percent) / 100,
            total_amount.currency,
        )

    status = 'CONFIRMED' if auto_confirm else 'PENDING'
    booking = DirectBooking.objects.create(
        property=property_obj,
        room_type=room_type,
        rate_plan=rate_plan,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        guest_name=guest_name,
        guest_email=guest_email,
        guest_phone=guest_phone or '',
        adults=adults,
        children=children,
        total_amount=total_amount,
        currency=str(total_amount.currency),
        deposit_amount=deposit,
        status=status,
        source=source,
        google_hotel_ads=google_hotel_ads,
        channel_host=channel_host,
    )

    reservation = Reservation.objects.create(
        property=property_obj,
        room_type=room_type,
        rate_plan=rate_plan,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        guest_name=guest_name,
        guest_email=guest_email,
        guest_phone=guest_phone or '',
        adults=adults,
        children=children,
        base_room_rate=total_amount,
        total_amount=total_amount,
        currency=str(total_amount.currency),
        status=status,
        provider_name='booking_engine',
        provider_reservation_id=booking.confirmation_code,
        provider_confirmation_code=booking.confirmation_code,
    )
    booking.reservation = reservation
    booking.save(update_fields=['reservation', 'updated_at'])

    for inv in Inventory.objects.filter(
        property=property_obj,
        room_type=room_type,
        date__gte=check_in,
        date__lt=check_out,
        available_rooms__gt=0,
    ):
        inv.available_rooms = max(0, inv.available_rooms - 1)
        inv.save(update_fields=['available_rooms', 'updated_at'])

    return booking
