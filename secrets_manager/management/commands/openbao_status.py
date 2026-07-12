"""
Show OpenBao connection / loaded secret status (no secret values).
"""
from django.core.management.base import BaseCommand

from channel_manager.openbao.client import OpenBaoClient, OpenBaoError
from channel_manager.openbao.loader import apply_openbao_secrets, base_secret_path, is_enabled, secret_status


class Command(BaseCommand):
    help = 'Show OpenBao secrets manager status'

    def handle(self, *args, **options):
        self.stdout.write('🔐 OpenBao status\n')
        self.stdout.write(f'  enabled:   {is_enabled()}')
        self.stdout.write(f'  path:      {base_secret_path()}')

        if not is_enabled():
            self.stdout.write(self.style.WARNING(
                '  OPENBAO_ENABLED is false — Django uses .env / process env only.'
            ))
            return

        client = OpenBaoClient()
        self.stdout.write(f'  addr:      {client.addr}')
        self.stdout.write(f'  mount:     {client.mount_point}')

        if not client.is_reachable():
            self.stdout.write(self.style.ERROR('  health:    unreachable'))
            return
        self.stdout.write(self.style.SUCCESS('  health:    ok'))

        try:
            client.client  # auth
            self.stdout.write(self.style.SUCCESS('  auth:      ok'))
            keys = client.list_secrets(base_secret_path().rsplit('/', 1)[0])
            self.stdout.write(f'  listed:    {keys or "(none / no list ACL)"}')
        except OpenBaoError as exc:
            self.stdout.write(self.style.ERROR(f'  auth:      {exc}'))
            return

        status = apply_openbao_secrets(force=True)
        self.stdout.write(f'  loaded:    {status.get("loaded")}')
        self.stdout.write(f'  source:    {status.get("source")}')
        self.stdout.write(f'  keys:      {", ".join(status.get("keys") or []) or "(none)"}')
        if status.get('error'):
            self.stdout.write(self.style.ERROR(f'  error:     {status["error"]}'))
        else:
            self.stdout.write(self.style.SUCCESS('  Ready.'))
        # silence unused
        _ = secret_status()
