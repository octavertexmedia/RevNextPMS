"""
RevNext Tours — tours.revnext.in

Industry-grade tour packages: itineraries, departures, seat inventory, public booking.
Standalone billable product — also included in the Hospitality Suite.
"""
import builtins
import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from core.models import TimeStampedModel


def generate_tour_code(prefix='TR'):
    alphabet = string.ascii_uppercase + string.digits
    return prefix + ''.join(secrets.choice(alphabet) for _ in range(8))


class ToursConfig(TimeStampedModel):
    """Per-tenant tours product configuration."""

    tenant = models.OneToOneField(
        'tenants.Tenant', on_delete=models.CASCADE, related_name='tours_config',
    )
    is_enabled = models.BooleanField(default=True)
    default_currency = models.CharField(max_length=3, default='INR')
    brand_name = models.CharField(max_length=200, blank=True)
    support_email = models.EmailField(blank=True)
    cancellation_policy = models.TextField(blank=True)
    require_phone = models.BooleanField(default=True)
    allow_agent_bookings = models.BooleanField(default=True)
    widget_primary_color = models.CharField(max_length=20, default='#1B3A4B')
    terms_url = models.URLField(blank=True)

    class Meta:
        db_table = 'tours_configs'
        verbose_name = 'Tours Config'

    def __str__(self):
        return f'Tours config — {self.tenant}'


class TourPackage(TimeStampedModel):
    """Sellable tour / holiday package."""

    DIFFICULTY = [
        ('EASY', 'Easy'),
        ('MODERATE', 'Moderate'),
        ('CHALLENGING', 'Challenging'),
    ]
    CATEGORY = [
        ('CULTURAL', 'Cultural'),
        ('ADVENTURE', 'Adventure'),
        ('WILDLIFE', 'Wildlife'),
        ('BEACH', 'Beach'),
        ('PILGRIMAGE', 'Pilgrimage'),
        ('CULINARY', 'Culinary'),
        ('CITY', 'City Break'),
        ('CUSTOM', 'Custom'),
    ]

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE, related_name='tour_packages',
    )
    property = models.ForeignKey(
        'core.Property', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tour_packages',
        help_text='Optional linked hotel for overnight stay packages',
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY, default='CULTURAL')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY, default='EASY')
    destinations = models.JSONField(
        default=list, blank=True,
        help_text='List of destination city/region names',
    )
    inclusions = models.JSONField(default=list, blank=True)
    exclusions = models.JSONField(default=list, blank=True)
    highlights = models.JSONField(default=list, blank=True)
    duration_days = models.PositiveIntegerField(default=1)
    duration_nights = models.PositiveIntegerField(default=0)
    min_pax = models.PositiveIntegerField(default=1)
    max_pax = models.PositiveIntegerField(default=20)
    base_price = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    child_price = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True,
    )
    currency = models.CharField(max_length=3, default='INR')
    cover_image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(
        default=False,
        help_text='Visible on public tours.revnext.in storefront',
    )

    class Meta:
        db_table = 'tour_packages'
        unique_together = [('tenant', 'slug')]
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'is_published', 'is_active']),
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:180] or generate_tour_code('PKG').lower()
        if self.duration_nights == 0 and self.duration_days > 0:
            self.duration_nights = max(0, self.duration_days - 1)
        super().save(*args, **kwargs)


class ItineraryDay(TimeStampedModel):
    """Day-by-day itinerary for a package."""

    id = models.BigAutoField(primary_key=True)
    package = models.ForeignKey(TourPackage, on_delete=models.CASCADE, related_name='itinerary_days')
    day_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    meals = models.CharField(max_length=100, blank=True, help_text='e.g. Breakfast, Lunch')
    overnight = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['day_number']
        unique_together = [('package', 'day_number')]

    def __str__(self):
        return f'Day {self.day_number}: {self.title}'


