"""
Custom admin configuration for django-constance
"""
from constance.admin import ConstanceAdmin, Config
from unfold.admin import ModelAdmin
from django.contrib import admin


# Unregister the default Constance admin if it exists
try:
    admin.site.unregister([Config])
except admin.sites.NotRegistered:
    pass


@admin.register(Config)
class CustomConstanceAdmin(ConstanceAdmin, ModelAdmin):
    """Custom Constance admin with Unfold styling"""
    
    change_list_template = 'admin/constance/change_list.html'
    
    class Media:
        css = {
            'all': ('admin/css/constance.css',)
        }
