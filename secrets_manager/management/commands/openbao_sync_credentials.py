"""
Push local GatewayConfig / PropertyIntegration credentials into OpenBao.
"""
from django.core.management.base import BaseCommand

from channel_manager.openbao.loader import is_enabled
from payment_gateways.models import GatewayConfig


class Command(BaseCommand):
    help = 'Sync payment gateway (and optionally integration) credentials into OpenBao'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-local',
            action='store_true',
            help='Blank local api_key/api_secret after a successful OpenBao write',
        )
        parser.add_argument(
            '--integrations',
            action='store_true',
            help='Also ensure PropertyIntegration.secret_ref paths exist (config JSON push)',
        )

    def handle(self, *args, **options):
        if not is_enabled():
            self.stdout.write(self.style.ERROR(
                'OPENBAO_ENABLED is false — enable it and set OPENBAO_ADDR/TOKEN first.'
            ))
            return

        synced = 0
        for cfg in GatewayConfig.objects.select_related('property').all():
            if cfg.sync_secrets_to_openbao(clear_local=options['clear_local']):
                synced += 1
                self.stdout.write(f'  ✓ gateway {cfg.gateway_name} → {cfg.secret_ref}')
            else:
                self.stdout.write(self.style.WARNING(
                    f'  skip gateway id={cfg.id} (no property/tenant or write failed)'
                ))

        if options['integrations']:
            from channel_manager.openbao.credentials import write_path
            from integrations.models import PropertyIntegration
            for pi in PropertyIntegration.objects.select_related('property', 'platform'):
                path = pi.ensure_secret_ref()
                if not path:
                    continue
                payload = {k: v for k, v in (pi.config or {}).items() if v not in (None, '')}
                if write_path(path, payload, merge=True):
                    pi.save(update_fields=['secret_ref', 'updated_at'])
                    synced += 1
                    self.stdout.write(f'  ✓ integration {pi} → {path}')

        self.stdout.write(self.style.SUCCESS(f'Synced {synced} credential sets to OpenBao'))