class Departure(TimeStampedModel):
    """Dated departure with seat inventory."""

    STATUS = [
        ('OPEN', 'Open'),
        ('GUARANTEED', 'Guaranteed'),
        ('FULL', 'Full'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    id = models.BigAutoField(primary_key=True)
    package = models.ForeignKey(TourPackage, on_delete=models.CASCADE, related_name='departures')
    start_date = models.DateField()
    end_date = models.DateField()
    capacity = models.PositiveIntegerField(default=20)
    booked_seats = models.PositiveIntegerField(default=0)
    adult_price = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True)
    child_price = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='OPEN')
    cutoff_days = models.PositiveIntegerField(
        default=3,
        help_text='Stop new bookings this many days before start',
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['start_date']
        indexes = [
            models.Index(fields=['package', 'start_date']),
            models.Index(fields=['status', 'start_date']),
        ]
        unique_together = [('package', 'start_date')]

    def __str__(self):
        return f'{self.package.name} @ {self.start_date}'

    @builtins.property
    def seats_remaining(self):
        return max(0, self.capacity - self.booked_seats)

    @builtins.property
    def is_bookable(self):
        if self.status in ('FULL', 'CANCELLED', 'COMPLETED'):
            return False
        if self.seats_remaining < 1:
            return False
        today = timezone.now().date()
        if self.start_date <= today:
            return False
        if (self.start_date - today).days < self.cutoff_days:
            return False
        return True

    def effective_adult_price(self):
        if self.adult_price:
            return self.adult_price
        return self.package.base_price

    def effective_child_price(self):
        if self.child_price:
            return self.child_price
        if self.package.child_price:
            return self.package.child_price
        adult = self.effective_adult_price()
        return Money(adult.amount * 0.7, adult.currency)


class TourAgent(TimeStampedModel):
    """Travel agent who can book tours on tours.revnext.in portal."""

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE, related_name='tour_agents',
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='tour_agent',
    )
    company_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    is_active = models.BooleanField(default=True)
    portal_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name


class TourBooking(TimeStampedModel):
    """Guest or agent booking against a departure."""

    STATUS = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
    ]

    id = models.BigAutoField(primary_key=True)
    departure = models.ForeignKey(Departure, on_delete=models.PROTECT, related_name='bookings')
    package = models.ForeignKey(TourPackage, on_delete=models.PROTECT, related_name='bookings')
    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE, related_name='tour_bookings',
    )
    agent = models.ForeignKey(
        TourAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name='bookings',
    )

    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=20, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    total_pax = models.PositiveIntegerField(default=1)

    total_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    currency = models.CharField(max_length=3, default='INR')
    status = models.CharField(max_length=20, choices=STATUS, default='CONFIRMED')
    confirmation_code = models.CharField(max_length=50, unique=True, blank=True)
    special_requests = models.TextField(blank=True)
    channel_host = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=50, default='tours_engine')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['confirmation_code']),
            models.Index(fields=['guest_email']),
        ]

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = generate_tour_code()
        self.total_pax = self.adults + self.children
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.confirmation_code} — {self.guest_name}'


def check_departure_availability(departure: Departure, pax: int):
    if not departure.package.is_active or not departure.package.is_published:
        # Staff may book unpublished; public callers check publish separately
        pass
    if not departure.is_bookable:
        return False, 0, 'Departure is not bookable'
    if pax < departure.package.min_pax:
        return False, departure.seats_remaining, f'Minimum {departure.package.min_pax} guests'
    if departure.seats_remaining < pax:
        return False, departure.seats_remaining, 'Not enough seats'
    return True, departure.seats_remaining, 'ok'


@transaction.atomic
def create_tour_booking(
    *,
    departure: Departure,
    guest_name,
    guest_email,
    guest_phone='',
    adults=1,
    children=0,
    special_requests='',
    agent=None,
    channel_host='',
    source='tours_engine',
    require_published=True,
):
    dep = Departure.objects.select_for_update().get(pk=departure.pk)
    package = dep.package
    if require_published and (not package.is_published or not package.is_active):
        raise ValueError('Package is not available for booking')

    pax = adults + children
    ok, _, msg = check_departure_availability(dep, pax)
    if not ok:
        raise ValueError(msg)

    config = ToursConfig.objects.filter(tenant=package.tenant).first()
    if config and not config.is_enabled:
        raise ValueError('Tours product disabled for this operator')
    if config and config.require_phone and not guest_phone:
        raise ValueError('Phone number is required')

    adult_rate = dep.effective_adult_price()
    child_rate = dep.effective_child_price()
    total = Money(
        adult_rate.amount * adults + child_rate.amount * children,
        adult_rate.currency,
    )

    booking = TourBooking.objects.create(
        departure=dep,
        package=package,
        tenant=package.tenant,
        agent=agent,
        guest_name=guest_name,
        guest_email=guest_email,
        guest_phone=guest_phone or '',
        adults=adults,
        children=children,
        total_amount=total,
        currency=str(total.currency),
        status='CONFIRMED',
        special_requests=special_requests or '',
        channel_host=channel_host,
        source=source,
    )

    dep.booked_seats += pax
    if dep.seats_remaining <= 0:
        dep.status = 'FULL'
    update_fields = ['booked_seats', 'updated_at']
    if dep.status == 'FULL':
        update_fields.append('status')
    dep.save(update_fields=update_fields)
    return booking
