"""
Management command to create a superuser non-interactively
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser non-interactively'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the superuser',
            default=os.getenv('SUPERUSER_USERNAME', 'admin')
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the superuser',
            default=os.getenv('SUPERUSER_EMAIL', 'admin@example.com')
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser',
            default=os.getenv('SUPERUSER_PASSWORD', None)
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Use environment variables or defaults only',
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        no_input = options['no_input']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists.')
            )
            return

        # If no password provided and not in no-input mode, prompt
        if not password and not no_input:
            import getpass
            password = getpass.getpass('Password: ')
            password_confirm = getpass.getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(
                    self.style.ERROR('Error: Passwords do not match.')
                )
                return

        # If still no password, generate a random one
        if not password:
            import secrets
            password = secrets.token_urlsafe(16)
            self.stdout.write(
                self.style.WARNING(f'No password provided. Generated random password: {password}')
            )
            self.stdout.write(
                self.style.WARNING('Please save this password securely!')
            )

        # Create superuser
        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {username}')
            )
            self.stdout.write(f'Email: {email}')
            if not no_input:
                self.stdout.write('You can now log in at http://localhost:8000/admin/')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )

