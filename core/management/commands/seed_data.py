"""
Industry-Grade Seed Data for Channel Manager
Creates 25 hotels, 15 OTA platforms, and comprehensive related data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from djmoney.money import Money
import random

from tenants.models import Tenant, TenantUser
from core.models import (
    Property, RoomType, MealPlan, Policy, RatePlan,
    Inventory, Restrictions, TaxFee, Promotion
)
from integrations.models import IntegrationPlatform, PropertyIntegration
from bookings.models import Reservation, Payment


class Command(BaseCommand):
    help = 'Seed the database with industry-grade sample data (25 hotels, 15 OTA platforms)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            Reservation.objects.all().delete()
            Payment.objects.all().delete()
            PropertyIntegration.objects.all().delete()
            Inventory.objects.all().delete()
            RatePlan.objects.all().delete()
            RoomType.objects.all().delete()
            Property.objects.all().delete()
            IntegrationPlatform.objects.all().delete()
            Promotion.objects.all().delete()
            Restrictions.objects.all().delete()
            TaxFee.objects.all().delete()
            Policy.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        self.stdout.write(self.style.SUCCESS('🌴 Seeding database with industry-grade data...\n'))

        # Get or create subscription plans first
        from tenants.models import SubscriptionPlan
        enterprise_plan, _ = SubscriptionPlan.objects.get_or_create(
            name='enterprise',
            defaults={
                'display_name': 'Enterprise Plan',
                'monthly_price': Money(29999, 'INR'),
                'yearly_price': Money(299999, 'INR'),
                'max_properties': 100,
                'max_integrations_per_property': 999,
                'max_users': 50,
                'max_api_calls_per_month': 999999,
                'is_active': True,
                'is_visible': True,
            }
        )
        
        # Get or create a default tenant
        default_tenant, _ = Tenant.objects.get_or_create(
            name='Default Hotel Group',
            defaults={
                'slug': 'default-hotel-group',
                'email': 'admin@hotelgroup.com',
                'subscription_plan': enterprise_plan,
                'subscription_status': 'active',
                'max_properties': 100,
                'is_active': True,
            }
        )
        
        # Upgrade subscription if plan exists
        if default_tenant.subscription_plan != enterprise_plan:
            default_tenant.upgrade_subscription(enterprise_plan, 'monthly')
        
        # Create a default tenant user for testing
        default_user, user_created = TenantUser.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@hotelgroup.com',
                'tenant': default_tenant,
                'role': 'owner',
                'first_name': 'Test',
                'last_name': 'User',
                'is_staff': True,
            }
        )
        if user_created:
            default_user.set_password('testpass123')
            default_user.save()
            self.stdout.write(self.style.SUCCESS(
                f'✅ Created test tenant user: username="testuser", password="testpass123"'
            ))
        else:
            # Update password if user already exists
            default_user.set_password('testpass123')
            default_user.tenant = default_tenant
            default_user.save()
            self.stdout.write(self.style.SUCCESS(
                f'✅ Updated test tenant user: username="testuser", password="testpass123"'
            ))

        # Create Policies
        self.stdout.write('📋 Creating policies...')
        policies = self._create_policies()

        # Create Taxes
        self.stdout.write('💰 Creating taxes and fees...')
        taxes = self._create_taxes()

        # Create 15 OTA Platforms
        self.stdout.write('🌐 Creating 15 OTA platforms...')
        platforms = self._create_ota_platforms()

        # Create 25 Hotels
        self.stdout.write('🏨 Creating 25 hotels across India...')
        hotels_data = self._create_hotels(default_tenant, policies, taxes)

        # Create Room Types for each hotel
        self.stdout.write('🛏️  Creating room types...')
        room_types_data = self._create_room_types(hotels_data)

        # Meal plans are required by rate plans
        self.stdout.write('🍽️  Ensuring meal plans...')
        self._ensure_meal_plans()

        # Create Rate Plans
        self.stdout.write('💵 Creating rate plans...')
        rate_plans_data = self._create_rate_plans(hotels_data, room_types_data, policies)

        # Create Inventory (1 year)
        self.stdout.write('📦 Creating inventory (365 days)...')
        self._create_inventory(hotels_data, room_types_data)

        # Create Property Integrations
        self.stdout.write('🔗 Creating property integrations...')
        self._create_property_integrations(hotels_data, room_types_data, rate_plans_data, platforms)

        # Create Sample Reservations
        self.stdout.write('📅 Creating sample reservations...')
        self._create_reservations(hotels_data, room_types_data, rate_plans_data, platforms)

        # Create Promotions
        self.stdout.write('🎁 Creating promotions...')
        self._create_promotions(hotels_data)

        # Summary
        self.stdout.write(self.style.SUCCESS('\n✅ Seed data created successfully!\n'))
        self._print_summary()

    def _create_policies(self):
        """Create cancellation and prepayment policies"""
        policies = {}
        
        policies['free_cancel_48h'] = Policy.objects.get_or_create(
            name='Free Cancellation 48h',
            defaults={
                'policy_type': 'CANCELLATION',
                'details': {
                    'cancellation_window_hours': 48,
                    'penalty_type': 'PERCENTAGE',
                    'penalty_value': 0,
                },
                'description': 'Free cancellation up to 48 hours before check-in'
            }
        )[0]

        policies['free_cancel_24h'] = Policy.objects.get_or_create(
            name='Free Cancellation 24h',
            defaults={
                'policy_type': 'CANCELLATION',
                'details': {
                    'cancellation_window_hours': 24,
                    'penalty_type': 'PERCENTAGE',
                    'penalty_value': 0,
                },
                'description': 'Free cancellation up to 24 hours before check-in'
            }
        )[0]

        policies['non_refundable'] = Policy.objects.get_or_create(
            name='Non-Refundable',
            defaults={
                'policy_type': 'CANCELLATION',
                'details': {
                    'cancellation_window_hours': 0,
                    'penalty_type': 'PERCENTAGE',
                    'penalty_value': 100,
                },
                'description': 'Non-refundable rate'
            }
        )[0]

        policies['prepayment_full'] = Policy.objects.get_or_create(
            name='Full Prepayment Required',
            defaults={
                'policy_type': 'PREPAYMENT',
                'details': {
                    'prepayment_percentage': 100,
                    'prepayment_deadline_hours': 24,
                },
                'description': 'Full payment required 24 hours before check-in'
            }
        )[0]

        policies['prepayment_partial'] = Policy.objects.get_or_create(
            name='Partial Prepayment (50%)',
            defaults={
                'policy_type': 'PREPAYMENT',
                'details': {
                    'prepayment_percentage': 50,
                    'prepayment_deadline_hours': 48,
                },
                'description': '50% payment required 48 hours before check-in'
            }
        )[0]

        return policies

    def _create_taxes(self):
        """Create GST and other taxes"""
        taxes = {}
        
        taxes['gst_12'] = TaxFee.objects.get_or_create(
            name='GST (12%)',
            defaults={
                'tax_type': 'PERCENTAGE',
                'value': 12.0,
                'is_inclusive': False,
                'gst_component': 'IGST',
                'hsn_sac_code': '9963',
                'description': 'Goods and Services Tax at 12%'
            }
        )[0]

        taxes['gst_18'] = TaxFee.objects.get_or_create(
            name='GST (18%)',
            defaults={
                'tax_type': 'PERCENTAGE',
                'value': 18.0,
                'is_inclusive': False,
                'gst_component': 'IGST',
                'hsn_sac_code': '9963',
                'description': 'Goods and Services Tax at 18%'
            }
        )[0]

        taxes['service_charge'] = TaxFee.objects.get_or_create(
            name='Service Charge (10%)',
            defaults={
                'tax_type': 'PERCENTAGE',
                'value': 10.0,
                'is_inclusive': False,
                'gst_component': 'NONE',
                'description': 'Service charge'
            }
        )[0]

        return taxes

    def _create_ota_platforms(self):
        """Create 75 OTA platforms"""
        platforms_data = [
            {
                'name': 'booking.com',
                'display_name': 'Booking.com',
                'platform_type': 'OTA',
                'api_base_url': 'https://distribution-xml.booking.com/2.0',
                'auth_type': 'BASIC_AUTH',
                'rate_limit_rpm': 10000,
                'rate_limit_rps': 100,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'expedia',
                'display_name': 'Expedia Group',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.expedia.com',
                'auth_type': 'SIGNATURE',
                'rate_limit_rpm': 5000,
                'rate_limit_rps': 50,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'agoda',
                'display_name': 'Agoda',
                'platform_type': 'OTA',
                'api_base_url': 'https://ycs.agoda.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'makemytrip',
                'display_name': 'MakeMyTrip',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.makemytrip.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'goibibo',
                'display_name': 'Goibibo',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.goibibo.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'yatra',
                'display_name': 'Yatra',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.yatra.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'cleartrip',
                'display_name': 'Cleartrip',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.cleartrip.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'ixigo',
                'display_name': 'Ixigo',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.ixigo.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1000,
                'rate_limit_rps': 10,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'tbo',
                'display_name': 'TBO (Travel Boutique Online)',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.tbo.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 5000,
                'rate_limit_rps': 50,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'hotelbeds',
                'display_name': 'Hotelbeds',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotelbeds.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'gta',
                'display_name': 'GTA (Global Travel Aggregator)',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.gta-travel.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'amadeus',
                'display_name': 'Amadeus GDS',
                'platform_type': 'GDS',
                'api_base_url': 'https://api.amadeus.com',
                'auth_type': 'OAUTH2',
                'rate_limit_rpm': 10000,
                'rate_limit_rps': 100,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'sabre',
                'display_name': 'Sabre GDS',
                'platform_type': 'GDS',
                'api_base_url': 'https://api.sabre.com',
                'auth_type': 'TOKEN',
                'rate_limit_rpm': 8000,
                'rate_limit_rps': 80,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'google_hotels',
                'display_name': 'Google Hotels',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://www.googleapis.com/hotels',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 5000,
                'rate_limit_rps': 50,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'trivago',
                'display_name': 'Trivago',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.trivago.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            # Additional 60 OTA Platforms
            {
                'name': 'airbnb',
                'display_name': 'Airbnb',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.airbnb.com',
                'auth_type': 'OAUTH2',
                'rate_limit_rpm': 5000,
                'rate_limit_rps': 50,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'hotels.com',
                'display_name': 'Hotels.com',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hotels.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 4000,
                'rate_limit_rps': 40,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'priceline',
                'display_name': 'Priceline',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.priceline.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'orbitz',
                'display_name': 'Orbitz',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.orbitz.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'travelocity',
                'display_name': 'Travelocity',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.travelocity.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotwire',
                'display_name': 'Hotwire',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hotwire.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'tripadvisor',
                'display_name': 'Tripadvisor',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.tripadvisor.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hrs',
                'display_name': 'HRS',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hrs.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2500,
                'rate_limit_rps': 25,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hostelworld',
                'display_name': 'Hostelworld',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hostelworld.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'ctrip',
                'display_name': 'Ctrip/Trip.com',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.ctrip.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 4000,
                'rate_limit_rps': 40,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'traveloka',
                'display_name': 'Traveloka',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.traveloka.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'thomas_cook',
                'display_name': 'Thomas Cook',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.thomascook.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'via_com',
                'display_name': 'Via.com',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.via.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'paytm_travel',
                'display_name': 'Paytm Travel',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.paytm.com/travel',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'bravofly',
                'display_name': 'Bravofly',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.bravofly.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'musafir',
                'display_name': 'Musafir',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.musafir.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'flipkart_travel',
                'display_name': 'Flipkart Travel',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.flipkart.com/travel',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'galileo_gds',
                'display_name': 'Galileo GDS',
                'platform_type': 'GDS',
                'api_base_url': 'https://api.galileo.com',
                'auth_type': 'TOKEN',
                'rate_limit_rpm': 8000,
                'rate_limit_rps': 80,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'worldspan_gds',
                'display_name': 'Worldspan GDS',
                'platform_type': 'GDS',
                'api_base_url': 'https://api.worldspan.com',
                'auth_type': 'TOKEN',
                'rate_limit_rpm': 7000,
                'rate_limit_rps': 70,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'gta_travel',
                'display_name': 'GTA Travel',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.gta-travel.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'hotusa',
                'display_name': 'Hotusa Hotels',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotusa.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotusa_hotels',
                'display_name': 'Hotusa Hotels',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotusa.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'tourico',
                'display_name': 'Tourico Holidays',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.tourico.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2500,
                'rate_limit_rps': 25,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'hotusa_group',
                'display_name': 'Hotusa Group',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotusagroup.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotel_planner',
                'display_name': 'Hotel Planner',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotelplanner.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotels_combined',
                'display_name': 'HotelsCombined',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.hotelscombined.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'kayak',
                'display_name': 'Kayak',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.kayak.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'skyscanner',
                'display_name': 'Skyscanner',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.skyscanner.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'momondo',
                'display_name': 'Momondo',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.momondo.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'wego',
                'display_name': 'Wego',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.wego.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotels_click',
                'display_name': 'HotelsClick',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotelsclick.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'hotel_runner',
                'display_name': 'Hotel Runner',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotelrunner.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotel_tonight',
                'display_name': 'Hotel Tonight',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hoteltonight.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'lastminute',
                'display_name': 'Lastminute.com',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.lastminute.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'laterooms',
                'display_name': 'LateRooms',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.laterooms.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'ebookers',
                'display_name': 'Ebookers',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.ebookers.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'cheaptickets',
                'display_name': 'CheapTickets',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.cheaptickets.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'venere',
                'display_name': 'Venere',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.venere.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'zenhotels',
                'display_name': 'ZenHotels',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.zenhotels.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'ostrovok',
                'display_name': 'Ostrovok',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.ostrovok.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'ostrovok_ru',
                'display_name': 'Ostrovok.ru',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.ostrovok.ru',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotels_ru',
                'display_name': 'Hotels.ru',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hotels.ru',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'booking_ua',
                'display_name': 'Booking.ua',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.booking.ua',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotels_24',
                'display_name': 'Hotels24',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hotels24.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotels_online',
                'display_name': 'HotelsOnline',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotelsonline.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'hotel_net',
                'display_name': 'Hotel.net',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotel.net',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotel_connect',
                'display_name': 'Hotel Connect',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotelconnect.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'hotel_wholesaler',
                'display_name': 'Hotel Wholesaler',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotelwholesaler.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotel_beds_connect',
                'display_name': 'Hotelbeds Connect',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.hotelbeds.com/connect',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'despegar',
                'display_name': 'Despegar',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.despegar.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'decolar',
                'display_name': 'Decolar',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.decolar.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'rumbo',
                'display_name': 'Rumbo',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.rumbo.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'edreams',
                'display_name': 'eDreams',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.edreams.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'opodo',
                'display_name': 'Opodo',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.opodo.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'gopili',
                'display_name': 'GoPili',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.gopili.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'liligo',
                'display_name': 'Liligo',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.liligo.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'japanican',
                'display_name': 'Japanican',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.japanican.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'rakuten_travel',
                'display_name': 'Rakuten Travel',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.travel.rakuten.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 3000,
                'rate_limit_rps': 30,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'jalan',
                'display_name': 'Jalan',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.jalan.net',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'relux',
                'display_name': 'Relux',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.relux.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'asiarooms',
                'display_name': 'Asiarooms',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.asiarooms.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'zenhotels_asia',
                'display_name': 'ZenHotels Asia',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.zenhotels.asia',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotels_combined_asia',
                'display_name': 'HotelsCombined Asia',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.hotelscombined.asia',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'wego_asia',
                'display_name': 'Wego Asia',
                'platform_type': 'METASEARCH',
                'api_base_url': 'https://api.wego.asia',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'tripadvisor_viator',
                'display_name': 'Tripadvisor Viator',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.viator.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'getaroom',
                'display_name': 'GetARoom',
                'platform_type': 'BEDBANK',
                'api_base_url': 'https://api.getaroom.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': True,
            },
            {
                'name': 'hotel_tonight_api',
                'display_name': 'Hotel Tonight API',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hoteltonight.com/v2',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 2000,
                'rate_limit_rps': 20,
                'supports_webhooks': True,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
            {
                'name': 'hotel_quickly',
                'display_name': 'Hotel Quickly',
                'platform_type': 'OTA',
                'api_base_url': 'https://api.hotelquickly.com',
                'auth_type': 'API_KEY',
                'rate_limit_rpm': 1500,
                'rate_limit_rps': 15,
                'supports_webhooks': False,
                'supports_polling': True,
                'supports_batch_updates': False,
            },
        ]

        platforms = {}
        for data in platforms_data:
            platform = IntegrationPlatform.objects.get_or_create(
                name=data['name'],
                defaults={
                    **data,
                    'is_active': True,
                    'is_connected': True,
                }
            )[0]
            platforms[data['name']] = platform
            self.stdout.write(f'  ✓ {platform.display_name}')

        return platforms

    def _create_hotels(self, tenant, policies, taxes):
        """Create 25 hotels across major Indian cities"""
        hotels_config = [
            # Mumbai (5 hotels)
            {'name': 'The Taj Mahal Palace', 'city': 'Mumbai', 'state': 'Maharashtra', 'postal': '400001', 
             'type': 'hotel', 'gstin': '27AABCU9603R1ZX', 'pan': 'AABCU9603R', 'address': 'Apollo Bunder, Colaba'},
            {'name': 'The Oberoi Mumbai', 'city': 'Mumbai', 'state': 'Maharashtra', 'postal': '400021',
             'type': 'hotel', 'gstin': '27AABCO1234R1ZX', 'pan': 'AABCO1234R', 'address': 'Nariman Point'},
            {'name': 'ITC Maratha', 'city': 'Mumbai', 'state': 'Maharashtra', 'postal': '400099',
             'type': 'hotel', 'gstin': '27AABCI5678R1ZX', 'pan': 'AABCI5678R', 'address': 'Sahar, Andheri East'},
            {'name': 'The Leela Mumbai', 'city': 'Mumbai', 'state': 'Maharashtra', 'postal': '400053',
             'type': 'hotel', 'gstin': '27AABCL9012R1ZX', 'pan': 'AABCL9012R', 'address': 'Sahar, Andheri East'},
            {'name': 'JW Marriott Mumbai', 'city': 'Mumbai', 'state': 'Maharashtra', 'postal': '400051',
             'type': 'hotel', 'gstin': '27AABCJ3456R1ZX', 'pan': 'AABCJ3456R', 'address': 'Juhu Tara Road, Juhu'},

            # Delhi (4 hotels)
            {'name': 'The Leela Palace New Delhi', 'city': 'New Delhi', 'state': 'Delhi', 'postal': '110023',
             'type': 'hotel', 'gstin': '07ABCDE1234F1Z5', 'pan': 'ABCDE1234F', 'address': 'Diplomatic Enclave, Chanakyapuri'},
            {'name': 'The Imperial New Delhi', 'city': 'New Delhi', 'state': 'Delhi', 'postal': '110001',
             'type': 'hotel', 'gstin': '07ABCDI5678F1Z5', 'pan': 'ABCDI5678F', 'address': 'Janpath, Connaught Place'},
            {'name': 'ITC Maurya', 'city': 'New Delhi', 'state': 'Delhi', 'postal': '110021',
             'type': 'hotel', 'gstin': '07ABCDM9012F1Z5', 'pan': 'ABCDM9012F', 'address': 'Sardar Patel Marg, Diplomatic Enclave'},
            {'name': 'The Lodhi New Delhi', 'city': 'New Delhi', 'state': 'Delhi', 'postal': '110003',
             'type': 'hotel', 'gstin': '07ABCDL3456F1Z5', 'pan': 'ABCDL3456F', 'address': 'Lodhi Road'},

            # Bangalore (3 hotels)
            {'name': 'The Ritz-Carlton Bangalore', 'city': 'Bangalore', 'state': 'Karnataka', 'postal': '560001',
             'type': 'hotel', 'gstin': '29AABCR7890K1Z2', 'pan': 'AABCR7890K', 'address': 'Residency Road'},
            {'name': 'ITC Gardenia', 'city': 'Bangalore', 'state': 'Karnataka', 'postal': '560025',
             'type': 'hotel', 'gstin': '29AABCG4567K1Z2', 'pan': 'AABCG4567K', 'address': 'Residency Road'},
            {'name': 'The Oberoi Bangalore', 'city': 'Bangalore', 'state': 'Karnataka', 'postal': '560052',
             'type': 'hotel', 'gstin': '29AABCO2345K1Z2', 'pan': 'AABCO2345K', 'address': 'MG Road'},

            # Goa (3 hotels)
            {'name': 'Taj Exotica Resort & Spa', 'city': 'Goa', 'state': 'Goa', 'postal': '403712',
             'type': 'resort', 'gstin': '30AABCT6789G1Z3', 'pan': 'AABCT6789G', 'address': 'Benaulim Beach'},
            {'name': 'The Leela Goa', 'city': 'Goa', 'state': 'Goa', 'postal': '403802',
             'type': 'resort', 'gstin': '30AABCL1234G1Z3', 'pan': 'AABCL1234G', 'address': 'Cavelossim Beach'},
            {'name': 'Park Hyatt Goa', 'city': 'Goa', 'state': 'Goa', 'postal': '403515',
             'type': 'resort', 'gstin': '30AABCP5678G1Z3', 'pan': 'AABCP5678G', 'address': 'Arossim Beach'},

            # Jaipur (2 hotels)
            {'name': 'The Rambagh Palace', 'city': 'Jaipur', 'state': 'Rajasthan', 'postal': '302005',
             'type': 'hotel', 'gstin': '08AABCR9012R1Z4', 'pan': 'AABCR9012R', 'address': 'Bhawani Singh Road'},
            {'name': 'ITC Rajputana', 'city': 'Jaipur', 'state': 'Rajasthan', 'postal': '302006',
             'type': 'hotel', 'gstin': '08AABCI3456R1Z4', 'pan': 'AABCI3456R', 'address': 'Palace Road'},

            # Udaipur (2 hotels)
            {'name': 'The Oberoi Udaivilas', 'city': 'Udaipur', 'state': 'Rajasthan', 'postal': '313001',
             'type': 'hotel', 'gstin': '08AABCO7890R1Z4', 'pan': 'AABCO7890R', 'address': 'Haridasji Ki Magri'},
            {'name': 'Taj Lake Palace', 'city': 'Udaipur', 'state': 'Rajasthan', 'postal': '313001',
             'type': 'hotel', 'gstin': '08AABCT2345R1Z4', 'pan': 'AABCT2345R', 'address': 'Lake Pichola'},

            # Agra (2 hotels)
            {'name': 'The Oberoi Amarvilas', 'city': 'Agra', 'state': 'Uttar Pradesh', 'postal': '282001',
             'type': 'hotel', 'gstin': '09AABCO5678U1Z5', 'pan': 'AABCO5678U', 'address': 'Taj East Gate Road'},
            {'name': 'ITC Mughal', 'city': 'Agra', 'state': 'Uttar Pradesh', 'postal': '282010',
             'type': 'hotel', 'gstin': '09AABCI1234U1Z5', 'pan': 'AABCI1234U', 'address': 'Taj Ganj'},

            # Kerala (2 hotels)
            {'name': 'Taj Bekal Resort & Spa', 'city': 'Kasaragod', 'state': 'Kerala', 'postal': '671316',
             'type': 'resort', 'gstin': '32AABCT9012K1Z6', 'pan': 'AABCT9012K', 'address': 'Kappil Beach'},
            {'name': 'The Leela Kovalam', 'city': 'Thiruvananthapuram', 'state': 'Kerala', 'postal': '695527',
             'type': 'resort', 'gstin': '32AABCL3456K1Z6', 'pan': 'AABCL3456K', 'address': 'Kovalam Beach'},

            # Hyderabad (2 hotels)
            {'name': 'ITC Kakatiya', 'city': 'Hyderabad', 'state': 'Telangana', 'postal': '500082',
             'type': 'hotel', 'gstin': '36AABCI7890T1Z7', 'pan': 'AABCI7890T', 'address': 'Begumpet'},
            {'name': 'The Park Hyderabad', 'city': 'Hyderabad', 'state': 'Telangana', 'postal': '500034',
             'type': 'hotel', 'gstin': '36AABCP2345T1Z7', 'pan': 'AABCP2345T', 'address': 'Raj Bhavan Road'},
        ]

        hotels = {}
        for idx, config in enumerate(hotels_config, 1):
            hotel = Property.objects.create(
                tenant=tenant,
                name=config['name'],
                legal_name=f"{config['name']} Pvt. Ltd.",
                property_type=config['type'],
                address_line1=config['address'],
                city=config['city'],
                state=config['state'],
                postal_code=config['postal'],
                country='India',
                phone=f'+91-{random.randint(10,99)}-{random.randint(10000000,99999999)}',
                email=f'info@{config["name"].lower().replace(" ", "").replace("-", "")}.com',
                website=f'https://www.{config["name"].lower().replace(" ", "").replace("-", "")}.com',
                timezone='Asia/Kolkata',
                currency='INR',
                gstin=config['gstin'],
                pan=config['pan'],
                is_active=True,
            )
            hotels[hotel.id] = {
                'hotel': hotel,
                'config': config,
            }
            self.stdout.write(f'  ✓ {idx}. {hotel.name} - {config["city"]}')

        return hotels

    def _create_room_types(self, hotels_data):
        """Create room types for each hotel"""
        room_types = {}
        
        room_type_templates = [
            {
                'name': 'Standard Room',
                'description': 'Comfortable standard room with essential amenities',
                'max_occupancy': 2,
                'base_occupancy': 2,
                'max_adults': 2,
                'max_children': 1,
                'size_sqm': 20.0,
                'bed_type': 'Double Bed',
                'amenities': ['wifi', 'ac', 'tv', 'telephone'],
            },
            {
                'name': 'Deluxe Room',
                'description': 'Spacious room with city or garden view',
                'max_occupancy': 3,
                'base_occupancy': 2,
                'max_adults': 3,
                'max_children': 2,
                'size_sqm': 30.0,
                'bed_type': 'King Size',
                'amenities': ['wifi', 'ac', 'tv', 'minibar', 'safe', 'balcony'],
            },
            {
                'name': 'Executive Suite',
                'description': 'Luxury suite with separate living area',
                'max_occupancy': 4,
                'base_occupancy': 2,
                'max_adults': 4,
                'max_children': 2,
                'size_sqm': 60.0,
                'bed_type': 'King Size + Sofa Bed',
                'amenities': ['wifi', 'ac', 'tv', 'minibar', 'safe', 'balcony', 'jacuzzi', 'work_desk'],
            },
            {
                'name': 'Presidential Suite',
                'description': 'Ultra-luxury suite with premium amenities',
                'max_occupancy': 6,
                'base_occupancy': 2,
                'max_adults': 6,
                'max_children': 4,
                'size_sqm': 120.0,
                'bed_type': 'King Size + Multiple Beds',
                'amenities': ['wifi', 'ac', 'tv', 'minibar', 'safe', 'balcony', 'jacuzzi', 'work_desk', 'dining_area', 'butler_service'],
            },
        ]

        for hotel_id, hotel_info in hotels_data.items():
            hotel = hotel_info['hotel']
            hotel_room_types = []
            
            # Each hotel gets 2-4 room types
            num_room_types = random.randint(2, 4)
            selected_templates = random.sample(room_type_templates, num_room_types)
            
            for template in selected_templates:
                room_type = RoomType.objects.create(
                    property=hotel,
                    name=template['name'],
                    description=template['description'],
                    max_occupancy=template['max_occupancy'],
                    base_occupancy=template['base_occupancy'],
                    max_adults=template['max_adults'],
                    max_children=template['max_children'],
                    size_sqm=template['size_sqm'],
                    bed_type=template['bed_type'],
                    amenities=template['amenities'],
                    is_active=True,
                )
                hotel_room_types.append(room_type)
            
            room_types[hotel_id] = hotel_room_types

        return room_types

    def _ensure_meal_plans(self):
        """Create standard meal plans if missing (required by rate plans)."""
        meal_plans = [
            ('ROOM_ONLY', 'Room Only', 'No meals included'),
            ('BREAKFAST', 'Breakfast', 'Breakfast included'),
            ('HALF_BOARD', 'Half Board', 'Breakfast and dinner included'),
            ('FULL_BOARD', 'Full Board', 'All meals included'),
            ('ALL_INCLUSIVE', 'All Inclusive', 'All meals and beverages included'),
        ]
        for code, name, description in meal_plans:
            meal_plan, created = MealPlan.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': description},
            )
            if created:
                self.stdout.write(f'  ✓ {name}')

    def _create_rate_plans(self, hotels_data, room_types_data, policies):
        """Create rate plans for each room type"""
        rate_plans = {}
        meal_plans = {
            'ro': MealPlan.objects.get(code='ROOM_ONLY'),
            'bf': MealPlan.objects.get(code='BREAKFAST'),
            'hb': MealPlan.objects.get(code='HALF_BOARD'),
            'fb': MealPlan.objects.get(code='FULL_BOARD'),
        }

        base_rates = {
            'Standard Room': (2000, 5000),
            'Deluxe Room': (4000, 8000),
            'Executive Suite': (8000, 15000),
            'Presidential Suite': (15000, 30000),
        }

        for hotel_id, hotel_info in hotels_data.items():
            hotel = hotel_info['hotel']
            hotel_room_types = room_types_data.get(hotel_id, [])
            hotel_rate_plans = []
            
            for room_type in hotel_room_types:
                room_name = room_type.name
                min_rate, max_rate = base_rates.get(room_name, (3000, 6000))
                base_rate = random.randint(min_rate, max_rate)
                
                # Flexible Rate
                rate_plan_flex = RatePlan.objects.create(
                    property=hotel,
                    room_type=room_type,
                    name=f'{room_name} - Flexible',
                    description='Flexible cancellation policy',
                    meal_plan=meal_plans['bf'],
                    inclusions=['wifi', 'breakfast'],
                    base_rate=Money(base_rate, 'INR'),
                    base_occupancy=2,
                    extra_adult_charge=Money(base_rate * 0.2, 'INR'),
                    extra_child_charge=Money(base_rate * 0.1, 'INR'),
                    cancellation_policy=policies['free_cancel_48h'],
                    prepayment_policy=policies['prepayment_partial'],
                    is_active=True,
                )
                hotel_rate_plans.append(rate_plan_flex)
                
                # Non-Refundable Rate (20% discount)
                rate_plan_nr = RatePlan.objects.create(
                    property=hotel,
                    room_type=room_type,
                    name=f'{room_name} - Non-Refundable',
                    description='Non-refundable discounted rate',
                    meal_plan=meal_plans['bf'],
                    inclusions=['wifi', 'breakfast'],
                    base_rate=Money(int(base_rate * 0.8), 'INR'),
                    base_occupancy=2,
                    extra_adult_charge=Money(int(base_rate * 0.16), 'INR'),
                    extra_child_charge=Money(int(base_rate * 0.08), 'INR'),
                    cancellation_policy=policies['non_refundable'],
                    prepayment_policy=policies['prepayment_full'],
                    is_derived=True,
                    parent_rate_plan=rate_plan_flex,
                    derivation_rule={'discount_percent': 20},
                    is_active=True,
                )
                hotel_rate_plans.append(rate_plan_nr)
                
                # Premium Rate (with more inclusions)
                if room_name in ['Executive Suite', 'Presidential Suite']:
                    rate_plan_premium = RatePlan.objects.create(
                        property=hotel,
                        room_type=room_type,
                        name=f'{room_name} - Premium',
                        description='Premium rate with all inclusions',
                        meal_plan=meal_plans['hb'],
                        inclusions=['wifi', 'breakfast', 'dinner', 'parking', 'airport_transfer', 'spa_access'],
                        base_rate=Money(int(base_rate * 1.3), 'INR'),
                        base_occupancy=2,
                        extra_adult_charge=Money(int(base_rate * 0.26), 'INR'),
                        extra_child_charge=Money(int(base_rate * 0.13), 'INR'),
                        cancellation_policy=policies['free_cancel_24h'],
                        prepayment_policy=policies['prepayment_partial'],
                        is_active=True,
                    )
                    hotel_rate_plans.append(rate_plan_premium)
            
            rate_plans[hotel_id] = hotel_rate_plans

        return rate_plans

    def _create_inventory(self, hotels_data, room_types_data):
        """Create inventory for 365 days"""
        today = date.today()
        total_inventory = 0
        
        for hotel_id, hotel_info in hotels_data.items():
            hotel = hotel_info['hotel']
            hotel_room_types = room_types_data.get(hotel_id, [])
            
            for room_type in hotel_room_types:
                # Random total rooms between 10-50
                total_rooms = random.randint(10, 50)
                
                for i in range(365):
                    inv_date = today + timedelta(days=i)
                    
                    # Simulate some bookings (reduce availability)
                    bookings = random.randint(0, int(total_rooms * 0.3))
                    available = total_rooms - bookings
                    blocked = random.randint(0, 2)
                    
                    Inventory.objects.get_or_create(
                        property=hotel,
                        room_type=room_type,
                        date=inv_date,
                        defaults={
                            'available_rooms': max(0, available - blocked),
                            'total_rooms': total_rooms,
                            'blocked_rooms': blocked,
                        }
                    )
                    total_inventory += 1
        
        self.stdout.write(f'  ✓ Created {total_inventory:,} inventory records')

    def _create_property_integrations(self, hotels_data, room_types_data, rate_plans_data, platforms):
        """Create property integrations with multiple platforms"""
        major_platforms = ['booking.com', 'expedia', 'agoda', 'makemytrip', 'goibibo']
        all_platforms = list(platforms.keys())
        
        total_integrations = 0
        for hotel_id, hotel_info in hotels_data.items():
            hotel = hotel_info['hotel']
            hotel_room_types = room_types_data.get(hotel_id, [])
            hotel_rate_plans = rate_plans_data.get(hotel_id, [])
            
            # Each hotel connects to 3-8 platforms
            num_platforms = random.randint(3, 8)
            selected_platforms = random.sample(all_platforms, min(num_platforms, len(all_platforms)))
            
            # Ensure major platforms are included for first 10 hotels
            if hotel_id <= 10:
                for major in major_platforms:
                    if major in all_platforms and major not in selected_platforms:
                        selected_platforms.append(major)
            
            for platform_name in selected_platforms:
                platform = platforms[platform_name]
                
                # Create room type mappings
                room_mappings = {}
                for idx, room_type in enumerate(hotel_room_types, 1):
                    room_mappings[str(room_type.id)] = f'room_type_{platform_name[:3]}_{hotel_id}_{idx}'
                
                # Create rate plan mappings
                rate_mappings = {}
                for idx, rate_plan in enumerate(hotel_rate_plans, 1):
                    rate_mappings[str(rate_plan.id)] = f'rate_plan_{platform_name[:3]}_{hotel_id}_{idx}'
                
                PropertyIntegration.objects.create(
                    property=hotel,
                    platform=platform,
                    provider_property_id=f'{platform_name[:3].upper()}{hotel_id:04d}',
                    provider_room_type_mappings=room_mappings,
                    provider_rate_plan_mappings=rate_mappings,
                    sync_availability=True,
                    sync_rates=True,
                    sync_inventory=True,
                    sync_reservations=True,
                    availability_sync_interval=5,
                    rates_sync_interval=15,
                    inventory_sync_interval=5,
                    reservations_sync_interval=10,
                    is_active=True,
                )
                total_integrations += 1
        
        self.stdout.write(f'  ✓ Created {total_integrations} property integrations')

    def _create_reservations(self, hotels_data, room_types_data, rate_plans_data, platforms):
        """Create sample reservations"""
        from bookings.models import Reservation, Payment
        
        platform_names = list(platforms.keys())
        first_names = ['Raj', 'Priya', 'Amit', 'Sneha', 'Vikram', 'Anjali', 'Rohit', 'Kavya', 'Arjun', 'Meera']
        last_names = ['Sharma', 'Patel', 'Kumar', 'Singh', 'Reddy', 'Nair', 'Gupta', 'Joshi', 'Mehta', 'Iyer']
        
        total_reservations = 0
        today = date.today()
        
        for hotel_id, hotel_info in hotels_data.items():
            hotel = hotel_info['hotel']
            hotel_room_types = room_types_data.get(hotel_id, [])
            hotel_rate_plans = rate_plans_data.get(hotel_id, [])
            
            if not hotel_room_types or not hotel_rate_plans:
                continue
            
            # Create 5-15 reservations per hotel
            num_reservations = random.randint(5, 15)
            
            for i in range(num_reservations):
                room_type = random.choice(hotel_room_types)
                rate_plan = random.choice([rp for rp in hotel_rate_plans if rp.room_type == room_type])
                platform_name = random.choice(platform_names)
                platform = platforms[platform_name]
                
                # Random check-in date (next 30-180 days)
                days_ahead = random.randint(30, 180)
                check_in = today + timedelta(days=days_ahead)
                nights = random.randint(1, 7)
                check_out = check_in + timedelta(days=nights)
                
                # Calculate amounts
                base_rate = float(rate_plan.base_rate.amount)
                adults = random.randint(1, min(room_type.max_adults, 4))
                children = random.randint(0, min(room_type.max_children, 2))
                
                extra_adults = max(0, adults - 2)
                extra_children = children
                
                base_room_rate = Money(
                    int(base_rate * nights + 
                        (extra_adults * float(rate_plan.extra_adult_charge.amount) * nights) +
                        (extra_children * float(rate_plan.extra_child_charge.amount) * nights)),
                    'INR'
                )
                
                # GST calculation (12%)
                gst_amount = base_room_rate.amount * Decimal('0.12')
                total_taxes = Money(int(gst_amount), 'INR')
                total_amount = base_room_rate + total_taxes
                
                # GST components (simplified - using IGST for inter-state)
                igst = total_taxes
                cgst = Money(0, 'INR')
                sgst = Money(0, 'INR')
                
                # Random status
                status = random.choice(['CONFIRMED', 'CONFIRMED', 'CONFIRMED', 'PENDING', 'CONFIRMED'])
                
                guest_name = f"{random.choice(first_names)} {random.choice(last_names)}"
                guest_email = f"{guest_name.lower().replace(' ', '.')}@example.com"
                
                reservation = Reservation.objects.create(
                    provider_name=platform_name,
                    provider_reservation_id=f'{platform_name[:3].upper()}{hotel_id:04d}{i:06d}',
                    provider_confirmation_code=f'CONF{hotel_id:04d}{i:06d}',
                    property=hotel,
                    room_type=room_type,
                    rate_plan=rate_plan,
                    check_in=check_in,
                    check_out=check_out,
                    nights=nights,
                    guest_name=guest_name,
                    guest_email=guest_email,
                    guest_phone=f'+91-{random.randint(9000000000, 9999999999)}',
                    guest_city=hotel.city,
                    guest_state=hotel.state,
                    guest_country='India',
                    adults=adults,
                    children=children,
                    base_room_rate=base_room_rate,
                    total_taxes_fees=total_taxes,
                    total_amount=total_amount,
                    currency='INR',
                    cgst_amount=cgst,
                    sgst_amount=sgst,
                    igst_amount=igst,
                    status=status,
                )
                
                # Create payment if confirmed
                if status == 'CONFIRMED':
                    Payment.objects.create(
                        reservation=reservation,
                        amount=total_amount,
                        currency='INR',
                        payment_method=random.choice(['CREDIT_CARD', 'UPI', 'NET_BANKING', 'DEBIT_CARD']),
                        payment_status='COMPLETED',
                        transaction_id=f'TXN{hotel_id:04d}{i:06d}',
                        gateway_name=random.choice(['razorpay', 'payu', 'ccavenue']),
                        paid_at=timezone.now() - timedelta(days=random.randint(1, 30)),
                    )
                
                total_reservations += 1
        
        self.stdout.write(f'  ✓ Created {total_reservations} reservations')

    def _create_promotions(self, hotels_data):
        """Create promotions for hotels"""
        today = date.today()
        
        promotion_types = [
            {
                'name': 'Early Bird Discount',
                'promotion_type': 'PERCENTAGE',
                'discount_value': 15.0,
                'eligibility_rules': {'min_los': 3, 'advance_booking_days': 30},
                'description': '15% discount for bookings made 30+ days in advance with minimum 3 nights stay',
            },
            {
                'name': 'Weekend Special',
                'promotion_type': 'PERCENTAGE',
                'discount_value': 10.0,
                'eligibility_rules': {'min_los': 2},
                'description': '10% discount on weekend stays',
            },
            {
                'name': 'Long Stay Discount',
                'promotion_type': 'PERCENTAGE',
                'discount_value': 20.0,
                'eligibility_rules': {'min_los': 5},
                'description': '20% discount for stays of 5 nights or more',
            },
            {
                'name': 'Last Minute Deal',
                'promotion_type': 'FIXED',
                'discount_value': 1000.0,
                'eligibility_rules': {'advance_booking_days': 7, 'max_advance_booking_days': 14},
                'description': '₹1000 off on last minute bookings',
            },
        ]
        
        total_promotions = 0
        for hotel_id, hotel_info in hotels_data.items():
            hotel = hotel_info['hotel']
            
            # Each hotel gets 1-2 promotions
            num_promotions = random.randint(1, 2)
            selected_promotions = random.sample(promotion_types, min(num_promotions, len(promotion_types)))
            
            for promo_template in selected_promotions:
                Promotion.objects.create(
                    name=promo_template['name'],
                    property=hotel,
                    promotion_type=promo_template['promotion_type'],
                    discount_value=promo_template['discount_value'],
                    start_date=today,
                    end_date=today + timedelta(days=90),
                    eligibility_rules=promo_template['eligibility_rules'],
                    description=promo_template['description'],
                    is_active=True,
                )
                total_promotions += 1
        
        self.stdout.write(f'  ✓ Created {total_promotions} promotions')

    def _print_summary(self):
        """Print summary of created data"""
        from integrations.models import IntegrationPlatform, PropertyIntegration
        from bookings.models import Reservation, Payment
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 SEED DATA SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'  🏨 Properties: {Property.objects.count()}')
        self.stdout.write(f'  🛏️  Room Types: {RoomType.objects.count()}')
        self.stdout.write(f'  💵 Rate Plans: {RatePlan.objects.count()}')
        self.stdout.write(f'  📦 Inventory Records: {Inventory.objects.count():,}')
        self.stdout.write(f'  🌐 Integration Platforms: {IntegrationPlatform.objects.count()}')
        self.stdout.write(f'  🔗 Property Integrations: {PropertyIntegration.objects.count()}')
        self.stdout.write(f'  📅 Reservations: {Reservation.objects.count()}')
        self.stdout.write(f'  💳 Payments: {Payment.objects.count()}')
        self.stdout.write(f'  🎁 Promotions: {Promotion.objects.count()}')
        self.stdout.write(f'  📋 Policies: {Policy.objects.count()}')
        self.stdout.write(f'  💰 Taxes: {TaxFee.objects.count()}')
        self.stdout.write('='*60 + '\n')
