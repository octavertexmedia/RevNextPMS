"""
Seed hospitality demo users for Boutique Demo Hotels (testuser2 tenant).

Creates one user per primary job role with RBAC assignments.
Password for all: testpass123

Usage:
  python manage.py seed_rbac
  python manage.py seed_rbac_demo_users
"""
from __future__ import annotations

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Property
from rbac.models import Role, UserRoleAssignment
from tenants.models import Tenant, TenantUser


# (username, email, first, last, legacy_role, system_role_code, property_scoped)
# property_scoped=True → assign to first property only (Oceanview)
DEMO_USERS = [
    ('demo_owner', 'owner@boutiquedemo.com', 'Demo', 'Owner', 'owner', 'owner', False),
    ('demo_gm', 'gm@boutiquedemo.com', 'Priya', 'GM', 'manager', 'general_manager', True),
    ('demo_frontdesk', 'frontdesk@boutiquedemo.com', 'Arjun', 'Desk', 'staff', 'front_desk_agent', True),
    ('demo_nightaudit', 'nightaudit@boutiquedemo.com', 'Meera', 'Auditor', 'staff', 'night_auditor', True),
    ('demo_hksup', 'hksup@boutiquedemo.com', 'Kavya', 'HK Sup', 'staff', 'housekeeping_manager', True),
    ('demo_hkatt', 'hkatt@boutiquedemo.com', 'Dev', 'HK Att', 'staff', 'housekeeping_attendant', True),
    ('demo_pos', 'pos@boutiquedemo.com', 'Nisha', 'Cashier', 'staff', 'pos_cashier', True),
    ('demo_revenue', 'revenue@boutiquedemo.com', 'Rahul', 'Revenue', 'manager', 'revenue_manager', True),
    ('demo_accountant', 'accountant@boutiquedemo.com', 'Sneha', 'Accounts', 'viewer', 'accountant', True),
]

PASSWORD = 'testpass123'
TENANT_SLUG = 'boutique-demo-hotels'


class Command(BaseCommand):
    help = 'Seed hospitality RBAC demo users on Boutique Demo Hotels'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-catalog',
            action='store_true',
            help='Do not run seed_rbac first',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if not options['skip_catalog']:
            call_command('seed_rbac')

        try:
            tenant = Tenant.objects.get(slug=TENANT_SLUG)
        except Tenant.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f'Tenant {TENANT_SLUG} not found. Run seed_testuser2 first.'
            ))
            return

        properties = list(Property.objects.filter(tenant=tenant, is_active=True).order_by('id'))
        first_prop = properties[0] if properties else None

        # Ensure testuser2 has owner RBAC assignment (tenant-wide)
        try:
            owner_user = TenantUser.objects.get(username='testuser2', tenant=tenant)
            owner_role = Role.objects.get(code='owner', is_system=True)
            UserRoleAssignment.objects.update_or_create(
                user=owner_user,
                role=owner_role,
                tenant=tenant,
                property=None,
                defaults={'is_active': True, 'notes': 'Demo owner'},
            )
            self.stdout.write(self.style.SUCCESS('✓ testuser2 → owner (tenant-wide)'))
        except TenantUser.DoesNotExist:
            self.stdout.write(self.style.WARNING('testuser2 not found; skipping owner assignment'))

        for username, email, first, last, legacy, role_code, scoped in DEMO_USERS:
            try:
                role = Role.objects.get(code=role_code, is_system=True, is_active=True)
            except Role.DoesNotExist:
                self.stderr.write(self.style.ERROR(f'Role {role_code} missing — run seed_rbac'))
                continue

            user, created = TenantUser.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'tenant': tenant,
                    'role': legacy,
                    'first_name': first,
                    'last_name': last,
                    'is_staff': True,
                },
            )
            user.tenant = tenant
            user.email = email
            user.role = legacy
            user.first_name = first
            user.last_name = last
            user.is_staff = True
            user.is_active = True
            user.set_password(PASSWORD)
            user.save()

            prop = first_prop if scoped and first_prop else None
            # Drop conflicting assignments for this user on this tenant
            UserRoleAssignment.objects.filter(user=user, tenant=tenant).exclude(
                role=role, property=prop
            ).update(is_active=False)

            assignment, _ = UserRoleAssignment.objects.update_or_create(
                user=user,
                role=role,
                tenant=tenant,
                property=prop,
                defaults={
                    'is_active': True,
                    'notes': f'Demo {role.name}',
                },
            )
            scope = prop.name if prop else 'ALL'
            mark = '+' if created else '✓'
            self.stdout.write(
                f'  {mark} {username} / {PASSWORD} → {role.code} @ {scope}'
            )

        self.stdout.write(self.style.SUCCESS(
            f'\nDone. {len(DEMO_USERS)} demo role users on {tenant.name}.'
        ))
