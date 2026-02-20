from django.contrib import admin
from .models import SiteTemplate, PropertyWebsite


@admin.register(SiteTemplate)
class SiteTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']


@admin.register(PropertyWebsite)
class PropertyWebsiteAdmin(admin.ModelAdmin):
    list_display = ['property', 'template', 'custom_domain', 'ssl_enabled', 'is_published']
