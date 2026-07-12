from django.core.management.base import BaseCommand
from django.db import transaction
from djmoney.money import Money

from products.catalog import PRODUCT_CATALOG, PRODUCT_PLANS, SUITE_PACKAGE
from products.models import Product, ProductPlan


class Command(BaseCommand):
    help = 'Seed RevNext multi-product catalog, plans, and suite package'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grant-suite-trial',
            action='store_true',
            help='Start a Hospitality Suite trial for all active tenants',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write('📦 Seeding products...')
        products = {}
        for (
            code, name, short_name, subdomain, host, paths, apis, app_label, tagline, sort
        ) in PRODUCT_CATALOG:
            product, created = Product.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'short_name': short_name,
                    'subdomain': subdomain,
                    'primary_host': host,
                    'path_prefixes': paths,
                    'api_prefixes': apis,
                    'app_label': app_label,
                    'tagline': tagline,
                    'sort_order': sort,
                    'is_active': True,
                    'is_billable': True,
                    'marketing_url': f'https://{host}/',
                },
            )
            products[code] = product
            self.stdout.write(f'  {"+" if created else "✓"} {code} → {host}')

        self.stdout.write('💳 Seeding product plans (monthly / yearly)...')
        for product_code, plans in PRODUCT_PLANS.items():
            product = products[product_code]
            for idx, (sku, display, monthly, yearly, tier, limits, features) in enumerate(plans):
                plan, created = ProductPlan.objects.update_or_create(
                    code=sku,
                    defaults={
                        'product': product,
                        'display_name': display,
                        'description': f'{display} — billed monthly or annually.',
                        'tier': tier,
                        'monthly_price': Money(monthly, 'INR'),
                        'yearly_price': Money(yearly, 'INR'),
                        'is_package': False,
                        'limits': limits,
                        'features': features,
                        'is_active': True,
                        'is_visible': True,
                        'sort_order': idx * 10,
                        'trial_days': 14,
                    },
                )
                self.stdout.write(
                    f'  {"+" if created else "✓"} {sku}  ₹{monthly}/mo · ₹{yearly}/yr'
                )

        self.stdout.write('🎁 Seeding Hospitality Suite package...')
        suite, created = ProductPlan.objects.update_or_create(
            code=SUITE_PACKAGE['code'],
            defaults={
                'product': None,
                'display_name': SUITE_PACKAGE['name'],
                'description': SUITE_PACKAGE['description'],
                'tier': 'suite',
                'monthly_price': Money(SUITE_PACKAGE['monthly_price'], 'INR'),
                'yearly_price': Money(SUITE_PACKAGE['yearly_price'], 'INR'),
                'is_package': True,
                'limits': SUITE_PACKAGE['limits'],
                'features': SUITE_PACKAGE['features'],
                'is_active': True,
                'is_visible': True,
                'sort_order': 0,
                'trial_days': 14,
            },
        )
        suite.package_products.set([products[c] for c in SUITE_PACKAGE['product_codes']])
        self.stdout.write(
            f'  {"+" if created else "✓"} {suite.code} includes '
            f'{suite.package_products.count()} products — '
            f'₹{SUITE_PACKAGE["monthly_price"]}/mo · ₹{SUITE_PACKAGE["yearly_price"]}/yr'
        )

        if options['grant_suite_trial']:
            from tenants.models import Tenant
            from products.services import start_product_trial, entitled_product_codes
            self.stdout.write('🆓 Granting suite trials to active tenants...')
            count = 0
            for tenant in Tenant.objects.filter(is_active=True):
                entitled = entitled_product_codes(tenant)
                # Skip if already on suite-like coverage (booking + networks + pms)
                if {'booking', 'networks', 'pms'}.issubset(entitled):
                    continue
                start_product_trial(tenant, suite)
                count += 1
                self.stdout.write(f'  ✓ trial → {tenant.name}')
            self.stdout.write(f'Granted {count} suite trials')

        self.stdout.write(self.style.SUCCESS(
            f'Done. {Product.objects.count()} products, '
            f'{ProductPlan.objects.count()} plans.'
        ))
