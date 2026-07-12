"""
Seed a ready-to-demo Cloud POS outlet (menu, tables/QR, inventory, aggregator inbox).

Usage:
  python manage.py seed_pos_demo
  python manage.py seed_pos_demo --reset
"""
from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from djmoney.money import Money

from cloud_pos.models import (
    DeliveryPartnerOrder,
    MenuCategory,
    MenuItem,
    POSTable,
)
from core.models import Property
from tenants.models import SubscriptionPlan, Tenant, TenantUser


MENU = [
    ('Burgers', 'burgers', [
        ('Veg Burger', '149', True, '40'),
        ('Chicken Burger', '179', True, '35'),
        ('Cheese Burger', '199', True, '30'),
    ]),
    ('Pizza', 'pizza', [
        ('Margherita', '299', True, '25'),
        ('Farmhouse', '349', True, '20'),
        ('Pepperoni', '399', True, '18'),
    ]),
    ('Pasta', 'pasta', [
        ('Alfredo', '249', True, '22'),
        ('Arrabbiata', '229', True, '22'),
    ]),
    ('Drinks', 'drinks', [
        ('Cold Coffee', '99', True, '50'),
        ('Fresh Lime', '79', True, '60'),
        ('Cola', '59', True, '80'),
    ]),
    ('Desserts', 'desserts', [
        ('Brownie', '129', True, '15'),
        ('Ice Cream Scoop', '89', True, '40'),
    ]),
    ('Combo', 'combo', [
        ('Burger + Drink', '199', False, '0'),
        ('Pizza Combo', '399', False, '0'),
    ]),
]

TABLES = [
    ('T1', 'Main hall', 2),
    ('T2', 'Main hall', 4),
    ('T3', 'Main hall', 4),
    ('T4', 'Patio', 4),
    ('T5', 'Patio', 6),
    ('T6', 'Private', 8),
]


