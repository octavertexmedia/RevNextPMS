# RevNext platform hosts

All **product** hosts are served by the same ChannelManager Django process
(`127.0.0.1:8001`) via `ProductHostMiddleware`. Infrastructure hosts are separate.

## Product hosts (same codebase)

| Host | Product | Django apps / paths |
|------|---------|---------------------|
| `channel-manager.revnext.in` | Channel Manager | `/tenants/`, `/api/integrations/`, … |
| `pms.revnext.in` | Cloud PMS | `/pms/`, `/api/pms/` |
| `pos.revnext.in` | Cloud POS | `/pos/`, `/api/pos/` |
| `cms.revnext.in` | Hotel CMS | `/website-builder/` |
| `booking.revnext.in` | Booking engine | `/booking/` |
| `hotels.revnext.in` | Hotels aggregator | `/hotels/` |
| `networks.revnext.in` | B2B networks | `/b2b/` |
| `tours.revnext.in` | Tours | `/tours/` |
| `revnext.in` / `www.revnext.in` | Marketing + aggregator | landing + `/hotels/` |

Canonical lists: `channel_manager/domains.py`, `products/catalog.py`.

Nginx site: **`channel-manager`** → upstream `127.0.0.1:8001`  
Deploy dir: **`~/channel-manager`**  
CI: **`.github/workflows/deploy.yml`**

## Infrastructure hosts (not the Django product app)

| Host | Service | Deploy |
|------|---------|--------|
| `secrets.revnext.in` | OpenBao (secrets SoT for app env) | `~/revnext-secrets`, workflow `deploy-secrets.yml` |
| `auth.revnext.in` | External OIDC IdP (SSO only) | Outside this repo (Keycloak / Authentik / Zitadel / cloud) |

### Env ownership

```
auth.revnext.in     → identity / login (SSO)
secrets.revnext.in  → SECRET_KEY, DB_PASSWORD, Razorpay, OIDC client secrets, …
~/channel-manager/.env  → OPENBAO_* bootstrap + DB_* for Postgres container only
```

ChannelManager CI **never** starts, stops, or wipes OpenBao volumes.

## Contabo port map

| Project | Port |
|---------|------|
| SuratBazaar | `:8000` |
| ChannelManager products | `:8001` |
| HappyNails | `:8002` |
| Packmold | `:8003` |
| OpenBao (secrets) | `:8200` (localhost only; nginx TLS terminates `secrets.revnext.in`) |

## Certbot

Products (one multi-SAN cert or per-host as preferred):

```bash
sudo certbot --nginx \
  -d channel-manager.revnext.in \
  -d booking.revnext.in -d networks.revnext.in \
  -d pms.revnext.in -d pos.revnext.in -d cms.revnext.in \
  -d hotels.revnext.in -d tours.revnext.in \
  -d revnext.in -d www.revnext.in
```

Secrets (separate):

```bash
sudo certbot --nginx -d secrets.revnext.in
```

Auth (IdP’s own stack):

```bash
sudo certbot --nginx -d auth.revnext.in
```
