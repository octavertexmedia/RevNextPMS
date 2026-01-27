"""
Management command to set up the database
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Set up the database (create if needed)'

    def handle(self, *args, **options):
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        
        self.stdout.write(f'Setting up database: {db_name}')
        
        # Try to connect to postgres database to create the target database
        try:
            # Connect to default postgres database
            from django.db import connections
            postgres_db = connections['default'].settings_dict.copy()
            postgres_db['NAME'] = 'postgres'  # Connect to default postgres DB
            
            import psycopg2
            conn = psycopg2.connect(
                host=postgres_db.get('HOST', 'localhost'),
                port=postgres_db.get('PORT', '5432'),
                user=postgres_db.get('USER', 'postgres'),
                password=postgres_db.get('PASSWORD', ''),
                database='postgres'
            )
            conn.autocommit = True
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                [db_name]
            )
            exists = cursor.fetchone()
            
            if not exists:
                # Create database
                cursor.execute(f'CREATE DATABASE {db_name}')
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created database: {db_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Database {db_name} already exists')
                )
            
            cursor.close()
            conn.close()
            
            self.stdout.write(
                self.style.SUCCESS('\nDatabase setup complete!')
            )
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Run migrations: python manage.py migrate')
            self.stdout.write('2. Create superuser: python manage.py createsuperuser')
            self.stdout.write('3. Load initial data: python manage.py setup_initial_data')
            
        except psycopg2.OperationalError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to connect to PostgreSQL: {e}')
            )
            self.stdout.write('\nPlease ensure:')
            self.stdout.write('1. PostgreSQL is installed and running')
            self.stdout.write('2. Database credentials in .env are correct')
            self.stdout.write('3. You have permission to create databases')
            self.stdout.write('\nOr create the database manually:')
            self.stdout.write(f'  createdb {db_name}')
        except ImportError:
            self.stdout.write(
                self.style.ERROR('psycopg2 is not installed')
            )
            self.stdout.write('Install it with: pip install psycopg2-binary')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )

