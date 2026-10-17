"""Bounded daily weather queries for the region comparison page."""

from __future__ import annotations

from typing import Any, Iterable

from ..utils.db import connection_scope
from ..utils.location_utils import city_query_values, province_query_values


def _numeric(column: str, *, temperature: bool = False) -> str:
    cleaned = f"TRIM(REPLACE(REPLACE(REPLACE(LOWER({column}), '℃', ''), '°c', ''), 'm/s', ''))"
    if temperature:
        cleaned = f"TRIM(REPLACE(REPLACE(REPLACE({column}, '℃', ''), '°C', ''), '°c', ''))"
    return f"CASE WHEN {cleaned} REGEXP '^[+-]?[0-9]+(\\.[0-9]+)?$' THEN CAST({cleaned} AS DECIMAL(12, 3)) END"


def _in_clause(column: str, values: Iterable[str]) -> tuple[str, list[str]]:
    values = tuple(dict.fromkeys(values))
    return f"{column} IN ({', '.join(['%s'] * len(values))})", list(values)


def get_comparison_locations(limit: int = 1000) -> list[dict[str, Any]]:
    sql = (
        "SELECT DISTINCT province, city FROM weather_data "
        "WHERE province IS NOT NULL AND city IS NOT NULL "
        "ORDER BY province, city LIMIT %s"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, [limit])
            return list(cursor.fetchall())


def get_date_bounds() -> dict[str, Any] | None:
    sql = (
        "SELECT MIN(date) AS start_date, MAX(date) AS end_date FROM weather_data "
        "WHERE date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchone()


def get_comparison_daily(refs: list[dict[str, str]], start_date: str, end_date: str) -> list[dict[str, Any]]:
    predicates: list[str] = []
    params: list[Any] = []
    for ref in refs:
        province_clause, province_params = _in_clause("province", province_query_values(ref["province"]))
        city_clause, city_params = _in_clause("city", city_query_values(ref["city"]))
        predicates.append(f"({province_clause} AND {city_clause})")
        params.extend(province_params)
        params.extend(city_params)
    max_temp = _numeric("max_temp", temperature=True)
    min_temp = _numeric("min_temp", temperature=True)
    avg_wind = _numeric("avg_wind")
    max_wind = _numeric("max_wind")
    precip = _numeric("total_precip")
    where = (
        f"({' OR '.join(predicates)}) AND date >= %s AND date <= %s "
        "AND date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'"
    )
    params.extend([start_date, end_date])
    district_daily = (
        "SELECT province, city, district, date, "
        f"AVG({max_temp}) AS max_temp, AVG({min_temp}) AS min_temp, "
        f"AVG({avg_wind}) AS avg_wind, AVG({max_wind}) AS max_wind, AVG({precip}) AS precip "
        f"FROM weather_data WHERE {where} GROUP BY province, city, district, date"
    )
    sql = (
        "SELECT province, city, date, AVG(max_temp) AS max_temp, AVG(min_temp) AS min_temp, "
        "AVG(avg_wind) AS avg_wind, AVG(max_wind) AS max_wind, AVG(precip) AS precip "
        f"FROM ({district_daily}) AS district_daily GROUP BY province, city, date "
        "ORDER BY date, province, city"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def get_radar_weather_baseline(common_dates: Iterable[str]) -> dict[str, Any]:
    """Return real weather-city ranges for radar normalization.

    The baseline uses the same district-day -> city-day aggregation as the
    comparison metrics, but it is calculated across every weather city on the
    selected comparable dates.  This keeps two-city comparisons from turning
    into a misleading 0/1 min-max contrast while avoiding invented bounds.
    """

    dates = tuple(dict.fromkeys(str(value) for value in common_dates if value))
    if not dates:
        return {}

    date_clause, date_params = _in_clause("date", dates)
    max_temp = _numeric("max_temp", temperature=True)
    min_temp = _numeric("min_temp", temperature=True)
    avg_wind = _numeric("avg_wind")
    precip = _numeric("total_precip")
    district_daily = (
        "SELECT province, city, district, date, "
        f"AVG({max_temp}) AS max_temp, AVG({min_temp}) AS min_temp, "
        f"AVG({avg_wind}) AS avg_wind, AVG({precip}) AS precip "
        f"FROM weather_data WHERE {date_clause} "
        "AND date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' "
        "GROUP BY province, city, district, date"
    )
    city_daily = (
        "SELECT province, city, date, AVG(max_temp) AS max_temp, "
        "AVG(min_temp) AS min_temp, AVG(avg_wind) AS avg_wind, "
        "AVG(precip) AS precip "
        f"FROM ({district_daily}) AS district_daily "
        "GROUP BY province, city, date"
    )
    city_summary = (
        "SELECT province, city, AVG(max_temp) AS avg_max_temp, "
        "AVG(min_temp) AS avg_min_temp, SUM(precip) AS total_precip, "
        "AVG(avg_wind) AS avg_wind "
        f"FROM ({city_daily}) AS city_daily GROUP BY province, city"
    )
    temperature_estimate = (
        "CASE WHEN avg_max_temp IS NOT NULL AND avg_min_temp IS NOT NULL "
        "THEN (avg_max_temp + avg_min_temp) / 2 END"
    )
    sql = (
        f"SELECT MIN({temperature_estimate}) AS avg_temp_min, "
        f"MAX({temperature_estimate}) AS avg_temp_max, "
        "MIN(total_precip) AS total_precip_min, MAX(total_precip) AS total_precip_max, "
        "MIN(avg_wind) AS avg_wind_min, MAX(avg_wind) AS avg_wind_max "
        f"FROM ({city_summary}) AS city_summary"
    )
    with connection_scope() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, date_params)
            return cursor.fetchone() or {}
