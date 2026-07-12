# RevNext Solutions Architecture

## Overview

This document describes the architecture for in-depth, detailed web applications for each solution in the RevNext hospitality platform. All solutions share the same codebase and integrate with the core multi-tenant model (tenants, properties, room types, rate plans, reservations).

---

## Solution Apps Structure

| App | Purpose | Key Models | Dashboard Features |
|-----|---------|------------|-------------------|
| **cloud_pms** | Property Management System | Folio, HousekeepingTask, LinkedRoomUnit | Front desk, housekeeping, billing, villa inventory |
| **cloud_pos** | Point of Sale | MenuCategory, MenuItem, POSOrder, Table | F&B orders, Bill to Room |
| **booking_engine** | Direct Booking | DirectBooking, BookingSession | One-page booking, multi-currency |
| **Hotel CMS (external)** | RevNextCMS on dedicated VPS | Organization / HotelSite (Wagtail) | `cms.revnext.in` + `app.revnext.in` — billed here as `cms` / suite |
| **b2b_network** | Stay B2B | B2BAgent, B2BRatePlan, CorporateAccount | Agent portals, special rates |
| **ota_listing** | OTA Listing Service | ListingProject, OTAListingStatus | Setup workflow, optimization |
| **google_hotel_ads** | Google Hotel Ads | HotelAdsConfig, FeedSubmission | Pay-per-conversion, feed management |
| **payment_gateways** | Payment Gateways | GatewayConfig, TransactionLog | Razorpay, PayPal config |

---

## Data Flow & Integration

```
Tenant → Properties → RoomTypes → RatePlans
                ↓
        [cloud_pms] Folios, Housekeeping, LinkedRoom
                ↓
        [cloud_pos] POS Orders → Bill to Room → Folio
                ↓
        [booking_engine] Direct bookings → Reservations
                ↓
        [RevNextCMS] Property website (external VPS) → Booking Engine
                ↓
        [b2b_network] Agent rates → RatePlans
                ↓
        [ota_listing] OTA setup → PropertyIntegration
                ↓
        [google_hotel_ads] Feed → Google
                ↓
        [payment_gateways] Payment processing
```

---

## URL Structure

- `/pms/` - Cloud PMS dashboard
- `/pos/` - Cloud POS dashboard  
- `/booking/` - Booking engine (public + admin)
- Hotel CMS → `https://app.revnext.in/` (RevNextCMS; `/website-builder/` redirects)
- `/b2b/` - B2B network (agent portal)
- `/ota-listing/` - OTA listing service
- `/google-hotel-ads/` - Google Hotel Ads config
- `/payments/` - Payment gateway management

---

## Shared Dependencies

- **tenants**: Tenant, TenantUser
- **core**: Property, RoomType, RatePlan, Inventory, Reservation
- **bookings**: Reservation, Payment
- **integrations**: PropertyIntegration, IntegrationPlatform
