"""Read-only repository functions for the ``weather_data`` table.

The model deliberately returns database-shaped dictionaries.  Unit cleaning,
date formatting, and snake_case-to-camelCase mapping belong to later service
layers.  Every query is bounded and selects only the columns needed by the
future services; no business HTTP concerns are imported here.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from ..utils.db import connection_scope
from ..utils.location_utils import city_query_values, province_query_values


WEATHER_COLUMNS = (
    "id",
    "province",
    "city",
    "district",
    "year",
    "month",
    "date",
    "weather",
    "max_temp",
    "min_temp",
    "avg_wind",
    "max_wind",
    "total_precip",
    "created_at",
)
_WEATHER_SELECT = ", ".join(WEATHER_COLUMNS)
_DEFAULT_HISTORY_LIMIT = 7
_MAX_HISTORY_LIMIT = 90
_MAX_LOCATION_LIMIT = 500


def _query_values(values: Iterable[str] | str | None, *, kind: str) -> tuple[str, ...]:
    """Return a non-empty tuple of raw/canonical values for an SQL ``IN``.

    Values are always passed as DB-API parameters.  Only the number of fixed
    ``%s`` placeholders is constructed in the SQL text.
    """

    if values is None:
        return ()
    if isinstance(values, str):
        values = (values,)
    cleaned = tuple(str(value).strip() for value in values if value is not None and str(value).strip())
    if not cleaned:
        return ()
    if kind == "city":
        return city_query_values(cleaned[0]) if len(cleaned) == 1 else _unique(cleaned)
    if kind == "province":
        return province_query_values(cleaned[0]) if len(cleaned) == 1 else _unique(cleaned)
    return _unique(cleaned)


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _in_filter(column: str, values: Sequence[str]) -> tuple[str, list[str]]:
    """Build a fixed-column ``IN`` predicate and its parameter list."""

    if not values:
        return "", []
    placeholders = ", ".join(["%s"] * len(values))
    return f"{column} IN ({placeholders})", list(values)


def _location_filters(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
) -> tuple[list[str], list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    province_values = _query_values(province, kind="province")
    province_clause, province_params = _in_filter("province", province_values)
    if province_clause:
        clauses.append(province_clause)
        params.extend(province_params)

    city_values = _query_values(city, kind="city")
    city_clause, city_params = _in_filter("city", city_values)
    if city_clause:
        clauses.append(city_clause)
        params.extend(city_params)

    if district is not None:
        district_value = str(district).strip()
        if district_value:
            clauses.append("district = %s")
            params.append(district_value)

    return clauses, params


def _require_city(city: str | None) -> str:
    if city is None or not str(city).strip():
        raise ValueError("city is required")
    return str(city).strip()


def get_latest_weather(
    city: str,
    province: str | None = None,
    district: str | None = None,
) -> dict[str, Any] | None:
    """Return the newest observed row for one city/location, if present."""

    _require_city(city)
    clauses, params = _location_filters(province=province, city=city, district=district)
    where_sql = " AND ".join(clauses)
    sql = (
        f"SELECT {_WEATHER_SELECT} FROM weather_data "
        f"WHERE {where_sql} "
        "ORDER BY STR_TO_DATE(NULLIF(TRIM(date), ''), '%%Y-%%m-%%d') DESC, id DESC "
        "LIMIT 1"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def get_weather_history(
    city: str,
    province: str | None = None,
    district: str | None = None,
    days: int = _DEFAULT_HISTORY_LIMIT,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Return a bounded newest-first history for one city/location.

    ``days`` is a bounded row limit at this repository layer.  The source
    schema has one row per observed date in normal data; services can perform
    any additional date grouping without loading the large table wholesale.
    """

    _require_city(city)
    requested_limit = days if limit is None else limit
    if isinstance(requested_limit, bool) or not isinstance(requested_limit, int):
        raise ValueError("limit must be an integer")
    if not 1 <= requested_limit <= _MAX_HISTORY_LIMIT:
        raise ValueError(f"limit must be between 1 and {_MAX_HISTORY_LIMIT}")

    clauses, params = _location_filters(province=province, city=city, district=district)
    where_sql = " AND ".join(clauses)
    sql = (
        f"SELECT {_WEATHER_SELECT} FROM weather_data "
        f"WHERE {where_sql} "
        "ORDER BY STR_TO_DATE(NULLIF(TRIM(date), ''), '%%Y-%%m-%%d') DESC, id DESC "
        "LIMIT %s"
    )
    params.append(requested_limit)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def get_city_weather_latest(
    cities: Iterable[str],
    province: str | None = None,
) -> list[dict[str, Any]]:
    """Return at most one latest row per requested city.

    Each city query remains bounded, which avoids reading the 83万-row table
    into Python and keeps the latest-date ordering explicit.
    """

    city_names = _unique(str(city).strip() for city in cities if city is not None and str(city).strip())
    if not city_names:
        return []
    if len(city_names) > _MAX_LOCATION_LIMIT:
        raise ValueError(f"cities must contain at most {_MAX_LOCATION_LIMIT} values")
    return [
        row
        for city in city_names
        if (row := get_latest_weather(city=city, province=province)) is not None
    ]


def get_distinct_provinces(limit: int = _MAX_LOCATION_LIMIT) -> list[dict[str, Any]]:
    """Return distinct raw province values with a hard upper bound."""

    _validate_location_limit(limit)
    sql = "SELECT DISTINCT province FROM weather_data WHERE province IS NOT NULL ORDER BY province LIMIT %s"
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, [limit])
            return list(cursor.fetchall())


def get_distinct_cities(province: str, limit: int = _MAX_LOCATION_LIMIT) -> list[dict[str, Any]]:
    """Return distinct raw cities for a province with a hard upper bound."""

    if province is None or not str(province).strip():
        raise ValueError("province is required")
    _validate_location_limit(limit)
    province_values = province_query_values(str(province).strip())
    clause, params = _in_filter("province", province_values)
    sql = (
        "SELECT DISTINCT city FROM weather_data "
        f"WHERE {clause} AND city IS NOT NULL ORDER BY city LIMIT %s"
    )
    params.append(limit)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def get_distinct_districts(
    province: str,
    city: str,
    limit: int = _MAX_LOCATION_LIMIT,
) -> list[dict[str, Any]]:
    """Return distinct non-null district values for a city."""

    if province is None or not str(province).strip():
        raise ValueError("province is required")
    _require_city(city)
    _validate_location_limit(limit)
    clauses, params = _location_filters(province=province, city=city)
    clauses.append("district IS NOT NULL")
    clauses.append("TRIM(district) <> ''")
    sql = (
        "SELECT DISTINCT district FROM weather_data "
        f"WHERE {' AND '.join(clauses)} ORDER BY district LIMIT %s"
    )
    params.append(limit)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def _validate_location_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if not 1 <= limit <= _MAX_LOCATION_LIMIT:
        raise ValueError(f"limit must be between 1 and {_MAX_LOCATION_LIMIT}")
