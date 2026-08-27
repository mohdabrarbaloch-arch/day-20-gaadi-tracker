# 🚗 Gaadi — Vehicle Maintenance & Fuel Tracker

> Never miss an oil change again. Track maintenance schedules, fuel mileage and service history — and share a clean report when it's time to sell.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)](https://www.sqlalchemy.org)
[![Tests](https://img.shields.io/badge/tests-39%20passed-22c55e)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Gaadi (گاڑی)** is a full-stack vehicle maintenance & fuel tracker built for
Pakistani roads — but useful anywhere. Add your car or bike, log services and
fuel fill-ups, and Gaadi tells you exactly what's due and when: oil changes,
tire rotations, brake inspections, general service. It tracks your real fuel
mileage (km/L) from full-tank fill-ups, shows what you're spending per km,
and gives you a shareable maintenance report for resale.

Built in a day as **Day 20** of the *Autonomous AI Software Engineer – 30 Day Challenge*.

---

## ✨ Features

- **🧠 Maintenance scheduler** — predicts the next service for every type
  using km + day intervals (oil 5000km/90d, tires 10000km/180d,
  brakes 20000km/365d, general 10000km/180d, all configurable via env)
- **⛽ Fuel & mileage analytics** — km/L computed between consecutive full-tank
  fill-ups; avg price/L, last km/L, cost-per-km
- **📋 Service history** — every service logged with odometer, cost, notes
- **🔗 Shareable report** — one toggle, public URL with the full service
  history — perfect for resale or a trusted mechanic
- **🔐 JWT auth + bcrypt** — accounts, per-user vehicle isolation
- **📱 Mobile-first dark SPA** — zero build step, works on any phone
- **🐳 Docker-ready** — SQLite for dev, PostgreSQL 16 in compose

## 🛠️ Tech stack

| Layer      | Technology |
|------------|------------|
| Backend    | Python 3.11 · FastAPI · SQLAlchemy 2.0 · Pydantic v2 |
| Auth       | JWT (HS256) · bcrypt (12 rounds) · SlowAPI rate limits |
| Database   | SQLite (dev) · PostgreSQL 16 (docker-compose) |
| Frontend   | Vanilla JS · mobile-first dark SPA · no build step |
| Infra      | Docker · docker-compose · Vercel-ready serverless |

## 🖼️ Screenshots

| Dashboard | Vehicles | Vehicle detail |
|-----------|----------|----------------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Vehicles](docs/screenshots/vehicles_filled.png) | ![Vehicle](docs/screenshots/vehicle.png) |

*Captured from the running app: dark mobile-first UI, maintenance schedule, fuel mileage and service history.*

## 🚀 Live demo

Deployment is pending a Vercel account connection. The app is **fully
deploy-ready** — see [Deployment](#deployment). Run it locally in two commands
below.

## 📦 Installation

### Quick start (Docker)

```bash
docker compose up --build
# → http://localhost:8000
```

### Manual (local dev)

```bash
# 1. clone & enter
git clone https://github.com/mohdabrarbaloch-arch/day-20-gaadi-tracker.git
cd day-20-gaadi-tracker

# 2. virtualenv + deps
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. env
cp .env.example .env   # default = SQLite, works out of the box

# 4. run
uvicorn app.main:app --reload
# → http://localhost:8000
```

## 🧪 Tests

```bash
pytest -q   # 39 tests: auth, vehicles, scheduler engine, fuel engine, share
```

## 🔌 API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account (JWT returned) |
| POST | `/api/auth/login` | Log in |
| GET | `/api/auth/me` | Current user |
| GET/POST | `/api/vehicles` | List / create vehicles |
| GET/PATCH/DELETE | `/api/vehicles/{id}` | Vehicle detail / update / delete |
| PUT | `/api/vehicles/{id}/share` | Toggle public report |
| GET/POST | `/api/vehicles/{id}/services` | List / add service records |
| GET | `/api/vehicles/{id}/schedule` | Maintenance predictions |
| GET | `/api/vehicles/{id}/schedule/alert-count` | Overdue count |
| GET/POST | `/api/vehicles/{id}/fuel` | List / add fill-ups |
| GET | `/api/vehicles/{id}/fuel/stats` | Fuel analytics |
| GET | `/api/public/vehicles/{token}` | Public share report |
| GET | `/api/health` | Health check |

Full reference in [docs/api.md](docs/api.md).

## 🚀 Deployment

**Vercel** (serverless):
```bash
vercel login
vercel --prod
```
The repo ships `vercel.json` + `api/index.py`; the SPA and API serve from
one deployment. For SQLite on Vercel, mount `/tmp` (ephemeral) or point
`DATABASE_URL` at a hosted Postgres.

**Docker / VPS**:
```bash
docker compose up --build -d
```

## 📁 Project structure

```
app/
  main.py            # FastAPI app, middleware, SPA fallback
  config.py          # env settings
  database.py        # engine/session (SQLite WAL → Postgres)
  models.py          # SQLAlchemy models
  schemas.py         # Pydantic v2 schemas
  security.py        # bcrypt + JWT
  deps.py            # auth/ownership dependencies
  services/
    scheduler.py     # maintenance prediction engine
    fuel.py          # mileage analytics engine
  routers/
    auth.py vehicles.py services.py fuel.py share.py
public/              # vanilla JS SPA (index.html, app.js, style.css)
tests/               # 39 pytest tests
api/index.py         # Vercel serverless entry
Dockerfile  docker-compose.yml  vercel.json
```

## 📄 License

MIT — see [LICENSE](LICENSE).

---

*Built by ABraz Baloch · Day 20 of the 30-day build challenge.*
