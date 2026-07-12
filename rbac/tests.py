"""
Basic RBAC service tests.
"""
from django.test import TestCase

from rbac.catalog import CAPABILITIES, SYSTEM_ROLES
from rbac.models import Capability, Role, UserRoleAssignment
from rbac.services import get_user_capabilities, user_has_capability, accessible_property_ids
from tenants.models import Tenant, TenantUser


class RbacCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.core.management import call_command
        call_command('seed_rbac', verbosity=0)

    def test_capabilities_seeded(self):
        self.assertEqual(Capability.objects.count(), len(CAPABILITIES))

    def test_system_roles_seeded(self):
        self.assertEqual(Role.objects.filter(is_system=True).count(), len(SYSTEM_ROLES))

    def test_front_desk_cannot_manage_billing(self):
        tenant = Tenant.objects.create(
            name='Test Hotel Co',
            slug='test-hotel-co',
            email='owner@test.com',
        )
        user = TenantUser.objects.create_user(
            username='frontdesk1',
            email='fd@test.com',
            password='pass12345',
            tenant=tenant,
            role='staff',
        )
        role = Role.objects.get(code='front_desk_agent', is_system=True)
        UserRoleAssignment.objects.create(
            user=user, role=role, tenant=tenant, property=None,
        )
        self.assertTrue(user_has_capability(user, 'reservations.checkin'))
        self.assertFalse(user_has_capability(user, 'billing.manage'))
        self.assertFalse(user_has_capability(user, 'users.manage'))

    def test_owner_has_all_and_tenantwide_scope(self):
        tenant = Tenant.objects.create(
            name='Owner Co',
            slug='owner-co',
            email='o@test.com',
        )
        user = TenantUser.objects.create_user(
            username='owner1',
            email='o@test.com',
            password='pass12345',
            tenant=tenant,
            role='owner',
        )
        role = Role.objects.get(code='owner', is_system=True)
        UserRoleAssignment.objects.create(
            user=user, role=role, tenant=tenant, property=None,
        )
        caps = get_user_capabilities(user)
        self.assertIn('billing.manage', caps)
        self.assertIn('users.manage', caps)
        self.assertIsNone(accessible_property_ids(user))

    def test_legacy_fallback_without_assignment(self):
        tenant = Tenant.objects.create(
            name='Legacy Co',
            slug='legacy-co',
            email='l@test.com',
        )
        user = TenantUser.objects.create_user(
            username='viewer1',
            email='v@test.com',
            password='pass12345',
            tenant=tenant,
            role='viewer',
        )
        self.assertTrue(user_has_capability(user, 'reports.view'))
        self.assertFalse(user_has_capability(user, 'reservations.create'))
