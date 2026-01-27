"""
Management command to seed subscription plans
"""
from django.core.management.base import BaseCommand
from djmoney.money import Money
from tenants.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Seed subscription plans'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🌱 Seeding subscription plans...\n'))
        
        plans_data = [
            {
                'name': 'free',
                'display_name': 'Free Plan',
                'description': 'Perfect for getting started. Ideal for small hotels with basic needs.',
                'monthly_price': Money(0, 'INR'),
                'yearly_price': Money(0, 'INR'),
                'max_properties': 1,
                'max_integrations_per_property': 5,
                'max_users': 1,
                'max_api_calls_per_month': 1000,
                'features': [
                    'basic_sync',
                    'email_support',
                    '1_property',
                    '5_integrations_per_property',
                ],
                'is_active': True,
                'is_visible': True,
            },
            {
                'name': 'basic',
                'display_name': 'Basic Plan',
                'description': 'For growing hotels. More properties and integrations.',
                'monthly_price': Money(2999, 'INR'),
                'yearly_price': Money(29999, 'INR'),  # ~17% discount
                'max_properties': 5,
                'max_integrations_per_property': 10,
                'max_users': 3,
                'max_api_calls_per_month': 10000,
                'features': [
                    'real_time_sync',
                    'priority_email_support',
                    '5_properties',
                    '10_integrations_per_property',
                    'api_access',
                    'basic_analytics',
                ],
                'is_active': True,
                'is_visible': True,
            },
            {
                'name': 'professional',
                'display_name': 'Professional Plan',
                'description': 'For established hotel chains. Advanced features and higher limits.',
                'monthly_price': Money(9999, 'INR'),
                'yearly_price': Money(99999, 'INR'),  # ~17% discount
                'max_properties': 25,
                'max_integrations_per_property': 25,
                'max_users': 10,
                'max_api_calls_per_month': 100000,
                'features': [
                    'real_time_sync',
                    'priority_support',
                    '25_properties',
                    '25_integrations_per_property',
                    'unlimited_api_access',
                    'advanced_analytics',
                    'custom_integrations',
                    'dedicated_account_manager',
                ],
                'is_active': True,
                'is_visible': True,
            },
            {
                'name': 'enterprise',
                'display_name': 'Enterprise Plan',
                'description': 'For large hotel groups. Unlimited everything with white-glove service.',
                'monthly_price': Money(29999, 'INR'),
                'yearly_price': Money(299999, 'INR'),  # ~17% discount
                'max_properties': 100,
                'max_integrations_per_property': 999,  # Effectively unlimited
                'max_users': 50,
                'max_api_calls_per_month': 999999,  # Effectively unlimited
                'features': [
                    'real_time_sync',
                    '24_7_phone_support',
                    'unlimited_properties',
                    'unlimited_integrations',
                    'unlimited_api_calls',
                    'enterprise_analytics',
                    'custom_integrations',
                    'dedicated_account_manager',
                    'onboarding_assistance',
                    'custom_contracts',
                    'sla_guarantee',
                ],
                'is_active': True,
                'is_visible': True,
            },
        ]
        
        for plan_data in plans_data:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {plan.display_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⊙ Updated: {plan.display_name}'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Subscription plans seeded successfully!'))
