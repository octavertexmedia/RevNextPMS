#!/bin/bash
# Quick fix script to configure nginx for channel-manager
# Run this on the VPS: ssh root@5.189.180.67

set -e

DEPLOY_DIR="${1:-/home/root/channel-manager}"

echo "=== Fixing Nginx Configuration ==="
echo "Deployment directory: $DEPLOY_DIR"

# Create nginx config with correct path
cat > /tmp/nginx-channel-manager.conf << EOF
# Nginx configuration for Channel Manager
upstream channel_manager {
    server 127.0.0.1:8001;
}

server {
    listen 80;
    server_name channel-manager.revnext.in;

    client_max_body_size 100M;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias ${DEPLOY_DIR}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias ${DEPLOY_DIR}/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # Health check endpoint
    location /health/ {
        proxy_pass http://channel_manager;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        access_log off;
    }

    # Main application
    location / {
        proxy_pass http://channel_manager;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Copy config
sudo cp /tmp/nginx-channel-manager.conf /etc/nginx/sites-available/channel-manager

# Create symlink
sudo ln -sf /etc/nginx/sites-available/channel-manager /etc/nginx/sites-enabled/channel-manager

# Remove default nginx site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Test nginx config
echo "Testing nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx config is valid"
    # Reload nginx
    sudo nginx -s reload || sudo systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx config test failed!"
    exit 1
fi

# Check if containers are running
echo ""
echo "Checking Docker containers..."
cd "$DEPLOY_DIR"
docker compose ps

echo ""
echo "✅ Nginx configuration complete!"
echo "Visit: http://channel-manager.revnext.in/"

