from django.contrib import admin
from .models import BookingEngineConfig, DirectBooking, BookingSession


@admin.register(BookingEngineConfig)
class BookingEngineConfigAdmin(admin.ModelAdmin):
    list_display = ['property', 'is_enabled', 'default_currency', 'deposit_percent', 'google_hotel_ads_enabled']
    list_filter = ['is_enabled', 'google_hotel_ads_enabled']


@admin.register(DirectBooking)
class DirectBookingAdmin(admin.ModelAdmin):
    list_display = [
        'confirmation_code', 'guest_name', 'property', 'check_in', 'check_out',
        'total_amount', 'status', 'source', 'channel_host',
    ]
    list_filter = ['status', 'source', 'channel_host']
    search_fields = ['confirmation_code', 'guest_email', 'guest_name']


@admin.register(BookingSession)
class BookingSessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'property', 'step', 'expires_at']
