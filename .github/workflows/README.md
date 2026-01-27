# GitHub Actions Workflow

This directory contains the CI/CD pipeline configuration for deploying the Channel Manager to a Contabo VPS.

## Workflow Overview

The workflow consists of three main jobs:

1. **Test**: Runs on pull requests to validate code changes
2. **Build**: Builds Docker image on pushes to main/master
3. **Deploy**: Deploys the application to the VPS

## Required GitHub Secrets

Configure these in your repository settings (Settings → Secrets and variables → Actions):

- `VPS_SSH_PRIVATE_KEY`: Private SSH key for VPS access
- `VPS_HOST`: VPS IP address or hostname
- `VPS_USER`: SSH username
- `VPS_DOMAIN`: Domain name (optional, for health checks)

## Workflow Triggers

- **Push to main/master**: Triggers build and deploy
- **Pull Request**: Triggers tests only
- **Manual**: Can be triggered via workflow_dispatch

## Deployment Process

1. Code is pushed to main/master branch
2. Docker image is built
3. Image is saved as artifact
4. Image is transferred to VPS via SSH
5. Deployment script runs on VPS
6. Health check verifies deployment

## Troubleshooting

### Workflow Fails at SSH Step

- Verify SSH key is correctly configured
- Check VPS_HOST and VPS_USER are correct
- Ensure VPS is accessible from GitHub Actions

### Deployment Fails

- Check VPS logs: `docker compose logs`
- Verify .env file exists on VPS
- Check disk space on VPS
- Verify Docker is running on VPS

### Health Check Fails

- Verify services are running: `docker compose ps`
- Check application logs: `docker compose logs web`
- Verify port 8000 is accessible
- Check firewall settings

