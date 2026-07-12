#!/bin/bash
set -e

# Deployment script for Channel Manager
# Usage: ./deploy.sh /tmp/deploy

IMAGE_DIR="${1:-/tmp/deploy}"
DEPLOY_DIR="${DEPLOY_DIR:-/home/$(whoami)/channel-manager}"
BACKUP_DIR="${BACKUP_DIR:-/home/$(whoami)/backups}"

echo "[INFO] Starting deployment..."
echo "[INFO] Image directory: $IMAGE_DIR"
echo "[INFO] Deploy directory: $DEPLOY_DIR"
echo "[INFO] Backup directory: $BACKUP_DIR"

# Ensure directories exist
mkdir -p "$DEPLOY_DIR"
mkdir -p "$BACKUP_DIR"

# Create required directories with proper permissions
echo "[INFO] Creating required directories..."
mkdir -p "$DEPLOY_DIR/logs" "$DEPLOY_DIR/media" "$DEPLOY_DIR/staticfiles"
chmod 777 "$DEPLOY_DIR/logs" 2>/dev/null || true
chmod 755 "$DEPLOY_DIR/media" "$DEPLOY_DIR/staticfiles" 2>/dev/null || true

# Load Docker image
if [ -f "$IMAGE_DIR/channel-manager-image.tar.gz" ]; then
    echo "[INFO] Loading Docker image..."
    if docker load -i "$IMAGE_DIR/channel-manager-image.tar.gz"; then
        echo "[INFO] Docker image loaded successfully"
        docker images | grep channel-manager || echo "[WARN] Image not found after load"
    else
        echo "[WARN] Image load failed, checking if image already exists..."
        if docker images | grep -q channel-manager; then
            echo "[INFO] Image already exists, continuing..."
        else
            echo "[ERROR] Image load failed and image doesn't exist!"
            exit 1
        fi
    fi
else
    echo "[WARN] Docker image file not found: $IMAGE_DIR/channel-manager-image.tar.gz"
    echo "[INFO] Checking if image already exists..."
    if docker images | grep -q channel-manager; then
        echo "[INFO] Image already exists, continuing..."
    else
        echo "[ERROR] No image file and image doesn't exist!"
        exit 1
    fi
fi

# Copy docker-compose + OpenBao deploy assets
if [ -f "$IMAGE_DIR/docker-compose.prod.yml" ]; then
    echo "[INFO] Copying docker-compose file..."
    cp "$IMAGE_DIR/docker-compose.prod.yml" "$DEPLOY_DIR/docker-compose.yml"
fi
if [ -d "$IMAGE_DIR/deploy" ]; then
    echo "[INFO] Copying deploy/ assets (OpenBao scripts)..."
    mkdir -p "$DEPLOY_DIR/deploy"
    cp -R "$IMAGE_DIR/deploy/." "$DEPLOY_DIR/deploy/"
fi

# Required production hosts (booking + networks + suite)
REQUIRED_HOSTS="revnext.in,www.revnext.in,channel-manager.revnext.in,booking.revnext.in,networks.revnext.in,pms.revnext.in,pos.revnext.in,cms.revnext.in,hotels.revnext.in,tours.revnext.in,secrets.revnext.in,auth.revnext.in,localhost,127.0.0.1"

ensure_env_hosts() {
    local envfile="$1"
    if [ ! -f "$envfile" ]; then
        return
    fi
    if grep -q '^ALLOWED_HOSTS=' "$envfile"; then
        # Merge any missing required hosts into existing ALLOWED_HOSTS
        local current
        current=$(grep '^ALLOWED_HOSTS=' "$envfile" | head -1 | cut -d= -f2-)
        local merged="$current"
        IFS=',' read -ra PARTS <<< "$REQUIRED_HOSTS"
        for h in "${PARTS[@]}"; do
            case ",$merged," in
                *",$h,"*) ;;
                *) merged="${merged},${h}" ;;
            esac
        done
        # Normalize leading comma
        merged=$(echo "$merged" | sed 's/^,//')
        if command -v python3 >/dev/null 2>&1; then
            python3 - "$envfile" "$merged" <<'PY'
import sys
path, hosts = sys.argv[1], sys.argv[2]
lines = open(path).read().splitlines()
out = []
replaced = False
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
        else
            echo "[WARN] Could not merge ALLOWED_HOSTS (no python3)"
        fi
        echo "[INFO] Ensured product hosts in ALLOWED_HOSTS"
    else
        echo "ALLOWED_HOSTS=$REQUIRED_HOSTS" >> "$envfile"
    fi
    # Ensure CSRF origins for product hosts if missing
    if ! grep -q '^CSRF_TRUSTED_ORIGINS=' "$envfile"; then
        echo "CSRF_TRUSTED_ORIGINS=https://revnext.in,https://www.revnext.in,https://channel-manager.revnext.in,https://booking.revnext.in,https://networks.revnext.in,https://pms.revnext.in,https://pos.revnext.in,https://cms.revnext.in,https://hotels.revnext.in,https://tours.revnext.in,https://secrets.revnext.in,https://auth.revnext.in" >> "$envfile"
        echo "[INFO] Added CSRF_TRUSTED_ORIGINS"
    fi
}

