"""
Bootstrap OpenBao KV mount and seed secrets from the current environment / .env.
"""
from __future__ import annotations

import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from channel_manager.openbao.catalog import SECRET_GROUPS
from channel_manager.openbao.client import OpenBaoClient, OpenBaoError
from channel_manager.openbao.loader import base_secret_path


class Command(BaseCommand):
    help = 'Enable KV v2 (if needed) and write RevNext secrets into OpenBao from env'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be written without writing',
        )
        parser.add_argument(
            '--groups',
            nargs='*',
            default=None,
            help=f'Secret groups to sync: {", ".join(SECRET_GROUPS)} (default: all)',
        )
        parser.add_argument(
            '--flat',
            action='store_true',
            help='Write all keys to a single path instead of nested group paths',
        )
        parser.add_argument(
            '--include-empty',
            action='store_true',
            help='Also write empty string values',
        )

    def handle(self, *args, **options):
        try:
            client = OpenBaoClient()
            # force auth
            _ = client.client
        except OpenBaoError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(f'Connecting to {client.addr} (mount={client.mount_point})')
        try:
            client.ensure_kv_v2()
            self.stdout.write(self.style.SUCCESS(f'KV v2 ready at mount "{client.mount_point}"'))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(
                f'Could not ensure KV mount (may already exist / insufficient ACL): {exc}'
            ))

        groups = options['groups'] or list(SECRET_GROUPS.keys())
        unknown = set(groups) - set(SECRET_GROUPS)
        if unknown:
            raise CommandError(f'Unknown groups: {", ".join(sorted(unknown))}')

        base = base_secret_path()
        dry = options['dry_run']
        written = 0

        if options['flat']:
            payload = {}
            for group in groups:
                for key in SECRET_GROUPS[group]:
                    val = os.getenv(key)
                    if val is None and hasattr(settings, key):
                        val = getattr(settings, key)
                    if val is None:
                        continue
                    if val == '' and not options['include_empty']:
                        continue
                    payload[key] = str(val)
            path = base
            self._write(client, path, payload, dry)
            written += len(payload)
        else:
            for group in groups:
                payload = {}
                for key in SECRET_GROUPS[group]:
                    val = os.getenv(key)
                    if val is None and hasattr(settings, key):
                        val = getattr(settings, key)
                    if val is None:
                        continue
                    if val == '' and not options['include_empty']:
                        continue
                    payload[key] = str(val)
                if not payload:
                    self.stdout.write(f'  skip {group}: no values in env')
                    continue
                path = f'{base}/{group}'
                self._write(client, path, payload, dry)
                written += len(payload)

        action = 'Would write' if dry else 'Wrote'
        self.stdout.write(self.style.SUCCESS(
            f'{action} {written} keys under {base}'
        ))
        self.stdout.write(
            'Enable in Django with OPENBAO_ENABLED=true and restart the app.'
        )

    def _write(self, client, path, payload, dry):
        masked = {k: ('***' if any(s in k for s in ('PASSWORD', 'SECRET', 'SALT', 'KEY', 'TOKEN', 'DSN')) else v)
                  for k, v in payload.items()}
        self.stdout.write(f'  {"DRY " if dry else ""}→ {path}: {list(masked.keys())}')
        if not dry:
            client.write_secret(path, payload, merge=True)
