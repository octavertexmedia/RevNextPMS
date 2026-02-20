"""
Google Hotel Ads - Pay-Per-Conversion

Display real-time rates on Google Search & Maps. Pay only for confirmed bookings.
"""
from django.db import models
from core.models import Property, TimeStampedModel


class HotelAdsConfig(TimeStampedModel):
    """Google Hotel Ads configuration per property"""
    id = models.BigAutoField(primary_key=True)
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='hotel_ads_config')
    
    # Google Hotel Ads IDs
    google_hotel_id = models.CharField(max_length=100, blank=True)
    partner_hotel_id = models.CharField(max_length=100, blank=True)
    
    # Pay-Per-Conversion
    is_enabled = models.BooleanField(default=False)
    commission_model = models.CharField(max_length=50, default='pay_per_conversion')
    
    # Feed
    last_feed_submitted = models.DateTimeField(null=True, blank=True)
    feed_status = models.CharField(max_length=50, blank=True)

    class Meta:
        verbose_name = 'Google Hotel Ads Config'
        verbose_name_plural = 'Google Hotel Ads Configs'


class FeedSubmission(TimeStampedModel):
    """Record of feed submissions to Google"""
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='hotel_ads_feeds')
    
    status = models.CharField(max_length=50)
    rooms_count = models.PositiveIntegerField(default=0)
    rates_count = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    response_data = models.JSONField(default=dict, blank=True)
