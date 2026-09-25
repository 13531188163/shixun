"""Read-only repository functions for ``air_quality_data``.

AQI is stored as ``VARCHAR`` in the source database.  Ranking therefore uses
an explicit numeric cast and ignores values that are not unsigned integers;
the original row values are returned unchanged for later service conversion.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..utils.db import connection_scope
from ..utils.location_utils import city_query_values, province_query_values


AIR_QUALITY_COLUMNS = ("id", "city", "province", "aqi", "status", "created_at")
_AIR_SELECT = ", ".join(AIR_QUALITY_COLUMNS)
_MAX_LIMIT = 1000
_MAX_DISTRIBUTION_GROUPS = 100


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _in_clause(column: str, values: tuple[str, ...]) -> tuple[str, list[str]]:
    placeholders = ", ".join(["%s"] * len(values))
    return f"{column} IN ({placeholders})", list(values)


def _location_filters(
    *, city: str | None = None, province: str | None = None
) -> tuple[list[str], list[str]]:
    clauses: list[str] = []
    params: list[str] = []
    if city is not None and str(city).strip():
        city_clause, city_params = _in_clause("city", city_query_values(str(city).strip()))
        clauses.append(city_clause)
        params.extend(city_params)
    if province is not None and str(province).strip():
        province_clause, province_params = _in_clause(
            "province", province_query_values(str(province).strip())
        )
        clauses.append(province_clause)
        params.extend(province_params)
    return clauses, params


def _validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if not 1 <= limit <= _MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {_MAX_LIMIT}")


def get_latest_air_quality(city: str, province: str | None = None) -> dict[str, Any] | None:
    """Return the newest AQI snapshot for a city, if present."""

    if city is None or not str(city).strip():
        raise ValueError("city is required")
    clauses, params = _location_filters(city=city, province=province)
    sql = (
        f"SELECT {_AIR_SELECT} FROM air_quality_data "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY created_at DESC, id DESC LIMIT 1"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def get_air_quality_ranking(
    limit: int = 10,
    order: str = "asc",
    province: str | None = None,
) -> list[dict[str, Any]]:
    """Return AQI rows ordered numerically, not lexicographically."""

    _validate_limit(limit)
    normalized_order = str(order).strip().lower()
    if normalized_order not in {"asc", "desc"}:
        raise ValueError("order must be 'asc' or 'desc'")
    direction = "ASC" if normalized_order == "asc" else "DESC"
    clauses, params = _location_filters(province=province)
    clauses.append("TRIM(aqi) REGEXP '^[0-9]+$'")
    sql = (
        f"SELECT {_AIR_SELECT} FROM air_quality_data "
        f"WHERE {' AND '.join(clauses)} "
        f"ORDER BY CAST(TRIM(aqi) AS UNSIGNED) {direction}, id ASC LIMIT %s"
    )
    params.append(limit)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def get_air_quality_distribution(
    city: str | None = None,
    province: str | None = None,
) -> list[dict[str, Any]]:
    """Return counts grouped by the source ``status`` text."""

    clauses, params = _location_filters(city=city, province=province)
    clauses.append("status IS NOT NULL")
    clauses.append("TRIM(status) <> ''")
    sql = (
        "SELECT status, COUNT(*) AS count FROM air_quality_data "
        f"WHERE {' AND '.join(clauses)} GROUP BY status ORDER BY status ASC LIMIT %s"
    )
    params.append(_MAX_DISTRIBUTION_GROUPS)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def get_all_air_quality(
    limit: int = _MAX_LIMIT,
    city: str | None = None,
    province: str | None = None,
) -> list[dict[str, Any]]:
    """Return a bounded set of raw AQI snapshots."""

    _validate_limit(limit)
    clauses, params = _location_filters(city=city, province=province)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT {_AIR_SELECT} FROM air_quality_data {where_sql} ORDER BY id ASC LIMIT %s"
    params.append(limit)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())
