"""Service record API + public share endpoint tests."""

from __future__ import annotations

from tests.conftest import auth_headers, make_vehicle, register


def test_add_service_flow(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg)).json()

    r = client.post(
        f"/api/vehicles/{v['id']}/services",
        json={
            "service_type": "oil",
            "odometer_km": 10500,
            "cost": 4500,
            "notes": "Mobil 1",
        },
        headers=auth_headers(reg),
    )
    assert r.status_code == 201
    assert r.json()["service_type"] == "oil"


def test_service_bumps_odometer(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg), odometer_km=10000).json()

    client.post(
        f"/api/vehicles/{v['id']}/services",
        json={"service_type": "oil", "odometer_km": 12000, "cost": 5000},
        headers=auth_headers(reg),
    )
    updated = client.get(f"/api/vehicles/{v['id']}", headers=auth_headers(reg)).json()
    assert updated["odometer_km"] == 12000


def test_service_odometer_not_below_current(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg), odometer_km=10000).json()
    r = client.post(
        f"/api/vehicles/{v['id']}/services",
        json={"service_type": "oil", "odometer_km": 9000, "cost": 100},
        headers=auth_headers(reg),
    )
    assert r.status_code == 400


def test_schedule_endpoint_shape(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg)).json()
    r = client.get(f"/api/vehicles/{v['id']}/schedule", headers=auth_headers(reg))
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 4
    assert all("due_km" in i and "overdue" in i for i in items)


def test_alert_count_endpoint(client):
    # Vehicle serviced at 10k, now at 25k → past the 5k oil interval → overdue
    reg = register(client, email="alert@test.pk")
    v = make_vehicle(client, auth_headers(reg), odometer_km=10000).json()
    client.post(
        f"/api/vehicles/{v['id']}/services",
        json={"service_type": "oil", "odometer_km": 10000, "cost": 4000},
        headers=auth_headers(reg),
    )
    client.patch(
        f"/api/vehicles/{v['id']}",
        json={"odometer_km": 25000},
        headers=auth_headers(reg),
    )
    r = client.get(f"/api/vehicles/{v['id']}/schedule/alert-count", headers=auth_headers(reg))
    assert r.status_code == 200
    assert r.json()["overdue"] >= 1


def test_shared_report_disabled_by_default(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg)).json()
    r = client.get(f"/api/public/vehicles/{v['share_token']}")
    assert r.status_code == 404


def test_shared_report_enabled(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg)).json()
    client.put(
        f"/api/vehicles/{v['id']}/share",
        json={"enabled": True},
        headers=auth_headers(reg),
    )

    client.post(
        f"/api/vehicles/{v['id']}/services",
        json={"service_type": "oil", "odometer_km": 10500, "cost": 4500},
        headers=auth_headers(reg),
    )

    r = client.get(f"/api/public/vehicles/{v['share_token']}")
    assert r.status_code == 200
    data = r.json()
    assert data["vehicle"]["plate"] == "ABC-123"
    assert data["service_count"] == 1
    assert data["total_service_cost"] == 4500


def test_unknown_share_token_404(client):
    assert client.get("/api/public/vehicles/nope-nope-nope").status_code == 404


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
