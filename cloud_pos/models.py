"""
Cloud POS - Point of Sale

F&B billing, waiter/table ops, QR guest ordering, inventory, and delivery aggregators.
"""
import secrets

from django.db import models
from django.core.validators import MinValueValidator
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from simple_history.models import HistoricalRecords
from core.models import Property, TimeStampedModel


def _qr_token():
    return secrets.token_urlsafe(16)


class MenuCategory(TimeStampedModel):
    """Menu category (e.g., Starters, Main Course, Beverages)"""
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pos_menu_categories')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=40, blank=True, help_text='Optional icon key, e.g. burgers, drinks')
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
    image_url = models.URLField(blank=True)
    is_available = models.BooleanField(default=True)
    track_inventory = models.BooleanField(
        default=False,
        help_text='When true, stock_qty is decremented on order send/pay',
    )
    stock_qty = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    low_stock_at = models.DecimalField(max_digits=12, decimal_places=2, default=5)
    history = HistoricalRecords()

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.track_inventory and self.stock_qty <= self.low_stock_at


class POSTable(TimeStampedModel):
    """Restaurant table"""
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pos_tables')
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(default=4)
    section = models.CharField(max_length=80, blank=True, help_text='Floor / section label')
    is_occupied = models.BooleanField(default=False)
    qr_token = models.CharField(max_length=64, unique=True, default=_qr_token, db_index=True)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.property.name} - Table {self.name}"


class POSOrder(TimeStampedModel):
    """POS order — dine-in, takeaway, delivery, room service, or aggregator."""

    STATUS = [
        ('OPEN', 'Open'),
        ('SENT', 'Sent to Kitchen'),
        ('SERVED', 'Served'),
        ('BILLED', 'Billed'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
        ('HELD', 'On Hold'),
    ]

    ORDER_TYPES = [
        ('DINE_IN', 'Dine In'),
        ('TAKEAWAY', 'Takeaway'),
        ('DELIVERY', 'Delivery'),
        ('ROOM_SERVICE', 'Room Service'),
        ('QR', 'QR Guest Order'),
        ('AGGREGATOR', 'Swiggy / Zomato'),
    ]

    CHANNELS = [
        ('POS', 'Billing POS'),
        ('WAITER', 'Waiter App'),
        ('QR', 'QR Ordering'),
        ('SWIGGY', 'Swiggy'),
        ('ZOMATO', 'Zomato'),
        ('OTHER', 'Other'),
    ]

    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='pos_orders')
    table = models.ForeignKey(
        POSTable, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders'
    )
    order_type = models.CharField(max_length=20, choices=ORDER_TYPES, default='DINE_IN')
    channel = models.CharField(max_length=20, choices=CHANNELS, default='POS')
    guest_name = models.CharField(max_length=120, blank=True)
    guest_phone = models.CharField(max_length=30, blank=True)
    delivery_address = models.TextField(blank=True)
    external_order_id = models.CharField(
        max_length=120, blank=True, db_index=True,
        help_text='Partner order id (Swiggy/Zomato)',
    )
    notes = models.TextField(blank=True)

    # Bill to Room
    bill_to_room = models.BooleanField(default=False)
    folio = models.ForeignKey(
        'cloud_pms.Folio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_orders',
    )
    room_number = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=20, choices=STATUS, default='OPEN')
    subtotal_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR')
    )
    tax_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR')
    )
    total_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR')
    )
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5)
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
    notes = models.CharField(max_length=255, blank=True)
    history = HistoricalRecords()


class InventoryMovement(TimeStampedModel):
    """Stock adjustment / consumption log for F&B items."""

    REASONS = [
        ('RECEIVE', 'Stock received'),
        ('SALE', 'Sold on order'),
        ('ADJUST', 'Manual adjustment'),
        ('WASTE', 'Wastage'),
    ]

    id = models.BigAutoField(primary_key=True)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='stock_movements')
    delta = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASONS, default='ADJUST')
    order = models.ForeignKey(
        POSOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements'
    )
    note = models.CharField(max_length=255, blank=True)
    history = HistoricalRecords()


class DeliveryPartnerOrder(TimeStampedModel):
    """Inbound online order from Swiggy / Zomato (manual or API sync)."""

    PARTNERS = [
        ('SWIGGY', 'Swiggy'),
        ('ZOMATO', 'Zomato'),
    ]
    STATUS = [
        ('NEW', 'New'),
        ('ACCEPTED', 'Accepted'),
        ('PREPARING', 'Preparing'),
        ('READY', 'Ready'),
        ('DISPATCHED', 'Dispatched'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected'),
    ]

    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='delivery_orders')
    partner = models.CharField(max_length=20, choices=PARTNERS)
    partner_order_id = models.CharField(max_length=120)
    customer_name = models.CharField(max_length=120, blank=True)
    customer_phone = models.CharField(max_length=30, blank=True)
    items_json = models.JSONField(default=list, blank=True)
    total_amount = MoneyField(
        max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR')
    )
    status = models.CharField(max_length=20, choices=STATUS, default='NEW')
    pos_order = models.OneToOneField(
        POSOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='delivery_partner_order',
    )
    raw_payload = models.JSONField(default=dict, blank=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = [('property', 'partner', 'partner_order_id')]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.partner} #{self.partner_order_id}"
