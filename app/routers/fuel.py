"""Fuel fill-up routes + mileage analytics."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_owned_vehicle
from ..models import FuelFillup, Vehicle
from ..schemas import FuelIn, FuelOut, FuelStats
from ..services.fuel import compute_mileage

router = APIRouter(prefix="/api/vehicles/{vehicle_id}", tags=["fuel"])


def _fetch_fillups(db: Session, vehicle_id: int) -> list[FuelFillup]:
    return (
        db.query(FuelFillup)
        .filter(FuelFillup.vehicle_id == vehicle_id)
        .order_by(FuelFillup.date.desc())
        .all()
    )


@router.get("/fuel", response_model=list[FuelOut])
def list_fillups(
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    """All fill-ups, with per-fillup mileage computed against the previous full tank."""
    fillups = _fetch_fillups(db, vehicle.id)
    stats = compute_mileage(fillups)
    mileage_map = stats["mileage_by_id"]
    out: list[FuelOut] = []
    for f in fillups:
        item = FuelOut.model_validate(f).model_dump()
        item["mileage_kmpl"] = mileage_map.get(f.id)
        out.append(FuelOut(**item))
    out.sort(key=lambda x: x.date, reverse=True)
    return out


@router.post("/fuel", response_model=FuelOut, status_code=status.HTTP_201_CREATED)
def add_fillup(
    payload: FuelIn,
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    """Log a fuel purchase. full_tank=true enables mileage calculation."""
    if payload.odometer_km < vehicle.odometer_km:
        raise HTTPException(
            status_code=400,
            detail="Fill-up odometer can't be less than the vehicle's current odometer",
        )
    fillup = FuelFillup(
        vehicle_id=vehicle.id,
        date=payload.date,
        odometer_km=payload.odometer_km,
        liters=payload.liters,
        cost=payload.cost,
        full_tank=payload.full_tank,
    )
    db.add(fillup)
    vehicle.odometer_km = max(vehicle.odometer_km, payload.odometer_km)
    db.commit()
    db.refresh(fillup)

    fillups = _fetch_fillups(db, vehicle.id)
    mileage_map = compute_mileage(fillups)["mileage_by_id"]
    item = FuelOut.model_validate(fillup).model_dump()
    item["mileage_kmpl"] = mileage_map.get(fillup.id)
    return FuelOut(**item)


@router.get("/fuel/stats", response_model=FuelStats)
def fuel_stats(
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    fillups = _fetch_fillups(db, vehicle.id)
    s = compute_mileage(fillups)
    return FuelStats(
        total_liters=s["total_liters"],
        total_cost=s["total_cost"],
        avg_price_per_liter=s["avg_price_per_liter"],
        avg_mileage_kmpl=s["avg_mileage_kmpl"],
        last_mileage_kmpl=s["last_mileage_kmpl"],
        fillup_count=s["fillup_count"],
        cost_per_km=s["cost_per_km"],
    )


@router.delete("/fuel/{fillup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_fillup(
    fillup_id: int,
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    fillup = db.get(FuelFillup, fillup_id)
    if fillup is None or fillup.vehicle_id != vehicle.id:
        raise HTTPException(status_code=404, detail="Fill-up not found")
    db.delete(fillup)
    db.commit()