# Copy .env file if it doesn't exist
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    if [ -f "$IMAGE_DIR/.env.example" ]; then
        echo "[INFO] Creating .env file from example..."
        cp "$IMAGE_DIR/.env.example" "$DEPLOY_DIR/.env"
        echo "[WARN] Please update .env file with your configuration!"
        echo "[WARN] At minimum, update SECRET_KEY and DB_PASSWORD"
    else
        echo "[WARN] .env file not found and .env.example not available"
        echo "[INFO] Creating minimal .env file..."
        # Generate secure random values
        if command -v openssl >/dev/null 2>&1; then
            SECRET_KEY=$(openssl rand -hex 32)
            DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        elif command -v python3 >/dev/null 2>&1; then
            SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
            DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(25))")
        else
            SECRET_KEY="django-insecure-$(date +%s | sha256sum | base64 | head -c 32)"
            DB_PASSWORD="changeme$(date +%s | sha256sum | base64 | head -c 20)"
            echo "[WARN] Using less secure fallback password generation"
        fi
        
        cat > "$DEPLOY_DIR/.env" << EOF
# Django Configuration
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$REQUIRED_HOSTS
CSRF_TRUSTED_ORIGINS=https://revnext.in,https://www.revnext.in,https://channel-manager.revnext.in,https://booking.revnext.in,https://networks.revnext.in,https://pms.revnext.in,https://pos.revnext.in,https://cms.revnext.in,https://hotels.revnext.in,https://tours.revnext.in,https://secrets.revnext.in,https://auth.revnext.in
SITE_URL=https://channel-manager.revnext.in
SECURE_SSL_REDIRECT=True

# Database Configuration
DB_NAME=channel_manager
DB_USER=postgres
DB_PASSWORD=$DB_PASSWORD
DB_HOST=db
DB_PORT=5432

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# OpenBao (docker network)
OPENBAO_ENABLED=false
OPENBAO_ADDR=http://openbao:8200
OPENBAO_TOKEN=dev-root-token
OPENBAO_ENVIRONMENT=production
OPENBAO_TLS_VERIFY=false

# OIDC
OIDC_ENABLED=false
OIDC_OP_ISSUER=https://auth.revnext.in

# Environment
ENVIRONMENT=production
SEED_ON_START=true
EOF
        echo "[INFO] Minimal .env file created with auto-generated values"
        echo "[WARN] Please review and update DB_PASSWORD in $DEPLOY_DIR/.env"
    fi
fi

ensure_env_hosts "$DEPLOY_DIR/.env"
# Copy nginx config if provided and nginx is installed
if [ -f "$IMAGE_DIR/nginx.conf" ]; then
    if command -v nginx >/dev/null 2>&1; then
        echo "[INFO] Copying nginx configuration..."
        # Replace deployment directory path in nginx config
        sed "s|/home/root/channel-manager|$DEPLOY_DIR|g" "$IMAGE_DIR/nginx.conf" > /tmp/nginx-channel-manager.conf || cp "$IMAGE_DIR/nginx.conf" /tmp/nginx-channel-manager.conf
        
        # Check if we can write to nginx directory
        if [ -w /etc/nginx/sites-available ] 2>/dev/null; then
            cp /tmp/nginx-channel-manager.conf /etc/nginx/sites-available/channel-manager || echo "[WARN] Nginx config copy failed (no write permission)"
            ln -sf /etc/nginx/sites-available/channel-manager /etc/nginx/sites-enabled/channel-manager 2>/dev/null || echo "[WARN] Nginx symlink failed"
            # Test and reload nginx
            if nginx -t 2>/dev/null; then
                nginx -s reload || systemctl reload nginx || echo "[WARN] Nginx reload failed"
            else
                echo "[WARN] Nginx config test failed, not reloading"
            fi
        elif sudo -n true 2>/dev/null; then
            sudo cp /tmp/nginx-channel-manager.conf /etc/nginx/sites-available/channel-manager || echo "[WARN] Nginx config copy failed"
            sudo ln -sf /etc/nginx/sites-available/channel-manager /etc/nginx/sites-enabled/channel-manager || echo "[WARN] Nginx symlink failed"
            # Test and reload nginx
            if sudo nginx -t 2>/dev/null; then
                sudo nginx -s reload || sudo systemctl reload nginx || echo "[WARN] Nginx reload failed"
            else
                echo "[WARN] Nginx config test failed, not reloading"
            fi
        else
            echo "[INFO] Nginx config found but cannot copy (no sudo access). Copy manually:"
            echo "  sudo cp $IMAGE_DIR/nginx.conf /etc/nginx/sites-available/channel-manager"
            echo "  sudo ln -s /etc/nginx/sites-available/channel-manager /etc/nginx/sites-enabled/"
            echo "  sudo nginx -t && sudo nginx -s reload"
        fi
        rm -f /tmp/nginx-channel-manager.conf
    else
        echo "[INFO] Nginx not installed, skipping nginx config"
    fi
