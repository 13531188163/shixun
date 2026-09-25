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
) -> list[dict[str, Any]]:
    """Return numeric AQI ranking rows with one-based rank values."""

    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")
    if not isinstance(order, str) or order.strip().lower() not in {"asc", "desc"}:
        raise ValueError("order must be asc or desc")
    province_value = _optional_text(province, "province")
    rows = air_quality_model.get_air_quality_ranking(
        limit=limit, order=order.strip().lower(), province=province_value
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