class Command(BaseCommand):
    help = 'Seed demo Cloud POS outlet with Billing/Waiter/QR/Inventory/Aggregator data'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Wipe and recreate POS demo outlet data')

    @transaction.atomic
    def handle(self, *args, **options):
        tenant = self._ensure_tenant()
        user = self._ensure_user(tenant)
        self._ensure_pos_entitlement(tenant)
        prop = self._ensure_property(tenant)

        if options['reset']:
            DeliveryPartnerOrder.objects.filter(property=prop).delete()
            MenuItem.objects.filter(category__property=prop).delete()
            MenuCategory.objects.filter(property=prop).delete()
            POSTable.objects.filter(property=prop).delete()
            self.stdout.write(self.style.WARNING(f'Reset POS data for {prop.name}'))

        self._seed_menu(prop)
        tables = self._seed_tables(prop)
        self._seed_delivery(prop)
        self._print_summary(tenant, user, prop, tables)

    def _ensure_tenant(self) -> Tenant:
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name='pos-demo',
            defaults={
                'display_name': 'POS Demo',
                'monthly_price': Money(0, 'INR'),
                'yearly_price': Money(0, 'INR'),
                'max_properties': 3,
                'max_integrations_per_property': 5,
                'max_users': 10,
                'max_api_calls_per_month': 10000,
                'is_active': True,
                'is_visible': False,
            },
        )
        tenant, created = Tenant.objects.get_or_create(
            slug='revnext-pos-demo',
            defaults={
                'name': 'RevNext POS Demo',
                'email': 'pos-demo@revnext.in',
                'subscription_plan': plan,
                'subscription_status': 'active',
                'max_properties': 3,
                'is_active': True,
            },
        )
        tenant.subscription_plan = plan
        tenant.subscription_status = 'active'
        tenant.is_active = True
        tenant.save()
        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} tenant {tenant.name}"
        ))
        return tenant

    def _ensure_user(self, tenant: Tenant) -> TenantUser:
        user, created = TenantUser.objects.get_or_create(
            username='posdemo',
            defaults={
                'email': 'posdemo@revnext.in',
                'tenant': tenant,
                'role': 'owner',
                'first_name': 'POS',
                'last_name': 'Demo',
                'is_staff': True,
            },
        )
        user.tenant = tenant
        user.role = 'owner'
        user.email = 'posdemo@revnext.in'
        user.is_staff = True
        user.is_active = True
        user.set_password('posdemo123')
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} user posdemo / posdemo123"
        ))
        return user

    def _ensure_pos_entitlement(self, tenant: Tenant) -> None:
        try:
            from products.models import ProductPlan
            from products.services import entitled_product_codes, start_product_trial
            if 'pos' in entitled_product_codes(tenant):
                return
            plan = (
                ProductPlan.objects.filter(product__code='pos', is_active=True)
                .order_by('id')
                .first()
            )
            if not plan:
                plan = ProductPlan.objects.filter(
                    package_products__code='pos', is_active=True
                ).order_by('id').first()
            if plan:
                start_product_trial(tenant, plan)
                self.stdout.write(self.style.SUCCESS(f'Granted POS trial via {plan.code}'))
            else:
                self.stdout.write(self.style.WARNING(
                    'No POS ProductPlan found — run seed_products; middleware may block /pos/'
                ))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'POS entitlement skipped: {exc}'))

    def _ensure_property(self, tenant: Tenant) -> Property:
        prop, created = Property.objects.get_or_create(
            tenant=tenant,
            name='All-Day Dining Outlet',
            defaults={
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'postal_code': '400001',
                'country': 'India',
                'address_line1': 'RevNext Demo Kitchen',
                'property_type': 'other',
                'timezone': 'Asia/Kolkata',
                'currency': 'INR',
                'is_active': True,
            },
        )
        if not created:
            prop.is_active = True
            prop.save(update_fields=['is_active', 'updated_at'])
        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Using'} property {prop.name}"
        ))
        return prop

    def _seed_menu(self, prop: Property) -> None:
        for order, (name, icon, items) in enumerate(MENU):
            cat, _ = MenuCategory.objects.update_or_create(
                property=prop,
                name=name,
                defaults={'icon': icon, 'display_order': order, 'is_active': True},
            )
            for iname, price, track, stock in items:
                MenuItem.objects.update_or_create(
                    category=cat,
                    name=iname,
                    defaults={
                        'description': iname,
                        'price': Money(price, 'INR'),
                        'is_available': True,
                        'track_inventory': track,
                        'stock_qty': Decimal(stock),
                        'low_stock_at': Decimal('5'),
                    },
                )
        self.stdout.write(self.style.SUCCESS(
            f'Menu: {MenuCategory.objects.filter(property=prop).count()} categories, '
            f'{MenuItem.objects.filter(category__property=prop).count()} items'
        ))

    def _seed_tables(self, prop: Property) -> list[POSTable]:
        tables = []
        for name, section, capacity in TABLES:
            table, _ = POSTable.objects.update_or_create(
                property=prop,
                name=name,
                defaults={
                    'section': section,
                    'capacity': capacity,
                    'is_occupied': False,
                },
            )
            if not table.qr_token:
                from cloud_pos.models import _qr_token
                table.qr_token = _qr_token()
                table.save(update_fields=['qr_token'])
            tables.append(table)
        self.stdout.write(self.style.SUCCESS(f'Tables: {len(tables)} with QR tokens'))
        return tables

    def _seed_delivery(self, prop: Property) -> None:
        DeliveryPartnerOrder.objects.update_or_create(
            property=prop,
            partner='SWIGGY',
            partner_order_id='SWG-DEMO-1001',
            defaults={
                'customer_name': 'Asha K.',
                'customer_phone': '9876500011',
                'items_json': [
                    {'name': 'Margherita', 'qty': 1},
                    {'name': 'Cold Coffee', 'qty': 2},
                ],
                'total_amount': Money('497', 'INR'),
                'status': 'NEW',
            },
        )
        DeliveryPartnerOrder.objects.update_or_create(
            property=prop,
            partner='ZOMATO',
            partner_order_id='ZOM-DEMO-2044',
            defaults={
                'customer_name': 'Rahul M.',
                'customer_phone': '9876500022',
                'items_json': [
                    {'name': 'Veg Burger', 'qty': 2},
                    {'name': 'Cola', 'qty': 2},
                ],
                'total_amount': Money('416', 'INR'),
                'status': 'NEW',
            },
        )
        self.stdout.write(self.style.SUCCESS('Seeded Swiggy + Zomato inbox samples'))

    def _print_summary(self, tenant, user, prop, tables):
        sample = tables[0] if tables else None
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Cloud POS demo ready'))
        self.stdout.write(f'  Login:  posdemo / posdemo123  (tenant: {tenant.slug})')
        self.stdout.write(f'  Outlet: {prop.name}')
        self.stdout.write('  Open:   https://pos.revnext.in/tenants/login/?next=/pos/billing/')
        if sample:
            self.stdout.write(f'  QR T1:  https://pos.revnext.in/pos/qr/{sample.qr_token}/')
