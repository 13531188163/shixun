"""Business operations for weather data.

The service layer owns validation, source-value conversion, location
normalisation, and the JSON shape consumed by the future routes.  Repository
functions remain responsible for SQL and return raw database column names.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import date, datetime
from typing import Any

from ..models import weather_model
from ..utils.data_converter import (
    format_date,
    parse_precipitation,
    parse_temperature,
    parse_wind_speed,
)
from ..utils.location_utils import normalize_city_name, normalize_province_name


_MAX_NAME_LENGTH = 50
_DEFAULT_TREND_DAYS = 7
_MAX_TREND_DAYS = 90
_MAX_COMPARISON_CITIES = 10


def _location_name(value: Any, *, field: str, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"{field} is required")
        return None
    text = str(value).strip()
    if not text:
        if required:
            raise ValueError(f"{field} is required")
        return None
    if len(text) > _MAX_NAME_LENGTH:
        raise ValueError(f"{field} must be between 1 and {_MAX_NAME_LENGTH} characters")
    return text


def _validate_days(days: Any) -> int:
    if isinstance(days, bool) or not isinstance(days, int):
        raise ValueError("days must be an integer between 1 and 90")
    if not 1 <= days <= _MAX_TREND_DAYS:
        raise ValueError("days must be an integer between 1 and 90")
    return days


def _format_datetime(value: Any) -> str | None:
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
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _weather_payload(
    row: dict[str, Any], *, include_location: bool = True, include_created_at: bool = False
) -> dict[str, Any]:
    """Convert one raw weather row to the public weather JSON fields."""

    payload: dict[str, Any] = {}
    if include_location:
        payload.update(
            {
                "province": normalize_province_name(row.get("province")),
                "city": normalize_city_name(row.get("city")),
                "district": row.get("district"),
            }
        )
    payload.update(
        {
            "date": format_date(row.get("date")),
            "weather": row.get("weather"),
            "maxTemp": parse_temperature(row.get("max_temp")),
            "minTemp": parse_temperature(row.get("min_temp")),
            "avgWind": parse_wind_speed(row.get("avg_wind")),
            "maxWind": parse_wind_speed(row.get("max_wind")),
            "precipitation": parse_precipitation(row.get("total_precip")),
        }
    )
    if include_created_at and "created_at" in row:
        payload["createdAt"] = _format_datetime(row.get("created_at"))
    return payload


def _trend_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = _weather_payload(row, include_location=False)
    return {
        key: payload[key]
        for key in ("date", "weather", "maxTemp", "minTemp", "avgWind", "maxWind", "precipitation")
    }


def _comparison_payload(row: dict[str, Any]) -> dict[str, Any]:
    payload = _weather_payload(row)
    return {
        key: payload[key]
        for key in ("province", "city", "district", "date", "weather", "maxTemp", "minTemp")
    }


def get_latest_weather(
    *, city: str,
    province: str | None = None,
    district: str | None = None,
) -> dict[str, Any] | None:
    """Return one latest weather record, converted to the API shape."""

    city_value = _location_name(city, field="city", required=True)
    province_value = _location_name(province, field="province")
    district_value = _location_name(district, field="district")
    row = weather_model.get_latest_weather(
        city=city_value,
        province=province_value,
        district=district_value,
    )
    return _weather_payload(row) if row is not None else None


def get_weather_trend(
    *,
    city: str,
    province: str | None = None,
    district: str | None = None,
    days: int = _DEFAULT_TREND_DAYS,
) -> list[dict[str, Any]]:
    """Return one stable representative row for each of the latest dates.

    The repository performs date de-duplication in MySQL because a city can
    have several district rows per date.  The service still validates and
    normalizes the result before returning dates oldest first.
    """

    city_value = _location_name(city, field="city", required=True)
    province_value = _location_name(province, field="province")
    district_value = _location_name(district, field="district")
    day_count = _validate_days(days)
    rows = weather_model.get_weather_history_by_date(
        city=city_value,
        province=province_value,
        district=district_value,
        days=day_count,
    )

    representatives: dict[str, dict[str, Any]] = {}
    for row in rows:
        parsed_date = format_date(row.get("date"))
        if parsed_date is None:
            continue
        current = representatives.get(parsed_date)
        if current is None or _representative_key(row) < _representative_key(current):
            representatives[parsed_date] = row
    selected = sorted(representatives.items(), key=lambda item: item[0], reverse=True)[:day_count]
    return [_trend_payload(row) for _, row in sorted(selected, key=lambda item: item[0])]


def _representative_key(row: dict[str, Any]) -> tuple[str, int]:
    district = str(row.get("district") or "")
    raw_id = row.get("id")
    try:
        row_id = int(raw_id)
    except (TypeError, ValueError):
        row_id = 0
    return district, row_id


def _parse_city_names(cities: str | Sequence[str] | Iterable[str]) -> list[str]:
    if cities is None:
        raise ValueError("cities must contain between 1 and 10 city names")
    if isinstance(cities, str):
        values = cities.split(",")
    else:
        try:
            values = list(cities)
        except TypeError as exc:
            raise ValueError("cities must contain between 1 and 10 city names") from exc
    names: list[str] = []
    canonical_names: set[str] = set()
    for value in values:
        name = _location_name(value, field="city", required=True)
        assert name is not None
        canonical_name = normalize_city_name(name)
        if canonical_name not in canonical_names:
            names.append(name)
            if canonical_name is not None:
                canonical_names.add(canonical_name)
    if not 1 <= len(names) <= _MAX_COMPARISON_CITIES:
        raise ValueError("cities must contain between 1 and 10 city names")
    return names


def compare_cities(
    cities: str | Sequence[str] | Iterable[str],
    *,
    province: str | None = None,
) -> dict[str, Any]:
    """Return latest weather rows in input order and comparison metadata."""

    city_names = _parse_city_names(cities)
    province_value = _location_name(province, field="province")
    rows = weather_model.get_city_weather_latest(city_names, province=province_value)
    by_name = {normalize_city_name(row.get("city")): row for row in rows}
    data: list[dict[str, Any]] = []
    for requested_name in city_names:
        canonical_name = normalize_city_name(requested_name)
        row = by_name.get(canonical_name)
        if row is not None:
            data.append(_comparison_payload(row))
    return {
        "data": data,
        "meta": {"requested": len(city_names), "returned": len(data)},
    }


def list_provinces(*, limit: int = 500) -> list[str]:
    rows = weather_model.get_distinct_provinces(limit=limit)
    return _unique_sorted(normalize_province_name(row.get("province")) for row in rows)


def list_cities(*, province: str, limit: int = 500) -> list[str]:
    province_value = _location_name(province, field="province", required=True)
    rows = weather_model.get_distinct_cities(province_value, limit=limit)
    return _unique_sorted(normalize_city_name(row.get("city")) for row in rows)


def list_districts(*, province: str, city: str, limit: int = 500) -> list[str]:
    province_value = _location_name(province, field="province", required=True)
    city_value = _location_name(city, field="city", required=True)
    rows = weather_model.get_distinct_districts(province_value, city_value, limit=limit)
    return _unique_sorted(str(row.get("district")).strip() if row.get("district") is not None else None for row in rows)


def _unique_sorted(values: Iterable[str | None]) -> list[str]:
    return sorted({value for value in values if value})


# Names matching the API terminology, kept as small aliases for route callers.
get_city_comparison = compare_cities
get_weather_history = get_weather_trend
get_provinces = list_provinces
get_cities = list_cities
get_districts = list_districts
