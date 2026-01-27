#!/bin/bash
# Quick fix script for VPS deployment issues
# Run this on the VPS

set -e

DEPLOY_DIR="${1:-/home/root/channel-manager}"

echo "=== Fixing Channel Manager Deployment ==="
cd "$DEPLOY_DIR"

# 1. Check and create docker-compose.yml
echo "1. Checking docker-compose configuration..."
if [ -f docker-compose.prod.yml ] && [ ! -f docker-compose.yml ]; then
    echo "   Creating docker-compose.yml from docker-compose.prod.yml..."
    cp docker-compose.prod.yml docker-compose.yml
    echo "   ✅ Created docker-compose.yml"
elif [ ! -f docker-compose.yml ] && [ ! -f docker-compose.prod.yml ]; then
    echo "   ❌ No docker-compose file found!"
    echo "   Please ensure docker-compose.prod.yml is deployed"
    exit 1
else
    echo "   ✅ docker-compose.yml exists"
fi

# 2. Check .env file
echo ""
echo "2. Checking .env file..."
if [ ! -f .env ]; then
    echo "   ⚠️  .env file not found, creating minimal one..."
    if command -v python3 >/dev/null 2>&1; then
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(25))")
    else
        SECRET_KEY="django-insecure-$(date +%s | sha256sum | base64 | head -c 32)"
        DB_PASSWORD="changeme$(date +%s | sha256sum | base64 | head -c 20)"
    fi
    
    cat > .env << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=channel-manager.revnext.in,5.189.180.67,localhost,127.0.0.1
DB_NAME=channel_manager
DB_USER=postgres
DB_PASSWORD=$DB_PASSWORD
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
ENVIRONMENT=production
EOF
    echo "   ✅ Created .env file"
    echo "   ⚠️  Please review and update DB_PASSWORD if needed"
else
    echo "   ✅ .env file exists"
fi

# 3. Check Docker image
echo ""
echo "3. Checking Docker image..."
if docker images | grep -q channel-manager; then
    echo "   ✅ channel-manager image exists"
    docker images | grep channel-manager
else
    echo "   ❌ channel-manager image not found!"
    if [ -f /tmp/deploy/channel-manager-image.tar.gz ]; then
        echo "   Loading image from /tmp/deploy..."
        docker load -i /tmp/deploy/channel-manager-image.tar.gz
    else
        echo "   ⚠️  Image file not found. Waiting for next deployment..."
    fi
fi

# 4. Stop any existing containers
echo ""
echo "4. Stopping existing containers..."
docker compose down || true

# 5. Start services
echo ""
echo "5. Starting services..."
if docker compose up -d; then
    echo "   ✅ Services started"
else
    echo "   ❌ Failed to start services"
    echo "   Logs:"
    docker compose logs --tail=30 || true
    exit 1
fi

# 6. Wait and check status
echo ""
echo "6. Waiting for services to be ready..."
sleep 10
docker compose ps

# 7. Check port 8001
echo ""
echo "7. Checking port 8001..."
sleep 5
if ss -tlnp 2>/dev/null | grep -q 8001 || netstat -tlnp 2>/dev/null | grep -q 8001; then
    echo "   ✅ Port 8001 is listening"
else
    echo "   ❌ Port 8001 is not listening"
    echo "   Container logs:"
    docker compose logs web --tail=30 || true
fi

# 8. Health check
echo ""
echo "8. Testing health endpoint..."
if curl -f http://localhost:8001/health/ 2>/dev/null; then
    echo "   ✅ Health check passed!"
else
    echo "   ❌ Health check failed"
    echo "   Web container logs:"
    docker compose logs web --tail=30 || true
fi

echo ""
echo "=== Fix Complete ==="

