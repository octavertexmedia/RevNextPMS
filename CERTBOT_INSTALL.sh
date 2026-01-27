#!/bin/bash
# Quick Certbot Installation and SSL Setup
# Run this on your VPS: root@5.189.180.67

set -e

echo "=== Installing Certbot ==="
apt update
apt install -y certbot python3-certbot-nginx

echo ""
echo "=== Verifying Installation ==="
certbot --version

echo ""
echo "=== Checking Nginx Configuration ==="
if [ -f /etc/nginx/sites-available/channel-manager ]; then
    echo "✅ Nginx config found"
    nginx -t
else
    echo "⚠️  Nginx config not found at /etc/nginx/sites-available/channel-manager"
    echo "   Make sure nginx.conf is copied to the VPS first"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Make sure nginx is running: systemctl status nginx"
echo "2. Verify domain DNS points to this server: dig channel-manager.revnext.in"
echo "3. Run certbot: certbot --nginx -d channel-manager.revnext.in"
echo "4. Follow the prompts to complete SSL setup"

