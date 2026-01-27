#!/bin/bash
# Diagnostic script to check VPS deployment status
# Run this on the VPS: ssh root@5.189.180.67

set -e

DEPLOY_DIR="${1:-/home/root/channel-manager}"

echo "=== Channel Manager VPS Diagnostic ==="
echo ""

# Check deployment directory
echo "1. Checking deployment directory..."
if [ -d "$DEPLOY_DIR" ]; then
    echo "   ✅ Directory exists: $DEPLOY_DIR"
    ls -la "$DEPLOY_DIR" | head -10
else
    echo "   ❌ Directory not found: $DEPLOY_DIR"
    exit 1
fi

# Check .env file
echo ""
echo "2. Checking .env file..."
if [ -f "$DEPLOY_DIR/.env" ]; then
    echo "   ✅ .env file exists"
    if grep -q "SECRET_KEY" "$DEPLOY_DIR/.env"; then
        echo "   ✅ SECRET_KEY found"
    else
        echo "   ❌ SECRET_KEY not found"
    fi
    if grep -q "DB_PASSWORD" "$DEPLOY_DIR/.env"; then
        echo "   ✅ DB_PASSWORD found"
    else
        echo "   ❌ DB_PASSWORD not found"
    fi
else
    echo "   ❌ .env file not found!"
    exit 1
fi

# Check docker-compose file
echo ""
echo "3. Checking docker-compose file..."
if [ -f "$DEPLOY_DIR/docker-compose.yml" ]; then
    echo "   ✅ docker-compose.yml exists"
else
    echo "   ❌ docker-compose.yml not found!"
    exit 1
fi

# Check Docker image
echo ""
echo "4. Checking Docker image..."
if docker images | grep -q channel-manager; then
    echo "   ✅ channel-manager image exists"
    docker images | grep channel-manager
else
    echo "   ❌ channel-manager image not found!"
    echo "   Run: docker load -i /tmp/deploy/channel-manager-image.tar.gz"
fi

# Check running containers
echo ""
echo "5. Checking running containers..."
cd "$DEPLOY_DIR"
docker compose ps

# Check container logs
echo ""
echo "6. Checking container logs..."
if docker compose ps | grep -q "channel_manager_web"; then
    echo "   Web container logs (last 20 lines):"
    docker compose logs web --tail=20 || true
else
    echo "   ⚠️  Web container not running"
fi

# Check port 8001
echo ""
echo "7. Checking port 8001..."
if command -v netstat >/dev/null 2>&1; then
    if netstat -tlnp 2>/dev/null | grep 8001; then
        echo "   ✅ Port 8001 is listening"
    else
        echo "   ❌ Port 8001 is not listening"
    fi
elif command -v ss >/dev/null 2>&1; then
    if ss -tlnp 2>/dev/null | grep 8001; then
        echo "   ✅ Port 8001 is listening"
    else
        echo "   ❌ Port 8001 is not listening"
    fi
fi

# Check nginx
echo ""
echo "8. Checking nginx configuration..."
if [ -f /etc/nginx/sites-available/channel-manager ]; then
    echo "   ✅ Nginx config exists"
    if [ -L /etc/nginx/sites-enabled/channel-manager ]; then
        echo "   ✅ Nginx site is enabled"
    else
        echo "   ⚠️  Nginx site not enabled (run: sudo ln -s /etc/nginx/sites-available/channel-manager /etc/nginx/sites-enabled/)"
    fi
    if sudo nginx -t 2>&1 | grep -q "successful"; then
        echo "   ✅ Nginx config is valid"
    else
        echo "   ❌ Nginx config has errors:"
        sudo nginx -t || true
    fi
else
    echo "   ⚠️  Nginx config not found"
fi

# Try to start services
echo ""
echo "9. Attempting to start services..."
cd "$DEPLOY_DIR"
if docker compose up -d; then
    echo "   ✅ Services started"
    sleep 5
    docker compose ps
else
    echo "   ❌ Failed to start services"
    echo "   Error logs:"
    docker compose logs --tail=30 || true
fi

# Health check
echo ""
echo "10. Health check..."
sleep 3
if curl -f http://localhost:8001/health/ 2>/dev/null; then
    echo "   ✅ Health check passed"
else
    echo "   ❌ Health check failed"
    echo "   Web container logs:"
    docker compose logs web --tail=30 || true
fi

echo ""
echo "=== Diagnostic Complete ==="

