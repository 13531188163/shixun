"""Business transformations for the optional ``wind_data`` table."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..models import wind_model
from ..utils.data_converter import format_date, parse_temperature
from ..utils.location_utils import normalize_city_name


def _optional_city(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("city must be a string")
    text = value.strip()
    if not text:
        return None
    if len(text) > 50:
        raise ValueError("city must be at most 50 characters")
    return text


def _format_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d 00:00:00")
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        parsed = format_date(text)
        return f"{parsed} 00:00:00" if parsed else None


def _to_api_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "city": normalize_city_name(row.get("city")),
        "year": row.get("year"),
        "month": row.get("month"),
        "date": format_date(row.get("date")),
        "weather": row.get("weather"),
        "maxTemp": parse_temperature(row.get("max_temp")),
        "minTemp": parse_temperature(row.get("min_temp")),
        "wind": row.get("wind"),
        "createdAt": _format_timestamp(row.get("created_at")),
    }


def has_wind_data() -> bool:
    """Report whether the source table contains at least one record."""

    return wind_model.has_wind_data()


def get_wind_data(city: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return converted wind rows; an empty table produces an empty list."""

    city_value = _optional_city(city)
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
        raise ValueError("limit must be an integer between 1 and 500")
    return [
        _to_api_row(row)
        for row in wind_model.get_wind_data(city=city_value, limit=limit)
    ]


def get_latest_wind(city: str) -> dict[str, Any] | None:
    """Return a converted latest row or ``None`` when the table has no data."""

    city_value = _optional_city(city)
    if city_value is None:
        raise ValueError("city is required")
    row = wind_model.get_latest_wind(city=city_value)
    return _to_api_row(row) if row else None


def get_wind_history(city: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    return get_wind_data(city=city, limit=limit)


latest = get_latest_wind
history = get_wind_history
