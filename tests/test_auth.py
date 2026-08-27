"""Auth tests: registration, login, password hashing, JWT."""

from __future__ import annotations

from tests.conftest import auth_headers, register


def test_register_success(client):
    r = register(client, email="ali@test.pk")
    assert r.status_code == 201
    data = r.json()
    assert data["access_token"]
    assert data["user"]["email"] == "ali@test.pk"
    assert data["user"]["name"] == "Ali"


def test_register_duplicate_email_conflict(client):
    register(client, email="dup@test.pk")
    r = register(client, email="dup@test.pk")
    assert r.status_code == 409


def test_register_rejects_short_password(client):
    r = register(client, password="short")
    assert r.status_code == 422


def test_login_success(client):
    register(client, email="login@test.pk")
    r = client.post("/api/auth/login", json={"email": "login@test.pk", "password": "password123"})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_wrong_password_rejected(client):
    register(client, email="login@test.pk")
    r = client.post("/api/auth/login", json={"email": "login@test.pk", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_unknown_email_rejected(client):
    r = client.post("/api/auth/login", json={"email": "nobody@test.pk", "password": "password123"})
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_returns_user(client):
    reg = register(client, email="me@test.pk")
    r = client.get("/api/auth/me", headers=auth_headers(reg))
    assert r.status_code == 200
    assert r.json()["email"] == "me@test.pk"
