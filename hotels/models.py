"""
RevNext Hotels Aggregator — hotels.revnext.in

Public hotel discovery, listing claims, and availability fan-out across
tenant properties. OTA listing ops (/ota-listing/) and Google Hotel Ads
remain companion apps under the same billable product (`aggregator`).
"""
import builtins
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify
from djmoney.models.fields import MoneyField
from djmoney.money import Money

from core.models import Inventory, Property, RatePlan, RoomType, TimeStampedModel


def generate_claim_token():
    return secrets.token_urlsafe(24)


class AggregatorListing(TimeStampedModel):
    """Published hotel listing on hotels.revnext.in discovery index."""

    STATUS = [
        ('DRAFT', 'Draft'),
        ('PENDING_REVIEW', 'Pending Review'),
        ('PUBLISHED', 'Published'),
        ('SUSPENDED', 'Suspended'),
    ]

    id = models.BigAutoField(primary_key=True)
    property = models.OneToOneField(
        Property, on_delete=models.CASCADE, related_name='aggregator_listing',
    )
    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE, related_name='aggregator_listings',
    )
    slug = models.SlugField(max_length=220, unique=True)
    headline = models.CharField(max_length=255, blank=True)
    summary = models.TextField(blank=True)
    amenities = models.JSONField(default=list, blank=True)
    star_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    cover_image_url = models.URLField(blank=True)
    gallery = models.JSONField(default=list, blank=True)
    check_in_time = models.CharField(max_length=20, blank=True, default='14:00')
    check_out_time = models.CharField(max_length=20, blank=True, default='11:00')
    status = models.CharField(max_length=20, choices=STATUS, default='DRAFT')
    is_featured = models.BooleanField(default=False)
    is_claimable = models.BooleanField(
        default=False,
        help_text='Allow unverified partners to claim this listing',
    )
    booking_engine_url = models.URLField(
        blank=True,
        help_text='Deep link to booking.revnext.in widget or property site',
    )
    min_price_hint = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', null=True, blank=True,
    )
    city = models.CharField(max_length=100, blank=True, db_index=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='India')
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-is_featured', 'city', 'headline']
        indexes = [
            models.Index(fields=['status', 'city']),
            models.Index(fields=['tenant', 'status']),
        ]

    def __str__(self):
        return self.headline or self.property.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.headline or self.property.name)[:180]
            self.slug = f'{base}-{self.property_id}'
        if not self.city and self.property_id:
            self.city = self.property.city
            self.state = self.property.state
            self.country = self.property.country
        if not self.headline and self.property_id:
            self.headline = self.property.name
        if self.status == 'PUBLISHED' and not self.published_at:
            self.published_at = timezone.now()
        if not self.booking_engine_url and self.property_id:
            self.booking_engine_url = f'https://booking.revnext.in/booking/widget/{self.property_id}/'
        super().save(*args, **kwargs)

    @builtins.property
    def is_public(self):
        return self.status == 'PUBLISHED'


class ListingClaim(TimeStampedModel):
    """Partner claim to own / manage a listing."""

    STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('EXPIRED', 'Expired'),
    ]

    id = models.BigAutoField(primary_key=True)
    listing = models.ForeignKey(AggregatorListing, on_delete=models.CASCADE, related_name='claims')
    claimant_tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE, related_name='listing_claims',
        null=True, blank=True,
    )
    claimant_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='listing_claims',
    )
    contact_email = models.EmailField()
    contact_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True)
    evidence_url = models.URLField(blank=True)
    evidence_notes = models.TextField(blank=True)
    verification_token = models.CharField(max_length=64, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.verification_token:
            self.verification_token = generate_claim_token()
        super().save(*args, **kwargs)


class MetasearchFeedJob(TimeStampedModel):
    """Metasearch / GHA-style feed export job record."""

    STATUS = [
        ('QUEUED', 'Queued'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]
    FEED_TYPES = [
        ('HOTEL_LIST', 'Hotel list'),
        ('LANDING_PAGES', 'Landing pages'),
        ('ARI', 'Availability & rates'),
    ]

    id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        'tenants.Tenant', on_delete=models.CASCADE, related_name='metasearch_jobs',
        null=True, blank=True,
    )
    feed_type = models.CharField(max_length=30, choices=FEED_TYPES, default='HOTEL_LIST')
    partner = models.CharField(max_length=50, default='google_hotel_ads')
    status = models.CharField(max_length=20, choices=STATUS, default='QUEUED')
    listings_count = models.PositiveIntegerField(default=0)
    artifact_url = models.URLField(blank=True)
    payload_summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


def sync_listing_from_property(property_obj, publish=False) -> AggregatorListing:
    """Create or update aggregator listing snapshot from a Property."""
    listing, _ = AggregatorListing.objects.get_or_create(
        property=property_obj,
        defaults={
            'tenant': property_obj.tenant,
            'headline': property_obj.name,
            'city': property_obj.city,
            'state': property_obj.state,
            'country': property_obj.country,
            'summary': getattr(property_obj, 'description', '') or '',
        },
    )
    listing.tenant = property_obj.tenant
    listing.city = property_obj.city
    listing.state = property_obj.state
    listing.country = property_obj.country
    if not listing.headline:
        listing.headline = property_obj.name
    if publish:
        listing.status = 'PUBLISHED'
    listing.save()
    return listing


def search_listings(*, city='', check_in=None, check_out=None, guests=2, q='', featured_only=False):
    """Return published listings, optionally filtered by inventory availability."""
    qs = AggregatorListing.objects.filter(status='PUBLISHED').select_related('property', 'tenant')
    if city:
        qs = qs.filter(city__icontains=city)
    if q:
        qs = qs.filter(Q(headline__icontains=q) | Q(summary__icontains=q) | Q(city__icontains=q))
    if featured_only:
        qs = qs.filter(is_featured=True)

    results = []
    for listing in qs[:100]:
        item = {
            'listing': listing,
            'available': True,
            'from_price': listing.min_price_hint,
            'nights': None,
        }
        if check_in and check_out and listing.property_id:
            nights = (check_out - check_in).days
            item['nights'] = nights
            if nights < 1:
                item['available'] = False
            else:
                dates = [check_in + timedelta(days=i) for i in range(nights)]
                room_types = RoomType.objects.filter(property=listing.property, is_active=True)
                best = None
                any_ok = False
                for rt in room_types:
                    inv = Inventory.objects.filter(
                        property=listing.property, room_type=rt, date__in=dates, available_rooms__gt=0,
                    )
                    if inv.count() < nights:
                        continue
                    any_ok = True
                    plan = RatePlan.objects.filter(room_type=rt, is_active=True).first()
                    if plan:
                        total = Money(plan.base_rate.amount * nights, plan.base_rate.currency)
                        if best is None or total.amount < best.amount:
                            best = total
                item['available'] = any_ok
                if best:
                    item['from_price'] = best
        results.append(item)
    return results
