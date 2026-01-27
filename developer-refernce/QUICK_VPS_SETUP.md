# Quick VPS Setup for Channel Manager

## Step 1: Create Directory and .env File

SSH into your VPS and run:

```bash
ssh root@5.189.180.67

# Create directories
mkdir -p ~/channel-manager
mkdir -p ~/backups
cd ~/channel-manager

# Create .env file
nano .env
```

**Paste this content and update the values:**

```env
# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=channel-manager.revnext.in,5.189.180.67,localhost,127.0.0.1

# Database Configuration
DB_NAME=channel_manager
DB_USER=postgres
DB_PASSWORD=your-secure-db-password-here
DB_HOST=db
DB_PORT=5432

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

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

**Save:** `Ctrl+X`, then `Y`, then `Enter`

## Step 2: Verify Directory

```bash
ls -la ~/channel-manager/
cat ~/channel-manager/.env
```

## Step 3: Install Docker (if not installed)

```bash
# Check if Docker is installed
docker --version

# If not installed:
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Step 4: Ready for Deployment

Once the directory and .env file are created, GitHub Actions deployment will:
- Copy files to `~/channel-manager/`
- Load Docker image
- Start services on port 8001
- Configure nginx

## Manual Deployment (Alternative)

If you want to deploy manually:

```bash
cd ~/channel-manager

# Copy docker-compose.prod.yml (from deployment)
# Copy nginx.conf (from deployment)

# Start services
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser
```

## Check Status

```bash
cd ~/channel-manager
docker compose ps
docker compose logs -f
```

