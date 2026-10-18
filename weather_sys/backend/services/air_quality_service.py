"""Business transformations for air-quality snapshots.

The service layer is deliberately independent from Flask.  It validates
public arguments, calls the read-only model and converts database snake_case
rows into the camelCase contract used by the future routes.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from ..models import air_quality_model
from ..utils.data_converter import format_date, parse_aqi
from ..utils.location_utils import normalize_city_name, normalize_province_name


def _required_text(value: Any, name: str, max_length: int = 50) -> str:
    if value is None or not isinstance(value, str):
        raise ValueError(f"{name} is required")
    text = value.strip()
    if not text:
        raise ValueError(f"{name} is required")
    if len(text) > max_length:
        raise ValueError(f"{name} must be at most {max_length} characters")
    return text


def _optional_text(value: Any, name: str, max_length: int = 50) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    text = value.strip()
    if not text:
        return None
    if len(text) > max_length:
        raise ValueError(f"{name} must be at most {max_length} characters")
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
    # ``format_date`` validates ISO-like input; preserve the timestamp only
    # when it has a valid date component and normalize the missing time.
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed_date = format_date(text)
        return f"{parsed_date} 00:00:00" if parsed_date else None
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def _to_api_row(row: dict[str, Any], *, include_id: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "city": normalize_city_name(row.get("city")),
        "province": normalize_province_name(row.get("province")),
        "aqi": parse_aqi(row.get("aqi")),
        "status": row.get("status").strip() if isinstance(row.get("status"), str) and row.get("status").strip() else None,
        "createdAt": _format_timestamp(row.get("created_at")),
    }
    if include_id:
        result["id"] = row.get("id")
    return result


def get_latest_air_quality(city: str, province: str | None = None) -> dict[str, Any] | None:
    """Return the latest snapshot for a city, or ``None`` when absent."""

    city_value = _required_text(city, "city")
    province_value = _optional_text(province, "province")
    row = air_quality_model.get_latest_air_quality(city=city_value, province=province_value)
    return _to_api_row(row) if row else None


def get_air_quality_ranking(
    limit: int = 10,
    order: str = "asc",
    province: str | None = None,
    city: str | None = None,
) -> list[dict[str, Any]]:
    """Return numeric AQI ranking rows with one-based rank values."""

    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")
    if not isinstance(order, str) or order.strip().lower() not in {"asc", "desc"}:
        raise ValueError("order must be asc or desc")
    province_value = _optional_text(province, "province")
    city_value = _optional_text(city, "city")
    rows = air_quality_model.get_air_quality_ranking(
        limit=limit, order=order.strip().lower(), province=province_value, city=city_value
    )
    return [
        {
            "rank": index,
            "city": normalize_city_name(row.get("city")),
            "province": normalize_province_name(row.get("province")),
            "aqi": parse_aqi(row.get("aqi")),
            "status": row.get("status").strip()
            if isinstance(row.get("status"), str) and row.get("status").strip()
            else None,
        }
        for index, row in enumerate(rows, start=1)
    ]


def get_air_quality_distribution(
    city: str | None = None,
    province: str | None = None,
) -> list[dict[str, Any]]:
    """Return counts by non-empty source status."""

    city_value = _optional_text(city, "city")
    province_value = _optional_text(province, "province")
    result: list[dict[str, Any]] = []
    rows = air_quality_model.get_air_quality_distribution(city=city_value, province=province_value)
    priority = {name: index for index, name in enumerate(("优", "良", "轻度", "中度", "重度", "严重污染"))}
    for row in sorted(rows, key=lambda item: (priority.get(str(item.get("status")).strip(), len(priority)), str(item.get("status")))):
        status = row.get("status")
        if isinstance(status, str):
            status = status.strip() or None
        if status is not None:
            result.append({"status": status, "count": int(row.get("count") or 0)})
    return result


def get_air_quality_distribution_result(
    *, city: str | None = None, province: str | None = None
) -> dict[str, Any]:
    """Return distribution data and its contract metadata."""

    data = get_air_quality_distribution(city=city, province=province)
    return {
        "data": data,
        "meta": {"totalKnown": sum(int(row.get("count") or 0) for row in data)},
    }


def get_province_air_quality_summary(province: str) -> dict[str, Any] | None:
    """Return an AQI summary for the fixed province snapshot, if available."""

    province_value = _required_text(province, "province")
    row = air_quality_model.get_province_air_quality_summary(province_value)
    if not row:
        return None
    average = row.get("average_aqi")
    try:
        average_value = float(average) if average is not None else None
    except (TypeError, ValueError):
        average_value = None
    if average_value is not None and average_value.is_integer():
        average_value = int(average_value)
    return {
        "province": normalize_province_name(province_value),
        "cityCount": int(row.get("city_count") or 0),
        "averageAqi": average_value,
        "minAqi": int(row["min_aqi"]) if row.get("min_aqi") is not None else None,
        "maxAqi": int(row["max_aqi"]) if row.get("max_aqi") is not None else None,
        "createdAt": _format_timestamp(row.get("latest_snapshot")),
    }


def classify_aqi(value: Any) -> str | None:
    """Classify numeric AQI using the page's fixed six ranges."""

    number = parse_aqi(value)
    if number is None or number < 0:
        return None
    if number <= 50:
        return "优"
    if number <= 100:
        return "良"
    if number <= 150:
        return "轻度污染"
    if number <= 200:
        return "中度污染"
    if number <= 300:
        return "重度污染"
    return "严重污染"


