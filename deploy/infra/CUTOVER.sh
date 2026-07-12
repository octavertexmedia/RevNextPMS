#!/bin/bash
# One-shot cutover: ChannelManager-embedded OpenBao → independent ~/revnext-secrets
# Run as root on Contabo 77.237.234.201:
#   bash /home/deploy/revnext-secrets/CUTOVER.sh
#
# Prereqs:
#   1) DNS A record: secrets.revnext.in → 77.237.234.201 (BigRock)
#   2) Files already staged by deploy user under /home/deploy/revnext-secrets

set -euo pipefail

SECRETS_DIR=/home/deploy/revnext-secrets
CM_DIR=/home/root/channel-manager
OLD_NAME=channel_manager_openbao
NEW_NAME=revnext_secrets_openbao

if [[ $(id -u) -ne 0 ]]; then
  echo "Run as root: sudo bash $0"
  exit 1
fi

if [[ ! -f "$SECRETS_DIR/docker-compose.yml" ]]; then
  echo "Missing $SECRETS_DIR/docker-compose.yml — stage secrets stack first"
  exit 1
fi

echo "==> Export snapshot from running OpenBao (best-effort; -dev may be in-memory)"
mkdir -p "$SECRETS_DIR/export"
if docker exec "$OLD_NAME" bao status -address=http://127.0.0.1:8200 >/dev/null 2>&1; then
  # If a root token is available in CM .env as OPENBAO_TOKEN, export KV
  TOKEN=$(grep -E '^OPENBAO_TOKEN=' "$CM_DIR/.env" 2>/dev/null | cut -d= -f2- || true)
  if [[ -n "${TOKEN:-}" ]]; then
    docker exec -e BAO_TOKEN="$TOKEN" -e BAO_ADDR=http://127.0.0.1:8200 "$OLD_NAME" \
      bao kv get -format=json secret/revnext/channel-manager/production \
      > "$SECRETS_DIR/export/channel-manager-production.json" 2>/dev/null || \
      echo "KV export skipped (path may differ)"
  else
    echo "No OPENBAO_TOKEN in $CM_DIR/.env — skip KV export"
  fi
fi

echo "==> Copy file volume data (if any) into independent data dir"
docker run --rm \
  -v channel-manager_openbao_data:/from:ro \
  -v "$SECRETS_DIR/data":/to \
  alpine:3.20 sh -c 'cp -a /from/. /to/ 2>/dev/null || true; ls -la /to | head'

echo "==> Stop embedded OpenBao (frees :8200)"
docker update --restart=no "$OLD_NAME" || true
docker stop "$OLD_NAME"

echo "==> Start independent OpenBao at $SECRETS_DIR"
cd "$SECRETS_DIR"
# Prefer file-mode image from compose; if data empty, operator must init
docker compose up -d
sleep 5
docker compose ps
curl -fsS http://127.0.0.1:8200/v1/sys/health || echo "OpenBao may need init/unseal"

echo "==> Point ChannelManager app containers at host OpenBao"
# Prod pattern: 172.17.0.1:8200 (not docker DNS name 'openbao')
if grep -q 'OPENBAO_ADDR=http://openbao:8200' "$CM_DIR/.env" 2>/dev/null; then
  sed -i 's|OPENBAO_ADDR=http://openbao:8200|OPENBAO_ADDR=http://172.17.0.1:8200|' "$CM_DIR/.env"
fi
# Soft-disable openbao service in CM compose so next up won't fight the port
if [[ -f "$CM_DIR/docker-compose.yml" ]] && grep -q '^  openbao:' "$CM_DIR/docker-compose.yml"; then
  cp "$CM_DIR/docker-compose.yml" "$CM_DIR/docker-compose.yml.bak.$(date +%s)"
  # Comment service block is fragile — instead rename service out of active use via profiles
  python3 - <<'PY'
from pathlib import Path
p = Path("/home/root/channel-manager/docker-compose.yml")
text = p.read_text()
if "profiles:" not in text.split("openbao:")[1].split("\n  ")[0]:
    text = text.replace(
        "  openbao:\n    image:",
        "  openbao:\n    profiles: [\"legacy-embedded-openbao\"]\n    image:",
        1,
    )
    p.write_text(text)
    print("Pinned openbao service behind profile legacy-embedded-openbao")
else:
    print("openbao already profiled or unexpected format")
PY
fi

echo "==> Recreate CM web/celery with new OPENBAO_ADDR (no openbao dependency)"
cd "$CM_DIR"
docker compose up -d --no-deps web celery celery-beat 2>/dev/null || \
  docker compose up -d web 2>/dev/null || true

echo "==> Install nginx site for secrets.revnext.in (HTTP first)"
install -d -m 755 /var/www/certbot
cp "$SECRETS_DIR/nginx/secrets.conf" /etc/nginx/sites-available/secrets
# Prefer HTTP template until cert exists
if [[ ! -f /etc/letsencrypt/live/secrets.revnext.in/fullchain.pem ]]; then
  # secrets.conf staged may be HTTPS — fall back if missing
  if [[ -f /home/deploy/revnext-secrets/nginx/secrets.http.conf ]]; then
    cp /home/deploy/revnext-secrets/nginx/secrets.http.conf /etc/nginx/sites-available/secrets
  elif [[ -f /tmp/nginx-secrets.http.conf ]]; then
    cp /tmp/nginx-secrets.http.conf /etc/nginx/sites-available/secrets
  fi
fi
ln -sf /etc/nginx/sites-available/secrets /etc/nginx/sites-enabled/secrets
nginx -t && systemctl reload nginx

echo "==> TLS (requires DNS A secrets.revnext.in → this host)"
if getent hosts secrets.revnext.in | grep -q "$(hostname -I | awk '{print $1}')\|77.237.234.201"; then
  certbot --nginx -d secrets.revnext.in --non-interactive --agree-tos -m admin@revnext.in --redirect || \
    echo "certbot failed — run manually after DNS propagates"
  # Swap to HTTPS template after cert
  if [[ -f /etc/letsencrypt/live/secrets.revnext.in/fullchain.pem ]] && [[ -f $SECRETS_DIR/../revnext-secrets ]]; then
    :
  fi
  if [[ -f /home/deploy/revnext-secrets/nginx/secrets.https.conf ]]; then
    cp /home/deploy/revnext-secrets/nginx/secrets.https.conf /etc/nginx/sites-available/secrets
  fi
  # Copy HTTPS conf from repo staging if present next to http
  if [[ -f /home/deploy/revnext-secrets/nginx/secrets.conf ]] && \
     grep -q 'listen 443' /home/deploy/revnext-secrets/nginx/secrets.conf && \
     [[ -f /etc/letsencrypt/live/secrets.revnext.in/fullchain.pem ]]; then
    cp /home/deploy/revnext-secrets/nginx/secrets.conf /etc/nginx/sites-available/secrets
    nginx -t && systemctl reload nginx
  fi
else
  echo "DNS for secrets.revnext.in not pointing here yet — skip certbot"
  echo "After DNS: certbot --nginx -d secrets.revnext.in && re-run HTTPS nginx swap"
fi

echo "==> Health"
curl -fsS http://127.0.0.1:8200/v1/sys/health || true
echo
curl -fsS -k https://secrets.revnext.in/v1/sys/health || curl -fsS http://secrets.revnext.in/v1/sys/health || true
echo
echo "Done. Independent stack: $SECRETS_DIR (container $NEW_NAME)"
echo "If OpenBao is uninitialized: cd $SECRETS_DIR && docker compose exec openbao sh /openbao/scripts/init.sh"
