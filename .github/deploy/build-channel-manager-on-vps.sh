#!/bin/bash
# Build Channel Manager Docker image on the Contabo VPS (no GitHub artifact upload).
# Usage: ./build-channel-manager-on-vps.sh /tmp/deploy-channel-manager
#
# Expects IMAGE_DIR to contain:
#   app/                         (full Django project + Dockerfile)
#   docker-compose.prod.yml
#   nginx-config.conf / nginx-config.https.conf / nginx.conf
#   env.example
#   deploy.sh
#   deploy/openbao/              (optional OpenBao scripts)

set -e

IMAGE_DIR="${1:?Usage: build-channel-manager-on-vps.sh <image-dir>}"

echo "[build] Building Channel Manager images in $IMAGE_DIR"
cd "$IMAGE_DIR"

if [ ! -d "$IMAGE_DIR/app" ]; then
  echo "[build] ERROR: $IMAGE_DIR/app missing (rsync failed?)"
  exit 1
fi

# Prefer Dockerfile next to compose staging; fall back to app/Dockerfile
DOCKERFILE="$IMAGE_DIR/Dockerfile"
if [ ! -f "$DOCKERFILE" ]; then
  DOCKERFILE="$IMAGE_DIR/app/Dockerfile"
fi

echo "[build] Building channel-manager:latest ..."
if ! docker build -f "$DOCKERFILE" -t channel-manager:latest "$IMAGE_DIR/app"; then
  echo ""
  echo "[build] FAILED — often: cannot pull from registry-1.docker.io (DNS)."
  echo "On the VPS (as root), point Docker at public DNS, then restart Docker:"
  echo "  sudo mkdir -p /etc/docker"
  echo "  echo '{\"dns\":[\"8.8.8.8\",\"1.1.1.1\"]}' | sudo tee /etc/docker/daemon.json"
  echo "  sudo systemctl restart docker"
  echo "Docs: .github/DEPLOYMENT.md"
  exit 1
fi

echo "[build] Image ready: channel-manager:latest"
docker images channel-manager --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}" || true

echo "[build] Running deploy..."
chmod +x "$IMAGE_DIR/deploy.sh"
"$IMAGE_DIR/deploy.sh" "$IMAGE_DIR"
