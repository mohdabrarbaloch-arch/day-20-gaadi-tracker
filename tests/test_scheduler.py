"""Maintenance scheduler engine tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models import ServiceRecord, Vehicle
from app.services.scheduler import due_alert_count, schedule_for_vehicle


def _vehicle(odometer=10000, created_days_ago=60):
    v = Vehicle(
        owner_id=1,
        name="City",
        make="Honda",
        model="City",
        year=2019,
        plate="ABC-123",
        odometer_km=odometer,
        share_token="tok",
    )
    v.created_at = datetime.now(UTC) - timedelta(days=created_days_ago)
    return v


def _service(service_type, odometer, days_ago, cost=1000):
    s = ServiceRecord(
        vehicle_id=1,
        service_type=service_type,
        odometer_km=odometer,
        cost=cost,
    )
    s.date = datetime.now(UTC) - timedelta(days=days_ago)
    return s


def test_new_vehicle_baseline_from_creation(client):
    # No services yet → baseline = vehicle odometer & creation date.
    # Default oil interval is 5000 km / 90 days.
    v = _vehicle(odometer=1000, created_days_ago=10)
    items = schedule_for_vehicle(v, [])
    oil = next(i for i in items if i.service_type == "oil")
    assert oil.due_km == 6000
    assert oil.overdue is False
    assert oil.reason == "On schedule"


def test_km_based_overdue_detection(client):
    # Oil changed at 5000 km, 10 days ago; vehicle now at 11000 km → overdue by 1000 km
    v = _vehicle(odometer=11000, created_days_ago=400)
    s = _service("oil", 5000, 10)
    items = schedule_for_vehicle(v, [s])
    oil = next(i for i in items if i.service_type == "oil")
    assert oil.overdue is True
    assert oil.km_remaining == -1000.0  # 1000 km past the due point
    assert "Overdue by 1000 km" in oil.reason


def test_days_based_overdue_detection(client):
    # Oil changed 100 days ago (interval 90 days) → overdue by days even at low km
    v = _vehicle(odometer=6000, created_days_ago=400)
    s = _service("oil", 5000, 100)
    items = schedule_for_vehicle(v, [s])
    oil = next(i for i in items if i.service_type == "oil")
    assert oil.overdue is True
    assert "day(s)" in oil.reason


def test_upcoming_window_flags_soon(client):
    # 500 km before the 5000 km interval = inside the 15% window
    v = _vehicle(odometer=9500, created_days_ago=400)
    s = _service("oil", 5000, 10)
    items = schedule_for_vehicle(v, [s])
    oil = next(i for i in items if i.service_type == "oil")
    assert oil.overdue is False
    assert oil.reason == "Coming up soon — plan this service"


def test_most_recent_record_wins(client):
    v = _vehicle(odometer=9000, created_days_ago=400)
    old = _service("oil", 5000, 200)
    recent = _service("oil", 7000, 20)
    items = schedule_for_vehicle(v, [old, recent])
    oil = next(i for i in items if i.service_type == "oil")
    assert oil.last_km == 7000
    assert oil.due_km == 12000


def test_due_alert_count(client):
    v = _vehicle(odometer=20000, created_days_ago=400)
    items = schedule_for_vehicle(v, [_service("oil", 5000, 200)])
    assert due_alert_count(items) >= 1


def test_all_types_present(client):
    v = _vehicle()
    items = schedule_for_vehicle(v, [])
    types = {i.service_type for i in items}
    assert {"oil", "tires", "brakes", "general"} <= types
