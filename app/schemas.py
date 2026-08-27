"""Pydantic v2 request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── User ──────────────────────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Vehicle ───────────────────────────────────────────────────────
class VehicleIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    make: str = Field(min_length=1, max_length=80)
    model: str = Field(min_length=1, max_length=80)
    year: int = Field(ge=1950, le=2100)
    plate: str = Field(min_length=2, max_length=20)
    fuel_type: str = Field(default="petrol", pattern="^(petrol|diesel|CNG|electric)$")
    odometer_km: float = Field(default=0.0, ge=0)

    @field_validator("name", "make", "model", "plate")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class VehicleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    plate: str | None = Field(default=None, min_length=2, max_length=20)
    odometer_km: float | None = Field(default=None, ge=0)
    fuel_type: str | None = Field(default=None, pattern="^(petrol|diesel|CNG|electric)$")


class ShareToggle(BaseModel):
    enabled: bool


class VehicleOut(BaseModel):
    id: int
    name: str
    make: str
    model: str
    year: int
    plate: str
    fuel_type: str
    odometer_km: float
    share_token: str
    share_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceDue(BaseModel):
    service_type: str
    name: str
    last_km: float | None = None
    last_date: datetime | None = None
    due_km: float | None = None
    due_date: datetime | None = None
    km_remaining: float | None = None
    days_remaining: int | None = None
    overdue: bool = False
    reason: str


# ── Service records ───────────────────────────────────────────────
class ServiceIn(BaseModel):
    service_type: str = Field(min_length=1, max_length=50)
    custom_name: str | None = Field(default=None, max_length=120)
    date: datetime | None = None
    odometer_km: float = Field(ge=0)
    cost: float = Field(default=0.0, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


class ServiceOut(BaseModel):
    id: int
    service_type: str
    custom_name: str | None
    date: datetime
    odometer_km: float
    cost: float
    notes: str | None

    model_config = {"from_attributes": True}


# ── Fuel ──────────────────────────────────────────────────────────
class FuelIn(BaseModel):
    date: datetime | None = None
    odometer_km: float = Field(ge=0)
    liters: float = Field(gt=0, le=500)
    cost: float = Field(ge=0)
    full_tank: bool = True


class FuelOut(BaseModel):
    id: int
    date: datetime
    odometer_km: float
    liters: float
    cost: float
    full_tank: bool
    mileage_kmpl: float | None = None  # computed vs previous full fill

    model_config = {"from_attributes": True}


class FuelStats(BaseModel):
    total_liters: float
    total_cost: float
    avg_price_per_liter: float
    avg_mileage_kmpl: float | None
    last_mileage_kmpl: float | None
    fillup_count: int
    cost_per_km: float | None


# ── Public share ──────────────────────────────────────────────────
class SharedService(BaseModel):
    service_type: str
    custom_name: str | None
    date: datetime
    odometer_km: float
    cost: float
    notes: str | None


class ShareReport(BaseModel):
    vehicle: PublicVehicleOut
    services: list[SharedService]
    total_service_cost: float
    service_count: int
    last_service: datetime | None


class PublicVehicleOut(BaseModel):
    id: int
    name: str
    year: int
    plate: str
    fuel_type: str
    odometer_km: float
    share_token: str
    share_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


TokenOut.model_rebuild()
