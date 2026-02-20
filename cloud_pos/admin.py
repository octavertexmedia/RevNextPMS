from django.contrib import admin
from .models import MenuCategory, MenuItem, POSTable, POSOrder, POSOrderItem


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'property', 'display_order', 'is_active']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available']


@admin.register(POSTable)
class POSTableAdmin(admin.ModelAdmin):
    list_display = ['name', 'property', 'capacity', 'is_occupied']


@admin.register(POSOrder)
class POSOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'property', 'table', 'bill_to_room', 'room_number', 'status', 'total_amount']


@admin.register(POSOrderItem)
class POSOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'menu_item', 'quantity', 'unit_price', 'line_total']
