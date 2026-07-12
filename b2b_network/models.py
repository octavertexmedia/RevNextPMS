"""
RevNext B2B Networks — corporate & travel-agent product (networks.revnext.in)

Standalone billable product — also included in the Hospitality Suite.
Agent portal, contracted rates, allotments, and B2B bookings.
"""
import builtins
from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from core.models import Inventory, Property, RatePlan, RoomType, TimeStampedModel


class B2BAgent(TimeStampedModel):
    """Corporate partner or travel agent scoped to a tenant."""

    AGENT_TYPES = [
        ('CORPORATE', 'Corporate'),
        ('TRAVEL_AGENT', 'Travel Agent'),
        ('WHOLESALER', 'Wholesaler'),
    ]

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='b2b_agents',
        null=True,
        blank=True,
        help_text='Owning hotel tenant (networks product subscriber)',
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='b2b_agent',
        null=True,
        blank=True,
    )

    company_name = models.CharField(max_length=255)
    agent_code = models.CharField(max_length=40, blank=True, db_index=True)
    agent_type = models.CharField(max_length=20, choices=AGENT_TYPES)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)

    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    credit_limit = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True,
    )

    is_active = models.BooleanField(default=True)
    portal_enabled = models.BooleanField(
        default=True,
        help_text='Allow this agent to use the networks.revnext.in portal',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['company_name']
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['agent_code']),
        ]

    def __str__(self):
        return self.company_name


class B2BRatePlan(TimeStampedModel):
    """Special B2B contracted rate for a rate plan."""

    id = models.BigAutoField(primary_key=True)
    agent = models.ForeignKey(B2BAgent, on_delete=models.CASCADE, related_name='rate_plans')
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name='b2b_rates')

    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    net_rate = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True,
    )

    is_active = models.BooleanField(default=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ['agent', 'rate_plan']

    def effective_rate(self):
        """Return Money for one night at contracted terms."""
        if self.net_rate:
            return self.net_rate
        base = self.rate_plan.base_rate
        if self.discount_percent:
            amount = base.amount * (1 - (self.discount_percent / 100))
            return Money(amount, base.currency)
        return base


class CorporateAccount(TimeStampedModel):
    """Property access grant for an agent."""

    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='corporate_accounts')
    agent = models.ForeignKey(B2BAgent, on_delete=models.CASCADE, related_name='property_access')
    has_access = models.BooleanField(default=True)

    class Meta:
        unique_together = ['property', 'agent']


class B2BAllotment(TimeStampedModel):
    """Room allotment reserved for an agent on a property/room type."""

    id = models.BigAutoField(primary_key=True)
    agent = models.ForeignKey(B2BAgent, on_delete=models.CASCADE, related_name='allotments')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='b2b_allotments')
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='b2b_allotments')
    date = models.DateField()
    allocated_rooms = models.PositiveIntegerField(default=0)
    used_rooms = models.PositiveIntegerField(default=0)
    release_days = models.PositiveIntegerField(
        default=7,
        help_text='Days before arrival when unused allotment is released',
    )

    class Meta:
        unique_together = ['agent', 'property', 'room_type', 'date']
        ordering = ['date']
        indexes = [
            models.Index(fields=['agent', 'date']),
            models.Index(fields=['property', 'date']),
        ]

    @builtins.property
    def remaining(self):
        return max(0, self.allocated_rooms - self.used_rooms)


class B2BBooking(TimeStampedModel):
    """Booking placed by a B2B agent (portal or API)."""

    STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('CHECKED_IN', 'Checked In'),
        ('CHECKED_OUT', 'Checked Out'),
    ]

    id = models.BigAutoField(primary_key=True)
    agent = models.ForeignKey(B2BAgent, on_delete=models.PROTECT, related_name='bookings')
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name='b2b_bookings')
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name='b2b_bookings')
    rate_plan = models.ForeignKey(
        RatePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='b2b_bookings',
    )
    b2b_rate = models.ForeignKey(
        B2BRatePlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings',
    )

    check_in = models.DateField()
    check_out = models.DateField()
    nights = models.PositiveIntegerField(default=1)

    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField(blank=True)
    guest_phone = models.CharField(max_length=20, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)

    total_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    commission_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True,
    )
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS, default='CONFIRMED')
    confirmation_code = models.CharField(max_length=50, unique=True, blank=True)
    channel_host = models.CharField(max_length=100, blank=True)
    special_requests = models.TextField(blank=True)

    reservation = models.ForeignKey(
        'bookings.Reservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='b2b_booking',
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['agent', 'status']),
            models.Index(fields=['confirmation_code']),
            models.Index(fields=['property', 'check_in']),
        ]

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            from booking_engine.models import generate_confirmation_code
            self.confirmation_code = generate_confirmation_code(prefix='B2B')
        if self.check_in and self.check_out:
            self.nights = max(1, (self.check_out - self.check_in).days)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.confirmation_code} — {self.guest_name}'


