#!/bin/bash
# Deploy Channel Manager to Contabo VPS (same host as Happynails / SuratBazaar / Packmold)
# Only touches channel_manager_* containers and channel-manager images.
# App port: 127.0.0.1:8001 → host nginx site "channel-manager"
#
# NEVER touch OpenBao / secrets stack:
#   ~/revnext-secrets, revnext_secrets_*, nginx site "secrets", port 8200
# Deploy secrets via deploy/infra/deploy-secrets.sh or workflow deploy-secrets.yml only.

set -e

IMAGE_DIR="${1:?Usage: deploy.sh <image-dir>}"
DEPLOY_DIR="${DEPLOY_DIR:-/home/$(whoami)/channel-manager}"
BACKUP_DIR="${BACKUP_DIR:-/home/$(whoami)/backups/channel-manager}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if [ "$(whoami)" != "deploy" ] && [ "$(whoami)" != "root" ]; then
  print_warning "Not running as deploy user, continuing anyway..."
fi

if ! command -v docker &>/dev/null; then
  print_error "Docker is not installed!"
  exit 1
fi

if command -v docker-compose &>/dev/null; then
  DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &>/dev/null; then
  DOCKER_COMPOSE_CMD="docker compose"
else
  print_error "Docker Compose not found."
  exit 1
fi

if ! docker ps &>/dev/null; then
  print_error "Cannot run Docker. Ensure Docker is running and user is in docker group."
  exit 1
fi

REQUIRED_HOSTS="revnext.in,www.revnext.in,channel-manager.revnext.in,booking.revnext.in,networks.revnext.in,pms.revnext.in,pos.revnext.in,cms.revnext.in,hotels.revnext.in,tours.revnext.in,secrets.revnext.in,auth.revnext.in,localhost,127.0.0.1"
REQUIRED_CSRF="https://revnext.in,https://www.revnext.in,https://channel-manager.revnext.in,https://booking.revnext.in,https://networks.revnext.in,https://pms.revnext.in,https://pos.revnext.in,https://cms.revnext.in,https://hotels.revnext.in,https://tours.revnext.in,https://secrets.revnext.in,https://auth.revnext.in"

ensure_env_hosts() {
  local envfile="$1"
  [ -f "$envfile" ] || return
  if grep -q '^ALLOWED_HOSTS=' "$envfile"; then
    local current merged
    current=$(grep '^ALLOWED_HOSTS=' "$envfile" | head -1 | cut -d= -f2-)
    merged="$current"
    IFS=',' read -ra PARTS <<< "$REQUIRED_HOSTS"
    for h in "${PARTS[@]}"; do
      case ",$merged," in
        *",$h,"*) ;;
        *) merged="${merged},${h}" ;;
      esac
    done
    merged=$(echo "$merged" | sed 's/^,//')
    if command -v python3 >/dev/null 2>&1; then
      python3 - "$envfile" "$merged" <<'PY'
import sys
path, hosts = sys.argv[1], sys.argv[2]
lines = open(path).read().splitlines()
out, replaced = [], False
for line in lines:
    if line.startswith('ALLOWED_HOSTS=') and not replaced:
        out.append(f'ALLOWED_HOSTS={hosts}')
        replaced = True
    else:
        out.append(line)
if not replaced:
    out.append(f'ALLOWED_HOSTS={hosts}')
open(path, 'w').write('\n'.join(out) + '\n')
PY
    fi
  else
    echo "ALLOWED_HOSTS=$REQUIRED_HOSTS" >> "$envfile"
  fi
  if ! grep -q '^CSRF_TRUSTED_ORIGINS=' "$envfile"; then
    echo "CSRF_TRUSTED_ORIGINS=$REQUIRED_CSRF" >> "$envfile"
  fi
}

print_status "Starting Channel Manager deployment (co-host safe)..."
mkdir -p "$BACKUP_DIR" "$DEPLOY_DIR"/{media,staticfiles,logs,nginx,deploy}

# Backup config (not DB volume — that is a named Docker volume)
if [ -f "$DEPLOY_DIR/.env" ]; then
  print_status "Creating config backup..."
  tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$DEPLOY_DIR" \
    --exclude='media' --exclude='staticfiles' --exclude='logs' . 2>/dev/null || true
fi

