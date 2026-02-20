from django.contrib import admin
from .models import HotelAdsConfig, FeedSubmission


@admin.register(HotelAdsConfig)
class HotelAdsConfigAdmin(admin.ModelAdmin):
    list_display = ['property', 'is_enabled', 'commission_model', 'last_feed_submitted']


@admin.register(FeedSubmission)
class FeedSubmissionAdmin(admin.ModelAdmin):
    list_display = ['property', 'status', 'rooms_count', 'rates_count', 'submitted_at']
