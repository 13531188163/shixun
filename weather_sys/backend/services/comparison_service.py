"""Comparison aggregation over real weather rows and AQI snapshots."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from ..models import comparison_model
from ..services import air_quality_service
from ..utils.location_utils import normalize_city_name, normalize_province_name

_MAX_CITIES = 4
_DATE_FORMAT = "%Y-%m-%d"


def _date(value: str | None, name: str) -> str | None:
    if value is None or value == "":
        return None
    try:
        return date.fromisoformat(value).strftime(_DATE_FORMAT)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a valid date in YYYY-MM-DD format") from exc


def _refs(cities: str | list[str]) -> list[dict[str, str]]:
    values = cities.split(",") if isinstance(cities, str) else list(cities)
    result: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        if "::" in text:
            province, city = (part.strip() for part in text.split("::", 1))
        else:
            province, city = "", text
        if not city:
            continue
        key = (normalize_province_name(province) or "", normalize_city_name(city) or city)
        if key in seen:
            raise ValueError("cities must not contain duplicate administrative locations")
        seen.add(key)
        result.append({"province": province, "city": city})
    if not 2 <= len(result) <= _MAX_CITIES:
        raise ValueError("cities must contain between 2 and 4 administrative locations")
    if any(not ref["province"] for ref in result):
        raise ValueError("each comparison city must include province and city")
    return result


def get_locations() -> list[dict[str, str]]:
    result = []
    seen: set[str] = set()
    for row in comparison_model.get_comparison_locations():
        province = normalize_province_name(row.get("province"))
        city = normalize_city_name(row.get("city"))
        if province and city:
            key = f"{province}::{city}"
            if key in seen:
                continue
            seen.add(key)
            result.append({"key": key, "province": province, "city": city})
    return result


def _matches(row: dict[str, Any], ref: dict[str, str]) -> bool:
    return normalize_province_name(row.get("province")) == normalize_province_name(ref["province"]) and normalize_city_name(row.get("city")) == normalize_city_name(ref["city"])


def _number(value: Any) -> float | None:
    try:
        number = float(value) if value is not None else None
        return round(number, 2) if number is not None and math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def _range(values: list[Any]) -> dict[str, float | None]:
    numbers = [_number(value) for value in values]
    numbers = [value for value in numbers if value is not None]
    return {"min": min(numbers) if numbers else None, "max": max(numbers) if numbers else None}


def _radar_baseline(common_dates: list[str]) -> dict[str, dict[str, float | None]]:
    weather = comparison_model.get_radar_weather_baseline(common_dates) if common_dates else {}
    aqi_rows = air_quality_service.get_air_quality_city_rows() if common_dates else []
    return {
        "avgTempEstimate": {"min": _number(weather.get("avg_temp_min")), "max": _number(weather.get("avg_temp_max"))},
        "totalPrecip": {"min": _number(weather.get("total_precip_min")), "max": _number(weather.get("total_precip_max"))},
        "avgWind": {"min": _number(weather.get("avg_wind_min")), "max": _number(weather.get("avg_wind_max"))},
        "aqiSnapshot": _range([row.get("aqi") for row in aqi_rows]),
    }


def compare(cities: str | list[str], start_date: str | None = None, end_date: str | None = None) -> dict[str, Any]:
    refs = _refs(cities)
    bounds = comparison_model.get_date_bounds() or {}
    requested_start = _date(start_date, "startDate")
    requested_end = _date(end_date, "endDate")
    if requested_start is None and requested_end is None:
        # Default to the latest complete 30-calendar-day window available in the database.
        end = str(bounds.get("end_date") or "")
        try:
            start = (date.fromisoformat(end) - timedelta(days=29)).strftime(_DATE_FORMAT)
        except ValueError:
            start = str(bounds.get("start_date") or "")
    else:
        start = requested_start or str(bounds.get("start_date") or "")
        end = requested_end or str(bounds.get("end_date") or "")
    if not start or not end or start > end:
        raise ValueError("startDate must be earlier than or equal to endDate")
    rows = comparison_model.get_comparison_daily(refs, start, end)
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for index, ref in enumerate(refs):
            if _matches(row, ref):
                grouped[index].append(row)
                break
    date_sets = [
        {
            str(row.get("date"))
            for row in grouped[index]
            if row.get("date") and any(
                row.get(field) is not None
                for field in ("max_temp", "min_temp", "avg_wind", "max_wind", "precip")
            )
        }
        for index in range(len(refs))
    ]
    common_dates = sorted(set.intersection(*date_sets)) if date_sets and all(date_sets) else []
    common = set(common_dates)
    result_cities = []
    for index, ref in enumerate(refs):
        daily = [row for row in grouped[index] if str(row.get("date")) in common]
        def values(field: str) -> list[float]:
            return [float(row[field]) for row in daily if row.get(field) is not None]
        max_t, min_t, wind, max_w, rain = (values(name) for name in ("max_temp", "min_temp", "avg_wind", "max_wind", "precip"))
        monthly = defaultdict(float)
        for row in daily:
            if row.get("precip") is not None:
                monthly[str(row["date"])[:7]] += float(row["precip"])
        aqi = air_quality_service.get_latest_air_quality(city=ref["city"], province=ref["province"])
        result_cities.append({
            "key": f"{normalize_province_name(ref['province'])}::{normalize_city_name(ref['city'])}",
            "province": normalize_province_name(ref["province"]), "city": normalize_city_name(ref["city"]),
            "weatherMetrics": {
                "avgMaxTemp": _number(sum(max_t) / len(max_t) if max_t else None),
                "avgMinTemp": _number(sum(min_t) / len(min_t) if min_t else None),
                "avgTempEstimate": _number((sum(max_t) / len(max_t) + sum(min_t) / len(min_t)) / 2 if max_t and min_t else None),
                "totalPrecip": _number(sum(rain) if rain else None), "avgWind": _number(sum(wind) / len(wind) if wind else None),
                "maxWind": _number(max(max_w) if max_w else None), "validDays": len(date_sets[index]),
            },
            "monthlyPrecip": [{"month": month, "precip": _number(value)} for month, value in sorted(monthly.items())],
            "aqiSnapshot": aqi or {"aqi": None, "status": None, "createdAt": None},
        })
    return {
        "weatherPeriod": {"startDate": start, "endDate": end},
        "comparableDates": common_dates,
        "dataCoverage": {
            "commonDays": len(common_dates),
            "cities": [{"key": item["key"], "validDays": item["weatherMetrics"]["validDays"]} for item in result_cities],
        },
        "radarBaseline": _radar_baseline(common_dates),
        "cities": result_cities,
    }
