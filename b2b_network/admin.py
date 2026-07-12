from django.contrib import admin
from .models import B2BAgent, B2BAllotment, B2BBooking, B2BRatePlan, CorporateAccount


@admin.register(B2BAgent)
class B2BAgentAdmin(admin.ModelAdmin):
    list_display = [
        'company_name', 'tenant', 'agent_type', 'contact_email',
        'commission_percent', 'is_active', 'portal_enabled',
    ]
    list_filter = ['agent_type', 'is_active', 'portal_enabled']
    search_fields = ['company_name', 'contact_email', 'agent_code']


@admin.register(B2BRatePlan)
class B2BRatePlanAdmin(admin.ModelAdmin):
    list_display = ['agent', 'rate_plan', 'discount_percent', 'net_rate', 'is_active']


@admin.register(CorporateAccount)
class CorporateAccountAdmin(admin.ModelAdmin):
    list_display = ['property', 'agent', 'has_access']


@admin.register(B2BAllotment)
class B2BAllotmentAdmin(admin.ModelAdmin):
    list_display = ['agent', 'property', 'room_type', 'date', 'allocated_rooms', 'used_rooms']
    list_filter = ['date', 'property']


@admin.register(B2BBooking)
class B2BBookingAdmin(admin.ModelAdmin):
    list_display = [
        'confirmation_code', 'agent', 'guest_name', 'property',
        'check_in', 'check_out', 'total_amount', 'status', 'channel_host',
    ]
    list_filter = ['status', 'channel_host']
    search_fields = ['confirmation_code', 'guest_name', 'guest_email']
