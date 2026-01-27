# SSL Certificate Setup for channel-manager.revnext.in

## Step 1: Install Certbot

On your VPS, run:

```bash
# Update package list
apt update

# Install certbot and nginx plugin
apt install -y certbot python3-certbot-nginx

# Verify installation
certbot --version
```

## Step 2: Configure Nginx First

Before running certbot, make sure your nginx configuration is in place:

```bash
# Check if nginx config exists
ls -la /etc/nginx/sites-available/channel-manager
ls -la /etc/nginx/sites-enabled/channel-manager

# If not, copy it from your deployment
# The nginx.conf should already be configured for your domain
```

## Step 3: Test Nginx Configuration

```bash
# Test nginx config
nginx -t

# If there are errors, fix them first
# Then reload nginx
systemctl reload nginx
```

## Step 4: Obtain SSL Certificate

```bash
# Run certbot with nginx plugin
certbot --nginx -d channel-manager.revnext.in

# Follow the prompts:
# - Enter your email address
# - Agree to terms of service
# - Choose whether to redirect HTTP to HTTPS (recommended: Yes)
```

Certbot will automatically:
- Obtain the certificate
- Update your nginx configuration
- Set up automatic renewal

## Step 5: Verify Certificate

```bash
# Check certificate status
certbot certificates

# Test renewal (dry run)
certbot renew --dry-run
```

## Step 6: Verify HTTPS Works

```bash
# Test from VPS
curl -I https://channel-manager.revnext.in/health/

# Or visit in browser
# https://channel-manager.revnext.in
```

## Automatic Renewal

Certbot sets up automatic renewal via systemd timer. Verify it's active:

```bash
# Check renewal timer
systemctl status certbot.timer

# List timers
systemctl list-timers | grep certbot
```

## Manual Renewal (if needed)

```bash
# Renew all certificates
certbot renew

# Renew specific certificate
certbot renew --cert-name channel-manager.revnext.in

# Reload nginx after renewal
systemctl reload nginx
```

## Troubleshooting

### If certbot fails with "Could not bind to port 80"

```bash
# Check what's using port 80
sudo lsof -i :80

# Stop conflicting service temporarily
# Then run certbot again
```

### If domain doesn't resolve

```bash
# Verify DNS
dig channel-manager.revnext.in
nslookup channel-manager.revnext.in

# Make sure A record points to: 5.189.180.67
```

### If nginx config has errors

```bash
# Check nginx config syntax
nginx -t

# View nginx error log
tail -f /var/log/nginx/error.log
```

