"""
Seed / sync the hospitality RBAC catalog into the database.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from rbac.catalog import CAPABILITIES, SYSTEM_ROLES
from rbac.models import Capability, Role, RoleCapability
from rbac.services import ensure_legacy_assignment


class Command(BaseCommand):
    help = 'Seed system capabilities and hospitality job roles for enterprise RBAC'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate-users',
            action='store_true',
            help='Create RBAC assignments from legacy TenantUser.role values',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('🔐 Seeding RBAC capabilities...')
        cap_map = {}
        for codename, module, action, label, description in CAPABILITIES:
            cap, created = Capability.objects.update_or_create(
                codename=codename,
                defaults={
                    'module': module,
                    'action': action,
                    'label': label,
                    'description': description,
                    'is_active': True,
                },
            )
            cap_map[codename] = cap
            mark = '✓' if not created else '+'
            self.stdout.write(f'  {mark} {codename}')

        self.stdout.write('👔 Seeding system hospitality roles...')
        for idx, (code, name, department, scope, description, caps) in enumerate(SYSTEM_ROLES):
            role, created = Role.objects.update_or_create(
                code=code,
                tenant=None,
                defaults={
                    'name': name,
                    'description': description,
                    'department': department,
                    'default_scope': scope,
                    'is_system': True,
                    'is_active': True,
                    'sort_order': idx * 10,
                },
            )
            # Sync capabilities exactly to catalog
            desired = {cap_map[c] for c in caps if c in cap_map}
            existing = set(role.capabilities.all())
            to_add = desired - existing
            to_remove = existing - desired
            if to_remove:
                RoleCapability.objects.filter(role=role, capability__in=to_remove).delete()
            for cap in to_add:
                RoleCapability.objects.get_or_create(role=role, capability=cap)
            mark = '+' if created else '✓'
            self.stdout.write(f'  {mark} {code} ({len(desired)} capabilities)')

        if options['migrate_users']:
            self.stdout.write('👥 Migrating legacy TenantUser.role → RBAC assignments...')
            from tenants.models import TenantUser
            count = 0
            for user in TenantUser.objects.filter(tenant__isnull=False, is_superuser=False):
                if ensure_legacy_assignment(user):
                    count += 1
                    self.stdout.write(f'  ✓ {user.username} ← {user.role}')
            self.stdout.write(self.style.SUCCESS(f'Migrated {count} users'))

        self.stdout.write(self.style.SUCCESS(
            f'Done. {Capability.objects.count()} capabilities, '
            f'{Role.objects.filter(is_system=True).count()} system roles.'
        ))
