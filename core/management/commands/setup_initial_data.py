"""
Management command to set up initial data
"""
from django.core.management.base import BaseCommand
from core.models import MealPlan


class Command(BaseCommand):
    help = 'Set up initial data (meal plans, etc.)'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create meal plans
        meal_plans = [
            ('ROOM_ONLY', 'Room Only', 'No meals included'),
            ('BREAKFAST', 'Breakfast', 'Breakfast included'),
            ('HALF_BOARD', 'Half Board', 'Breakfast and dinner included'),
            ('FULL_BOARD', 'Full Board', 'All meals included'),
            ('ALL_INCLUSIVE', 'All Inclusive', 'All meals and beverages included'),
        ]
        
        created_count = 0
        for code, name, description in meal_plans:
            meal_plan, created = MealPlan.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': description}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created meal plan: {name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} meal plans.'))

