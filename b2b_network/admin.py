from django.contrib import admin
from .models import B2BAgent, B2BRatePlan, CorporateAccount


@admin.register(B2BAgent)
class B2BAgentAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'agent_type', 'contact_email', 'commission_percent', 'is_active']


@admin.register(B2BRatePlan)
class B2BRatePlanAdmin(admin.ModelAdmin):
    list_display = ['agent', 'rate_plan', 'discount_percent', 'net_rate', 'is_active']


@admin.register(CorporateAccount)
class CorporateAccountAdmin(admin.ModelAdmin):
    list_display = ['property', 'agent', 'has_access']
