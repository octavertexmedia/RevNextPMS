#!/usr/bin/env bash
# Docker entrypoint: optionally migrate/seed, then exec CMD
set -e

wait_for_db() {
  echo "[entrypoint] Waiting for database..."
  python - <<'PY'
import os, time, sys
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'channel_manager.settings')
django.setup()
from django.db import connection
for i in range(60):
    try:
        connection.ensure_connection()
        print('[entrypoint] Database ready')
        sys.exit(0)
    except Exception as exc:
        print(f'[entrypoint] DB not ready ({i+1}/60): {exc}')
        time.sleep(2)
print('[entrypoint] Database unavailable', file=sys.stderr)
sys.exit(1)
PY
}

wait_for_db

if [ "${SKIP_MIGRATE:-false}" != "true" ]; then
  echo "[entrypoint] Applying migrations..."
  python manage.py migrate --noinput
else
  echo "[entrypoint] SKIP_MIGRATE=true — skipping migrations"
fi

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "[entrypoint] Seeding products catalog..."
  python manage.py seed_products || echo "[entrypoint] WARN: seed_products failed"
  if [ "${SEED_RBAC_ON_START:-false}" = "true" ]; then
    python manage.py seed_rbac || echo "[entrypoint] WARN: seed_rbac failed"
  fi
fi

if [ "${COLLECTSTATIC_ON_START:-false}" = "true" ]; then
  echo "[entrypoint] Collecting static files..."
  python manage.py collectstatic --noinput || true
fi

echo "[entrypoint] Starting: $*"
exec "$@"
