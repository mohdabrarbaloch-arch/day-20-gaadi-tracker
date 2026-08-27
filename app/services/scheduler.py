"""Maintenance scheduler engine.

Predicts the next service due date/odometer for each service type using
configured km + day intervals, based on the most recent service record
of that type (or the vehicle's birth/odometer if none exists yet).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ..config import settings
from ..models import ServiceRecord, Vehicle
from ..schemas import ServiceDue


def _is_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def schedule_for_vehicle(vehicle: Vehicle, services: list[ServiceRecord]) -> list[ServiceDue]:
    """Compute due items for every configured maintenance type."""
    due_items: list[ServiceDue] = []
    now = datetime.now(UTC)

    for key, interval in settings.MAINTENANCE_INTERVALS.items():
        km_interval: int = interval["km_interval"]
        days_interval: int = interval["days_interval"]
        name: str = interval["name"]

        # most recent record of this type (fall back to any service if none)
        matching = [s for s in services if s.service_type == key]
        if matching:
            last = max(matching, key=lambda s: _is_aware(s.date))
            base_km = last.odometer_km
            base_date = _is_aware(last.date)
        else:
            # no record yet — baseline is the vehicle's current state
            base_km = vehicle.odometer_km
            base_date = _is_aware(vehicle.created_at)

        due_km = base_km + km_interval
        due_date = base_date + timedelta(days=days_interval)
        # km_remaining: negative means we've passed the due km
        km_remaining = round(due_km - vehicle.odometer_km, 1)
        days_remaining = (due_date - now).days
        overdue = km_remaining <= 0 or days_remaining <= 0

        # explain why it's due, in a human way
        if km_remaining <= 0 and days_remaining <= 0:
            reason = f"Overdue by {abs(days_remaining)} day(s) and {int(abs(km_remaining))} km"
        elif km_remaining <= 0:
            reason = f"Overdue by {int(abs(km_remaining))} km"
        elif days_remaining <= 0:
            reason = f"Overdue by {abs(days_remaining)} day(s)"
        elif km_remaining < 0.15 * km_interval or days_remaining < max(
            1, int(0.15 * days_interval)
        ):
            reason = "Coming up soon — plan this service"
        else:
            reason = "On schedule"

        due_items.append(
            ServiceDue(
                service_type=key,
                name=name,
                last_km=base_km,
                last_date=base_date if matching else None,
                due_km=due_km,
                due_date=due_date,
                km_remaining=km_remaining,
                days_remaining=days_remaining,
                overdue=overdue,
                reason=reason,
            )
        )

    # most urgent first
    due_items.sort(key=lambda d: (d.overdue is False, d.due_date or now))
    return due_items


def due_alert_count(due_items: list[ServiceDue]) -> int:
    return sum(1 for d in due_items if d.overdue)
