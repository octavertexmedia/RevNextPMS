from django.contrib import admin
from .models import ListingProject, OTAListingStatus


@admin.register(ListingProject)
class ListingProjectAdmin(admin.ModelAdmin):
    list_display = ['property', 'platform', 'status', 'listing_score', 'completed_at']


@admin.register(OTAListingStatus)
class OTAListingStatusAdmin(admin.ModelAdmin):
    list_display = ['property_integration', 'status', 'recorded_at']
