"""Read-only access to the currently empty ``wind_data`` structure.

The table is kept separate from ``weather_data`` because its schema is a
different future extension.  These functions never synthesize wind records;
an empty table naturally produces ``False`` or ``[]``.
"""

from __future__ import annotations

from typing import Any

from ..utils.db import connection_scope
from ..utils.location_utils import city_query_values


WIND_COLUMNS = (
    "id",
    "city",
    "year",
    "month",
    "date",
    "weather",
    "max_temp",
    "min_temp",
    "wind",
    "created_at",
)
_WIND_SELECT = ", ".join(WIND_COLUMNS)
_MAX_LIMIT = 500


def _validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if not 1 <= limit <= _MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {_MAX_LIMIT}")


def has_wind_data() -> bool:
    """Return whether at least one source row exists."""

    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS has_data FROM wind_data LIMIT 1")
            return cursor.fetchone() is not None


def get_wind_data(city: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Return a bounded newest-first set of raw wind rows."""

    _validate_limit(limit)
    clauses: list[str] = []
    params: list[Any] = []
    if city is not None and str(city).strip():
        values = city_query_values(str(city).strip())
        placeholders = ", ".join(["%s"] * len(values))
        clauses.append(f"city IN ({placeholders})")
        params.extend(values)
    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        f"SELECT {_WIND_SELECT} FROM wind_data {where_sql} "
        "ORDER BY STR_TO_DATE(NULLIF(TRIM(date), ''), '%%Y-%%m-%%d') DESC, id DESC LIMIT %s"
    )
    params.append(limit)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def get_latest_wind(city: str) -> dict[str, Any] | None:
    """Return the latest raw wind row for a city, or ``None`` when absent."""

    if city is None or not str(city).strip():
        raise ValueError("city is required")
    values = city_query_values(str(city).strip())
    placeholders = ", ".join(["%s"] * len(values))
    sql = (
        f"SELECT {_WIND_SELECT} FROM wind_data WHERE city IN ({placeholders}) "
        "ORDER BY STR_TO_DATE(NULLIF(TRIM(date), ''), '%%Y-%%m-%%d') DESC, id DESC LIMIT 1"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, list(values))
            return cursor.fetchone()


def get_wind_history(city: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """Compatibility alias for future services needing bounded history."""

    return get_wind_data(city=city, limit=limit)
