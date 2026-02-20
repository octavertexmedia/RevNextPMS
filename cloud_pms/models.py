"""
Cloud PMS - Property Management System

Front desk, housekeeping, billing, Linked Room (villa/apartment) support.
Integrates with Bill to Room from Cloud POS.
"""
from django.db import models
from django.core.validators import MinValueValidator
from djmoney.models.fields import MoneyField
from djmoney.money import Money
from simple_history.models import HistoricalRecords
from core.models import Property, RoomType, TimeStampedModel


class LinkedRoomUnit(TimeStampedModel):
    """
    Villa/Apartment unit that can be sold as whole or as individual rooms.
    Linked Room feature - syncs unit vs. room inventory.
    """
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='linked_units')
    name = models.CharField(max_length=255, help_text="Unit name, e.g., 'Villa A', 'Apartment 101'")
    
    # Unit can be sold as whole or as individual rooms
    room_types = models.ManyToManyField(
        RoomType,
        blank=True,
        related_name='linked_units',
        help_text="Room types in this unit (for individual room sales)"
    )
    total_rooms = models.PositiveIntegerField(default=1, help_text="Number of rooms in unit")
    
    # Whole-unit sale
    sell_as_whole = models.BooleanField(default=True, help_text="Can sell entire unit as one booking")
    whole_unit_price_multiplier = models.DecimalField(
        max_digits=5, decimal_places=2, default=1.0,
        help_text="Price multiplier when selling whole unit (e.g., 0.9 for 10% discount)"
    )
    
    is_active = models.BooleanField(default=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ['property', 'name']
        verbose_name = 'Linked Room Unit'
        verbose_name_plural = 'Linked Room Units'

    def __str__(self):
        return f"{self.property.name} - {self.name}"


class Folio(TimeStampedModel):
    """Guest folio for billing - combines room charges, POS, etc."""
    
    STATUS = [
        ('OPEN', 'Open'),
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Paid'),
        ('CLOSED', 'Closed'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='folios')
    
    # Link to reservation (from bookings app)
    reservation = models.ForeignKey(
        'bookings.Reservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='folios'
    )
    
    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField(blank=True)
    room_number = models.CharField(max_length=50, blank=True)
    
    # Totals
    total_charges = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    total_payments = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    balance = MoneyField(max_digits=14, decimal_places=2, default_currency='INR', default=Money(0, 'INR'))
    
    status = models.CharField(max_length=20, default='OPEN')
    closed_at = models.DateTimeField(null=True, blank=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Folio {self.id} - {self.guest_name}"


class FolioLineItem(TimeStampedModel):
    """Individual charge or payment on a folio"""
    
    TYPE = [
        ('ROOM', 'Room Charge'),
        ('POS', 'POS / F&B'),
        ('MINIBAR', 'Minibar'),
        ('SERVICE', 'Service Charge'),
        ('TAX', 'Tax'),
        ('PAYMENT', 'Payment'),
        ('ADJUSTMENT', 'Adjustment'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    folio = models.ForeignKey(Folio, on_delete=models.CASCADE, related_name='line_items')
    
    item_type = models.CharField(max_length=20, choices=TYPE)
    description = models.CharField(max_length=500)
    amount = MoneyField(max_digits=14, decimal_places=2, default_currency='INR')
    quantity = models.PositiveIntegerField(default=1)
    
    # For Bill to Room from POS
    pos_order_id = models.CharField(max_length=100, blank=True)
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['created_at']


class HousekeepingTask(TimeStampedModel):
    """Housekeeping task for a room"""
    
    STATUS = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('INSPECTED', 'Inspected'),
        ('COMPLETED', 'Completed'),
    ]
    
    PRIORITY = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='housekeeping_tasks')
    
    room_number = models.CharField(max_length=50)
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True, blank=True)
    
    task_type = models.CharField(max_length=50, default='Cleaning')
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING')
    priority = models.CharField(max_length=20, choices=PRIORITY, default='NORMAL')
    
    assigned_to = models.CharField(max_length=255, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Link to reservation for check-out cleaning
    reservation = models.ForeignKey(
        'bookings.Reservation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='housekeeping_tasks'
    )
    
    history = HistoricalRecords()

    class Meta:
        ordering = ['-priority', 'due_date', 'created_at']

    def __str__(self):
        return f"{self.room_number} - {self.task_type} ({self.get_status_display()})"