def agent_has_property_access(agent: B2BAgent, property_obj: Property) -> bool:
    return CorporateAccount.objects.filter(
        agent=agent, property=property_obj, has_access=True,
    ).exists()


@transaction.atomic
def create_b2b_booking(
    *,
    agent: B2BAgent,
    property_obj: Property,
    room_type: RoomType,
    check_in,
    check_out,
    guest_name,
    guest_email='',
    guest_phone='',
    adults=1,
    children=0,
    rate_plan=None,
    special_requests='',
    channel_host='',
    use_allotment=True,
):
    """Create a B2B booking, optionally consuming allotment then inventory."""
    from bookings.models import Reservation

    if not agent.is_active or not agent.portal_enabled:
        raise ValueError('Agent is not active')
    if not agent_has_property_access(agent, property_obj):
        raise ValueError('Agent does not have access to this property')

    nights = (check_out - check_in).days
    if nights < 1:
        raise ValueError('Check-out must be after check-in')

    b2b_rate = None
    if rate_plan:
        b2b_rate = B2BRatePlan.objects.filter(
            agent=agent, rate_plan=rate_plan, is_active=True,
        ).first()

    if b2b_rate:
        night_rate = b2b_rate.effective_rate()
    elif rate_plan:
        night_rate = rate_plan.base_rate
    else:
        night_rate = Money(0, 'INR')

    total = Money(night_rate.amount * nights, night_rate.currency)
    commission = Money(
        (total.amount * agent.commission_percent) / 100,
        total.currency,
    )

    # Prefer allotment, else open inventory
    dates = [check_in + timedelta(days=i) for i in range(nights)]
    if use_allotment:
        allotments = list(B2BAllotment.objects.select_for_update().filter(
            agent=agent,
            property=property_obj,
            room_type=room_type,
            date__in=dates,
        ))
        if len(allotments) == nights and all(a.remaining > 0 for a in allotments):
            for a in allotments:
                a.used_rooms += 1
                a.save(update_fields=['used_rooms', 'updated_at'])
        else:
            # Fall back to open inventory
            for d in dates:
                inv = Inventory.objects.select_for_update().filter(
                    property=property_obj, room_type=room_type, date=d, available_rooms__gt=0,
                ).first()
                if not inv:
                    raise ValueError(f'No availability on {d}')
                inv.available_rooms = max(0, inv.available_rooms - 1)
                inv.save(update_fields=['available_rooms', 'updated_at'])
    else:
        for d in dates:
            inv = Inventory.objects.select_for_update().filter(
                property=property_obj, room_type=room_type, date=d, available_rooms__gt=0,
            ).first()
            if not inv:
                raise ValueError(f'No availability on {d}')
            inv.available_rooms = max(0, inv.available_rooms - 1)
            inv.save(update_fields=['available_rooms', 'updated_at'])

    booking = B2BBooking.objects.create(
        agent=agent,
        property=property_obj,
        room_type=room_type,
        rate_plan=rate_plan,
        b2b_rate=b2b_rate,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        guest_name=guest_name,
        guest_email=guest_email or '',
        guest_phone=guest_phone or '',
        adults=adults,
        children=children,
        total_amount=total,
        commission_amount=commission,
        currency=str(total.currency),
        status='CONFIRMED',
        channel_host=channel_host,
        special_requests=special_requests or '',
    )

    reservation = Reservation.objects.create(
        property=property_obj,
        room_type=room_type,
        rate_plan=rate_plan,
        check_in=check_in,
        check_out=check_out,
        nights=nights,
        guest_name=guest_name,
        guest_email=guest_email or agent.contact_email,
        guest_phone=guest_phone or '',
        adults=adults,
        children=children,
        base_room_rate=total,
        total_amount=total,
        currency=str(total.currency),
        status='CONFIRMED',
        provider_name='b2b_network',
        provider_reservation_id=booking.confirmation_code,
        provider_confirmation_code=booking.confirmation_code,
        special_requests=special_requests or '',
        provider_specific_data={
            'agent_id': agent.id,
            'agent_name': agent.company_name,
            'commission_percent': float(agent.commission_percent),
        },
    )
    booking.reservation = reservation
    booking.save(update_fields=['reservation', 'updated_at'])
    return booking