def _numeric(value: Any) -> int | None:
    return parse_aqi(value)


def get_air_quality_overview(province: str | None = None) -> dict[str, Any]:
    province_value = _optional_text(province, "province")
    row = air_quality_model.get_air_quality_overview(province=province_value)
    average = row.get("average_aqi")
    try:
        average = float(average) if average is not None else None
        if average is not None and average.is_integer():
            average = int(average)
    except (TypeError, ValueError, OverflowError):
        average = None
    return {
        "cityCount": int(row.get("city_count") or 0),
        "averageAqi": average,
        "goodCityCount": int(row.get("good_city_count") or 0),
        "pollutedCityCount": int(row.get("polluted_city_count") or 0),
        "createdAt": _format_timestamp(row.get("latest_snapshot")),
    }


def _api_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    aqi = _numeric(row.get("aqi"))
    return {
        "city": normalize_city_name(row.get("city")),
        "province": normalize_province_name(row.get("province")),
        "aqi": aqi,
        "status": classify_aqi(aqi) or (row.get("status").strip() if isinstance(row.get("status"), str) else None),
        "createdAt": _format_timestamp(row.get("created_at")),
    }


def get_air_quality_province_summaries() -> list[dict[str, Any]]:
    result = []
    for row in air_quality_model.get_air_quality_province_summaries():
        average = row.get("average_aqi")
        try:
            average = float(average) if average is not None else None
            if average is not None and average.is_integer():
                average = int(average)
        except (TypeError, ValueError, OverflowError):
            average = None
        result.append({
            "province": normalize_province_name(row.get("province")),
            "cityCount": int(row.get("city_count") or 0),
            "averageAqi": average,
            "status": classify_aqi(average),
            "createdAt": _format_timestamp(row.get("latest_snapshot")),
        })
    return result


def get_air_quality_city_rows(province: str | None = None) -> list[dict[str, Any]]:
    return [_api_snapshot(row) for row in air_quality_model.get_air_quality_city_rows(province=_optional_text(province, "province"))]


def get_air_quality_level_distribution(province: str | None = None) -> list[dict[str, Any]]:
    rows = air_quality_model.get_air_quality_level_distribution(province=_optional_text(province, "province"))
    counts = {str(row.get("level")): int(row.get("count") or 0) for row in rows}
    levels = ("优", "良", "轻度污染", "中度污染", "重度污染", "严重污染")
    total = sum(counts.get(level, 0) for level in levels)
    return [{"status": level, "count": counts.get(level, 0), "percentage": round(counts.get(level, 0) / total * 100, 1) if total else 0} for level in levels]


def get_all_air_quality(
    limit: int = 1000,
    city: str | None = None,
    province: str | None = None,
) -> list[dict[str, Any]]:
    """Return a bounded list of snapshots in API shape."""

    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
        raise ValueError("limit must be an integer between 1 and 1000")
    city_value = _optional_text(city, "city")
    province_value = _optional_text(province, "province")
    return [
        _to_api_row(row, include_id=True)
        for row in air_quality_model.get_all_air_quality(
            limit=limit, city=city_value, province=province_value
        )
    ]


# Short aliases make route naming natural while retaining explicit functions
# for callers and tests that follow the API specification wording.
latest = get_latest_air_quality
ranking = get_air_quality_ranking
distribution = get_air_quality_distribution
all_records = get_all_air_quality
