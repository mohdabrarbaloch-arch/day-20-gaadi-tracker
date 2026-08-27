"""Vehicle CRUD + ownership tests."""

from __future__ import annotations

from tests.conftest import auth_headers, make_vehicle, register


def test_create_vehicle(client):
    reg = register(client)
    r = make_vehicle(client, auth_headers(reg))
    assert r.status_code == 201
    assert r.json()["plate"] == "ABC-123"


def test_create_vehicle_requires_auth(client):
    r = make_vehicle(client, {})
    assert r.status_code == 401


def test_list_vehicles_only_own(client):
    reg1 = register(client, email="a@test.pk")
    reg2 = register(client, email="b@test.pk")
    make_vehicle(client, auth_headers(reg1))
    make_vehicle(client, auth_headers(reg1), name="Second", plate="XYZ-999")
    make_vehicle(client, auth_headers(reg2), name="Other", plate="QWE-111")

    r = client.get("/api/vehicles", headers=auth_headers(reg1))
    assert r.status_code == 200
    names = [v["name"] for v in r.json()]
    assert names == ["Second", "City 2019"]  # newest first, only own


def test_foreign_vehicle_is_404(client):
    reg1 = register(client, email="a@test.pk")
    reg2 = register(client, email="b@test.pk")
    v = make_vehicle(client, auth_headers(reg1)).json()

    r = client.get(f"/api/vehicles/{v['id']}", headers=auth_headers(reg2))
    assert r.status_code == 404  # don't leak existence


def test_update_vehicle(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg)).json()
    r = client.patch(
        f"/api/vehicles/{v['id']}",
        json={"plate": "NEW-777", "odometer_km": 12500},
        headers=auth_headers(reg),
    )
    assert r.status_code == 200
    assert r.json()["plate"] == "NEW-777"
    assert r.json()["odometer_km"] == 12500


def test_delete_vehicle(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg)).json()
    r = client.delete(f"/api/vehicles/{v['id']}", headers=auth_headers(reg))
    assert r.status_code == 204
    assert client.get(f"/api/vehicles/{v['id']}", headers=auth_headers(reg)).status_code == 404


def test_vehicle_limit_ten(client):
    reg = register(client)
    h = auth_headers(reg)
    for i in range(10):
        make_vehicle(client, h, name=f"V{i}", plate=f"PL-{i:04d}")
    r = make_vehicle(client, h, name="TooMany", plate="OVER-99")
    assert r.status_code == 400


def test_share_toggle(client):
    reg = register(client)
    v = make_vehicle(client, auth_headers(reg)).json()
    r = client.put(
        f"/api/vehicles/{v['id']}/share",
        json={"enabled": True},
        headers=auth_headers(reg),
    )
    assert r.status_code == 200
    assert r.json()["share_enabled"] is True
