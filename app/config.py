"""Application configuration — everything overridable via environment."""

from __future__ import annotations

import os
from functools import lru_cache


def _csv_list(value: str | None) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()] if value else []


@lru_cache
def get_settings() -> Settings:
    return Settings()


class Settings:
    """Central settings object. Reads from env with safe defaults."""

    def __init__(self) -> None:
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-change-me")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
        )
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./gaadi.db")
        self.CORS_ORIGINS: list[str] = _csv_list(
            os.getenv("CORS_ORIGINS", "http://localhost:8000,http://localhost:5173")
        )

        # Maintenance intervals: "key=Name:km_interval:days_interval" comma separated
        raw_intervals = os.getenv(
            "MAINTENANCE_INTERVALS",
            "oil=Oil Change:5000:90,"
            "tires=Tire Rotation:10000:180,"
            "brakes=Brake Inspection:20000:365,"
            "general=General Service:10000:180",
        )
        self.MAINTENANCE_INTERVALS: dict[str, dict] = {}
        for part in raw_intervals.split(","):
            key, _, rest = part.partition("=")
            name, _, vals = rest.partition(":")
            km_str, _, days_str = vals.partition(":")
            self.MAINTENANCE_INTERVALS[key.strip()] = {
                "name": name.strip(),
                "km_interval": int(km_str),
                "days_interval": int(days_str),
            }


settings = get_settings()
