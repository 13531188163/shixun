"""Centralized environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc


def _env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _env_origins(name: str) -> Tuple[str, ...]:
    raw_value = os.getenv(name, "http://localhost:5173,http://127.0.0.1:5173")
    origins = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    return origins or ("http://localhost:5173",)


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    flask_host: str
    flask_port: int
    flask_debug: bool
    cors_origins: Tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            db_host=os.getenv("DB_HOST", "127.0.0.1"),
            db_port=_env_int("DB_PORT", 3306),
            db_user=os.getenv("DB_USER", "root"),
            db_password=os.getenv("DB_PASSWORD", ""),
            db_name=os.getenv("DB_NAME", "weather_db"),
            flask_host=os.getenv("FLASK_HOST", "0.0.0.0"),
            flask_port=_env_int("FLASK_PORT", 5000),
            flask_debug=_env_bool("FLASK_DEBUG", False),
            cors_origins=_env_origins("CORS_ORIGINS"),
        )


settings = Settings.from_environment()
