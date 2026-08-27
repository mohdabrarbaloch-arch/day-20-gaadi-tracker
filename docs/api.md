# API Reference

Base URL: `http://localhost:8000` · Interactive docs: `/docs` (Swagger).

Auth: `Authorization: Bearer <jwt>` on all `/api/*` routes except
`/api/auth/register`, `/api/auth/login`, `/api/public/*`, `/api/health`.

---

## Auth

### POST /api/auth/register
Creates an account; returns a JWT.
```json
{ "name": "Ali", "email": "ali@example.com", "password": "secret123" }
```
→ `201` `{ access_token, token_type, user: {...} }`
Errors: `409` email exists · `422` validation · `429` rate limit (5/min)

### POST /api/auth/login
```json
{ "email": "ali@example.com", "password": "secret123" }
```
→ `200` same shape as register · `401` bad credentials · `429` (10/min)

### GET /api/auth/me
→ `200` `{ id, email, name, created_at }` · `401` missing/invalid token

---

## Vehicles

### GET /api/vehicles
→ `200` `[VehicleOut]` — only the caller's vehicles, newest first

### POST /api/vehicles
```json
{
  "name": "City 2019", "make": "Honda", "model": "City",
  "year": 2019, "plate": "ABC-123", "fuel_type": "petrol", "odometer_km": 10000
}
```
→ `201` VehicleOut · `400` over 10-vehicle limit · `422` validation

### GET /api/vehicles/{id} → `200` VehicleOut · `404` not owned/unknown
### PATCH /api/vehicles/{id}
```json
{ "plate": "NEW-777", "odometer_km": 12500 }
```
→ `200` VehicleOut (partial update, any field optional)

### PUT /api/vehicles/{id}/share
```json
{ "enabled": true }
```
→ `200` VehicleOut (share_token + share_enabled in response)

### DELETE /api/vehicles/{id} → `204`

**VehicleOut**: `{ id, name, make, model, year, plate, fuel_type,
odometer_km, share_token, share_enabled, created_at }`

---

## Services

### GET /api/vehicles/{id}/services → `200` [ServiceOut]
### POST /api/vehicles/{id}/services
```json
{
  "service_type": "oil", "custom_name": null,
  "date": null, "odometer_km": 10500, "cost": 4500, "notes": "Mobil 1"
}
```
→ `201` ServiceOut · `400` odometer below vehicle current

### GET /api/vehicles/{id}/schedule
→ `200` `[ServiceDue]` — one per configured interval, most urgent first
```json
{
  "service_type": "oil", "name": "Oil Change",
  "last_km": 10000.0, "last_date": "...", "due_km": 15000.0,
  "due_date": "...", "km_remaining": 2500.0, "days_remaining": 40,
  "overdue": false, "reason": "On schedule"
}
```

### GET /api/vehicles/{id}/schedule/alert-count → `200` `{ "overdue": 2 }`
### DELETE /api/vehicles/{id}/services/{service_id} → `204`

---

## Fuel

### GET /api/vehicles/{id}/fuel → `200` [FuelOut] (mileage_kmpl computed)
### POST /api/vehicles/{id}/fuel
```json
{ "date": null, "odometer_km": 10500, "liters": 30, "cost": 9000, "full_tank": true }
```
→ `201` FuelOut · `400` odometer below vehicle current

### GET /api/vehicles/{id}/fuel/stats
→ `200`
```json
{
  "total_liters": 90.0, "total_cost": 27000.0,
  "avg_price_per_liter": 300.0, "avg_mileage_kmpl": 16.67,
  "last_mileage_kmpl": 16.67, "fillup_count": 3, "cost_per_km": 18.0
}
```

### DELETE /api/vehicles/{id}/fuel/{fillup_id} → `204`

---

## Public share (no auth)

### GET /api/public/vehicles/{share_token}
→ `200`
```json
{
  "vehicle": { "id": 1, "name": "City 2019", "year": 2019, "plate": "ABC-123",
               "fuel_type": "petrol", "odometer_km": 10500,
               "share_token": "...", "share_enabled": true, "created_at": "..." },
  "services": [ { "service_type": "oil", "custom_name": null, "date": "...",
                  "odometer_km": 10500, "cost": 4500, "notes": null } ],
  "total_service_cost": 4500, "service_count": 1, "last_service": "..."
}
```
`404` when sharing is disabled or the token is unknown.

---

## Health

### GET /api/health → `200` `{ "status": "ok", "service": "gaadi", "version": "1.0.0" }`

## Error format

All errors: `{ "detail": "human readable message" }` with appropriate status
(`400` bad input, `401` auth, `404` not found, `409` conflict, `422`
validation, `429` rate limit).
