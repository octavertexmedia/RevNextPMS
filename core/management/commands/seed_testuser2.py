"""
Seed a compact demo tenant for mobile PMS testing.

Creates:
  - Tenant: Boutique Demo Hotels (max 3 properties)
  - User: testuser2 / testpass123 (owner)
  - Exactly 3 properties with full related data:
      room types, rate plans, inventory, OTA integrations, sync logs,
      reservations (arrivals/departures/in-house/upcoming), payments,
      promotions, linked rooms, housekeeping, folios, POS menu & orders

Usage:
  python manage.py seed_testuser2
  python manage.py seed_testuser2 --reset   # wipe this tenant's data and reseed
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from djmoney.money import Money

from tenants.models import Tenant, TenantUser, SubscriptionPlan
from core.models import (
    Property, RoomType, MealPlan, Policy, RatePlan, Inventory, Promotion, TaxFee,
    Restrictions,
)
from integrations.models import IntegrationPlatform, PropertyIntegration, SyncLog
from bookings.models import Reservation, Payment
from cloud_pms.models import LinkedRoomUnit, Folio, FolioLineItem, HousekeepingTask
from cloud_pos.models import MenuCategory, MenuItem, POSTable, POSOrder, POSOrderItem


HOTELS = [
    {
        'name': 'Oceanview Boutique Hotel',
        'city': 'Goa',
        'state': 'Goa',
        'postal': '403516',
        'type': 'hotel',
        'gstin': '30AABCOCEAN1Z3',
        'pan': 'AABCOCEAN1',
        'address': 'Calangute Beach Road',
        'rooms': [
            ('Deluxe King', 4500, 12),
            ('Sea View Suite', 7800, 6),
            ('Garden Twin', 3800, 10),
        ],
    },
    {
        'name': 'Grand Plaza City Centre',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'postal': '400001',
        'type': 'hotel',
        'gstin': '27AABCGPLAZ1ZX',
        'pan': 'AABCGPLAZ1',
        'address': 'Fort District, Near CST',
        'rooms': [
            ('Executive King', 6200, 20),
            ('Business Twin', 5200, 16),
            ('Presidential Suite', 15000, 2),
        ],
    },
    {
        'name': 'Hillside Heritage Resort',
        'city': 'Udaipur',
        'state': 'Rajasthan',
        'postal': '313001',
        'type': 'resort',
        'gstin': '08AABCHILLS1Z4',
        'pan': 'AABCHILLS1',
        'address': 'Lake Pichola Foothills',
        'rooms': [
            ('Heritage Room', 5500, 14),
            ('Lake Villa', 11000, 4),
            ('Courtyard Deluxe', 4800, 10),
        ],
    },
]

GUEST_FIRST = [
    'Priya', 'Aditya', 'Ananya', 'Rohan', 'Meera', 'Kabir', 'Ishita',
    'Vikram', 'Sneha', 'Arjun', 'Kavya', 'Dev', 'Nisha', 'Rahul',
]
GUEST_LAST = [
    'Sharma', 'Mehta', 'Kapoor', 'Iyer', 'Patel', 'Singh', 'Reddy',
    'Nair', 'Gupta', 'Joshi',
]


class Command(BaseCommand):
    help = 'Create testuser2 with exactly 3 fully seeded properties for PMS demo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete Boutique Demo Hotels tenant data and recreate',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🌱 Seeding testuser2 demo tenant (3 properties)...\n'))

        tenant = self._ensure_tenant(reset=options['reset'])
        user = self._ensure_user(tenant)
        policies = self._ensure_policies()
        meal = self._ensure_meal_plan()
        platforms = self._ensure_platforms()
        self._ensure_taxes()

        # Clear properties for this tenant if reset or re-running cleanly
        if options['reset'] or tenant.properties.count() != 3:
            self._wipe_tenant_ops(tenant)

        if tenant.properties.count() == 0:
            props = self._create_properties(tenant)
        else:
            props = list(tenant.properties.order_by('id')[:3])
            self.stdout.write(self.style.WARNING(
                f'Using existing {len(props)} properties for tenant (pass --reset to rebuild)'
            ))

        # Cap at 3: deactivate extras if any
        extras = tenant.properties.exclude(id__in=[p.id for p in props])
        if extras.exists():
            extras.update(is_active=False)
            self.stdout.write(self.style.WARNING(f'Deactivated {extras.count()} extra properties'))

        for prop, cfg in zip(props, HOTELS):
            self._seed_property(prop, cfg, policies, meal, platforms)

        # RBAC catalog + hospitality demo users
        from django.core.management import call_command
        call_command('seed_rbac', migrate_users=True)
        call_command('seed_rbac_demo_users', skip_catalog=True)

        self._print_summary(tenant, user)

    def _ensure_tenant(self, reset: bool) -> Tenant:
        plan, _ = SubscriptionPlan.objects.get_or_create(
            name='professional',
            defaults={
                'display_name': 'Professional Plan',
                'monthly_price': Money(9999, 'INR'),
                'yearly_price': Money(99999, 'INR'),
                'max_properties': 25,
                'max_integrations_per_property': 25,
                'max_users': 10,
                'max_api_calls_per_month': 100000,
                'is_active': True,
                'is_visible': True,
            },
        )

        if reset:
            existing = Tenant.objects.filter(slug='boutique-demo-hotels').first()
            if existing:
                self.stdout.write(self.style.WARNING('Resetting Boutique Demo Hotels tenant...'))
                self._wipe_tenant_ops(existing)
                # Keep tenant row; wipe ops only

        tenant, created = Tenant.objects.get_or_create(
            slug='boutique-demo-hotels',
            defaults={
                'name': 'Boutique Demo Hotels',
                'email': 'demo2@boutiquedemo.com',
                'subscription_plan': plan,
                'subscription_status': 'active',
                'max_properties': 3,
                'is_active': True,
            },
        )
        tenant.subscription_plan = plan
        tenant.subscription_status = 'active'
        tenant.max_properties = 3
        tenant.is_active = True
        tenant.save()
        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} tenant: {tenant.name} (max 3 properties)"
        ))
        return tenant

    def _ensure_user(self, tenant: Tenant) -> TenantUser:
        user, created = TenantUser.objects.get_or_create(
            username='testuser2',
            defaults={
                'email': 'testuser2@boutiquedemo.com',
                'tenant': tenant,
                'role': 'owner',
                'first_name': 'Demo',
                'last_name': 'Owner',
                'is_staff': True,
            },
        )
        user.tenant = tenant
        user.role = 'owner'
        user.email = 'testuser2@boutiquedemo.com'
        user.first_name = 'Demo'
        user.last_name = 'Owner'
        user.is_staff = True
        user.is_active = True
        user.set_password('testpass123')
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"{'Created' if created else 'Updated'} user testuser2 / testpass123"
        ))
        return user

    def _wipe_tenant_ops(self, tenant: Tenant):
        props = list(tenant.properties.all())
        if not props:
            return
        prop_ids = [p.id for p in props]
        POSOrderItem.objects.filter(order__property_id__in=prop_ids).delete()
        POSOrder.objects.filter(property_id__in=prop_ids).delete()
        MenuItem.objects.filter(category__property_id__in=prop_ids).delete()
        MenuCategory.objects.filter(property_id__in=prop_ids).delete()
        POSTable.objects.filter(property_id__in=prop_ids).delete()
        FolioLineItem.objects.filter(folio__property_id__in=prop_ids).delete()
        Folio.objects.filter(property_id__in=prop_ids).delete()
        HousekeepingTask.objects.filter(property_id__in=prop_ids).delete()
        LinkedRoomUnit.objects.filter(property_id__in=prop_ids).delete()
        Payment.objects.filter(reservation__property_id__in=prop_ids).delete()
        Reservation.objects.filter(property_id__in=prop_ids).delete()
        SyncLog.objects.filter(property_integration__property_id__in=prop_ids).delete()
        PropertyIntegration.objects.filter(property_id__in=prop_ids).delete()
        Promotion.objects.filter(property_id__in=prop_ids).delete()
        Restrictions.objects.filter(property_id__in=prop_ids).delete()
        TaxFee.objects.filter(property_id__in=prop_ids).delete()
        Inventory.objects.filter(property_id__in=prop_ids).delete()
        RatePlan.objects.filter(property_id__in=prop_ids).delete()
        RoomType.objects.filter(property_id__in=prop_ids).delete()
        Property.objects.filter(id__in=prop_ids).delete()
        self.stdout.write('  Cleared existing boutique demo property data')

    def _ensure_policies(self):
        free, _ = Policy.objects.get_or_create(
            name='Free Cancellation 24h',
            defaults={
                'policy_type': 'CANCELLATION',
                'details': {
                    'cancellation_window_hours': 24,
                    'penalty_type': 'PERCENTAGE',
                    'penalty_value': 0,
                },
                'description': 'Free cancellation up to 24 hours before check-in',
            },
        )
        prepaid, _ = Policy.objects.get_or_create(
            name='Partial Prepayment (50%)',
            defaults={
                'policy_type': 'PREPAYMENT',
                'details': {
                    'prepayment_percentage': 50,
                    'prepayment_deadline_hours': 48,
                },
                'description': '50% payment required 48 hours before check-in',
            },
        )
        return {'cancel': free, 'prepay': prepaid}

    def _ensure_meal_plan(self):
        meal, _ = MealPlan.objects.get_or_create(
            code='BREAKFAST',
            defaults={'name': 'Breakfast', 'description': 'Complimentary breakfast'},
        )
        MealPlan.objects.get_or_create(
            code='ROOM_ONLY',
            defaults={'name': 'Room Only', 'description': 'No meals included'},
        )
        return meal

    def _ensure_taxes(self):
        TaxFee.objects.get_or_create(
            name='GST (12%)',
            defaults={
                'tax_type': 'PERCENTAGE',
                'value': Decimal('12'),
                'is_inclusive': False,
                'description': 'Goods and Services Tax 12%',
            },
        )

    def _ensure_platforms(self):
        names = [
            ('booking.com', 'Booking.com', 'OTA'),
            ('expedia', 'Expedia', 'OTA'),
            ('makemytrip', 'MakeMyTrip', 'OTA'),
            ('agoda', 'Agoda', 'OTA'),
            ('direct', 'Direct / Walk-in', 'OTHER'),
        ]
        platforms = {}
        for name, display, ptype in names:
            platform, _ = IntegrationPlatform.objects.get_or_create(
                name=name,
                defaults={
                    'display_name': display,
                    'platform_type': ptype,
                    'api_base_url': f'https://api.{name.replace(" ", "")}.example',
                    'auth_type': 'API_KEY',
                    'is_active': True,
                    'is_connected': True,
                    'supports_polling': True,
                },
            )
            platforms[name] = platform
        return platforms

    def _create_properties(self, tenant: Tenant):
        props = []
        for cfg in HOTELS:
            prop = Property.objects.create(
                tenant=tenant,
                name=cfg['name'],
                legal_name=f"{cfg['name']} Pvt. Ltd.",
                property_type=cfg['type'],
                address_line1=cfg['address'],
                city=cfg['city'],
                state=cfg['state'],
                postal_code=cfg['postal'],
                country='India',
                phone=f'+91-98{random.randint(10000000, 99999999)}',
                email=f'frontdesk@{cfg["name"].lower().replace(" ", "").replace("-", "")[:20]}.com',
                website=f'https://www.example-{cfg["city"].lower()}.com',
                timezone='Asia/Kolkata',
                currency='INR',
                gstin=cfg['gstin'],
                pan=cfg['pan'],
                is_active=True,
            )
            props.append(prop)
            self.stdout.write(f'  ✓ Property: {prop.name} ({prop.city})')
        return props

    def _seed_property(self, prop: Property, cfg: dict, policies, meal, platforms):
        self.stdout.write(f'\n📦 Seeding {prop.name}...')

        # Room types + rate plans
        room_types = []
        rate_plans = []
        for name, base_rate, total_rooms in cfg['rooms']:
            rt, _ = RoomType.objects.get_or_create(
                property=prop,
                name=name,
                defaults={
                    'description': f'{name} at {prop.name}',
                    'max_occupancy': 3,
                    'base_occupancy': 2,
                    'max_adults': 2,
                    'max_children': 1,
                    'bed_type': 'King' if 'King' in name or 'Suite' in name or 'Villa' in name else 'Twin',
                    'amenities': ['wifi', 'ac', 'tv', 'minibar'],
                    'is_active': True,
                    'size_sqm': Decimal('28.00'),
                },
            )
            # stash total rooms on instance for inventory
            rt._seed_total_rooms = total_rooms  # type: ignore[attr-defined]
            room_types.append(rt)

            rp, _ = RatePlan.objects.get_or_create(
                property=prop,
                room_type=rt,
                name=f'{name} - Flexible',
                defaults={
                    'description': 'Flexible cancellation rate',
                    'meal_plan': meal,
                    'inclusions': ['wifi', 'breakfast'],
                    'base_rate': Money(base_rate, 'INR'),
                    'base_occupancy': 2,
                    'extra_adult_charge': Money(int(base_rate * 0.25), 'INR'),
                    'extra_child_charge': Money(int(base_rate * 0.12), 'INR'),
                    'cancellation_policy': policies['cancel'],
                    'prepayment_policy': policies['prepay'],
                    'is_active': True,
                },
            )
            rate_plans.append(rp)

            RatePlan.objects.get_or_create(
                property=prop,
                room_type=rt,
                name=f'{name} - Non-Refundable',
                defaults={
                    'description': 'Non-refundable discounted rate',
                    'meal_plan': meal,
                    'inclusions': ['wifi'],
                    'base_rate': Money(int(base_rate * 0.85), 'INR'),
                    'base_occupancy': 2,
                    'extra_adult_charge': Money(int(base_rate * 0.25), 'INR'),
                    'extra_child_charge': Money(int(base_rate * 0.12), 'INR'),
                    'cancellation_policy': policies['cancel'],
                    'prepayment_policy': policies['prepay'],
                    'is_active': True,
                },
            )

        # Inventory — 120 days (full operational horizon for demo)
        today = date.today()
        inv_count = 0
        for rt in room_types:
            total_rooms = getattr(rt, '_seed_total_rooms', 10)
            for i in range(120):
                inv_date = today + timedelta(days=i)
                booked = random.randint(0, max(1, int(total_rooms * 0.4)))
                Inventory.objects.get_or_create(
                    property=prop,
                    room_type=rt,
                    date=inv_date,
                    defaults={
                        'available_rooms': max(0, total_rooms - booked),
                        'total_rooms': total_rooms,
                        'blocked_rooms': 0,
                    },
                )
                inv_count += 1
        self.stdout.write(f'  ✓ Room types={len(room_types)}, inventory rows≈{inv_count}')

        # Integrations + sync logs
        for pname in ['booking.com', 'expedia', 'makemytrip', 'direct']:
            platform = platforms[pname]
            room_mappings = {
                str(rt.id): f'{pname[:3].upper()}_RT_{rt.id}' for rt in room_types
            }
            rate_mappings = {
                str(rp.id): f'{pname[:3].upper()}_RP_{rp.id}' for rp in rate_plans
            }
            pi, created = PropertyIntegration.objects.get_or_create(
                property=prop,
                platform=platform,
                defaults={
                    'provider_property_id': f'{pname[:3].upper()}{prop.id:04d}',
                    'provider_room_type_mappings': room_mappings,
                    'provider_rate_plan_mappings': rate_mappings,
                    'sync_availability': True,
                    'sync_rates': True,
                    'sync_inventory': True,
                    'sync_reservations': True,
                    'is_active': True,
                    'config': {'auto_sync': True, 'api_key': f'demo-{pname}-{prop.id}'},
                },
            )
            if created or not SyncLog.objects.filter(property_integration=pi).exists():
                for sync_type, status in [
                    ('AVAILABILITY', 'SUCCESS'),
                    ('RATES', 'SUCCESS'),
                    ('RESERVATIONS', 'PARTIAL'),
                    ('FULL', 'FAILED'),
                ]:
                    started = timezone.now() - timedelta(hours=random.randint(1, 48))
                    SyncLog.objects.create(
                        property_integration=pi,
                        platform=platform,
                        sync_type=sync_type,
                        status=status,
                        started_at=started,
                        completed_at=started + timedelta(minutes=random.randint(1, 12)),
                        duration_seconds=float(random.randint(30, 600)),
                        records_processed=random.randint(10, 200),
                        records_succeeded=random.randint(8, 180),
                        records_failed=random.randint(0, 5) if status != 'SUCCESS' else 0,
                        error_message='Channel timeout on batch 3' if status == 'FAILED' else '',
                    )

        # Promotions
        for promo in [
            ('Early Bird 15%', 'PERCENTAGE', 15),
            ('Stay 3 Pay 2', 'FREE_NIGHT', 1),
            ('Monsoon Special ₹1000 off', 'FIXED', 1000),
        ]:
            Promotion.objects.get_or_create(
                property=prop,
                name=promo[0],
                defaults={
                    'promotion_type': promo[1],
                    'discount_value': Decimal(str(promo[2])),
                    'start_date': today,
                    'end_date': today + timedelta(days=90),
                    'eligibility_rules': {'min_nights': 1},
                    'description': promo[0],
                    'is_active': True,
                },
            )

        # Property-level tax + sample restrictions
        TaxFee.objects.get_or_create(
            property=prop,
            name='GST (12%)',
            defaults={
                'tax_type': 'PERCENTAGE',
                'value': Decimal('12'),
                'is_inclusive': False,
                'gst_component': 'IGST',
                'description': 'Goods and Services Tax 12%',
            },
        )
        for i, rp in enumerate(rate_plans[:2]):
            Restrictions.objects.get_or_create(
                property=prop,
                rate_plan=rp,
                date=today + timedelta(days=i * 7),
                defaults={
                    'room_type': rp.room_type,
                    'min_los': 2,
                    'max_los': 14,
                    'closed_to_arrival': False,
                    'closed_to_departure': False,
                    'min_advance_booking_days': 1,
                },
            )

        # Linked rooms
        villa = LinkedRoomUnit.objects.create(
            property=prop,
            name=f'{prop.city} Villa Unit',
            total_rooms=2,
            sell_as_whole=True,
            whole_unit_price_multiplier=Decimal('0.90'),
            is_active=True,
        )
        villa.room_types.set(room_types[:2])

        # Reservations covering all front-desk lists
        reservations = self._create_reservations(prop, room_types, rate_plans, platforms)

        # Folios + housekeeping for checked-in / departing
        self._create_folios_and_hk(prop, reservations, room_types)

        # POS
        self._create_pos(prop, reservations)

        self.stdout.write(self.style.SUCCESS(f'  ✅ Done: {prop.name}'))

    def _guest(self):
        name = f'{random.choice(GUEST_FIRST)} {random.choice(GUEST_LAST)}'
        email = f'{name.lower().replace(" ", ".")}@example.com'
        phone = f'+91-{random.randint(9000000000, 9999999999)}'
        return name, email, phone

    def _create_reservations(self, prop, room_types, rate_plans, platforms):
        today = date.today()
        created = []

        def make(status, check_in, nights, provider='direct', with_payment=False, index=0):
            rt = room_types[index % len(room_types)]
            rp = next((r for r in rate_plans if r.room_type_id == rt.id), rate_plans[0])
            check_out = check_in + timedelta(days=nights)
            name, email, phone = self._guest()
            base = Money(int(float(rp.base_rate.amount) * nights), 'INR')
            tax = Money(int(base.amount * Decimal('0.12')), 'INR')
            total = base + tax
            res = Reservation.objects.create(
                provider_name=provider,
                provider_reservation_id=f'DEMO{prop.id}{status[:3]}{index:04d}{random.randint(100,999)}',
                provider_confirmation_code=f'CF{prop.id}{index:04d}',
                property=prop,
                room_type=rt,
                rate_plan=rp,
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                guest_name=name,
                guest_email=email,
                guest_phone=phone,
                guest_city=prop.city,
                guest_state=prop.state,
                guest_country='India',
                adults=random.randint(1, 2),
                children=random.randint(0, 1),
                base_room_rate=base,
                total_taxes_fees=tax,
                total_amount=total,
                currency='INR',
                cgst_amount=Money(0, 'INR'),
                sgst_amount=Money(0, 'INR'),
                igst_amount=tax,
                status=status,
                special_requests=random.choice([
                    '', 'High floor preferred', 'Late check-in after 10pm',
                    'Anniversary — cake if possible', 'Extra pillows',
                ]),
            )
            if with_payment:
                Payment.objects.create(
                    reservation=res,
                    amount=Money(int(total.amount * Decimal('0.5')), 'INR'),
                    currency='INR',
                    payment_method=random.choice(['UPI', 'CREDIT_CARD', 'NET_BANKING']),
                    payment_status='COMPLETED',
                    transaction_id=f'TXN{prop.id}{res.id}',
                    gateway_name=random.choice(['razorpay', 'payu']),
                    paid_at=timezone.now() - timedelta(days=1),
                )
            created.append(res)
            return res

        # Arrivals today (CONFIRMED)
        for i in range(4):
            make('CONFIRMED', today, random.randint(2, 4),
                 provider=random.choice(['booking.com', 'expedia', 'direct']),
                 with_payment=True, index=i)

        # Departures today (CHECKED_IN ending today)
        for i in range(3):
            make('CHECKED_IN', today - timedelta(days=random.randint(2, 4)),
                 nights=random.randint(2, 4),  # may not end today exactly
                 provider='direct', with_payment=True, index=10 + i)
        # Force exact departure-today stays
        for i in range(3):
            nights = random.randint(2, 3)
            make('CHECKED_IN', today - timedelta(days=nights), nights,
                 provider='makemytrip', with_payment=True, index=20 + i)

        # In-house spanning today
        for i in range(4):
            make('CHECKED_IN', today - timedelta(days=1), random.randint(3, 5),
                 provider='booking.com', with_payment=True, index=30 + i)

        # Upcoming
        for i in range(6):
            make('CONFIRMED', today + timedelta(days=random.randint(2, 21)),
                 random.randint(1, 5),
                 provider=random.choice(['agoda', 'expedia', 'direct']),
                 with_payment=i % 2 == 0, index=40 + i)

        # Pending / cancelled samples
        make('PENDING', today + timedelta(days=5), 2, provider='direct', index=50)
        make('CANCELLED', today + timedelta(days=8), 2, provider='booking.com', index=51)
        make('MODIFIED', today + timedelta(days=3), 2, provider='expedia', with_payment=True, index=52)

        self.stdout.write(f'  ✓ Reservations={len(created)}')
        return created

    def _create_folios_and_hk(self, prop, reservations, room_types):
        hk = 0
        folios = 0
        room_num = 100
        for res in reservations:
            if res.status not in ('CHECKED_IN', 'CONFIRMED'):
                continue
            room_num += 1
            rn = str(room_num)

            if res.status == 'CHECKED_IN' or res.check_in == date.today():
                folio = Folio.objects.create(
                    property=prop,
                    reservation=res,
                    guest_name=res.guest_name,
                    guest_email=res.guest_email,
                    room_number=rn,
                    total_charges=res.total_amount,
                    total_payments=Money(
                        int(float(res.total_amount.amount) * 0.4), 'INR'
                    ),
                    balance=Money(
                        int(float(res.total_amount.amount) * 0.6), 'INR'
                    ),
                    status='OPEN',
                )
                FolioLineItem.objects.create(
                    folio=folio,
                    item_type='ROOM',
                    description=f'Room charge · {res.room_type.name}',
                    amount=res.base_room_rate,
                    quantity=1,
                )
                FolioLineItem.objects.create(
                    folio=folio,
                    item_type='TAX',
                    description='GST 12%',
                    amount=res.total_taxes_fees,
                    quantity=1,
                )
                if random.random() > 0.4:
                    FolioLineItem.objects.create(
                        folio=folio,
                        item_type='POS',
                        description='In-room dining',
                        amount=Money(random.randint(800, 2500), 'INR'),
                        quantity=1,
                    )
                FolioLineItem.objects.create(
                    folio=folio,
                    item_type='PAYMENT',
                    description='Advance payment',
                    amount=Money(int(float(res.total_amount.amount) * 0.4), 'INR'),
                    quantity=1,
                )
                folios += 1

            # Housekeeping mix
            status = random.choice(['PENDING', 'PENDING', 'IN_PROGRESS', 'INSPECTED', 'COMPLETED'])
            HousekeepingTask.objects.create(
                property=prop,
                room_number=rn,
                room_type=res.room_type,
                task_type=random.choice(['Cleaning', 'Turndown', 'Deep Clean', 'Inspection']),
                description=f'{status.title()} task for {res.guest_name}',
                status=status,
                priority=random.choice(['LOW', 'NORMAL', 'NORMAL', 'HIGH', 'URGENT']),
                assigned_to=random.choice(['Anita', 'Ramesh', 'Sunita', '']),
                due_date=date.today() if status != 'COMPLETED' else date.today() - timedelta(days=1),
                reservation=res if res.status == 'CHECKED_IN' else None,
                completed_at=timezone.now() if status == 'COMPLETED' else None,
            )
            hk += 1

        # Extra standalone HK tasks
        for i in range(5):
            HousekeepingTask.objects.create(
                property=prop,
                room_number=str(200 + i),
                room_type=random.choice(room_types),
                task_type='Maintenance Clean',
                description='Vacant room turnover',
                status=random.choice(['PENDING', 'IN_PROGRESS']),
                priority='NORMAL',
                assigned_to='Housekeeping Team',
                due_date=date.today(),
            )
            hk += 1

        self.stdout.write(f'  ✓ Folios={folios}, HK tasks={hk}')

    def _create_pos(self, prop, reservations):
        cat_map = {}
        for cname, items in [
            ('Starters', [('Tomato Soup', 280), ('Paneer Tikka', 420), ('Caesar Salad', 360)]),
            ('Mains', [('Club Sandwich', 480), ('Butter Chicken', 620), ('Veg Thali', 550)]),
            ('Beverages', [('Fresh Lime Soda', 180), ('Masala Chai', 120), ('Filter Coffee', 140)]),
        ]:
            cat, _ = MenuCategory.objects.get_or_create(
                property=prop,
                name=cname,
                defaults={'display_order': len(cat_map), 'is_active': True},
            )
            cat_map[cname] = []
            for iname, price in items:
                item, _ = MenuItem.objects.get_or_create(
                    category=cat,
                    name=iname,
                    defaults={
                        'description': iname,
                        'price': Money(price, 'INR'),
                        'is_available': True,
                    },
                )
                cat_map[cname].append(item)

        table, _ = POSTable.objects.get_or_create(
            property=prop,
            name='T1',
            defaults={'capacity': 4, 'is_occupied': False},
        )

        all_items = [i for items in cat_map.values() for i in items]
        checked_in = [r for r in reservations if r.status == 'CHECKED_IN']
        for idx, status in enumerate(['OPEN', 'SENT', 'SERVED', 'BILLED', 'PAID']):
            room = ''
            folio = None
            bill_to_room = False
            if checked_in and idx % 2 == 0:
                res = checked_in[idx % len(checked_in)]
                folio = Folio.objects.filter(reservation=res).first()
                if folio:
                    room = folio.room_number
                    bill_to_room = True

            order = POSOrder.objects.create(
                property=prop,
                table=table,
                bill_to_room=bill_to_room,
                folio=folio,
                room_number=room,
                status=status,
                total_amount=Money(0, 'INR'),
            )
            total = Decimal('0')
            for item in random.sample(all_items, k=min(3, len(all_items))):
                qty = random.randint(1, 2)
                line = Money(item.price.amount * qty, 'INR')
                POSOrderItem.objects.create(
                    order=order,
                    menu_item=item,
                    quantity=qty,
                    unit_price=item.price,
                    line_total=line,
                )
                total += line.amount
            order.total_amount = Money(total, 'INR')
            order.save(update_fields=['total_amount'])

        self.stdout.write(f'  ✓ POS menu categories={len(cat_map)}, sample orders=5')

    def _print_summary(self, tenant: Tenant, user: TenantUser):
        props = tenant.properties.filter(is_active=True)
        prop_ids = list(props.values_list('id', flat=True))
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('📊 TESTUSER2 DEMO SUMMARY'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'  Username:     testuser2')
        self.stdout.write(f'  Password:     testpass123')
        self.stdout.write(f'  Tenant:       {tenant.name}')
        self.stdout.write(f'  Properties:   {props.count()} (capped at 3)')
        for p in props:
            self.stdout.write(f'               • {p.name} ({p.city})')
        self.stdout.write(f'  Room types:   {RoomType.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Rate plans:   {RatePlan.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Inventory:    {Inventory.objects.filter(property_id__in=prop_ids).count():,}')
        self.stdout.write(f'  Reservations: {Reservation.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Payments:     {Payment.objects.filter(reservation__property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Folios:       {Folio.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  HK tasks:     {HousekeepingTask.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Linked rooms: {LinkedRoomUnit.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  POS orders:   {POSOrder.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Menu items:   {MenuItem.objects.filter(category__property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Promotions:   {Promotion.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Integrations: {PropertyIntegration.objects.filter(property_id__in=prop_ids).count()}')
        self.stdout.write(f'  Sync logs:    {SyncLog.objects.filter(property_integration__property_id__in=prop_ids).count()}')
        self.stdout.write('=' * 60 + '\n')
        self.stdout.write(self.style.SUCCESS(
            'Login to the Flutter app with testuser2 / testpass123\n'
            'RBAC demos (password testpass123): demo_gm, demo_frontdesk, demo_hkatt, demo_pos, demo_revenue, ...'
        ))
