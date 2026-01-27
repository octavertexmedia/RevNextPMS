# VPS Setup Guide for Channel Manager

This guide helps you set up your VPS at `5.189.180.67` (channel-manager.revnext.in) for deployment.

## Prerequisites

- VPS with Ubuntu/Debian
- SSH access to the VPS
- Root or sudo access

## Step 1: Initial VPS Setup

### 1.1 Install Docker and Docker Compose

```bash
# SSH into your VPS
ssh root@5.189.180.67

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker compose version
```

### 1.2 Install Nginx (Optional but Recommended)

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 1.3 Create Deployment Directory

```bash
# Create directories
mkdir -p ~/channel-manager
mkdir -p ~/backups

# Set permissions
chmod 755 ~/channel-manager
```

## Step 2: Create .env File on VPS

**Important:** Create the `.env` file on your VPS before the first deployment:

```bash
# SSH into VPS
ssh root@5.189.180.67

# Navigate to deployment directory
cd ~/channel-manager

# Create .env file
nano .env
```

**Paste this content (update values as needed):**

```env
# Django Configuration
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=channel-manager.revnext.in,5.189.180.67,localhost,127.0.0.1

# Database Configuration
DB_NAME=channel_manager
DB_USER=postgres
DB_PASSWORD=your-secure-database-password-here
DB_HOST=db
DB_PORT=5432

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Google Maps API (optional)
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Environment
ENVIRONMENT=production
```

**Generate secure values:**

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate DB_PASSWORD
python3 -c "import secrets; print(secrets.token_urlsafe(25))"
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

## Step 3: Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Step 4: Set Up Domain (channel-manager.revnext.in)

### 4.1 DNS Configuration

Point your domain to the VPS IP:
- **A Record**: `channel-manager.revnext.in` → `5.189.180.67`

### 4.2 Configure Nginx

After first deployment, the nginx config will be copied. You may need to:

```bash
# Edit nginx config
sudo nano /etc/nginx/sites-available/channel-manager

# Update server_name if needed
# Update paths if your username is not 'root'

# Test nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Step 5: SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d channel-manager.revnext.in

# Auto-renewal is set up automatically
```

## Step 6: First Deployment

After setting up GitHub Secrets, push to trigger deployment:

```bash
git commit --allow-empty -m "Trigger first deployment"
git push origin main
```

## Step 7: Post-Deployment Setup

### 7.1 Create Superuser

```bash
# SSH into VPS
ssh root@5.189.180.67

# Navigate to deployment directory
cd ~/channel-manager

# Create superuser
docker compose exec web python manage.py createsuperuser
```

### 7.2 Load Initial Data

```bash
docker compose exec web python manage.py setup_initial_data
docker compose exec web python manage.py seed_data
```

## Monitoring

### Check Service Status

```bash
cd ~/channel-manager
docker compose ps
docker compose logs -f
```

### Check Specific Service

```bash
docker compose logs -f web
docker compose logs -f celery
docker compose logs -f db
```

### Restart Services

```bash
cd ~/channel-manager
docker compose restart
# Or restart specific service
docker compose restart web
```

## Troubleshooting

### Services Won't Start

1. **Check logs:**
   ```bash
   docker compose logs
   ```

2. **Check .env file:**
   ```bash
   cat ~/channel-manager/.env
   ```

3. **Check disk space:**
   ```bash
   df -h
   ```

### Database Connection Issues

1. **Check database is running:**
   ```bash
   docker compose ps db
   ```

2. **Check database logs:**
   ```bash
   docker compose logs db
   ```

3. **Test connection:**
   ```bash
   docker compose exec db psql -U postgres -d channel_manager
   ```

### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>
```

### Update Application

```bash
# Pull latest code (if using git on VPS)
cd ~/channel-manager
git pull origin main

# Or let GitHub Actions handle it via deployment
```

## Backup

### Manual Database Backup

```bash
cd ~/channel-manager
docker compose exec -T db pg_dump -U postgres channel_manager > ~/backups/db_$(date +%Y%m%d_%H%M%S).sql
```

### Automated Daily Backup (Cron)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd ~/channel-manager && docker compose exec -T db pg_dump -U postgres channel_manager > ~/backups/db_$(date +\%Y\%m\%d).sql
```

## Security Checklist

- [ ] Strong SECRET_KEY in .env
- [ ] Strong DB_PASSWORD in .env
- [ ] Firewall configured (UFW)
- [ ] SSH key authentication only
- [ ] SSL certificate installed
- [ ] Regular backups configured
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured correctly

## Quick Commands Reference

```bash
# View logs
docker compose logs -f

# Restart services
docker compose restart

# Stop services
docker compose down

# Start services
docker compose up -d

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Access Django shell
docker compose exec web python manage.py shell

# Database backup
docker compose exec -T db pg_dump -U postgres channel_manager > backup.sql
```

