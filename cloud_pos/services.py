"""POS domain helpers — totals, inventory, table occupancy."""
from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from djmoney.money import Money

from .models import InventoryMovement, MenuItem, POSOrder, POSOrderItem, POSTable


def recalculate_order_totals(order: POSOrder) -> POSOrder:
    agg = order.items.aggregate(s=Sum('line_total'))
    currency = order.total_amount.currency
    subtotal = agg.get('s') or Money(0, currency)
    if not isinstance(subtotal, Money):
        subtotal = Money(subtotal, currency)
    rate = Decimal(str(order.tax_rate or 0)) / Decimal('100')
    tax = Money((subtotal.amount * rate).quantize(Decimal('0.01')), currency)
    total = subtotal + tax
    order.subtotal_amount = subtotal
    order.tax_amount = tax
    order.total_amount = total
    order.save(update_fields=['subtotal_amount', 'tax_amount', 'total_amount'])
    return order


def sync_table_occupancy(table: POSTable | None) -> None:
    if not table:
        return
    openish = table.orders.filter(status__in=['OPEN', 'SENT', 'SERVED', 'HELD', 'BILLED']).exists()
    if table.is_occupied != openish:
        table.is_occupied = openish
        table.save(update_fields=['is_occupied'])


@transaction.atomic
def add_item_to_order(order: POSOrder, menu_item: MenuItem, quantity: int = 1, notes: str = '') -> POSOrderItem:
    quantity = max(1, int(quantity))
    item = POSOrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        quantity=quantity,
        unit_price=menu_item.price,
        line_total=menu_item.price * quantity,
        notes=notes or '',
    )
    recalculate_order_totals(order)
    if order.table_id:
        sync_table_occupancy(order.table)
    return item


@transaction.atomic
def consume_inventory_for_order(order: POSOrder) -> None:
    """Decrement tracked stock when order is sent to kitchen (once)."""
    if order.stock_movements.filter(reason='SALE').exists():
        return
    for line in order.items.select_related('menu_item'):
        mi = line.menu_item
        if not mi.track_inventory:
            continue
        delta = Decimal(line.quantity) * Decimal('-1')
        mi.stock_qty = max(Decimal('0'), Decimal(mi.stock_qty) + delta)
        if mi.stock_qty <= 0:
            mi.is_available = False
        mi.save(update_fields=['stock_qty', 'is_available'])
        InventoryMovement.objects.create(
            menu_item=mi,
            delta=delta,
            reason='SALE',
            order=order,
            note=f'Order #{order.id}',
        )


@transaction.atomic
def adjust_stock(menu_item: MenuItem, delta: Decimal, reason: str = 'ADJUST', note: str = '') -> MenuItem:
    menu_item.stock_qty = max(Decimal('0'), Decimal(menu_item.stock_qty) + Decimal(delta))
    menu_item.track_inventory = True
    if menu_item.stock_qty > 0:
        menu_item.is_available = True
    menu_item.save(update_fields=['stock_qty', 'track_inventory', 'is_available'])
    InventoryMovement.objects.create(
        menu_item=menu_item,
        delta=delta,
        reason=reason,
        note=note,
    )
    return menu_item
