"""Small model tests.

The integration class is opt-in so the pure unit suite remains useful without
MySQL.  When ``RUN_DB_TESTS=1`` is set, all assertions below are read-only
SELECT-backed checks against the configured ``weather_db``.
"""

from __future__ import annotations

import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from weather_sys.backend.models import air_quality_model, weather_model, wind_model


RUN_DB_TESTS = os.getenv("RUN_DB_TESTS", "").strip().lower() in {"1", "true", "yes", "on"}


class ModelValidationTests(unittest.TestCase):
    def test_limits_are_bounded(self):
        with self.assertRaises(ValueError):
            weather_model.get_weather_history("北京", limit=0)
        with self.assertRaises(ValueError):
            air_quality_model.get_air_quality_ranking(limit=1001)
        with self.assertRaises(ValueError):
            wind_model.get_wind_data(limit=0)

    def test_required_location_arguments(self):
        with self.assertRaises(ValueError):
            weather_model.get_latest_weather("")
        with self.assertRaises(ValueError):
            air_quality_model.get_latest_air_quality("")
        with self.assertRaises(ValueError):
            wind_model.get_latest_wind("")

    def test_national_weather_sql_avoids_cte_requirement(self):
        sql = weather_model._national_weather_daily_sql("date = %s")
        self.assertNotIn("WITH ", sql.upper())
        self.assertIn("GROUP BY province, city", sql)
        self.assertIn("GROUP BY province, date", sql)
        self.assertIn("GROUP BY date", sql)

    def test_city_trend_sql_avoids_window_function(self):
        class Cursor:
            def __init__(self):
                self.sql = ""
                self.params = []

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def execute(self, sql, params):
                self.sql = sql
                self.params = params

            def fetchall(self):
                return []

        cursor = Cursor()

        class Connection:
            def cursor(self):
                return cursor

            def close(self):
                return None

        @contextmanager
        def connection_scope_stub():
            yield Connection()

        with patch.object(weather_model, "connection_scope", connection_scope_stub):
            self.assertEqual(weather_model.get_weather_history_by_date("北京", days=2), [])
        self.assertNotIn("ROW_NUMBER", cursor.sql.upper())
        self.assertIn("NOT EXISTS", cursor.sql.upper())


@unittest.skipUnless(RUN_DB_TESTS, "set RUN_DB_TESTS=1 for MySQL read-only integration checks")
class ModelDatabaseReadOnlyTests(unittest.TestCase):
    def test_weather_queries_are_bounded_and_return_raw_fields(self):
        provinces = weather_model.get_distinct_provinces(limit=3)
        self.assertLessEqual(len(provinces), 3)
        latest = weather_model.get_latest_weather("北京市", province="北京市")
        self.assertIsNotNone(latest)
        self.assertIn("max_temp", latest)
        self.assertIn("date", latest)
        history = weather_model.get_weather_history("北京市", province="北京市", limit=3)
        self.assertLessEqual(len(history), 3)

    def test_air_quality_queries_cast_aqi_numerically(self):
        rows = air_quality_model.get_air_quality_ranking(limit=10)
        self.assertLessEqual(len(rows), 10)
        values = [int(row["aqi"]) for row in rows]
        self.assertEqual(values, sorted(values))
        distribution = air_quality_model.get_air_quality_distribution()
        self.assertTrue(all("status" in row and "count" in row for row in distribution))

    def test_wind_table_is_not_fabricated(self):
        self.assertFalse(wind_model.has_wind_data())
        self.assertEqual(wind_model.get_wind_data(limit=5), [])


if __name__ == "__main__":
    unittest.main()
