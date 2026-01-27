# RevNext Channel Manager API Documentation

## Overview

The RevNext Channel Manager API provides comprehensive REST endpoints for managing hotel properties, OTA integrations, reservations, and subscriptions in a multi-tenant SaaS environment.

## Base URL

- **Development**: `http://localhost:8000/api/`
- **Production**: `https://channel-manager.revnext.in/api/`

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `/api/docs/`
- **ReDoc**: `/api/redoc/`
- **OpenAPI Schema (JSON)**: `/api/docs.json`
- **OpenAPI Schema (YAML)**: `/api/docs.yaml`

## Authentication

The API supports two authentication methods:

### 1. Token Authentication

Include the token in the Authorization header:

```http
Authorization: Token <your-token>
```

To obtain a token:
1. Log in to the admin panel at `/admin/`
2. Navigate to your user profile
3. Generate or view your API token

### 2. Session Authentication

For browser-based access, use Django session cookies. Simply log in through the admin panel and access the API through Swagger UI.

## Rate Limiting

- **Anonymous users**: 100 requests/hour
- **Authenticated users**: 1000 requests/hour
- **API calls per month**: Tracked per tenant subscription plan

## Subscription Plans

| Plan | Properties | Integrations/Property | Users | API Calls/Month | Monthly Price |
|------|-----------|---------------------|-------|----------------|---------------|
| Free | 1 | 5 | 1 | 1,000 | ₹0 |
| Basic | 5 | 10 | 3 | 10,000 | ₹2,999 |
| Professional | 25 | 25 | 10 | 100,000 | ₹9,999 |
| Enterprise | 100 | Unlimited | 50 | Unlimited | ₹29,999 |

## API Endpoints

### Tenant Management

- `GET /api/tenants/` - List tenants (admin only)
- `GET /api/tenants/{id}/` - Get tenant details
- `GET /api/tenants/{id}/stats/` - Get tenant statistics
- `POST /api/tenants/{id}/upgrade_subscription/` - Upgrade subscription

### Subscription Plans

- `GET /api/subscription-plans/` - List available plans
- `GET /api/subscription-plans/{id}/` - Get plan details

### Properties

- `GET /api/core/properties/` - List properties
- `POST /api/core/properties/` - Create property
- `GET /api/core/properties/{id}/` - Get property details
- `PUT /api/core/properties/{id}/` - Update property
- `DELETE /api/core/properties/{id}/` - Delete property
- `GET /api/core/properties/{id}/inventory/` - Get property inventory
- `GET /api/core/properties/{id}/stats/` - Get property statistics

### Room Types

- `GET /api/core/room-types/` - List room types
- `POST /api/core/room-types/` - Create room type
- `GET /api/core/room-types/{id}/` - Get room type details
- `PUT /api/core/room-types/{id}/` - Update room type
- `DELETE /api/core/room-types/{id}/` - Delete room type

### Rate Plans

- `GET /api/core/rate-plans/` - List rate plans
- `POST /api/core/rate-plans/` - Create rate plan
- `GET /api/core/rate-plans/{id}/` - Get rate plan details
- `PUT /api/core/rate-plans/{id}/` - Update rate plan
- `DELETE /api/core/rate-plans/{id}/` - Delete rate plan

### Inventory

- `GET /api/core/inventory/` - List inventory records
- `POST /api/core/inventory/` - Create inventory record
- `GET /api/core/inventory/{id}/` - Get inventory details
- `PUT /api/core/inventory/{id}/` - Update inventory
- `DELETE /api/core/inventory/{id}/` - Delete inventory

### Integrations

- `GET /api/integrations/platforms/` - List OTA platforms
- `GET /api/integrations/integrations/` - List property integrations
- `POST /api/integrations/integrations/` - Create integration
- `GET /api/integrations/integrations/{id}/` - Get integration details
- `POST /api/integrations/integrations/{id}/sync/` - Trigger sync
- `GET /api/integrations/sync-logs/` - List sync logs

### Reservations

- `GET /api/bookings/reservations/` - List reservations
- `POST /api/bookings/reservations/` - Create reservation
- `GET /api/bookings/reservations/{id}/` - Get reservation details
- `PUT /api/bookings/reservations/{id}/` - Update reservation
- `POST /api/bookings/reservations/{id}/cancel/` - Cancel reservation
- `GET /api/bookings/reservations/upcoming/` - Get upcoming reservations
- `GET /api/bookings/reservations/today/` - Get today's check-ins

### Payments

- `GET /api/bookings/payments/` - List payments
- `GET /api/bookings/payments/{id}/` - Get payment details

## Example Requests

### Create a Property

```bash
curl -X POST http://localhost:8000/api/core/properties/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Grand Hotel Mumbai",
    "property_type": "hotel",
    "address_line1": "123 Main Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "postal_code": "400001",
    "phone": "+91-22-12345678",
    "email": "info@grandhotel.com",
    "gstin": "27AABCU9603R1ZX"
  }'
```

### Get Tenant Statistics

```bash
curl -X GET http://localhost:8000/api/tenants/1/stats/ \
  -H "Authorization: Token <your-token>"
```

### Trigger Integration Sync

```bash
curl -X POST http://localhost:8000/api/integrations/integrations/1/sync/ \
  -H "Authorization: Token <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sync_type": "FULL"
  }'
```

## Error Responses

The API uses standard HTTP status codes:

- `200 OK` - Request successful
- `201 Created` - Resource created
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions or subscription expired
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "field_name": ["Field-specific errors"]
}
```

## Pagination

List endpoints support pagination:

- `?page=1` - Page number
- `?page_size=20` - Items per page (default: 20)

Response format:

```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

## Filtering and Search

Most list endpoints support filtering and search:

- `?property_type=hotel` - Filter by property type
- `?city=Mumbai` - Filter by city
- `?search=grand` - Search across multiple fields
- `?ordering=-created_at` - Order by field (prefix with `-` for descending)

## Support

For API support:
- **Email**: support@revnext.in
- **Documentation**: `/api/docs/`
- **Website**: https://www.revnext.in
