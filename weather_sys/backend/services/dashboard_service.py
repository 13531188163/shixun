"""Business aggregation for the Phase 4 dashboard overview.

This module composes existing weather and AQI services without introducing a
route or a second database access path.  The returned structure intentionally
contains only fields supported by the configured source tables.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..models import air_quality_model, weather_model
from ..utils.data_converter import format_date
from .air_quality_service import get_latest_air_quality
from .weather_service import get_latest_weather


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
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        normalized_date = format_date(text)
        return f"{normalized_date} 00:00:00" if normalized_date else None
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _stat_value(row: dict[str, Any] | None, key: str, default: Any = None) -> Any:
    if not row:
        return default
    return row.get(key, default)


def get_dashboard_overview(
    *,
    city: str,
    province: str | None = None,
    district: str | None = None,
) -> dict[str, Any] | None:
    """Return location, latest source-backed values, and basic statistics."""

    latest_weather = get_latest_weather(city=city, province=province, district=district)
    if latest_weather is None:
        return None

    resolved_province = latest_weather.get("province") or province
    resolved_city = latest_weather.get("city") or city
    latest_air_quality = get_latest_air_quality(
        city=str(resolved_city),
        province=str(resolved_province) if resolved_province else None,
    )

    weather_stats = weather_model.get_weather_statistics()
    air_quality_stats = air_quality_model.get_air_quality_statistics()
    return {
        "location": {
            "province": latest_weather.get("province"),
            "city": latest_weather.get("city"),
            "district": latest_weather.get("district"),
        },
        "latestWeather": latest_weather,
        "latestAirQuality": latest_air_quality,
        "basicStatistics": {
            "weatherRecordCount": int(_stat_value(weather_stats, "record_count", 0) or 0),
            "airQualityRecordCount": int(_stat_value(air_quality_stats, "record_count", 0) or 0),
            "weatherLatestDate": format_date(_stat_value(weather_stats, "latest_date")),
            "airQualitySnapshotAt": _format_timestamp(
                _stat_value(air_quality_stats, "latest_snapshot")
            ),
        },
    }


overview = get_dashboard_overview
