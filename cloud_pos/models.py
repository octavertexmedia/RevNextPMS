"""
Cloud POS - Point of Sale

F&B management, touch-friendly, Bill to Room integration with PMS folios.
"""
from django.db import models
from django.core.validators import MinValueValidator
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from simple_history.models import HistoricalRecords
from core.models import Property, TimeStampedModel


class MenuCategory(TimeStampedModel):
    """Menu category (e.g., Starters, Main Course, Beverages)"""
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pos_menu_categories')
    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.property.name} - {self.name}"


class MenuItem(TimeStampedModel):
    """POS menu item"""
    id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(MenuCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    is_available = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class POSTable(TimeStampedModel):
    """Restaurant table"""
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pos_tables')
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=4)
    is_occupied = models.BooleanField(default=False)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.property.name} - Table {self.name}"


class POSOrder(TimeStampedModel):
    """POS order - can be Bill to Room"""
    
    STATUS = [
        ('OPEN', 'Open'),
        ('SENT', 'Sent to Kitchen'),
        ('SERVED', 'Served'),
        ('BILLED', 'Billed'),
        ('PAID', 'Paid'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pos_orders')
    table = models.ForeignKey(POSTable, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Bill to Room
    bill_to_room = models.BooleanField(default=False)
    folio = models.ForeignKey(
        'cloud_pms.Folio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_orders'
    )
    room_number = models.CharField(max_length=50, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS, default='OPEN')
    total_amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.get_status_display()}"


class POSOrderItem(TimeStampedModel):
    """Line item in POS order"""
    id = models.BigAutoField(primary_key=True)
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    line_total = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    history = HistoricalRecords()
