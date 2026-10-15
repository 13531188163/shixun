"""Business service for historical temperature analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import temperature_model
from ..utils.data_converter import format_date, parse_temperature
from . import weather_service


_DEFAULT_TREND_DAYS = 30
_DEFAULT_RECENT_DAYS = 7
_MAX_TREND_DAYS = 30
_MAX_RECENT_DAYS = 7
_MAX_DATE_COUNT = 1000


def _location_values(
    *,
    province: Any = None,
    city: Any = None,
    district: Any = None,
) -> dict[str, str | None]:
    province_value = weather_service._location_name(province, field="province")
    city_value = weather_service._location_name(city, field="city")
    district_value = weather_service._location_name(district, field="district")
    if district_value is not None and city_value is None:
        raise ValueError("district requires city")
    return {
        "province": province_value,
        "city": city_value,
        "district": district_value,
    }


def _date_range(start_date: Any = None, end_date: Any = None) -> dict[str, str | None]:
    start_value = _validate_date(start_date, "startDate") if start_date is not None else None
    end_value = _validate_date(end_date, "endDate") if end_date is not None else None
    if start_value and end_value and start_value > end_value:
        raise ValueError("startDate must be earlier than or equal to endDate")
    return {"start_date": start_value, "end_date": end_value}


def _validate_date(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a valid date in YYYY-MM-DD format")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid date in YYYY-MM-DD format") from exc
    return value


def get_temperature_dates(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
) -> list[str]:
    """Return only dates that exist in weather_data for the selected scope."""

    location = _location_values(province=province, city=city, district=district)
    rows = temperature_model.get_temperature_dates(**location, limit=_MAX_DATE_COUNT)
    return [
        parsed_date
        for row in rows
        if (parsed_date := format_date(row.get("date"))) is not None
    ]


def _numeric(value: Any) -> int | float | None:
    return parse_temperature(value)


def get_temperature_average(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any] | None:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    row = temperature_model.get_temperature_average(**location, **dates)
    if not row or int(row.get("record_count") or 0) == 0:
        return None
    avg_max = _numeric(row.get("avg_max_temp"))
    avg_min = _numeric(row.get("avg_min_temp"))
    if avg_max is None and avg_min is None:
        return None
    avg_temp = (avg_max + avg_min) / 2 if avg_max is not None and avg_min is not None else None
    return {
        "avgMaxTemp": avg_max,
        "avgMinTemp": avg_min,
        "avgTemp": avg_temp,
    }


def get_temperature_extremes(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any] | None:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    row = temperature_model.get_temperature_extremes(**location, **dates)
    if row is None:
        return None
    return {
        "maxTemperature": _numeric(row.get("max_temperature")),
        "maxDate": format_date(row.get("max_date")),
        "minTemperature": _numeric(row.get("min_temperature")),
        "minDate": format_date(row.get("min_date")),
    }


def get_temperature_trend(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    rows = temperature_model.get_temperature_trend(
        **location,
        **dates,
        days=_MAX_TREND_DAYS,
    )
    return [
        {
            "date": format_date(row.get("date")),
            "maxTemp": _numeric(row.get("max_temp")),
            "minTemp": _numeric(row.get("min_temp")),
        }
        for row in reversed(rows)
        if format_date(row.get("date")) is not None
    ]


def get_temperature_monthly(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    rows = temperature_model.get_temperature_monthly(**location, **dates)
    result: list[dict[str, Any]] = []
    for row in rows:
        try:
            month_number = int(row.get("month_number"))
        except (TypeError, ValueError):
            continue
        if not 1 <= month_number <= 12:
            continue
        result.append({"month": f"{month_number}月", "avgTemp": _numeric(row.get("avg_temp"))})
    return result


def get_recent_temperature(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    rows = temperature_model.get_recent_temperature(
        **location,
        **dates,
        days=_MAX_RECENT_DAYS,
    )
    result: list[dict[str, Any]] = []
    for row in reversed(rows):
        parsed_date = format_date(row.get("date"))
        if parsed_date is None:
            continue
        result.append(
            {
                "date": parsed_date,
                "weather": row.get("weather"),
                "maxTemp": _numeric(row.get("max_temp")),
                "minTemp": _numeric(row.get("min_temp")),
            }
        )
    return result


# Public constants keep endpoint metadata explicit without exposing SQL limits.
TREND_DAYS = _DEFAULT_TREND_DAYS
RECENT_DAYS = _DEFAULT_RECENT_DAYS
