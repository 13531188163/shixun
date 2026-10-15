"""Read-only temperature analysis queries for ``weather_data``.

The source table stores temperatures and dates as strings.  This repository
keeps numeric cleaning and canonical date filtering inside parameterized SQL
aggregates so a temperature page never has to load the weather table into
Python.
"""

from __future__ import annotations

from typing import Any

from ..utils.db import connection_scope
from . import weather_model


def _temperature_filters(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[list[str], list[Any]]:
    # The source dump stores observation dates in canonical YYYY-MM-DD text.
    # Comparing that text is chronological, avoids STR_TO_DATE for every row,
    # and allows the optional date index migration to be used by MySQL.
    clauses, params = weather_model._location_filters(
        province=province,
        city=city,
        district=district,
    )
    clauses.extend([
        "date IS NOT NULL",
        "date >= '0000-01-01'",
        "date <= '9999-12-31'",
    ])
    if start_date is not None:
        clauses.append("date >= %s")
        params.append(start_date)
    if end_date is not None:
        clauses.append("date <= %s")
        params.append(end_date)
    return clauses, params


def _numeric_temperature(column: str) -> str:
    return weather_model._numeric_expression(column, temperature=True)


def get_temperature_average(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any] | None:
    """Return area averages for maximum, minimum and derived mean temperature."""

    clauses, params = _temperature_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    max_temp = _numeric_temperature("max_temp")
    min_temp = _numeric_temperature("min_temp")
    sql = (
        f"SELECT COUNT(*) AS record_count, AVG({max_temp}) AS avg_max_temp, "
        f"AVG({min_temp}) AS avg_min_temp FROM weather_data "
        f"WHERE {' AND '.join(clauses)}"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def _temperature_extreme_query(
    expression: str,
    clauses: list[str],
    *,
    descending: bool,
) -> str:
    order = "DESC" if descending else "ASC"
    return (
        f"SELECT {expression} AS temperature, date FROM weather_data "
        f"WHERE {' AND '.join([*clauses, f'{expression} IS NOT NULL'])} "
        f"ORDER BY {expression} {order}, "
        "date DESC, id ASC LIMIT 1"
    )


def _latest_dates(cursor: Any, clauses: list[str], params: list[Any], days: int) -> list[str]:
    """Read only the bounded set of dates needed by a trend card."""

    sql = (
        "SELECT DISTINCT date FROM weather_data "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY date DESC LIMIT %s"
    )
    cursor.execute(sql, [*params, days])
    return [
        str(row.get("date")).strip()
        for row in cursor.fetchall()
        if row.get("date") is not None and str(row.get("date")).strip()
    ]


def _date_values_clause(dates: list[str]) -> tuple[str, list[str]]:
    """Build a parameterized date IN clause for a small bounded date list."""

    placeholders = ", ".join(["%s"] * len(dates))
    return f"date IN ({placeholders})", dates


def get_temperature_dates(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """Return the real observed dates available for a temperature scope."""

    clauses, params = _temperature_filters(
        province=province,
        city=city,
        district=district,
    )
    sql = (
        "SELECT DISTINCT date FROM weather_data "
        f"WHERE {' AND '.join(clauses)} "
        "ORDER BY date DESC LIMIT %s"
    )
    params.append(limit)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def get_temperature_extremes(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any] | None:
    """Return the highest maximum and lowest minimum temperatures and dates."""

    clauses, params = _temperature_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    max_temp = _numeric_temperature("max_temp")
    min_temp = _numeric_temperature("min_temp")
    max_sql = _temperature_extreme_query(max_temp, clauses, descending=True)
    min_sql = _temperature_extreme_query(min_temp, clauses, descending=False)
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(max_sql, list(params))
            highest = cursor.fetchone()
            cursor.execute(min_sql, list(params))
            lowest = cursor.fetchone()
    if not highest and not lowest:
        return None
    return {
        "max_temperature": highest.get("temperature") if highest else None,
        "max_date": highest.get("date") if highest else None,
        "min_temperature": lowest.get("temperature") if lowest else None,
        "min_date": lowest.get("date") if lowest else None,
    }


def get_temperature_trend(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 30,
) -> list[dict[str, Any]]:
    """Return date-level area-average maximum and minimum temperatures."""

    clauses, params = _temperature_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    max_temp = _numeric_temperature("max_temp")
    min_temp = _numeric_temperature("min_temp")
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            dates = _latest_dates(cursor, clauses, params, days)
            if not dates:
                return []
            date_clause, date_params = _date_values_clause(dates)
            aggregate_clauses = [*clauses, date_clause]
            sql = (
                "SELECT date, AVG(" + max_temp + ") AS max_temp, "
                "AVG(" + min_temp + ") AS min_temp FROM weather_data "
                f"WHERE {' AND '.join(aggregate_clauses)} "
                "GROUP BY date ORDER BY date DESC"
            )
            cursor.execute(sql, [*params, *date_params])
            return list(cursor.fetchall())


def get_temperature_monthly(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """Return observed monthly average temperatures ordered by month number."""

    clauses, params = _temperature_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    max_temp = _numeric_temperature("max_temp")
    min_temp = _numeric_temperature("min_temp")
    month_number = "CAST(SUBSTRING(date, 6, 2) AS UNSIGNED)"
    sql = (
        f"SELECT {month_number} AS month_number, "
        f"AVG(({max_temp} + {min_temp}) / 2) AS avg_temp FROM weather_data "
        f"WHERE {' AND '.join(clauses)} "
        f"GROUP BY {month_number} ORDER BY month_number ASC"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def get_recent_temperature(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 7,
) -> list[dict[str, Any]]:
    """Return recent date-level temperatures and observed weather descriptions."""

    clauses, params = _temperature_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    max_temp = _numeric_temperature("max_temp")
    min_temp = _numeric_temperature("min_temp")
    # 用最小/最大天气文本判断是否只有一种天气，避免对整张表执行
    # COUNT(DISTINCT ...)。全国范围查询时这会显著降低分组聚合的开销，
    # 同时保留“区域多种天气”的业务含义。
    weather_value = "NULLIF(TRIM(weather), '')"
    weather_expression = (
        f"CASE WHEN MIN({weather_value}) IS NULL THEN NULL "
        f"WHEN MIN({weather_value}) = MAX({weather_value}) THEN MAX({weather_value}) "
        "ELSE '区域多种天气' END"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            dates = _latest_dates(cursor, clauses, params, days)
            if not dates:
                return []
            date_clause, date_params = _date_values_clause(dates)
            aggregate_clauses = [*clauses, date_clause]
            sql = (
                "SELECT date, "
                f"{weather_expression} AS weather, AVG({max_temp}) AS max_temp, "
                f"AVG({min_temp}) AS min_temp FROM weather_data "
                f"WHERE {' AND '.join(aggregate_clauses)} "
                "GROUP BY date ORDER BY date DESC"
            )
            cursor.execute(sql, [*params, *date_params])
            return list(cursor.fetchall())