# DB dump before recreate
if [ -f "$DEPLOY_DIR/.env" ] && [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
  print_status "Taking DB backup..."
  cd "$DEPLOY_DIR"
  set -a; [ -f .env ] && . ./.env; set +a
  TS=$(date +%Y%m%d_%H%M%S)
  if $DOCKER_COMPOSE_CMD -f docker-compose.yml ps 2>/dev/null | grep -q "channel_manager_db.*Up"; then
    $DOCKER_COMPOSE_CMD -f docker-compose.yml exec -T db \
      pg_dump -U "${DB_USER:-postgres}" "${DB_NAME:-channel_manager}" \
      > "$BACKUP_DIR/db_$TS.sql" 2>/dev/null \
      && print_success "DB backup: db_$TS.sql" \
      || print_warning "DB backup skipped"
  else
    print_warning "DB backup skipped (db container not running)"
  fi
  cd - >/dev/null
fi

# Stop only Channel Manager stack — never revnext_secrets_* / OpenBao
print_status "Stopping Channel Manager containers (leaving OpenBao / secrets stack alone)..."
if [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
  cd "$DEPLOY_DIR"
  $DOCKER_COMPOSE_CMD -f docker-compose.yml down 2>/dev/null || true
  cd - >/dev/null
fi
docker ps -a --filter "name=channel_manager_" --format "{{.ID}}" | xargs -r docker rm -f || true
# Safety note: never docker rm revnext_secrets_* — those belong to ~/revnext-secrets
if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -qE 'revnext_secrets_'; then
  print_status "OpenBao/secrets containers present — left untouched (correct)."
fi

print_status "Pruning old channel-manager images (keep latest)..."
docker images channel-manager --format "{{.ID}}" | tail -n +3 | xargs -r docker rmi -f || true
# Do NOT: docker volume prune / system prune -v (would risk other projects)

# Verify image exists (built by build-channel-manager-on-vps.sh)
if ! docker images channel-manager --format "{{.Repository}}:{{.Tag}}" | grep -q "channel-manager:latest"; then
  print_error "channel-manager:latest not found. Build step must run first."
  exit 1
fi
docker tag channel-manager:latest channel-manager:prod 2>/dev/null || true

# Landing / marketing assets (compose mounts ./static over the image — keep host in sync)
if [ -d "$IMAGE_DIR/app/static" ]; then
  print_status "Syncing static/ from build (landing CSS must not go stale)..."
  mkdir -p "$DEPLOY_DIR/static"
  rsync -a --delete "$IMAGE_DIR/app/static/" "$DEPLOY_DIR/static/"
fi

# Compose
if [ -f "$IMAGE_DIR/docker-compose.prod.yml" ]; then
  cp "$IMAGE_DIR/docker-compose.prod.yml" "$DEPLOY_DIR/docker-compose.yml"
fi

# Optional local reference scripts (OpenBao infra lives in ~/revnext-secrets, not here)
if [ -d "$IMAGE_DIR/deploy" ]; then
  mkdir -p "$DEPLOY_DIR/deploy"
  cp -R "$IMAGE_DIR/deploy/." "$DEPLOY_DIR/deploy/" 2>/dev/null || true
fi

# .env — bootstrap OPENBAO_* (+ DB_* for postgres container). App secrets come from OpenBao.
if [ ! -f "$DEPLOY_DIR/.env" ]; then
  if [ -f "$IMAGE_DIR/env.example" ]; then
    cp "$IMAGE_DIR/env.example" "$DEPLOY_DIR/.env"
    print_warning "Created .env from env.example — set OPENBAO_* AppRole and DB_PASSWORD for postgres."
  else
    print_error "No .env or env.example. Create $DEPLOY_DIR/.env manually."
    exit 1
  fi
fi
ensure_env_hosts "$DEPLOY_DIR/.env"

OPENBAO_ON=0
grep -qE '^[[:space:]]*OPENBAO_ENABLED=(1|true|yes)' "$DEPLOY_DIR/.env" 2>/dev/null && OPENBAO_ON=1

if ! grep -qE '^DB_PASSWORD=.' "$DEPLOY_DIR/.env"; then
  print_error "DB_PASSWORD must be set in $DEPLOY_DIR/.env (required by Postgres container at compose up)."
  exit 1
fi
if [ "$OPENBAO_ON" != 1 ] && ! grep -qE '^SECRET_KEY=.' "$DEPLOY_DIR/.env"; then
  print_error "SECRET_KEY must be set in $DEPLOY_DIR/.env (or enable OPENBAO_ENABLED and store it in OpenBao)."
  exit 1
fi
if [ "$OPENBAO_ON" = 1 ]; then
  print_status "OPENBAO_ENABLED — Django will load app secrets from OpenBao (secrets.revnext.in / :8200)."
  if ! grep -qE '^OPENBAO_ADDR=.' "$DEPLOY_DIR/.env"; then
    echo "OPENBAO_ADDR=http://172.17.0.1:8200" >> "$DEPLOY_DIR/.env"
    print_warning "Added default OPENBAO_ADDR=http://172.17.0.1:8200"
  fi
fi

# Nginx: product hosts only (never rewrite sites-available/secrets)
NGINX_SRC=""
for candidate in \
  "$IMAGE_DIR/nginx-config.https.conf" \
  "$IMAGE_DIR/nginx.conf" \
  "$IMAGE_DIR/nginx-config.conf"; do
  [ -f "$candidate" ] && NGINX_SRC="$candidate" && break
done
_LE="/etc/letsencrypt/live/channel-manager.revnext.in"
if [ -f "$IMAGE_DIR/nginx-config.https.conf" ]; then
  if [ -r "$_LE/fullchain.pem" ] 2>/dev/null || [ -r "$_LE/README" ] 2>/dev/null; then
    NGINX_SRC="$IMAGE_DIR/nginx-config.https.conf"
    print_status "Using nginx HTTPS template (Let's Encrypt readable)."
  elif grep -qE '^[[:space:]]*CHANNEL_MANAGER_NGINX_TLS=(1|true|yes)' "$DEPLOY_DIR/.env" 2>/dev/null; then
    NGINX_SRC="$IMAGE_DIR/nginx-config.https.conf"
    print_status "Using nginx HTTPS template (CHANNEL_MANAGER_NGINX_TLS in .env)."
  elif [ -f "$IMAGE_DIR/nginx-config.conf" ]; then
    NGINX_SRC="$IMAGE_DIR/nginx-config.conf"
    print_warning "Using HTTP-only nginx. After certbot, set CHANNEL_MANAGER_NGINX_TLS=1 and redeploy."
  fi
fi
if [ -n "$NGINX_SRC" ]; then
  sed "s|/home/root/channel-manager|$DEPLOY_DIR|g; s|/home/deploy/channel-manager|$DEPLOY_DIR|g" \
    "$NGINX_SRC" > "$DEPLOY_DIR/nginx/channel-manager.conf"
fi

chmod 755 "$DEPLOY_DIR/media" "$DEPLOY_DIR/staticfiles" 2>/dev/null || true
chmod 777 "$DEPLOY_DIR/logs" 2>/dev/null || true

# Start
print_status "Starting containers..."
cd "$DEPLOY_DIR"
$DOCKER_COMPOSE_CMD -f docker-compose.yml up -d

# Ensure independent OpenBao is reachable via Docker DNS alias `openbao`
# (stack lives in ~/revnext-secrets; CM compose does not own that container)
print_status "Linking OpenBao network alias (if secrets stack is running)..."
CM_NET="$($DOCKER_COMPOSE_CMD -f docker-compose.yml ps -q web 2>/dev/null | xargs -r docker inspect --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}{{end}}' 2>/dev/null | head -1)"
if [ -z "$CM_NET" ]; then
  CM_NET="$(docker network ls --format '{{.Name}}' | grep -E 'channel-manager.*network|channel-manager_default' | head -1 || true)"
fi
if [ -n "$CM_NET" ] && docker inspect revnext_secrets_openbao >/dev/null 2>&1; then
  docker network connect --alias openbao "$CM_NET" revnext_secrets_openbao 2>/dev/null \
    || print_status "OpenBao already on $CM_NET (or connect skipped)"
  # Prefer in-network alias over docker-bridge IP when AppRole .env uses openbao hostname
  if grep -qE '^OPENBAO_ADDR=http://172\.17\.0\.1:8200' "$DEPLOY_DIR/.env" 2>/dev/null; then
    sed -i 's|^OPENBAO_ADDR=http://172\.17\.0\.1:8200|OPENBAO_ADDR=http://openbao:8200|' "$DEPLOY_DIR/.env" || true
  fi
else
  print_warning "OpenBao container revnext_secrets_openbao not linked — ensure ~/revnext-secrets is up"
fi

print_status "Waiting for services..."
sleep 20

print_status "Running migrations..."
MIGRATE_OK=0
for i in 1 2 3 4 5; do
  if $DOCKER_COMPOSE_CMD -f docker-compose.yml exec -T web \
    python manage.py migrate --noinput 2>&1; then
    print_success "Migrations applied"
    MIGRATE_OK=1
    break
  fi
  print_warning "Migration attempt $i failed, retrying in 5s..."
  sleep 5
done
if [ "$MIGRATE_OK" != 1 ]; then
  print_error "Migrations failed — check: $DOCKER_COMPOSE_CMD -f $DEPLOY_DIR/docker-compose.yml logs web"
  exit 1
fi

print_status "Seeding product catalog..."
$DOCKER_COMPOSE_CMD -f docker-compose.yml exec -T web \
  python manage.py seed_products || print_warning "seed_products failed"

print_status "Collecting static files..."
$DOCKER_COMPOSE_CMD -f docker-compose.yml exec -T --user root web \
  sh -c "mkdir -p /app/staticfiles && chmod -R 777 /app/staticfiles" 2>/dev/null || true
$DOCKER_COMPOSE_CMD -f docker-compose.yml exec -T web \
  python manage.py collectstatic --noinput || print_warning "collectstatic failed"

# Nginx (passwordless sudo — same pattern as Happynails)
print_status "Updating Nginx site channel-manager..."
if [ -f "$DEPLOY_DIR/nginx/channel-manager.conf" ] && command -v nginx &>/dev/null; then
  if sudo -n mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled 2>/dev/null \
    && sudo -n cp "$DEPLOY_DIR/nginx/channel-manager.conf" /etc/nginx/sites-available/channel-manager 2>/dev/null \
    && sudo -n ln -sf /etc/nginx/sites-available/channel-manager /etc/nginx/sites-enabled/channel-manager 2>/dev/null \
    && sudo -n nginx -t 2>/dev/null \
    && (sudo -n systemctl reload nginx 2>/dev/null || sudo -n service nginx reload 2>/dev/null); then
    print_success "Nginx updated"
  else
    print_warning "Nginx update skipped (needs passwordless sudo for deploy)."
    print_warning "  sudo cp $DEPLOY_DIR/nginx/channel-manager.conf /etc/nginx/sites-available/channel-manager"
    print_warning "  sudo ln -sf /etc/nginx/sites-available/channel-manager /etc/nginx/sites-enabled/channel-manager"
    print_warning "  sudo nginx -t && sudo systemctl reload nginx"
  fi
fi

print_status "Service status..."
$DOCKER_COMPOSE_CMD -f docker-compose.yml ps

if ! $DOCKER_COMPOSE_CMD -f docker-compose.yml ps | grep -q "channel_manager_web.*Up"; then
  print_error "Web container is not running!"
  $DOCKER_COMPOSE_CMD -f docker-compose.yml logs web --tail=50 || true
  exit 1
fi

print_status "Health check on :8001..."
sleep 5
if curl -fsS -H "Host: channel-manager.revnext.in" http://127.0.0.1:8001/health/; then
  print_success "Health check passed"
else
  print_warning "Health check failed — see logs"
  $DOCKER_COMPOSE_CMD -f docker-compose.yml logs web --tail=30 || true
fi

$DOCKER_COMPOSE_CMD -f docker-compose.yml exec -T web \
  python manage.py deploy_ready || print_warning "deploy_ready reported issues"

ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | tail -n +6 | xargs -r rm -f || true
docker builder prune -f 2>/dev/null || true

print_success "Channel Manager deployment completed."
print_status "Hosts: channel-manager · pms · pos · cms · booking · hotels · networks · tours · apex"
print_status "Upstream: 127.0.0.1:8001  |  Logs: cd $DEPLOY_DIR && $DOCKER_COMPOSE_CMD logs -f"
print_status "OpenBao (independent): ~/revnext-secrets — deploy via .github/workflows/deploy-secrets.yml"
print_status "TLS products: certbot --nginx -d channel-manager.revnext.in -d booking.revnext.in -d networks.revnext.in -d pms.revnext.in -d pos.revnext.in -d hotels.revnext.in -d tours.revnext.in -d revnext.in -d www.revnext.in"
print_status "cms.revnext.in + hotel sites → VPS 84.247.183.69 (RevNextCMS), not this stack"
