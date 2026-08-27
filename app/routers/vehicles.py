"""Vehicle routes: CRUD + share token management."""

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_owned_vehicle
from ..models import User, Vehicle
from ..schemas import ShareToggle, VehicleIn, VehicleOut, VehicleUpdate

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


def _new_share_token(db: Session) -> str:
    while True:
        token = secrets.token_urlsafe(12)
        exists = db.query(Vehicle).filter(Vehicle.share_token == token).first()
        if not exists:
            return token


@router.get("", response_model=list[VehicleOut])
def list_vehicles(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """All vehicles owned by the current user, newest first."""
    return (
        db.query(Vehicle)
        .filter(Vehicle.owner_id == user.id)
        .order_by(Vehicle.created_at.desc())
        .all()
    )


@router.post("", response_model=VehicleOut, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    payload: VehicleIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a vehicle. Max 10 per account (keeps abuse low)."""
    count = db.query(Vehicle).filter(Vehicle.owner_id == user.id).count()
    if count >= 10:
        raise HTTPException(status_code=400, detail="Vehicle limit reached (10 per account)")

    vehicle = Vehicle(
        owner_id=user.id,
        name=payload.name,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        plate=payload.plate.upper(),
        fuel_type=payload.fuel_type,
        odometer_km=payload.odometer_km,
        share_token=_new_share_token(db),
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle: Vehicle = Depends(get_owned_vehicle)):
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    payload: VehicleUpdate,
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    """Update name / plate / odometer / fuel type."""
    data = payload.model_dump(exclude_unset=True)
    if data.get("plate"):
        data["plate"] = data["plate"].upper()
    for key, value in data.items():
        setattr(vehicle, key, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.put("/{vehicle_id}/share", response_model=VehicleOut)
def toggle_share(
    payload: ShareToggle,
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    """Turn the public maintenance report on/off for this vehicle."""
    vehicle.share_enabled = payload.enabled
    db.commit()
    db.refresh(vehicle)
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    db.delete(vehicle)
    db.commit()
