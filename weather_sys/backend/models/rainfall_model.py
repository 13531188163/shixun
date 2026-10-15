"""Read-only rainfall analysis queries for ``weather_data``.

The source dump stores district-level ``total_precip`` and ``date`` values as
strings. This model keeps numeric conversion and date/location filtering in
parameterized SQL, and builds hierarchy-aware regional daily values before
returning database-shaped dictionaries for the service layer.
"""

from __future__ import annotations

from typing import Any

from ..utils.db import connection_scope
from . import weather_model


_MAX_DATE_LIMIT = 1000


def _rainfall_filters(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> tuple[list[str], list[Any]]:
    """Build fixed-column location/date predicates and bound parameters."""

    clauses, params = weather_model._location_filters(
        province=province,
        city=city,
        district=district,
    )
    # The dump uses canonical YYYY-MM-DD text.  Text comparison is
    # chronological for this format and can use the date migration index.
    clauses.extend([
        "date IS NOT NULL",
        "TRIM(date) <> ''",
        "date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'",
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


def _precipitation_expression() -> str:
    """Return a fixed SQL expression that parses numeric precipitation."""

    cleaned = "TRIM(total_precip)"
    return (
        f"CASE WHEN {cleaned} REGEXP '^[0-9]+(\\.[0-9]+)?$' "
        f"THEN CAST({cleaned} AS DECIMAL(12, 2)) END"
    )


def _validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= _MAX_DATE_LIMIT:
        raise ValueError(f"limit must be an integer between 1 and {_MAX_DATE_LIMIT}")


def _validate_days(days: int, maximum: int) -> None:
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= maximum:
        raise ValueError(f"days must be an integer between 1 and {maximum}")


def _latest_dates(cursor: Any, clauses: list[str], params: list[Any], days: int) -> list[str]:
    valid_precipitation = (
        "TRIM(total_precip) REGEXP '^[0-9]+(\\.[0-9]+)?$'"
    )
    sql = (
        "SELECT DISTINCT date FROM weather_data "
        f"WHERE {' AND '.join([*clauses, valid_precipitation])} "
        "ORDER BY date DESC LIMIT %s"
    )
    cursor.execute(sql, [*params, days])
    return [
        str(row.get("date")).strip()
        for row in cursor.fetchall()
        if row.get("date") is not None and str(row.get("date")).strip()
    ]


def _date_values_clause(dates: list[str]) -> tuple[str, list[str]]:
    placeholders = ", ".join(["%s"] * len(dates))
    return f"date IN ({placeholders})", dates


def _regional_daily_sql(
    clauses: list[str],
    *,
    precipitation: str,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
) -> str:
    """Build one daily precipitation series for the selected admin level.

    ``weather_data`` contains district-level observations only.  Aggregating
    raw rows directly would weight a date by the number of districts in the
    selected scope.  The nested levels below give every child admin unit one
    vote for each date: duplicate source rows are collapsed at district level,
    then district → city → province → national means are calculated.
    """

    where_sql = " AND ".join(clauses)
    district_daily = (
        "SELECT province, city, district, date, "
        f"AVG({precipitation}) AS precip, "
        f"COUNT({precipitation}) AS source_records "
        "FROM weather_data "
        f"WHERE {where_sql} "
        "GROUP BY province, city, district, date"
    )
    city_daily = (
        "SELECT province, city, date, AVG(precip) AS precip, "
        "SUM(source_records) AS source_records "
        f"FROM ({district_daily}) AS district_daily "
        "GROUP BY province, city, date"
    )
    province_daily = (
        "SELECT province, date, AVG(precip) AS precip, "
        "SUM(source_records) AS source_records "
        f"FROM ({city_daily}) AS city_daily "
        "GROUP BY province, date"
    )
    national_daily = (
        "SELECT date, AVG(precip) AS precip, "
        "SUM(source_records) AS source_records "
        f"FROM ({province_daily}) AS province_daily "
        "GROUP BY date"
    )

    if district:
        scoped_daily = district_daily
    elif city:
        scoped_daily = city_daily
    elif province:
        scoped_daily = province_daily
    else:
        scoped_daily = national_daily

    # The final grouping produces the same shape for every scope and removes
    # any duplicate keys that can remain when a caller omits a parent filter.
    return (
        "SELECT date, AVG(precip) AS precip, "
        "SUM(source_records) AS source_records "
        f"FROM ({scoped_daily}) AS scoped_daily "
        "GROUP BY date"
    )


def get_rainfall_dates(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    limit: int = _MAX_DATE_LIMIT,
) -> list[dict[str, Any]]:
    """Return actual historical dates available for a selected scope."""

    _validate_limit(limit)
    clauses, params = _rainfall_filters(
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


def get_rainfall_core(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any] | None:
    """Return indicators calculated from one hierarchy-aware regional value per day."""

    clauses, params = _rainfall_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    precipitation = _precipitation_expression()
    daily_sql = _regional_daily_sql(
        clauses,
        precipitation=precipitation,
        province=province,
        city=city,
        district=district,
    )
    sql = (
        "SELECT COUNT(precip) AS observation_days, "
        "SUM(source_records) AS observation_records, "
        "SUM(precip) AS total_precip, "
        "AVG(precip) AS avg_precip, "
        "MAX(precip) AS max_precip, "
        "COUNT(CASE WHEN precip > 0 THEN 1 END) AS rainy_days "
        f"FROM ({daily_sql}) AS regional_daily"
    )
    max_date_sql = (
        f"SELECT date FROM ({daily_sql}) AS regional_daily "
        "WHERE precip IS NOT NULL "
        "ORDER BY precip DESC, date DESC LIMIT 1"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            aggregate = cursor.fetchone()
            cursor.execute(max_date_sql, list(params))
            max_date = cursor.fetchone()
    if not aggregate or int(aggregate.get("observation_days") or 0) == 0:
        return None
    return {
        **aggregate,
        "max_precip_date": max_date.get("date") if max_date else None,
    }


def get_recent_rainfall(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 7,
) -> list[dict[str, Any]]:
    """Return hierarchy-aware regional precipitation and weather for recent dates."""

    _validate_days(days, 30)
    clauses, params = _rainfall_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    precipitation = _precipitation_expression()
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            dates = _latest_dates(cursor, clauses, params, days)
            if not dates:
                return []
            date_clause, date_params = _date_values_clause(dates)
            aggregate_clauses = [*clauses, date_clause]
            daily_sql = _regional_daily_sql(
                aggregate_clauses,
                precipitation=precipitation,
                province=province,
                city=city,
                district=district,
            )
            weather_sql = (
                "SELECT date, MIN(NULLIF(TRIM(weather), '')) AS min_weather, "
                "MAX(NULLIF(TRIM(weather), '')) AS max_weather "
                "FROM weather_data "
                f"WHERE {' AND '.join(aggregate_clauses)} "
                "GROUP BY date"
            )
            weather_expression = (
                "CASE WHEN weather_daily.min_weather IS NULL THEN NULL "
                "WHEN weather_daily.min_weather = weather_daily.max_weather "
                "THEN weather_daily.max_weather ELSE '区域多种天气' END"
            )
            sql = (
                "SELECT regional_daily.date, regional_daily.precip, "
                f"{weather_expression} AS weather "
                f"FROM ({daily_sql}) AS regional_daily "
                f"LEFT JOIN ({weather_sql}) AS weather_daily "
                "ON weather_daily.date = regional_daily.date "
                "ORDER BY regional_daily.date DESC"
            )
            cursor.execute(sql, [*params, *date_params, *params, *date_params])
            return list(cursor.fetchall())


def get_rainfall_trend(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    days: int = 30,
) -> list[dict[str, Any]]:
    """Return hierarchy-aware regional precipitation for recent observation dates."""

    _validate_days(days, 90)
    clauses, params = _rainfall_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    precipitation = _precipitation_expression()
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            dates = _latest_dates(cursor, clauses, params, days)
            if not dates:
                return []
            date_clause, date_params = _date_values_clause(dates)
            aggregate_clauses = [*clauses, date_clause]
            daily_sql = _regional_daily_sql(
                aggregate_clauses,
                precipitation=precipitation,
                province=province,
                city=city,
                district=district,
            )
            sql = f"SELECT date, precip FROM ({daily_sql}) AS regional_daily ORDER BY date DESC"
            cursor.execute(sql, [*params, *date_params])
            return list(cursor.fetchall())


def get_rainfall_distribution(
    *,
    province: str | None = None,
    city: str | None = None,
    district: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    """Count hierarchy-aware regional daily precipitation by fixed levels."""

    clauses, params = _rainfall_filters(
        province=province,
        city=city,
        district=district,
        start_date=start_date,
        end_date=end_date,
    )
    precipitation = _precipitation_expression()
    level_expression = (
        "CASE WHEN regional_daily.precip IS NULL OR regional_daily.precip <= 0 THEN '无降水' "
        "WHEN regional_daily.precip < 10 THEN '小雨' "
        "WHEN regional_daily.precip < 25 THEN '中雨' "
        "WHEN regional_daily.precip < 50 THEN '大雨' "
        "ELSE '暴雨' END"
    )
    daily_sql = _regional_daily_sql(
        clauses,
        precipitation=precipitation,
        province=province,
        city=city,
        district=district,
    )
    sql = (
        f"SELECT {level_expression} AS level, COUNT(*) AS count "
        f"FROM ({daily_sql}) AS regional_daily "
        "WHERE regional_daily.precip IS NOT NULL "
        f"GROUP BY {level_expression} "
        "ORDER BY FIELD(level, '无降水', '小雨', '中雨', '大雨', '暴雨')"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())
