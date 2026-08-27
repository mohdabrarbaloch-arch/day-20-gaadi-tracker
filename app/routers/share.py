"""Public share routes — no auth, but only for vehicles with sharing enabled."""

from fastapi import APIRouter, HTTPException

from ..database import SessionLocal
from ..models import ServiceRecord, Vehicle
from ..schemas import PublicVehicleOut, SharedService, ShareReport

router = APIRouter(prefix="/api/public", tags=["public"])


@router.get("/vehicles/{share_token}", response_model=ShareReport)
def shared_report(share_token: str):
    """Return a public maintenance report for a shared vehicle.

    Falls back to 404 if sharing is disabled or the token is unknown.
    """
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).filter(Vehicle.share_token == share_token).first()
        if vehicle is None or not vehicle.share_enabled:
            raise HTTPException(status_code=404, detail="Report not found or sharing disabled")

        services = (
            db.query(ServiceRecord)
            .filter(ServiceRecord.vehicle_id == vehicle.id)
            .order_by(ServiceRecord.date.desc())
            .all()
        )

        shared_services = [
            SharedService(
                service_type=s.service_type,
                custom_name=s.custom_name,
                date=s.date,
                odometer_km=s.odometer_km,
                cost=s.cost,
                notes=s.notes,
            )
            for s in services
        ]

        return ShareReport(
            vehicle=PublicVehicleOut.model_validate(vehicle),
            services=shared_services,
            total_service_cost=round(sum(s.cost for s in services), 2),
            service_count=len(services),
            last_service=max((s.date for s in services), default=None),
        )
    finally:
        db.close()
