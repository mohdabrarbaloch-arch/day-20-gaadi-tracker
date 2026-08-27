# Setup Guide

## Prerequisites

- Python 3.11+
- pip
- (optional) Docker + Docker Compose
- (optional) Node.js only if you want to use `npx vercel` for deployment

## 1. Local development (SQLite)

```bash
git clone https://github.com/mohdabrarbaloch-arch/day-20-gaadi-tracker.git
cd day-20-gaadi-tracker

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # SQLite default — works immediately
uvicorn app.main:app --reload
```

Open http://localhost:8000 — the SPA loads at `/`, API docs at `/docs`.

## 2. Docker (PostgreSQL)

```bash
docker compose up --build
```

The compose file runs the API + a PostgreSQL 16 database. The app uses
`DATABASE_URL=postgresql+psycopg2://gaadi:gaadi@db:5432/gaadi` automatically.

## 3. Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-insecure-change-me` | JWT signing secret — **generate a long random one** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT lifetime in minutes |
| `DATABASE_URL` | `sqlite:///./gaadi.db` | SQLAlchemy connection string |
| `CORS_ORIGINS` | `http://localhost:8000,...` | Comma-separated allowed origins |
| `MAINTENANCE_INTERVALS` | built-in defaults | Comma-separated `key=Name:km:days` |

Generate a secret: `python -c "import secrets; print(secrets.token_hex(32))"`

## 4. Verification

```bash
pytest -q                          # 39 tests
ruff check . && ruff format .      # lint + format
python -c "from app.main import app; print('import ok')"
```

## 5. Troubleshooting

- **SQLite "database is locked"** — the app enables WAL mode; if you see this
  under heavy load, switch to PostgreSQL.
- **Register returns 429** — rate limit (5/min per IP). Wait a minute or run
  via `localhost` in dev.
- **Frontend 404 on refresh** — served by the SPA fallback at `/{full_path}`;
  the API returns proper 404s for unknown `/api/*` routes.
