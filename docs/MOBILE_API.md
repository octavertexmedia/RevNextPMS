# Mobile / Flutter API notes

Operational status values use **UPPER_SNAKE** (`CONFIRMED`, `CHECKED_IN`, `PENDING`, etc.).

## Auth

Token: `Authorization: Token <key>`

### Devices / FCM

| Method | Path |
|--------|------|
| GET | `/api/auth/devices/` |
| POST | `/api/auth/devices/register/` `{token, platform, device_name?}` |
| POST | `/api/auth/devices/unregister/` `{token}` |

Set `FCM_SERVER_KEY` for outbound pushes. Flutter: `ENABLE_FIREBASE=true` + Firebase dart-defines for real FCM tokens.

## Suite APIs (mobile)

| Mount | Resources / actions |
|-------|---------------------|
| `/api/booking-engine/` | bookings list/detail; `cancel`, `confirm` |
| `/api/website-builder/` | **retired** — use RevNextCMS (`app.revnext.in`); path redirects |
| `/api/b2b/` | agents; `set_active` |
| `/api/ota-listing/` | projects; `set_status` |
| `/api/google-hotel-ads/` | configs; `toggle`, `submit_feed` |
| `/api/pos/` | menu-items, orders; `add_item`, `set_status` |
| `/api/pms/` | folios, housekeeping, linked-rooms (writable), dashboard |
| `/api/reports/` | templates; `POST …/templates/{id}/generate/`; generated download |

## Docker

From `revnext_pms_app`:

```bash
docker compose up --build
```

- PMS web: http://localhost:18080  
- API: http://localhost:18001  
