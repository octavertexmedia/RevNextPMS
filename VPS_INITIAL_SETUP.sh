#!/bin/bash
# Initial VPS Setup Script for Channel Manager
# Run this on your VPS: root@5.189.180.67

set -e

echo "=== Channel Manager VPS Initial Setup ==="
echo ""

# Create deployment directory
echo "Creating deployment directory..."
mkdir -p ~/channel-manager
mkdir -p ~/backups
cd ~/channel-manager

# Create .env file
echo ""
echo "Creating .env file..."
cat > .env << 'ENVEOF'
# Django Configuration
SECRET_KEY=CHANGE-THIS-GENERATE-SECURE-KEY
DEBUG=False
ALLOWED_HOSTS=channel-manager.revnext.in,5.189.180.67,localhost,127.0.0.1

# Database Configuration
DB_NAME=channel_manager
DB_USER=postgres
DB_PASSWORD=CHANGE-THIS-GENERATE-SECURE-PASSWORD
DB_HOST=db
DB_PORT=5432

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Environment
ENVIRONMENT=production
ENVEOF

echo "✅ .env file created at ~/channel-manager/.env"
echo ""
echo "⚠️  IMPORTANT: Update .env file with secure values:"
echo "   1. Generate SECRET_KEY:"
echo "      python3 -c \"import secrets; print(secrets.token_hex(32))\""
echo ""
echo "   2. Generate DB_PASSWORD:"
echo "      python3 -c \"import secrets; print(secrets.token_urlsafe(25))\""
echo ""
echo "   3. Edit .env file:"
echo "      nano ~/channel-manager/.env"
echo ""
echo "✅ Directory structure ready for deployment!"
echo ""
echo "Next steps:"
echo "  1. Update .env file with secure values"
echo "  2. Push to GitHub to trigger deployment"
echo "  3. Or manually deploy using docker-compose"

