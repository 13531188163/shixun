"""Business service for historical rainfall analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import rainfall_model
from ..utils.data_converter import format_date, parse_precipitation
from . import weather_service


_MAX_DATE_COUNT = 1000
_TREND_DAYS = 30
_RECENT_DAYS = 7


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


def _validate_date(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a valid date in YYYY-MM-DD format")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid date in YYYY-MM-DD format") from exc
    return value


def _date_range(start_date: Any = None, end_date: Any = None) -> dict[str, str | None]:
    start_value = _validate_date(start_date, "startDate") if start_date is not None else None
    end_value = _validate_date(end_date, "endDate") if end_date is not None else None
    if start_value and end_value and start_value > end_value:
        raise ValueError("startDate must be earlier than or equal to endDate")
    return {"start_date": start_value, "end_date": end_value}


def _numeric(value: Any) -> int | float | None:
    return parse_precipitation(value)


def get_rainfall_dates(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
) -> list[str]:
    location = _location_values(province=province, city=city, district=district)
    rows = rainfall_model.get_rainfall_dates(**location, limit=_MAX_DATE_COUNT)
    return [
        parsed_date
        for row in rows
        if (parsed_date := format_date(row.get("date"))) is not None
    ]


def get_rainfall_core(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any] | None:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    row = rainfall_model.get_rainfall_core(**location, **dates)
    if row is None:
        return None
    total = _numeric(row.get("total_precip"))
    average = _numeric(row.get("avg_precip"))
    maximum = _numeric(row.get("max_precip"))
    if total is None and average is None and maximum is None:
        return None
    return {
        "totalPrecip": total,
        "avgPrecip": average,
        "maxPrecip": maximum,
        "maxPrecipDate": format_date(row.get("max_precip_date")),
        "rainyDays": int(row.get("rainy_days") or 0),
    }


def get_recent_rainfall(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    rows = rainfall_model.get_recent_rainfall(
        **location,
        **dates,
        days=_RECENT_DAYS,
    )
    return [
        {
            "date": format_date(row.get("date")),
            "precip": _numeric(row.get("precip")),
            "weather": row.get("weather"),
        }
        for row in reversed(rows)
        if format_date(row.get("date")) is not None
    ]


def get_rainfall_trend(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    rows = rainfall_model.get_rainfall_trend(
        **location,
        **dates,
        days=_TREND_DAYS,
    )
    return [
        {"date": format_date(row.get("date")), "precip": _numeric(row.get("precip"))}
        for row in reversed(rows)
        if format_date(row.get("date")) is not None
    ]


def get_rainfall_distribution(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    rows = rainfall_model.get_rainfall_distribution(**location, **dates)
    counts = {str(row.get("level")): int(row.get("count") or 0) for row in rows}
    levels = ("无降水", "小雨", "中雨", "大雨", "暴雨")
    return [{"level": level, "count": counts.get(level, 0)} for level in levels]


TREND_DAYS = _TREND_DAYS
RECENT_DAYS = _RECENT_DAYS
