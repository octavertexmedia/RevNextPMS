#!/bin/bash
# Deploy RevNext OpenBao (secrets.revnext.in) on Contabo — independent of ChannelManager.
# Usage: ./deploy-secrets.sh /tmp/deploy-revnext-secrets
#
# Never run from ChannelManager product deploy. Does not touch channel_manager_* containers.

set -e

IMAGE_DIR="${1:-.}"
DEPLOY_DIR="${DEPLOY_DIR:-/home/$(whoami)/revnext-secrets}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

if ! command -v docker &>/dev/null; then
  print_error "Docker is not installed"
  exit 1
fi

if command -v docker-compose &>/dev/null; then
  DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &>/dev/null; then
  DOCKER_COMPOSE_CMD="docker compose"
else
  print_error "Docker Compose not found"
  exit 1
fi

print_status "Deploying RevNext secrets stack → $DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"/{data,config,scripts,nginx}

# Compose
if [ -f "$IMAGE_DIR/docker-compose.secrets.yml" ]; then
  cp "$IMAGE_DIR/docker-compose.secrets.yml" "$DEPLOY_DIR/docker-compose.yml"
elif [ -f "$IMAGE_DIR/deploy/infra/docker-compose.secrets.yml" ]; then
  cp "$IMAGE_DIR/deploy/infra/docker-compose.secrets.yml" "$DEPLOY_DIR/docker-compose.yml"
else
  print_error "docker-compose.secrets.yml not found in $IMAGE_DIR"
  exit 1
fi

# Config + scripts
if [ -f "$IMAGE_DIR/config.hcl" ]; then
  cp "$IMAGE_DIR/config.hcl" "$DEPLOY_DIR/config/config.hcl"
elif [ -f "$IMAGE_DIR/deploy/infra/config.hcl" ]; then
  cp "$IMAGE_DIR/deploy/infra/config.hcl" "$DEPLOY_DIR/config/config.hcl"
elif [ -f "$IMAGE_DIR/deploy/openbao/config.hcl" ]; then
  cp "$IMAGE_DIR/deploy/openbao/config.hcl" "$DEPLOY_DIR/config/config.hcl"
fi

if [ -f "$IMAGE_DIR/init.sh" ]; then
  cp "$IMAGE_DIR/init.sh" "$DEPLOY_DIR/scripts/init.sh"
elif [ -f "$IMAGE_DIR/deploy/infra/init.sh" ]; then
  cp "$IMAGE_DIR/deploy/infra/init.sh" "$DEPLOY_DIR/scripts/init.sh"
elif [ -f "$IMAGE_DIR/deploy/openbao/init.sh" ]; then
  cp "$IMAGE_DIR/deploy/openbao/init.sh" "$DEPLOY_DIR/scripts/init.sh"
fi
chmod +x "$DEPLOY_DIR/scripts/init.sh" 2>/dev/null || true

# Preserve data volume — never wipe ./data
print_status "Starting OpenBao (preserving $DEPLOY_DIR/data)..."
cd "$DEPLOY_DIR"
$DOCKER_COMPOSE_CMD -f docker-compose.yml up -d
sleep 5
$DOCKER_COMPOSE_CMD -f docker-compose.yml ps

# Nginx
NGINX_SRC=""
_LE="/etc/letsencrypt/live/secrets.revnext.in"
if [ -f "$IMAGE_DIR/nginx-secrets.conf" ] && { [ -r "$_LE/fullchain.pem" ] 2>/dev/null || [ -r "$_LE/README" ] 2>/dev/null; }; then
  NGINX_SRC="$IMAGE_DIR/nginx-secrets.conf"
  print_status "Using HTTPS nginx template for secrets.revnext.in"
elif [ -f "$IMAGE_DIR/nginx-secrets.http.conf" ]; then
  NGINX_SRC="$IMAGE_DIR/nginx-secrets.http.conf"
  print_warning "Using HTTP nginx for secrets — run certbot then redeploy secrets stack"
elif [ -f "$IMAGE_DIR/nginx-secrets.conf" ]; then
  NGINX_SRC="$IMAGE_DIR/nginx-secrets.conf"
fi

if [ -n "$NGINX_SRC" ]; then
  cp "$NGINX_SRC" "$DEPLOY_DIR/nginx/secrets.conf"
  if command -v nginx &>/dev/null; then
    if sudo -n mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled 2>/dev/null \
      && sudo -n cp "$DEPLOY_DIR/nginx/secrets.conf" /etc/nginx/sites-available/secrets 2>/dev/null \
      && sudo -n ln -sf /etc/nginx/sites-available/secrets /etc/nginx/sites-enabled/secrets 2>/dev/null \
      && sudo -n nginx -t 2>/dev/null \
      && (sudo -n systemctl reload nginx 2>/dev/null || sudo -n service nginx reload 2>/dev/null); then
      print_success "Nginx site 'secrets' updated"
    else
      print_warning "Nginx update skipped — run manually:"
      print_warning "  sudo cp $DEPLOY_DIR/nginx/secrets.conf /etc/nginx/sites-available/secrets"
      print_warning "  sudo ln -sf /etc/nginx/sites-available/secrets /etc/nginx/sites-enabled/secrets"
      print_warning "  sudo nginx -t && sudo systemctl reload nginx"
    fi
  fi
fi

print_status "Health: curl -fsS http://127.0.0.1:8200/v1/sys/health || true"
curl -fsS http://127.0.0.1:8200/v1/sys/health 2>/dev/null || print_warning "OpenBao not responding yet (may need init/unseal)"

print_success "Secrets stack deploy complete → $DEPLOY_DIR"
print_status "First-time init: docker compose -f $DEPLOY_DIR/docker-compose.yml exec openbao sh /openbao/scripts/init.sh"
print_status "TLS: sudo certbot --nginx -d secrets.revnext.in"
print_status "ChannelManager .env: OPENBAO_ADDR=http://172.17.0.1:8200 (or https://secrets.revnext.in) + AppRole"
