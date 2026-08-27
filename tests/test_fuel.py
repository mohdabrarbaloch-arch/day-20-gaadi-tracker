"""Fuel mileage analytics tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.models import FuelFillup
from app.services.fuel import compute_mileage


def _fillup(odometer, liters, cost, days_ago=0, full=True):
    f = FuelFillup(
        vehicle_id=1,
        odometer_km=odometer,
        liters=liters,
        cost=cost,
        full_tank=full,
    )
    f.date = datetime.now(UTC) - timedelta(days=days_ago)
    return f


def test_mileage_between_full_fills(client):
    f1 = _fillup(10000, 30, 9000, days_ago=10)
    f2 = _fillup(10500, 30, 9000, days_ago=1)
    stats = compute_mileage([f1, f2])
    # 500 km / 30 L = 16.67 km/L
    assert stats["mileage_by_id"][f2.id] == 16.67
    assert stats["avg_mileage_kmpl"] == 16.67
    assert stats["last_mileage_kmpl"] == 16.67


def test_partial_fillups_ignored_for_mileage(client):
    f1 = _fillup(10000, 30, 9000, days_ago=10)
    partial = _fillup(10200, 10, 3000, days_ago=5, full=False)
    f2 = _fillup(10500, 30, 9000, days_ago=1)
    stats = compute_mileage([f1, partial, f2])
    # ids are None for unsaved objects — compare by odometer instead
    entries = {stats["mileage_by_id"].get(f.id): f.odometer_km for f in [f1, partial, f2]}
    assert 10500 in [v for k, v in entries.items() if k is not None]
    assert partial.odometer_km not in [v for k, v in entries.items() if k is not None]
    assert stats["avg_mileage_kmpl"] == 16.67


def test_totals_include_partial(client):
    f1 = _fillup(10000, 30, 9000)
    p = _fillup(10200, 10, 3000, full=False)
    stats = compute_mileage([f1, p])
    assert stats["total_liters"] == 40
    assert stats["total_cost"] == 12000
    assert stats["avg_price_per_liter"] == 300.0


def test_no_mileage_with_single_fill(client):
    stats = compute_mileage([_fillup(10000, 30, 9000)])
    assert stats["avg_mileage_kmpl"] is None
    assert stats["last_mileage_kmpl"] is None
    assert stats["mileage_by_id"] == {}


def test_no_mileage_with_decreasing_odometer(client):
    f1 = _fillup(11000, 30, 9000, days_ago=5)
    f2 = _fillup(10500, 30, 9000)  # odometer went backwards — ignore
    stats = compute_mileage([f1, f2])
    assert f2.id not in stats["mileage_by_id"]


def test_cost_per_km(client):
    f1 = _fillup(10000, 30, 9000, days_ago=10)
    f2 = _fillup(10500, 30, 9000, days_ago=1)
    stats = compute_mileage([f1, f2])
    # span 500 km, cost 18000 → 36 Rs/km
    assert stats["cost_per_km"] == 36.0


def test_empty_fillups(client):
    stats = compute_mileage([])
    assert stats["total_liters"] == 0
    assert stats["fillup_count"] == 0
