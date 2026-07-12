from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Departure, ItineraryDay, TourAgent, TourBooking, TourPackage, ToursConfig


@admin.register(ToursConfig)
class ToursConfigAdmin(ModelAdmin):
    list_display = ['tenant', 'is_enabled', 'default_currency', 'brand_name']


@admin.register(TourPackage)
class TourPackageAdmin(ModelAdmin):
    list_display = ['name', 'tenant', 'category', 'duration_days', 'base_price', 'is_published', 'is_active']
    list_filter = ['is_active', 'is_published', 'category']
    search_fields = ['name', 'slug', 'tenant__name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ItineraryDay)
class ItineraryDayAdmin(ModelAdmin):
    list_display = ['package', 'day_number', 'title', 'location']
    list_filter = ['package']


@admin.register(Departure)
class DepartureAdmin(ModelAdmin):
    list_display = ['package', 'start_date', 'end_date', 'capacity', 'booked_seats', 'status']
    list_filter = ['status']


@admin.register(TourAgent)
class TourAgentAdmin(ModelAdmin):
    list_display = ['company_name', 'tenant', 'contact_email', 'is_active', 'portal_enabled']


@admin.register(TourBooking)
class TourBookingAdmin(ModelAdmin):
    list_display = ['confirmation_code', 'guest_name', 'package', 'departure', 'total_pax', 'status']
    list_filter = ['status']
    search_fields = ['confirmation_code', 'guest_email', 'guest_name']
