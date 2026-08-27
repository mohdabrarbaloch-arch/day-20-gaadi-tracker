"""SQLAlchemy ORM models for Gaadi."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    vehicles: Mapped[list[Vehicle]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)  # e.g. "Honda City 2019"
    make: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    plate: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    fuel_type: Mapped[str] = mapped_column(
        String(20), default="petrol"
    )  # petrol/diesel/CNG/electric
    odometer_km: Mapped[float] = mapped_column(Float, default=0.0)
    share_token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    share_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner: Mapped[User] = relationship(back_populates="vehicles")
    services: Mapped[list[ServiceRecord]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )
    fillups: Mapped[list[FuelFillup]] = relationship(
        back_populates="vehicle", cascade="all, delete-orphan"
    )


class ServiceRecord(Base):
    __tablename__ = "service_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    service_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    # ^ one of the interval keys (oil, tires, brakes, general) or custom
    custom_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    odometer_km: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    vehicle: Mapped[Vehicle] = relationship(back_populates="services")


class FuelFillup(Base):
    __tablename__ = "fuel_fillups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(
        ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    odometer_km: Mapped[float] = mapped_column(Float, nullable=False)
    liters: Mapped[float] = mapped_column(Float, nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    full_tank: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    vehicle: Mapped[Vehicle] = relationship(back_populates="fillups")
