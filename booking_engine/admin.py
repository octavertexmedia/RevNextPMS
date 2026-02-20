from django.contrib import admin
from .models import DirectBooking, BookingSession


@admin.register(DirectBooking)
class DirectBookingAdmin(admin.ModelAdmin):
    list_display = ['confirmation_code', 'guest_name', 'property', 'check_in', 'check_out', 'total_amount', 'status', 'source']


@admin.register(BookingSession)
class BookingSessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'property', 'step', 'expires_at']
