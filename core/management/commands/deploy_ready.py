"""
Validate production deployment readiness (hosts, apps, migrations, catalog, OpenBao).
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
        for host in NGINX_APP_HOSTS:
            if host not in allowed and '*' not in allowed:
                errors.append(f'ALLOWED_HOSTS missing {host}')

        csrf = set(settings.CSRF_TRUSTED_ORIGINS or [])
        for host in NGINX_APP_HOSTS:
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
            required = {
                'booking', 'networks', 'channel_manager', 'tours', 'aggregator',
                'pms', 'pos', 'cms',
            }
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

        openbao_enabled = getattr(settings, 'OPENBAO_ENABLED', False)
        openbao_required = getattr(settings, 'OPENBAO_REQUIRED', False)
        self.stdout.write(self.style.MIGRATE_HEADING('Deploy readiness'))
        self.stdout.write(f'  ALLOWED_HOSTS ({len(allowed)})')
        self.stdout.write(f'  Production hosts expected: {len(PRODUCTION_HOSTS)}')
        self.stdout.write(f'  Nginx app hosts: {", ".join(NGINX_APP_HOSTS)}')
        self.stdout.write(f'  OIDC_ENABLED={getattr(settings, "OIDC_ENABLED", False)}')
        self.stdout.write(f'  OPENBAO_ENABLED={openbao_enabled}')
        self.stdout.write(f'  OPENBAO_REQUIRED={openbao_required}')
        self.stdout.write(f'  OPENBAO_ADDR={getattr(settings, "OPENBAO_ADDR", "")}')

        # OpenBao reachability (secrets.revnext.in / host :8200 — independent stack)
        if openbao_enabled:
            try:
                from channel_manager.openbao.loader import secret_status, apply_openbao_secrets
                from channel_manager.openbao.client import OpenBaoClient

                st = secret_status()
                if not st.get('loaded') and not st.get('error'):
                    st = apply_openbao_secrets(force=True)

                # Confirm API auth works against independent OpenBao
                try:
                    client = OpenBaoClient()
                    authenticated = client.client.is_authenticated()
                except Exception as auth_exc:
                    authenticated = False
                    if not st.get('error'):
                        st['error'] = str(auth_exc)

                if st.get('error') and not st.get('loaded'):
                    msg = f'OpenBao error: {st["error"]}'
                    if openbao_required:
                        errors.append(msg)
                    else:
                        warnings.append(msg)
                elif not st.get('loaded') and not authenticated:
                    msg = (
                        'OpenBao enabled but secrets not loaded — '
                        'is ~/revnext-secrets running on :8200?'
                    )
                    if openbao_required:
                        errors.append(msg)
                    else:
                        warnings.append(msg)
                else:
                    self.stdout.write(
                        f'  OpenBao OK — {len(st.get("keys") or [])} keys '
                        f'from {st.get("path") or "(status only)"}'
                    )
            except Exception as exc:
                msg = f'OpenBao check failed: {exc}'
                if openbao_required:
                    errors.append(msg)
                else:
                    warnings.append(msg)
        elif openbao_required:
            errors.append('OPENBAO_REQUIRED=true but OPENBAO_ENABLED is false')


        for w in warnings:
            self.stdout.write(self.style.WARNING(f'  WARN: {w}'))
        for e in errors:
            self.stdout.write(self.style.ERROR(f'  FAIL: {e}'))

        if errors:
            self.stdout.write(self.style.ERROR('NOT READY — fix FAIL items before deploy'))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS('READY — safe to deploy (review WARN items)'))
