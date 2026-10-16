"""Hierarchy-aware wind statistics over the real ``weather_data`` table."""

from __future__ import annotations

from typing import Any

from ..utils.db import connection_scope
from . import weather_model

_MAX_DATE_LIMIT = 1000


def _wind_expression(column: str) -> str:
    """Parse the dump's numeric m/s strings and reject invalid/negative values."""

    cleaned = (
        f"TRIM(REPLACE(REPLACE(REPLACE(LOWER({column}), 'm/s', ''), "
        "'m／s', ''), '米/秒', ''))"
    )
    return (
        f"CASE WHEN {cleaned} REGEXP '^[0-9]+(\\.[0-9]+)?$' "
        f"THEN CAST({cleaned} AS DECIMAL(12, 3)) END"
    )


def _filters(*, province=None, city=None, district=None, start_date=None, end_date=None):
    clauses, params = weather_model._location_filters(
        province=province, city=city, district=district,
    )
    clauses.extend([
        "date IS NOT NULL", "TRIM(date) <> ''",
        "date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'",
    ])
    if start_date is not None:
        clauses.append("date >= %s")
        params.append(start_date)
    if end_date is not None:
        clauses.append("date <= %s")
        params.append(end_date)
    return clauses, params


def _regional_daily_sql(clauses, *, province=None, city=None, district=None):
    where_sql = " AND ".join(clauses)
    avg_wind = _wind_expression("avg_wind")
    max_wind = _wind_expression("max_wind")
    district_daily = (
        "SELECT province, city, district, date, "
        f"AVG({avg_wind}) AS avg_wind, AVG({max_wind}) AS max_wind, "
        f"COUNT({avg_wind}) AS source_records "
        "FROM weather_data "
        f"WHERE {where_sql} AND ({avg_wind} IS NOT NULL OR {max_wind} IS NOT NULL) "
        "GROUP BY province, city, district, date"
    )
    city_daily = (
        "SELECT province, city, date, AVG(avg_wind) AS avg_wind, "
        "AVG(max_wind) AS max_wind, SUM(source_records) AS source_records "
        f"FROM ({district_daily}) AS district_daily GROUP BY province, city, date"
    )
    province_daily = (
        "SELECT province, date, AVG(avg_wind) AS avg_wind, AVG(max_wind) AS max_wind, "
        "SUM(source_records) AS source_records "
        f"FROM ({city_daily}) AS city_daily GROUP BY province, date"
    )
    national_daily = (
        "SELECT date, AVG(avg_wind) AS avg_wind, AVG(max_wind) AS max_wind, "
        "SUM(source_records) AS source_records "
        f"FROM ({province_daily}) AS province_daily GROUP BY date"
    )
    scoped = district_daily if district else city_daily if city else province_daily if province else national_daily
    return (
        "SELECT date, AVG(avg_wind) AS avg_wind, AVG(max_wind) AS max_wind, "
        "SUM(source_records) AS source_records "
        f"FROM ({scoped}) AS scoped_daily GROUP BY date"
    )


def _valid_clause():
    avg_wind = _wind_expression("avg_wind")
    max_wind = _wind_expression("max_wind")
    return f"({avg_wind} IS NOT NULL OR {max_wind} IS NOT NULL)"


def _date_values_clause(dates: list[str]):
    return f"date IN ({', '.join(['%s'] * len(dates))})", dates


def _latest_dates(cursor: Any, clauses, params, limit: int):
    sql = (
        "SELECT DISTINCT date FROM weather_data "
        f"WHERE {' AND '.join([*clauses, _valid_clause()])} "
        "ORDER BY date DESC LIMIT %s"
    )
    cursor.execute(sql, [*params, limit])
    return [str(row["date"]).strip() for row in cursor.fetchall() if row.get("date")]


def get_wind_dates(*, province=None, city=None, district=None, limit=_MAX_DATE_LIMIT):
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= _MAX_DATE_LIMIT:
        raise ValueError(f"limit must be an integer between 1 and {_MAX_DATE_LIMIT}")
    clauses, params = _filters(province=province, city=city, district=district)
    sql = (
        "SELECT DISTINCT date FROM weather_data "
        f"WHERE {' AND '.join([*clauses, _valid_clause()])} ORDER BY date DESC LIMIT %s"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, [*params, limit])
            return list(cursor.fetchall())


def get_wind_core(*, province=None, city=None, district=None, start_date=None, end_date=None):
    clauses, params = _filters(
        province=province, city=city, district=district,
        start_date=start_date, end_date=end_date,
    )
    daily = _regional_daily_sql(clauses, province=province, city=city, district=district)
    aggregate_sql = (
        "SELECT COUNT(avg_wind) AS observation_days, SUM(source_records) AS observation_records, "
        "AVG(avg_wind) AS avg_wind, MAX(max_wind) AS max_wind "
        f"FROM ({daily}) AS regional_daily"
    )
    max_sql = (
        f"SELECT date FROM ({daily}) AS regional_daily WHERE max_wind IS NOT NULL "
        "ORDER BY max_wind DESC, date DESC LIMIT 1"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(aggregate_sql, params)
            aggregate = cursor.fetchone()
            cursor.execute(max_sql, list(params))
            peak = cursor.fetchone()
    if not aggregate or not aggregate.get("observation_days"):
        return None
    return {**aggregate, "max_wind_date": peak.get("date") if peak else None}


def get_wind_trend(*, province=None, city=None, district=None, start_date=None, end_date=None, days=30):
    clauses, params = _filters(
        province=province, city=city, district=district,
        start_date=start_date, end_date=end_date,
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            dates = _latest_dates(cursor, clauses, params, days)
            if not dates:
                return []
            date_clause, date_params = _date_values_clause(dates)
            daily = _regional_daily_sql(
                [*clauses, date_clause], province=province, city=city, district=district,
            )
            cursor.execute(
                f"SELECT date, avg_wind, max_wind FROM ({daily}) AS regional_daily ORDER BY date DESC",
                [*params, *date_params],
            )
            return list(cursor.fetchall())


def get_recent_wind(*, province=None, city=None, district=None, start_date=None, end_date=None, days=7):
    return get_wind_trend(
        province=province, city=city, district=district,
        start_date=start_date, end_date=end_date, days=days,
    )


def get_wind_distribution(*, province=None, city=None, district=None, start_date=None, end_date=None):
    clauses, params = _filters(
        province=province, city=city, district=district,
        start_date=start_date, end_date=end_date,
    )
    daily = _regional_daily_sql(clauses, province=province, city=city, district=district)
    level = (
        "CASE WHEN avg_wind < 0.3 THEN 0 WHEN avg_wind < 1.6 THEN 1 "
        "WHEN avg_wind < 3.4 THEN 2 WHEN avg_wind < 5.5 THEN 3 "
        "WHEN avg_wind < 8.0 THEN 4 WHEN avg_wind < 10.8 THEN 5 "
        "WHEN avg_wind < 13.9 THEN 6 WHEN avg_wind < 17.2 THEN 7 "
        "WHEN avg_wind < 20.8 THEN 8 ELSE 9 END"
    )
    sql = (
        f"SELECT {level} AS level, COUNT(*) AS count FROM ({daily}) AS regional_daily "
        "WHERE avg_wind IS NOT NULL GROUP BY level ORDER BY level"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())