fi

# Navigate to deploy directory
cd "$DEPLOY_DIR"

# Pull latest images (if using registry)
echo "[INFO] Pulling latest images..."
docker compose pull || echo "[WARN] Image pull failed, using local images"

# Check if .env exists before running commands that need it
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    echo "[ERROR] .env file is required but not found!"
    echo "[ERROR] Please create .env file manually or ensure .env.example is available"
    exit 1
fi

# Verify .env file has required variables
echo "[INFO] Verifying .env file..."
if ! grep -q "SECRET_KEY" "$DEPLOY_DIR/.env"; then
    echo "[WARN] SECRET_KEY not found in .env file"
fi
if ! grep -q "DB_PASSWORD" "$DEPLOY_DIR/.env"; then
    echo "[WARN] DB_PASSWORD not found in .env file"
fi

# Run migrations + seed product catalog (also runs via web entrypoint)
echo "[INFO] Running database migrations..."
docker compose run --rm -e SKIP_MIGRATE=false -e SEED_ON_START=true web \
  python manage.py migrate --noinput || {
    echo "[WARN] Migrations failed - this is normal on first deployment if database doesn't exist yet"
    echo "[INFO] Database will be initialized when services start"
}

echo "[INFO] Seeding product catalog (booking + networks + suite)..."
docker compose run --rm -e SKIP_MIGRATE=true -e SEED_ON_START=false web \
  python manage.py seed_products || echo "[WARN] seed_products failed"

echo "[INFO] Seeding RBAC catalog (optional)..."
docker compose run --rm -e SKIP_MIGRATE=true -e SEED_ON_START=false web \
  python manage.py seed_rbac || echo "[WARN] seed_rbac failed (ok if first boot)"

# Collect static files
echo "[INFO] Collecting static files..."
docker compose run --rm -e SKIP_MIGRATE=true -e SEED_ON_START=false web \
  python manage.py collectstatic --noinput || echo "[WARN] Static files collection failed"

# Start/restart services
echo "[INFO] Starting services..."
docker compose down || true

echo "[INFO] Starting services with docker compose..."
if docker compose up -d; then
    echo "[INFO] Services started, waiting for them to be ready..."
else
    echo "[ERROR] Failed to start services"
    echo "[INFO] Docker compose logs:"
    docker compose logs --tail=50 || true
    echo "[INFO] Check logs with: docker compose logs"
    exit 1
fi

# Wait for services to be healthy
echo "[INFO] Waiting for services to be healthy..."
sleep 15

# Check service status
echo "[INFO] Checking service status..."
docker compose ps

# Check if web container is running
if ! docker compose ps | grep -q "channel_manager_web.*Up"; then
    echo "[ERROR] Web container is not running!"
    echo "[INFO] Web container logs:"
    docker compose logs web --tail=50 || true
    echo "[INFO] All container logs:"
    docker compose logs --tail=50 || true
    exit 1
fi

# Check if port 8001 is listening
echo "[INFO] Checking if port 8001 is listening..."
if command -v netstat >/dev/null 2>&1; then
    netstat -tlnp | grep 8001 || echo "[WARN] Port 8001 not found in netstat"
elif command -v ss >/dev/null 2>&1; then
    ss -tlnp | grep 8001 || echo "[WARN] Port 8001 not found in ss"
fi

# Run health check
echo "[INFO] Running health check..."
sleep 5
if curl -f http://localhost:8001/health/; then
    echo "[INFO] Health check passed!"
else
    echo "[WARN] Health check failed"
    echo "[INFO] Web container logs:"
    docker compose logs web --tail=30 || true
    echo "[INFO] Trying to check container status..."
    docker compose ps || true
fi

echo "[INFO] Running deploy_ready checks..."
docker compose exec -T web python manage.py deploy_ready || echo "[WARN] deploy_ready reported issues"

echo "[INFO] Deployment completed!"
echo "[INFO] Product hosts: booking.revnext.in · networks.revnext.in · channel-manager.revnext.in · …"
echo "[INFO] Services are running. Check logs with: docker compose logs -f"
echo "[INFO] Expand TLS SANs if needed:"
echo "  certbot --nginx -d channel-manager.revnext.in -d booking.revnext.in -d networks.revnext.in -d pms.revnext.in -d pos.revnext.in -d cms.revnext.in -d hotels.revnext.in -d tours.revnext.in -d revnext.in -d www.revnext.in"

