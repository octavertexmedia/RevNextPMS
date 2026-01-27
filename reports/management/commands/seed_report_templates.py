"""
Management command to seed report templates
"""
from django.core.management.base import BaseCommand
from reports.models import ReportTemplate


class Command(BaseCommand):
    help = 'Seed report templates'

    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Revenue Report',
                'report_type': 'revenue',
                'description': 'Comprehensive revenue report with property and channel breakdown',
                'format': 'pdf',
                'fields': ['total_revenue', 'total_bookings', 'property_breakdown', 'channel_breakdown'],
                'filters': {},
                'can_schedule': True,
                'default_schedule': '0 0 * * *',  # Daily at midnight
            },
            {
                'name': 'Occupancy Report',
                'report_type': 'occupancy',
                'description': 'Room occupancy statistics and availability analysis',
                'format': 'pdf',
                'fields': ['occupancy_rate', 'total_room_nights', 'property_breakdown'],
                'filters': {},
                'can_schedule': True,
                'default_schedule': '0 0 * * *',  # Daily at midnight
            },
            {
                'name': 'Bookings Report',
                'report_type': 'bookings',
                'description': 'Booking statistics by channel and status',
                'format': 'pdf',
                'fields': ['total_bookings', 'confirmed', 'cancelled', 'pending', 'channel_breakdown'],
                'filters': {},
                'can_schedule': True,
                'default_schedule': '0 0 * * *',  # Daily at midnight
            },
            {
                'name': 'Channel Performance Report',
                'report_type': 'channel_performance',
                'description': 'Performance metrics for each OTA channel',
                'format': 'excel',
                'fields': ['bookings', 'revenue', 'avg_booking_value', 'sync_success_rate'],
                'filters': {},
                'can_schedule': True,
                'default_schedule': '0 0 * * 1',  # Weekly on Monday
            },
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = ReportTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created template: {template.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⊘ Template already exists: {template.name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Created {created_count} new report templates'))
