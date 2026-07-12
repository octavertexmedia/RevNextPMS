#!/usr/bin/env sh
# Initialize a non-dev OpenBao file backend (run once against a fresh volume).
# Usage (from host):
#   docker compose -f docker-compose.prod.yml exec openbao sh /openbao/scripts/init.sh
set -e
export BAO_ADDR="${BAO_ADDR:-http://127.0.0.1:8200}"

if bao status 2>/dev/null | grep -q 'Initialized.*true'; then
  echo "OpenBao already initialized"
  bao status
  exit 0
fi

echo "Initializing OpenBao..."
bao operator init -key-shares=1 -key-threshold=1 -format=json > /openbao/file/init.json
UNSEAL=$(python3 -c "import json;print(json.load(open('/openbao/file/init.json'))['unseal_keys_b64'][0])")
ROOT=$(python3 -c "import json;print(json.load(open('/openbao/file/init.json'))['root_token'])")
bao operator unseal "$UNSEAL"
echo "Root token and unseal key written to /openbao/file/init.json — move to a secure store, then delete."
echo "ROOT_TOKEN=$ROOT"
