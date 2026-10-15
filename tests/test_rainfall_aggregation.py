"""Regression tests for the rainfall daily-aggregation contract.

These tests do not connect to MySQL.  The fixture mirrors the source table's
district-level grain, including a duplicate district/date row and a zero-rain
day.  The SQL-shape assertions protect the production query from regressing
to a spatial ``SUM(total_precip)`` or a raw-record rainy-day count.
"""

from __future__ import annotations

import unittest
from collections import defaultdict
from contextlib import contextmanager
from unittest.mock import patch

from weather_sys.backend.models import rainfall_model
from weather_sys.backend.services import rainfall_service


ROWS = [
    # 2026-05-01: duplicate d1 rows must be averaged before city/province means.
    {"province": "甲省", "city": "甲市", "district": "甲区", "date": "2026-05-01", "precip": 2},
    {"province": "甲省", "city": "甲市", "district": "甲区", "date": "2026-05-01", "precip": 4},
    {"province": "甲省", "city": "甲市", "district": "乙区", "date": "2026-05-01", "precip": 5},
    {"province": "甲省", "city": "乙市", "district": "丙区", "date": "2026-05-01", "precip": 10},
    {"province": "乙省", "city": "丙市", "district": "丁区", "date": "2026-05-01", "precip": 0},
    # A second rainy date and a valid zero-rain date keep rainyDays distinct.
    {"province": "甲省", "city": "甲市", "district": "甲区", "date": "2026-05-02", "precip": 4},
    {"province": "甲省", "city": "乙市", "district": "丙区", "date": "2026-05-02", "precip": 20},
    {"province": "乙省", "city": "丙市", "district": "丁区", "date": "2026-05-02", "precip": 2},
    {"province": "甲省", "city": "甲市", "district": "甲区", "date": "2026-05-03", "precip": 0},
    {"province": "甲省", "city": "乙市", "district": "丙区", "date": "2026-05-03", "precip": 0},
    {"province": "乙省", "city": "丙市", "district": "丁区", "date": "2026-05-03", "precip": 0},
]


def reference_national_daily(rows):
    """Compute the documented equal-weight hierarchy for a small fixture."""

    district_values = defaultdict(list)
    for row in rows:
        district_values[
            (row["province"], row["city"], row["district"], row["date"])
        ].append(float(row["precip"]))
    district_daily = {
        key: sum(values) / len(values) for key, values in district_values.items()
    }

    city_values = defaultdict(list)
    for (province, city, _district, date), value in district_daily.items():
        city_values[(province, city, date)].append(value)
    city_daily = {key: sum(values) / len(values) for key, values in city_values.items()}

    province_values = defaultdict(list)
    for (province, _city, date), value in city_daily.items():
        province_values[(province, date)].append(value)
    province_daily = {key: sum(values) / len(values) for key, values in province_values.items()}

    national_values = defaultdict(list)
    for (province, date), value in province_daily.items():
        national_values[date].append(value)
    return {
        date: sum(values) / len(values)
        for date, values in national_values.items()
    }


class _Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params or [])))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        return []


class _Connection:
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def cursor(self):
        return self._cursor


