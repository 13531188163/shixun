"""Business transformations for regional wind analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import wind_analysis_model
from ..utils.data_converter import format_date, parse_wind_speed
from . import weather_service

TREND_DAYS = 30
RECENT_DAYS = 7

WIND_LEVELS = (
    (0, "无风", "0–0.2 m/s"), (1, "软风", "0.3–1.5 m/s"),
    (2, "轻风", "1.6–3.3 m/s"), (3, "微风", "3.4–5.4 m/s"),
    (4, "和风", "5.5–7.9 m/s"), (5, "清劲风", "8.0–10.7 m/s"),
    (6, "强风", "10.8–13.8 m/s"), (7, "疾风", "13.9–17.1 m/s"),
    (8, "大风", "17.2–20.7 m/s"), (9, "烈风及以上", "≥20.8 m/s"),
)


def _location_values(*, province=None, city=None, district=None):
    values = {
        "province": weather_service._location_name(province, field="province"),
        "city": weather_service._location_name(city, field="city"),
        "district": weather_service._location_name(district, field="district"),
    }
    if values["district"] and not values["city"]:
        raise ValueError("district requires city")
    return values


def _date_range(start_date=None, end_date=None):
    for value, field in ((start_date, "startDate"), (end_date, "endDate")):
        if value is not None:
            if not isinstance(value, str):
                raise ValueError(f"{field} must be a valid date in YYYY-MM-DD format")
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError(f"{field} must be a valid date in YYYY-MM-DD format") from exc
    if start_date and end_date and start_date > end_date:
        raise ValueError("startDate must be earlier than or equal to endDate")
    return {"start_date": start_date, "end_date": end_date}


def _numeric(value):
    value = parse_wind_speed(value)
    return value if value is None or value >= 0 else None


def _count(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def classify_wind_level(value):
    value = _numeric(value)
    if value is None:
        return None
    for level, name, _range in WIND_LEVELS:
        if level == 9 or value < (0.3, 1.6, 3.4, 5.5, 8.0, 10.8, 13.9, 17.2, 20.8)[level]:
            return {"level": level, "name": name, "range": _range}
    return None


def get_wind_dates(*, province=None, city=None, district=None):
    location = _location_values(province=province, city=city, district=district)
    return [format_date(row.get("date")) for row in wind_analysis_model.get_wind_dates(**location) if format_date(row.get("date"))]


def get_wind_core(*, province=None, city=None, district=None, start_date=None, end_date=None):
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    row = wind_analysis_model.get_wind_core(**location, **dates)
    if row is None:
        return None
    avg = _numeric(row.get("avg_wind")); maximum = _numeric(row.get("max_wind"))
    dominant = get_wind_distribution(**location, **dates)
    dominant = max(dominant, key=lambda item: item["count"]) if dominant and max(item["count"] for item in dominant) > 0 else None
    if avg is None and maximum is None:
        return None
    return {
        "avgWind": avg, "maxWind": maximum,
        "maxWindDate": format_date(row.get("max_wind_date")),
        "avgWindKmh": round(avg * 3.6, 2) if avg is not None else None,
        "dominantLevel": dominant,
        "observationDays": _count(row.get("observation_days")),
        "observationRecords": _count(row.get("observation_records")),
    }


def _rows(function, *, location, dates, days):
    rows = function(**location, **dates, days=days)
    result = []
    for row in rows:
        date = format_date(row.get("date"))
        if not date:
            continue
        result.append({"date": date, "avgWind": _numeric(row.get("avg_wind")), "maxWind": _numeric(row.get("max_wind"))})
    return list(reversed(result))


def get_wind_trend(**kwargs):
    location = _location_values(province=kwargs.get("province"), city=kwargs.get("city"), district=kwargs.get("district"))
    dates = _date_range(kwargs.get("start_date"), kwargs.get("end_date"))
    return _rows(wind_analysis_model.get_wind_trend, location=location, dates=dates, days=TREND_DAYS)


def get_recent_wind(**kwargs):
    location = _location_values(province=kwargs.get("province"), city=kwargs.get("city"), district=kwargs.get("district"))
    dates = _date_range(kwargs.get("start_date"), kwargs.get("end_date"))
    rows = _rows(wind_analysis_model.get_recent_wind, location=location, dates=dates, days=RECENT_DAYS)
    for row in rows:
        row["level"] = classify_wind_level(row["avgWind"])
    return rows


def get_wind_distribution(*, province=None, city=None, district=None, start_date=None, end_date=None):
    location = _location_values(province=province, city=city, district=district)
    dates = _date_range(start_date, end_date)
    raw = {int(row.get("level")): _count(row.get("count")) or 0 for row in wind_analysis_model.get_wind_distribution(**location, **dates)}
    total = sum(raw.values())
    return [
        {"level": level, "name": name, "range": span, "count": raw.get(level, 0), "percentage": round(raw.get(level, 0) / total * 100, 1) if total else 0}
        for level, name, span in WIND_LEVELS
    ]
