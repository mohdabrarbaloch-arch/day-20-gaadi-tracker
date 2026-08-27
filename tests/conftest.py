"""Shared test fixtures — isolated SQLite DB per test."""

from __future__ import annotations

import os
import sys
import tempfile
import uuid

import pytest
from fastapi.testclient import TestClient

# Use a throwaway SQLite DB before importing the app
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ["SECRET_KEY"] = "test-secret-key-0123456789abcdef0123456789abcdef"
os.environ["CORS_ORIGINS"] = "http://localhost"
os.environ["RATELIMIT_ENABLED"] = "false"  # slowapi app-config key to keep limits off

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine
from app.main import app

# Disable rate limiting during tests — the decorators hold the module-level
# limiter instance, so poke it directly (app.state may be re-created).
from app.main import limiter as _app_limiter

_app_limiter.enabled = False
app.state.limiter = _app_limiter

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


@pytest.fixture()
def client():
    # Disable rate limiting per-client — TestClient re-creates app state on enter
    app.state.limiter.enabled = False
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db():
    # Reset the database BEFORE every test, guaranteeing isolation
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def register(
    client: TestClient,
    email: str | None = None,
    password: str = "password123",
    name: str = "Ali",
):
    """Register a user. Generates a unique email unless one is given."""
    email = email or f"user{uuid.uuid4().hex[:10]}@test.pk"
    return client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": password},
    )


def auth_headers(resp) -> dict:
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def make_vehicle(client, token, **overrides):
    body = {
        "name": "City 2019",
        "make": "Honda",
        "model": "City",
        "year": 2019,
        "plate": "ABC-123",
        "fuel_type": "petrol",
        "odometer_km": 10000,
    }
    body.update(overrides)
    return client.post("/api/vehicles", json=body, headers=token)
