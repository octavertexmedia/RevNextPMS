#!/usr/bin/env sh
# Initialize OpenBao file backend (run once against a fresh volume).
# Usage (from VPS):
#   cd ~/revnext-secrets
#   docker compose exec openbao sh /openbao/scripts/init.sh
#
# After init: copy /openbao/file/init.json off the server, store unseal key + root
# token securely, then delete init.json from the volume. Prefer AppRole for apps.
set -e
export BAO_ADDR="${BAO_ADDR:-http://127.0.0.1:8200}"

if bao status 2>/dev/null | grep -q 'Initialized.*true'; then
  echo "OpenBao already initialized"
  bao status || true
  exit 0
fi

echo "Initializing OpenBao (1 share / threshold 1 — rotate for production)..."
bao operator init -key-shares=1 -key-threshold=1 -format=json > /openbao/file/init.json
UNSEAL=$(python3 -c "import json;print(json.load(open('/openbao/file/init.json'))['unseal_keys_b64'][0])")
ROOT=$(python3 -c "import json;print(json.load(open('/openbao/file/init.json'))['root_token'])")
bao operator unseal "$UNSEAL"
echo "Root token and unseal key written to /openbao/file/init.json — move to a secure store, then delete."
echo "ROOT_TOKEN=$ROOT"
echo ""
echo "Next:"
echo "  1) bao login \$ROOT_TOKEN"
echo "  2) bao secrets enable -path=secret kv-v2  (if not already enabled)"
echo "  3) Write app secrets under revnext/channel-manager/production"
echo "  4) Create AppRole for ChannelManager; put ROLE_ID/SECRET_ID in ~/channel-manager/.env"
echo "  5) After reboot: unseal with the key from init.json"
