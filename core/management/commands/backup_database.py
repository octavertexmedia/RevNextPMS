"""
Management command for automated database backups
"""
import os
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create a PostgreSQL database backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to save backup files'
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='Number of days to retain backups'
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        retention_days = options['retention_days']
        
        # Create backup directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get database settings
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT']
        
        # Generate backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'{db_name}_{timestamp}.sql'
        backup_path = os.path.join(output_dir, backup_filename)
        
        # Create backup using pg_dump
        try:
            pg_dump_cmd = [
                'pg_dump',
                '-h', db_host,
                '-p', str(db_port),
                '-U', db_user,
                '-d', db_name,
                '-F', 'c',  # Custom format
                '-f', backup_path,
            ]
            
            # Set PGPASSWORD environment variable if password is provided
            env = os.environ.copy()
            db_password = settings.DATABASES['default'].get('PASSWORD')
            if db_password:
                env['PGPASSWORD'] = db_password
            
            result = subprocess.run(
                pg_dump_cmd,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                file_size = os.path.getsize(backup_path)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Backup created successfully: {backup_path} ({file_size / 1024 / 1024:.2f} MB)'
                    )
                )
                logger.info(f'Database backup created: {backup_path}')
                
                # Clean up old backups
                self.cleanup_old_backups(output_dir, retention_days)
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Backup failed: {result.stderr}')
                )
                logger.error(f'Database backup failed: {result.stderr}')
        
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('✗ pg_dump not found. Please install PostgreSQL client tools.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error creating backup: {str(e)}')
            )
            logger.error(f'Error creating backup: {e}', exc_info=True)
    
    def cleanup_old_backups(self, backup_dir, retention_days):
        """Remove backups older than retention_days"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        deleted_count = 0
        for filename in os.listdir(backup_dir):
            file_path = os.path.join(backup_dir, filename)
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f'Deleted old backup: {file_path}')
                    except Exception as e:
                        logger.error(f'Error deleting backup {file_path}: {e}')
        
        if deleted_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'✓ Cleaned up {deleted_count} old backup(s)')
            )
