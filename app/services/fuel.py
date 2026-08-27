"""Fuel mileage analytics engine.

Mileage (km per liter) is computed between two consecutive FULL-TANK
fill-ups: distance driven ÷ liters pumped. Partial fill-ups are
ignored for the calculation but counted in totals.
"""

from __future__ import annotations

from ..models import FuelFillup


def compute_mileage(fillups: list[FuelFillup]) -> dict:
    """Return per-fillup mileage + aggregate stats.

    Mutates nothing; returns a dict mapping fillup id -> kmpl, plus stats.
    """
    full_fills = sorted(
        [f for f in fillups if f.full_tank],
        key=lambda f: f.date,
    )

    mileage_by_id: dict[int, float] = {}
    for prev, curr in zip(full_fills, full_fills[1:], strict=False):
        distance = curr.odometer_km - prev.odometer_km
        if distance > 0 and curr.liters > 0:
            mileage_by_id[curr.id] = round(distance / curr.liters, 2)

    total_liters = sum(f.liters for f in fillups)
    total_cost = sum(f.cost for f in fillups)

    kmpl_values = list(mileage_by_id.values())
    avg_kmpl = round(sum(kmpl_values) / len(kmpl_values), 2) if kmpl_values else None
    last_kmpl = kmpl_values[-1] if kmpl_values else None

    # cost per km: only over full-tank pairs we can attribute
    cost_per_km = None
    if full_fills and full_fills[-1].odometer_km > full_fills[0].odometer_km:
        span_distance = full_fills[-1].odometer_km - full_fills[0].odometer_km
        span_cost = sum(f.cost for f in full_fills)
        if span_distance > 0:
            cost_per_km = round(span_cost / span_distance, 3)

    avg_price_per_liter = round(total_cost / total_liters, 2) if total_liters else 0.0

    return {
        "mileage_by_id": mileage_by_id,
        "total_liters": round(total_liters, 2),
        "total_cost": round(total_cost, 2),
        "avg_price_per_liter": avg_price_per_liter,
        "avg_mileage_kmpl": avg_kmpl,
        "last_mileage_kmpl": last_kmpl,
        "fillup_count": len(fillups),
        "cost_per_km": cost_per_km,
    }
