"""
Read a secret path from OpenBao (values redacted unless --reveal).
"""
from django.core.management.base import BaseCommand, CommandError

from channel_manager.openbao.client import OpenBaoClient, OpenBaoError
from channel_manager.openbao.loader import base_secret_path


class Command(BaseCommand):
    help = 'Read secrets from OpenBao at the configured path'

    def add_arguments(self, parser):
        parser.add_argument(
            'path',
            nargs='?',
            default='',
            help='Path relative to mount (default: OPENBAO_SECRET_PATH/env)',
        )
        parser.add_argument(
            '--reveal',
            action='store_true',
            help='Print secret values (dangerous — local use only)',
        )

    def handle(self, *args, **options):
        path = options['path'] or base_secret_path()
        try:
            client = OpenBaoClient()
            data = client.read_secret(path)
        except OpenBaoError as exc:
            raise CommandError(str(exc)) from exc

        if not data:
            self.stdout.write(self.style.WARNING(f'No data at {path}'))
            return

        self.stdout.write(f'Secrets at {client.mount_point}/{path}:')
        for key, value in sorted(data.items()):
            if options['reveal']:
                self.stdout.write(f'  {key}={value}')
            else:
                shown = '***' if value else '(empty)'
                self.stdout.write(f'  {key}={shown}')