class RainfallAggregationTests(unittest.TestCase):
    def test_reference_daily_metrics_use_hierarchy_means(self):
        daily = reference_national_daily(ROWS)
        self.assertEqual(daily, {
            "2026-05-01": 3.5,
            "2026-05-02": 7.0,
            "2026-05-03": 0.0,
        })
        self.assertAlmostEqual(sum(daily.values()), 10.5)
        self.assertEqual(max(daily.values()), 7.0)
        self.assertEqual(sum(value > 0 for value in daily.values()), 2)
        self.assertEqual(len(daily), 3)

        distribution = {
            "无降水": sum(value <= 0 for value in daily.values()),
            "小雨": sum(0 < value < 10 for value in daily.values()),
            "中雨": sum(10 <= value < 25 for value in daily.values()),
            "大雨": sum(25 <= value < 50 for value in daily.values()),
            "暴雨": sum(value >= 50 for value in daily.values()),
        }
        self.assertEqual(sum(distribution.values()), len(daily))
        self.assertEqual(distribution, {"无降水": 1, "小雨": 2, "中雨": 0, "大雨": 0, "暴雨": 0})

    def test_sql_has_hierarchy_levels_and_no_spatial_sum(self):
        clauses, _params = rainfall_model._rainfall_filters(start_date="2026-05-01", end_date="2026-05-03")
        scopes = (
            ({}, ("GROUP BY province, city, district, date", "GROUP BY province, city, date", "GROUP BY province, date", "GROUP BY date")),
            ({"province": "甲省"}, ("GROUP BY province, city, district, date", "GROUP BY province, city, date", "GROUP BY province, date", "GROUP BY date")),
            ({"province": "甲省", "city": "甲市"}, ("GROUP BY province, city, district, date", "GROUP BY province, city, date", "GROUP BY date")),
            ({"province": "甲省", "city": "甲市", "district": "甲区"}, ("GROUP BY province, city, district, date", "GROUP BY date")),
        )
        for scope, grouping_levels in scopes:
            sql = rainfall_model._regional_daily_sql(
                clauses,
                precipitation=rainfall_model._precipitation_expression(),
                **scope,
            )
            self.assertNotIn("SUM(total_precip)", sql)
            self.assertIn("COUNT(", sql)
            self.assertIn("SUM(source_records)", sql)
            for grouping in grouping_levels:
                self.assertIn(grouping, sql)

    def test_core_keeps_daily_days_and_source_records_separate(self):
        cursor = _Cursor([
            {
                "observation_days": 3,
                "observation_records": 11,
                "total_precip": 10.5,
                "avg_precip": 3.5,
                "max_precip": 7.0,
                "rainy_days": 2,
            },
            {"date": "2026-05-02"},
        ])

        @contextmanager
        def connection_scope_stub():
            yield _Connection(cursor)

        with patch.object(rainfall_model, "connection_scope", connection_scope_stub):
            result = rainfall_model.get_rainfall_core(
                start_date="2026-05-01",
                end_date="2026-05-03",
            )

        self.assertEqual(result["observation_days"], 3)
        self.assertEqual(result["observation_records"], 11)
        self.assertEqual(result["rainy_days"], 2)
        self.assertEqual(result["max_precip_date"], "2026-05-02")
        aggregate_sql = cursor.calls[0][0]
        self.assertIn("COUNT(precip) AS observation_days", aggregate_sql)
        self.assertIn("SUM(source_records) AS observation_records", aggregate_sql)
        self.assertIn("COUNT(CASE WHEN precip > 0 THEN 1 END)", aggregate_sql)
        self.assertNotIn("SUM(total_precip)", aggregate_sql)

    @patch.object(rainfall_service.rainfall_model, "get_rainfall_core")
    def test_service_exposes_counts_without_coercing_unknown_to_zero(self, model_call):
        model_call.return_value = {
            "total_precip": "10.5",
            "avg_precip": "3.5",
            "max_precip": "7",
            "max_precip_date": "2026-05-02",
            "rainy_days": "2",
            "observation_days": "3",
            "observation_records": "11",
        }
        result = rainfall_service.get_rainfall_core(start_date="2026-05-01", end_date="2026-05-03")
        self.assertEqual(result["rainyDays"], 2)
        self.assertEqual(result["observationDays"], 3)
        self.assertEqual(result["observationRecords"], 11)

        model_call.return_value = {
            "total_precip": None,
            "avg_precip": None,
            "max_precip": None,
            "max_precip_date": None,
            "rainy_days": None,
            "observation_days": None,
            "observation_records": None,
        }
        self.assertIsNone(rainfall_service.get_rainfall_core())

    @patch.object(rainfall_service.rainfall_model, "get_recent_rainfall")
    def test_recent_keeps_null_measurements_and_normalizes_blank_weather(self, model_call):
        model_call.return_value = [
            {"date": "2026-05-02", "precip": None, "weather": "  "},
            {"date": "2026-05-01", "precip": "2.5", "weather": "区域多种天气"},
        ]
        result = rainfall_service.get_recent_rainfall()
        self.assertEqual(result, [
            {"date": "2026-05-01", "precip": 2.5, "weather": "区域多种天气"},
            {"date": "2026-05-02", "precip": None, "weather": None},
        ])

    @patch.object(rainfall_service.rainfall_model, "get_rainfall_distribution")
    def test_distribution_always_returns_fixed_levels_whose_counts_are_daily(self, model_call):
        model_call.return_value = [
            {"level": "无降水", "count": 1},
            {"level": "小雨", "count": 2},
        ]
        result = rainfall_service.get_rainfall_distribution(
            province="甲省",
            start_date="2026-05-01",
            end_date="2026-05-03",
        )
        self.assertEqual([row["level"] for row in result], ["无降水", "小雨", "中雨", "大雨", "暴雨"])
        self.assertEqual(sum(row["count"] for row in result), 3)


if __name__ == "__main__":
    unittest.main()
