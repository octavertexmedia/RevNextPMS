# Deployment Guide

This guide explains how to deploy the Channel Manager to a Contabo VPS using GitHub Actions CI/CD.

## Prerequisites

1. **Contabo VPS** with:
   - Ubuntu 20.04+ or Debian 11+
   - Docker and Docker Compose installed
   - Nginx installed (optional, for reverse proxy)
   - SSH access configured

2. **GitHub Repository** with:
   - Secrets configured (see below)
   - Main/master branch for production

## GitHub Secrets Configuration

Configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets

- `VPS_SSH_PRIVATE_KEY`: Private SSH key for VPS access
- `VPS_HOST`: VPS IP address or hostname
- `VPS_USER`: SSH username (usually `root` or your user)
- `VPS_DOMAIN`: Your domain name (optional, for health checks)

### Optional Secrets

- `DOCKER_HUB_USERNAME`: Docker Hub username (if pushing images)
- `DOCKER_HUB_PASSWORD`: Docker Hub password/token

## VPS Setup

### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group (if not root)
sudo usermod -aG docker $USER
```

### 2. Install Nginx (Optional)

```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 3. Create Deployment Directory

```bash
mkdir -p ~/channel-manager
mkdir -p ~/backups
```

### 4. Set Up SSH Key for GitHub Actions

```bash
# On your local machine, generate SSH key pair
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/vps_deploy

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/vps_deploy.pub user@your-vps-ip

# Add private key to GitHub Secrets (VPS_SSH_PRIVATE_KEY)
cat ~/.ssh/vps_deploy
# Copy the output and add to GitHub Secrets
```

## Environment Configuration

### 1. Create .env File on VPS

```bash
cd ~/channel-manager
nano .env
```

Add the following configuration:

```env
# Django
SECRET_KEY=your-very-secure-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-vps-ip

# Database
DB_NAME=channel_manager
DB_USER=postgres
DB_PASSWORD=secure-db-password
DB_HOST=db
DB_PORT=5432

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Google Maps (optional)
GOOGLE_MAPS_API_KEY=your-google-maps-api-key

# Environment
ENVIRONMENT=production
```

### 2. Generate Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Deployment Process

### Automatic Deployment (via GitHub Actions)

1. **Push to main/master branch**
   ```bash
   git push origin main
   ```

2. **GitHub Actions will:**
   - Run tests (on pull requests)
   - Build Docker image
   - Deploy to VPS
   - Run health checks

### Manual Deployment

If you need to deploy manually:

```bash
# SSH into VPS
ssh user@your-vps-ip

# Navigate to deployment directory
cd ~/channel-manager

# Pull latest code (if using git)
git pull origin main

# Build and start services
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker compose exec web python manage.py migrate

# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# Restart services
docker compose restart
```

## Post-Deployment

### 1. Create Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### 2. Load Initial Data

```bash
docker compose exec web python manage.py setup_initial_data
```

### 3. Configure Nginx

Edit the nginx.conf file and update:
- `server_name` with your domain
- Path to static/media files
- User directory paths

Then:

```bash
sudo cp nginx.conf /etc/nginx/sites-available/channel-manager
sudo ln -s /etc/nginx/sites-available/channel-manager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Set Up SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Monitoring

### Check Service Status

```bash
docker compose ps
docker compose logs -f web
docker compose logs -f celery
docker compose logs -f celery-beat
```

### Health Check

```bash
curl http://localhost:8000/health/
```

### Database Backup

```bash
# Manual backup
docker compose exec db pg_dump -U postgres channel_manager > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T db psql -U postgres channel_manager < backup_20240101.sql
```

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker compose logs

# Check service status
docker compose ps

# Restart services
docker compose restart
```

### Database Connection Issues

```bash
# Check database is running
docker compose ps db

# Check database logs
docker compose logs db

# Test connection
docker compose exec web python manage.py dbshell
```

### Celery Not Working

```bash
# Check Redis connection
docker compose exec redis redis-cli ping

# Check Celery logs
docker compose logs celery

# Restart Celery
docker compose restart celery celery-beat
```

### Static Files Not Loading

```bash
# Collect static files
docker compose exec web python manage.py collectstatic --noinput

# Check permissions
ls -la ~/channel-manager/staticfiles/
```

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker compose exec web python manage.py migrate

# Restart services
docker compose restart
```

### Clean Up

```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove old logs
find ~/channel-manager/logs -name "*.log" -mtime +30 -delete
```

## Security Considerations

1. **Firewall Configuration**
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Database Security**
   - Use strong passwords
   - Restrict database access to localhost only
   - Regular backups

3. **Django Security**
   - Set `DEBUG=False` in production
   - Use strong `SECRET_KEY`
   - Configure `ALLOWED_HOSTS`
   - Enable HTTPS

4. **SSH Security**
   - Disable password authentication
   - Use SSH keys only
   - Change default SSH port (optional)

## Backup Strategy

### Automated Backups

Create a cron job for daily backups:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd ~/channel-manager && docker compose exec -T db pg_dump -U postgres channel_manager > ~/backups/db_$(date +\%Y\%m\%d).sql
```

### Backup Retention

```bash
# Keep last 30 days of backups
find ~/backups -name "*.sql" -mtime +30 -delete
```

## Scaling

### Add More Workers

Edit `docker-compose.prod.yml`:

```yaml
web:
  command: gunicorn --bind 0.0.0.0:8000 --workers 8 ...
```

### Add More Celery Workers

```bash
docker compose up -d --scale celery=3
```

## Support

For issues or questions:
- Check logs: `docker compose logs`
- Review GitHub Actions workflow runs
- Check service health: `curl http://localhost:8000/health/`

