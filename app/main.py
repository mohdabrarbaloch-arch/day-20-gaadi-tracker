"""Gaadi — vehicle maintenance & fuel tracker.

FastAPI app entrypoint. Mounts routers, static SPA, and safety middleware.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from .config import settings
from .database import init_db
from .routers import auth, fuel, services, share, vehicles

limiter = Limiter(key_func=get_remote_address)

STATIC_DIR = Path(__file__).resolve().parent.parent / "public"
INDEX_FILE = STATIC_DIR / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Gaadi API",
    description="Vehicle maintenance scheduler & fuel mileage tracker",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── routers ───────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(services.router)
app.include_router(fuel.router)
app.include_router(share.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "gaadi", "version": "1.0.0"}


# ── SPA + static files (public/) ──────────────────────────────────
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        """Serve index.html for any non-API route (SPA fallback)."""
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        candidate = STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        if INDEX_FILE.exists():
            return FileResponse(INDEX_FILE)
        return JSONResponse(status_code=404, content={"detail": "Not found"})
else:

    @app.get("/", include_in_schema=False)
    def root():
        return {"detail": "Gaadi API is running. Frontend not built."}


# attach request param typing for slowapi decorators (used in routers)
Request  # noqa: B018 (kept for clarity)
