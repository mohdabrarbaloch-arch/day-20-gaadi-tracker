# Gaadi — Architecture

**Gaadi (گاڑی)** is a vehicle maintenance & fuel tracker. Users add vehicles,
log services and fuel fill-ups, and get automatic maintenance predictions
(oil change, tire rotation, brake inspection, general service) based on
km + day intervals. A public share link documents a vehicle's full service
history for resale.

## System diagram

```
┌────────────────────────┐        ┌──────────────────────────────────┐
│   Browser (mobile-first    │        │         FastAPI app          │
│   vanilla JS SPA)          │  JSON  │  ┌─────────────────────────┐  │
│  /  auth / dashboard       │ ──────► │  │ Routers               │  │
│  /vehicles /vehicle/:id    │  ◄────── │  │  auth   vehicles      │  │
│  /share/:token (public)    │        │  │  services  fuel  share │  │
└────────────────────────┘        │  └─────────┬─────────────┘  │
                                      │             │                │
                                      │  ┌──────────▼───────────┐  │
                                      │  │ Engines                │  │
                                      │  │  scheduler.py (due     │  │
                                      │  │   km/date prediction)  │  │
                                      │  │  fuel.py (km/L from    │  │
                                      │  │   full-tank pairs)     │  │
                                      │  └──────────┬───────────┘  │
                                      │             │ SQLAlchemy 2.0 │
                                      │  ┌──────────▼───────────┐  │
                                      │  │ SQLite (dev) /         │  │
                                      │  │ PostgreSQL 16 (prod)   │  │
                                      │  └──────────────────────┘  │
                                      └──────────────────────────┘
```

## Tech stack

| Layer      | Choice                                            |
|------------|---------------------------------------------------|
| Backend    | Python 3.11 · FastAPI 0.115 · Pydantic v2         |
| ORM        | SQLAlchemy 2.0 (typed models, WAL for SQLite)     |
| Auth       | JWT (HS256, 24h) + bcrypt (12 rounds)             |
| Rate limit | SlowAPI (5/min register, 10/min login)            |
| Database   | SQLite (dev) → PostgreSQL 16 (docker-compose)     |
| Frontend   | Vanilla JS SPA, mobile-first dark UI, no build    |
| Infra      | Docker · docker-compose · Vercel-ready serverless |

## Data model

- **users** — email (unique), name, bcrypt hash, created_at
- **vehicles** — owner FK, name/make/model/year/plate/fuel_type,
  odometer_km, share_token (unique), share_enabled
- **service_records** — vehicle FK, service_type (interval key or custom),
  custom_name, date, odometer_km, cost, notes
- **fuel_fillups** — vehicle FK, date, odometer_km, liters, cost, full_tank

## Key flows

### Maintenance scheduling
Intervals come from env (`MAINTENANCE_INTERVALS`, default oil 5000km/90d,
tires 10000km/180d, brakes 20000km/365d, general 10000km/180d). For each
type, the scheduler takes the **most recent** service record of that type as
the baseline (odometer + date), adds the interval, and compares against the
vehicle's current odometer and today. It returns `due_km`, `due_date`,
`km_remaining` (negative = overdue), `days_remaining`, and a human reason.
If no record exists yet, the baseline is the vehicle's creation odometer
and date — so a brand-new car with no services shows "on schedule" until
its first interval passes.

### Fuel mileage
Mileage (km/L) is only computed between **consecutive full-tank** fill-ups:
distance ÷ liters. Partial fill-ups count in totals but never in mileage.
Aggregates: total liters/cost, avg price/L, avg & last km/L, cost/km over
the full-tank span.

### Public share
`PUT /api/vehicles/:id/share {enabled:true}` turns on a public report at
`/api/public/vehicles/{share_token}` (and `/#/share/{token}` in the SPA).
The report exposes vehicle basics + the full service history, without
requiring auth. It 404s when disabled or the token is unknown.

## Security

- JWT in `Authorization: Bearer` header; 24h expiry
- bcrypt with 12 rounds; no plaintext storage
- Ownership checks via `get_owned_vehicle` — foreign vehicles return 404
  (no existence leak)
- SlowAPI rate limits on register/login
- CORS allow-list (env), Pydantic validation on every input
- Secrets only via env (`.env.example` documents all)
- No API keys, no hardcoded credentials

## Scaling notes

- **PostgreSQL** via `DATABASE_URL` — used in docker-compose; SQLite WAL
  is fine for single-user dev
- Read-heavy share links can be cached (Redis/CDN) later; the report query
  is a single indexed lookup on `share_token`
- Adding a queue worker (Celery/RQ) would let service-due alerts email users
  on a schedule; the scheduler engine is pure and testable, so it drops in
  cleanly
- The SPA is static — it can be served from any CDN; API stays separate
