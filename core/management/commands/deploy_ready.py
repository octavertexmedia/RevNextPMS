"""
Validate production deployment readiness (hosts, apps, migrations, catalog).
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

from channel_manager.domains import NGINX_APP_HOSTS, PRODUCTION_HOSTS


class Command(BaseCommand):
    help = 'Check that multi-product infra is ready for deployment'

    def handle(self, *args, **options):
        errors = []
        warnings = []

        for app in (
            'products', 'booking_engine', 'b2b_network', 'tours', 'hotels',
            'rbac', 'secrets_manager',
        ):
            if app not in settings.INSTALLED_APPS:
                errors.append(f'Missing INSTALLED_APPS entry: {app}')

        allowed = set(h.strip() for h in settings.ALLOWED_HOSTS if h.strip())
        for host in (
            'booking.revnext.in', 'networks.revnext.in', 'tours.revnext.in',
            'hotels.revnext.in', 'channel-manager.revnext.in',
        ):
            if host not in allowed and '*' not in allowed:
                errors.append(f'ALLOWED_HOSTS missing {host}')

        csrf = set(settings.CSRF_TRUSTED_ORIGINS or [])
        for host in ('booking.revnext.in', 'networks.revnext.in', 'tours.revnext.in', 'hotels.revnext.in'):
            origin = f'https://{host}'
            if origin not in csrf:
                warnings.append(f'CSRF_TRUSTED_ORIGINS missing {origin}')

        try:
            connection.ensure_connection()
        except Exception as exc:
            errors.append(f'Database unreachable: {exc}')
        else:
            from django.db.migrations.executor import MigrationExecutor
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            if plan:
                pending = [f'{m.app_label}.{m.name}' for m, _ in plan]
                errors.append(f'Unapplied migrations: {", ".join(pending)}')

            from products.models import Product
            required = {'booking', 'networks', 'channel_manager', 'tours', 'aggregator'}
            present = set(Product.objects.filter(is_active=True).values_list('code', flat=True))
            missing = required - present
            if missing:
                warnings.append(
                    f'Products not seeded: {", ".join(sorted(missing))} '
                    f'(run: python manage.py seed_products)'
                )

        if settings.DEBUG:
            warnings.append('DEBUG=True — set DEBUG=False for production')
        if 'insecure' in (settings.SECRET_KEY or '').lower():
            warnings.append('SECRET_KEY looks insecure')

        self.stdout.write(self.style.MIGRATE_HEADING('Deploy readiness'))
        self.stdout.write(f'  ALLOWED_HOSTS ({len(allowed)})')
        self.stdout.write(f'  Production hosts expected: {len(PRODUCTION_HOSTS)}')
        self.stdout.write(f'  Nginx app hosts: {", ".join(NGINX_APP_HOSTS)}')
        self.stdout.write(f'  OIDC_ENABLED={getattr(settings, "OIDC_ENABLED", False)}')
        self.stdout.write(f'  OPENBAO_ENABLED={getattr(settings, "OPENBAO_ENABLED", False)}')

        for w in warnings:
            self.stdout.write(self.style.WARNING(f'  WARN: {w}'))
        for e in errors:
            self.stdout.write(self.style.ERROR(f'  FAIL: {e}'))

        if errors:
            self.stdout.write(self.style.ERROR('NOT READY — fix FAIL items before deploy'))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('READY — safe to deploy (review WARN items)'))
