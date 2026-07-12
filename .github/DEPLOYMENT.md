# Contabo VPS deployment — Channel Manager (RevNext)

Same pattern as **HappyNails** / **SuratBazaar** / **Packmold** on the shared Contabo VPS, plus an **independent OpenBao stack** for secrets.

See also: [docs/PLATFORM_HOSTS.md](../docs/PLATFORM_HOSTS.md)

## Two stacks (do not mix)

| Stack | Path | Port | Nginx site | CI workflow |
|-------|------|------|------------|-------------|
| **Products** | `~/channel-manager` | `127.0.0.1:8001` | `channel-manager` | `deploy.yml` |
| **Secrets (OpenBao)** | `~/revnext-secrets` | `127.0.0.1:8200` | `secrets` | `deploy-secrets.yml` (path-filtered / manual) |

ChannelManager product deploy **never** touches OpenBao containers, volumes, or the `secrets` nginx site.

```
Product hosts  → nginx → :8001  (Django)
secrets.revnext.in → nginx → :8200  (OpenBao)
auth.revnext.in    → external IdP (SSO only)
cms / app / *.sites → 84.247.183.69 (RevNextCMS — not this stack)
```

**Env SoT:** OpenBao at `secrets.revnext.in` holds app secrets.  
**`auth.revnext.in`:** OIDC IdP only — does not store `SECRET_KEY` / DB passwords.

---

## GitHub secrets

Repo: **octavertexmedia/RevNextPMS** → Settings → Secrets and variables → Actions

| Secret | Value |
|--------|--------|
| `VPS_SSH_PRIVATE_KEY` | Full contents of `~/.ssh/suratbazaar_actions` |
| `VPS_HOST` | VPS IP, e.g. `77.237.234.201` |
| `VPS_USER` | `deploy` |
| `VPS_DOMAIN` (optional) | `channel-manager.revnext.in` |

Same three SSH values as Happynails / SuratBazaar / Packmold.

```bash
ssh -i ~/.ssh/suratbazaar_actions -o BatchMode=yes deploy@YOUR_VPS_IP "echo OK"
```

---

## 1) First-time: OpenBao (`secrets.revnext.in`)

```bash
# Deploy secrets stack (Actions → Deploy RevNext Secrets, or manual):
# Copies compose + config to ~/revnext-secrets and starts OpenBao.

cd ~/revnext-secrets
docker compose exec openbao sh /openbao/scripts/init.sh
# Save init.json (unseal key + root) off-box, then delete from volume.

# Enable KV v2, write secrets under:
#   secret/data/revnext/channel-manager/production
#   …/django | database | billing | oidc | …

sudo certbot --nginx -d secrets.revnext.in
```

Workflow: `.github/workflows/deploy-secrets.yml` (only on `deploy/infra/**`, `nginx-secrets*.conf`, or `workflow_dispatch`).

---

## 2) ChannelManager product deploy

```bash
# Actions → Deploy Channel Manager to Contabo
# Or push to main (product paths).

# ~/channel-manager/.env — bootstrap only (see env.example):
OPENBAO_ENABLED=true
OPENBAO_REQUIRED=true
OPENBAO_ADDR=http://openbao:8200   # or http://172.17.0.1:8200
OPENBAO_ROLE_ID=...
OPENBAO_SECRET_ID=...
DB_PASSWORD=...   # still required for Postgres container
```

Passwordless sudo for nginx (same as Happynails):

```bash
# visudo — deploy may reload nginx for site "channel-manager" only
deploy ALL=(root) NOPASSWD: /usr/bin/mkdir, /bin/cp, /bin/ln, /usr/sbin/nginx, /bin/systemctl, /usr/sbin/service
```

Product TLS (shared Contabo — **not** cms / Vercel apex):

```bash
sudo mkdir -p /var/www/certbot
sudo certbot --nginx \
  -d channel-manager.revnext.in \
  -d booking.revnext.in -d networks.revnext.in \
  -d pms.revnext.in -d pos.revnext.in \
  -d hotels.revnext.in -d tours.revnext.in
```

`cms.revnext.in` + `app` + `*.sites` → **`84.247.183.69`** (RevNextCMS).  
`revnext.in` / `www.revnext.in` → **Vercel** (do not terminate on Contabo).  
`secrets.revnext.in` → separate cert / nginx site `secrets`.

