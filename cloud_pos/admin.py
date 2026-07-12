from django.contrib import admin
from .models import (
    MenuCategory, MenuItem, POSTable, POSOrder, POSOrderItem,
    InventoryMovement, DeliveryPartnerOrder,
)


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'property', 'icon', 'display_order', 'is_active']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'is_available', 'track_inventory', 'stock_qty']
    list_filter = ['is_available', 'track_inventory']


@admin.register(POSTable)
class POSTableAdmin(admin.ModelAdmin):
    list_display = ['name', 'property', 'section', 'capacity', 'is_occupied', 'qr_token']
    readonly_fields = ['qr_token']


class POSOrderItemInline(admin.TabularInline):
    model = POSOrderItem
    extra = 0


@admin.register(POSOrder)
class POSOrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'property', 'order_type', 'channel', 'table',
        'bill_to_room', 'status', 'total_amount',
    ]
    list_filter = ['order_type', 'channel', 'status']
    inlines = [POSOrderItemInline]


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ['menu_item', 'delta', 'reason', 'order', 'created_at']


@admin.register(DeliveryPartnerOrder)
class DeliveryPartnerOrderAdmin(admin.ModelAdmin):
    list_display = ['partner', 'partner_order_id', 'property', 'status', 'total_amount', 'pos_order']
    list_filter = ['partner', 'status']
