from django.contrib import admin
from .models import LinkedRoomUnit, Folio, FolioLineItem, HousekeepingTask


@admin.register(LinkedRoomUnit)
class LinkedRoomUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'property', 'total_rooms', 'sell_as_whole', 'is_active']
    list_filter = ['property', 'sell_as_whole', 'is_active']
    search_fields = ['name', 'property__name']


@admin.register(Folio)
class FolioAdmin(admin.ModelAdmin):
    list_display = ['id', 'guest_name', 'property', 'total_charges', 'balance', 'status', 'created_at']
    list_filter = ['property', 'status']
    search_fields = ['guest_name', 'guest_email']


@admin.register(FolioLineItem)
class FolioLineItemAdmin(admin.ModelAdmin):
    list_display = ['folio', 'item_type', 'description', 'amount', 'quantity', 'created_at']
    list_filter = ['item_type']


@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'property', 'task_type', 'status', 'priority', 'assigned_to', 'due_date']
    list_filter = ['property', 'status', 'priority']