### Migrations (important)

- `docker-compose.prod.yml` sets **`SKIP_MIGRATE=true`** on **web / celery / beat** so entrypoint does not race `deploy.sh`.
- `deploy.sh` runs a **single** `manage.py migrate` after containers are up.
- Do not run concurrent migrates (entrypoint + deploy) — that caused POS `0002` index collisions.

### Cloud POS (`pos.revnext.in`)

After a successful product deploy:

```bash
cd ~/channel-manager
docker compose exec -T web python manage.py seed_products
docker compose exec -T web python manage.py seed_pos_demo   # or --reset
```

Demo login (seed_pos_demo): `posdemo` / `posdemo123`  
Public QR: Tables list → `/pos/qr/<token>/` (no login).

Modules: `/pos/billing/`, `/pos/waiter/`, `/pos/inventory/`, `/pos/delivery/`, `/pos/qr/<token>/`.

---

## 3) auth.revnext.in (SSO)

Deploy Keycloak **outside** this Django app (realm `revnext`).  
Issuer: `https://auth.revnext.in/realms/revnext` (`OIDC_OP_ISSUER`).

Register RP redirect URIs for ChannelManager product hosts from `PRODUCT_OIDC_REDIRECT_URIS` in `channel_manager/domains.py`.  
**Hotel CMS** callbacks live on RevNextCMS (`https://cms.revnext.in/oidc/callback/`, `https://app.revnext.in/oidc/callback/`) — client `revnext-platform`.

Store client secrets + `ENTITLEMENTS_SERVICE_TOKEN` in OpenBao `…/oidc`; set `OIDC_ENABLED=true`.

Suite packaging: `cms` remains in `PRODUCT_CATALOG` / `revnext_suite` but is externally served — see `EXTERNAL_PRODUCT_RUNTIME` in `products/catalog.py` and RevNextCMS `docs/channel-manager-cms-bridge.md`.

---

## Workflow files

| Path | Role |
|------|------|
| `.github/workflows/deploy.yml` | Product: SSH → rsync → build on VPS → `~/channel-manager` |
| `.github/workflows/deploy-secrets.yml` | OpenBao only: `~/revnext-secrets` |
| `.github/deploy/build-channel-manager-on-vps.sh` | `docker build` on VPS |
| `.github/deploy/deploy.sh` | Compose up products; **skips** secrets stack; runs migrate once |
| `deploy/infra/*` | OpenBao compose, config, init, deploy-secrets.sh |
| `nginx-config*.conf` | Product hosts |
| `nginx-secrets*.conf` | `secrets.revnext.in` |
| `env.example` | Bootstrap OPENBAO_* + DB_* + OIDC notes |

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Permission denied (publickey)` | Same `VPS_SSH_PRIVATE_KEY` as Happynails |
| 502 on product hosts | `docker compose -f ~/channel-manager/docker-compose.yml ps` — web Up on `:8001` |
| App missing SECRET_KEY | OpenBao KV empty or `OPENBAO_ENABLED` false; check `manage.py openbao_status` |
| OpenBao wiped after product deploy | Should not happen — file a bug if CM deploy touched `revnext_secrets_*` |
| Port 5432 in use | Prod compose does not bind host 5432 |
| `qr_token_*_like already exists` / migrate race | Ensure `SKIP_MIGRATE=true` on web; only `deploy.sh` migrates; drop orphan indexes if needed |
| Celery “unhealthy” | Often no HTTP healthcheck — check `docker compose logs celery` for `ready` |
| POS empty after deploy | `seed_pos_demo` (and `seed_products` for plans/entitlements) |
| Product hero looks stacked (not split) | Host `./static` was stale — deploy now rsyncs `app/static` → `~/channel-manager/static` before collectstatic |

```bash
cd ~/channel-manager && docker compose ps && docker compose logs web --tail=80
curl -fsS -H 'Host: channel-manager.revnext.in' http://127.0.0.1:8001/health/
curl -fsS -H 'Host: pos.revnext.in' http://127.0.0.1:8001/health/
grep -c dawn-split-hero static/landing/css/dawn-concierge.css staticfiles/landing/css/dawn-concierge.css
curl -fsS http://127.0.0.1:8200/v1/sys/health
cd ~/revnext-secrets && docker compose ps
```
