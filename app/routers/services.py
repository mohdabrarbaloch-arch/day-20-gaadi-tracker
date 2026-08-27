"""Service-record routes + the maintenance schedule endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_owned_vehicle
from ..models import ServiceRecord, Vehicle
from ..schemas import ServiceDue, ServiceIn, ServiceOut
from ..services.scheduler import due_alert_count, schedule_for_vehicle

router = APIRouter(prefix="/api/vehicles/{vehicle_id}", tags=["services"])


def _fetch_services(db: Session, vehicle_id: int) -> list[ServiceRecord]:
    return (
        db.query(ServiceRecord)
        .filter(ServiceRecord.vehicle_id == vehicle_id)
        .order_by(ServiceRecord.date.desc())
        .all()
    )


@router.get("/services", response_model=list[ServiceOut])
def list_services(
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    return _fetch_services(db, vehicle.id)


@router.post("/services", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def add_service(
    payload: ServiceIn,
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    """Record a completed service (oil change, tire rotation, ...)."""
    if payload.odometer_km < vehicle.odometer_km:
        raise HTTPException(
            status_code=400,
            detail="Service odometer can't be less than the vehicle's current odometer",
        )
    record = ServiceRecord(
        vehicle_id=vehicle.id,
        service_type=payload.service_type.strip().lower(),
        custom_name=payload.custom_name.strip() if payload.custom_name else None,
        date=payload.date,
        odometer_km=payload.odometer_km,
        cost=payload.cost,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(record)

    # bump the vehicle odometer if this record shows a higher reading
    vehicle.odometer_km = max(vehicle.odometer_km, payload.odometer_km)

    db.commit()
    db.refresh(record)
    return record


@router.get("/schedule", response_model=list[ServiceDue])
def get_schedule(
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    """Maintenance predictions for this vehicle (most urgent first)."""
    services = _fetch_services(db, vehicle.id)
    return schedule_for_vehicle(vehicle, services)


@router.get("/schedule/alert-count", response_model=dict)
def get_alert_count(
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    services = _fetch_services(db, vehicle.id)
    return {"overdue": due_alert_count(schedule_for_vehicle(vehicle, services))}


@router.delete("/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    vehicle: Vehicle = Depends(get_owned_vehicle),
    db: Session = Depends(get_db),
):
    record = db.get(ServiceRecord, service_id)
    if record is None or record.vehicle_id != vehicle.id:
        raise HTTPException(status_code=404, detail="Service record not found")
    db.delete(record)
    db.commit()
