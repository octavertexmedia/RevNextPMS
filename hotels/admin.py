from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import AggregatorListing, ListingClaim, MetasearchFeedJob


@admin.register(AggregatorListing)
class AggregatorListingAdmin(ModelAdmin):
    list_display = ['headline', 'city', 'tenant', 'status', 'is_featured', 'published_at']
    list_filter = ['status', 'is_featured', 'city']
    search_fields = ['headline', 'slug', 'city']
    prepopulated_fields = {'slug': ('headline',)}


@admin.register(ListingClaim)
class ListingClaimAdmin(ModelAdmin):
    list_display = ['listing', 'contact_name', 'contact_email', 'status', 'created_at']
    list_filter = ['status']


@admin.register(MetasearchFeedJob)
class MetasearchFeedJobAdmin(ModelAdmin):
    list_display = ['partner', 'feed_type', 'tenant', 'status', 'listings_count', 'created_at']
    list_filter = ['status', 'partner', 'feed_type']
