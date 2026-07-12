# RevNext platform hosts

## Shared Contabo — `77.237.234.201` (this ChannelManager / RevNextPMS process)

Product hosts below are served by one Django process (`127.0.0.1:8001`) via
`ProductHostMiddleware`.

| Host | Product | Django apps / paths |
|------|---------|---------------------|
| `channel-manager.revnext.in` | Channel Manager | `/tenants/`, `/api/integrations/`, … |
| `pms.revnext.in` | Cloud PMS | `/pms/`, `/api/pms/` |
| `pos.revnext.in` | Cloud POS | `/pos/`, `/api/pos/` |
| `booking.revnext.in` | Booking engine | `/booking/` |
| `hotels.revnext.in` | Hotels aggregator | `/hotels/` |
| `networks.revnext.in` | B2B networks | `/b2b/` |
| `tours.revnext.in` | Tours | `/tours/` |
| `revnext.in` / `www.revnext.in` | Marketing + aggregator | landing + `/hotels/` |

Nginx site: **`channel-manager`** → upstream `127.0.0.1:8001`  
Deploy dir: **`~/channel-manager`**  
CI: **`.github/workflows/deploy.yml`** (repo `octavertexmedia/RevNextPMS`)

Canonical lists: `channel_manager/domains.py` (`NGINX_APP_HOSTS` excludes CMS).

## Dedicated CMS VPS — `84.247.183.69` (RevNextCMS — separate repo)

| Host | Purpose |
|------|---------|
| `cms.revnext.in` | Wagtail CMS admin (sole runtime for Hotel CMS) |
| `app.revnext.in` | Owner portal — suite / solo launch URL |
| `*.sites.revnext.in` | Public **hotel websites** |

DNS for these hosts **must** point at `84.247.183.69`, not the shared Contabo IP.  
See RevNextCMS `docs/HOSTING-TOPOLOGY.md` and `docs/channel-manager-cms-bridge.md`.

**Billing:** ChannelManager catalogs `cms` as an **externally served** product (`is_externally_served=true`, `runtime_url=https://app.revnext.in`).  
Subscribe via `cms_starter` / `cms_pro` or `revnext_suite`. Legacy `/website-builder/` on this process redirects to RevNextCMS.

**SSO:** Shared Keycloak IdP at `auth.revnext.in` (issuer `https://auth.revnext.in/realms/revnext`).  
RevNextCMS client: `revnext-platform`. ChannelManager products: `OIDC_CLIENT_*` / `revnext-channel-manager`, etc.

**Entitlements S2S:** `GET /api/internal/entitlements/?email=` (Bearer `ENTITLEMENTS_SERVICE_TOKEN`) — used by RevNextCMS when `REVNEXT_BILLING_SOURCE=channel_manager`.

## DNS → VPS map (BigRock SoT)

| Host | A record | VPS / runtime |
|------|----------|---------------|
| `revnext.in` | `216.198.79.1` | Vercel (marketing) |
| `channel-manager` · `pms` · `pos` · `booking` · `networks` · `tours` · `hotels` | `77.237.234.201` | Shared Contabo — ChannelManager |
| `secrets.revnext.in` | `77.237.234.201` | Shared Contabo — OpenBao (`~/revnext-secrets`) |
| `auth.revnext.in` | per BigRock (propagate) | Keycloak IdP — confirm target after TTL |
| `cms` · `app` · `*.sites` | `84.247.183.69` | RevNextCMS Contabo |

## Infrastructure (shared Contabo `77.237.234.201`)

| Host | Service | Deploy |
|------|---------|--------|
| `secrets.revnext.in` | OpenBao (secrets SoT for app env) | `~/revnext-secrets`, workflow `deploy-secrets.yml` |
| `auth.revnext.in` | External OIDC IdP (SSO only) | Outside ChannelManager repo — must match BigRock A target |

### Env ownership

```
auth.revnext.in     → identity / login (SSO)
secrets.revnext.in  → SECRET_KEY, DB_PASSWORD, Razorpay, OIDC client secrets, …
~/channel-manager/.env  → OPENBAO_* bootstrap + DB_* for Postgres container only
```

ChannelManager CI **never** starts, stops, or wipes OpenBao volumes.

## Contabo port map (shared VPS `77.237.234.201`)

| Project | Port |
|---------|------|
| SuratBazaar | `:8000` |
| ChannelManager products | `:8001` |
| HappyNails | `:8002` |
| Packmold | `:8003` |
| OpenBao (secrets) | `:8200` (localhost only) |

CMS VPS `84.247.183.69` uses its own stack (`127.0.0.1:8005` behind nginx/Caddy).

## Certbot (shared Contabo products only)

```bash
sudo certbot --nginx \
  -d channel-manager.revnext.in \
  -d booking.revnext.in -d networks.revnext.in \
  -d pms.revnext.in -d pos.revnext.in \
  -d hotels.revnext.in -d tours.revnext.in
```

Do **not** include `revnext.in` / `www` (Vercel) or `cms` / `app` (dedicated CMS VPS) on this Contabo cert.

CMS / hotel sites (on `84.247.183.69`):

```bash
sudo certbot --nginx -d cms.revnext.in -d app.revnext.in
# + wildcard / per-tenant TLS for *.sites.revnext.in as documented in RevNextCMS
```

Secrets:

```bash
sudo certbot --nginx -d secrets.revnext.in
```
