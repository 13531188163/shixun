import unittest
from unittest.mock import patch

from weather_sys.backend.models.wind_analysis_model import _regional_daily_sql
from weather_sys.backend.services import wind_analysis_service as service


class WindLevelTests(unittest.TestCase):
    def test_beaufort_boundaries_are_continuous(self):
        expected = [(0.0, 0), (0.29, 0), (0.3, 1), (1.59, 1), (1.6, 2),
                    (3.39, 2), (3.4, 3), (5.49, 3), (5.5, 4), (7.99, 4),
                    (8.0, 5), (10.79, 5), (10.8, 6), (13.89, 6), (13.9, 7),
                    (17.19, 7), (17.2, 8), (20.79, 8), (20.8, 9)]
        for value, level in expected:
            self.assertEqual(service.classify_wind_level(value)["level"], level)

    def test_invalid_and_negative_values_are_missing(self):
        self.assertIsNone(service.classify_wind_level("--"))
        self.assertIsNone(service.classify_wind_level(-0.1))
        self.assertIsNone(service.classify_wind_level("not-a-speed"))


class WindServiceTests(unittest.TestCase):
    def test_hierarchy_sql_aggregates_daily_admin_units(self):
        sql = _regional_daily_sql(["date >= %s"], province=None, city=None, district=None)
        self.assertIn("GROUP BY province, city, district, date", sql)
        self.assertIn("GROUP BY province, city, date", sql)
        self.assertIn("GROUP BY province, date", sql)
        self.assertIn("GROUP BY date", sql)
        self.assertNotIn("SUM(avg_wind)", sql)
        self.assertNotIn("SUM(max_wind)", sql)

    @patch.object(service.wind_analysis_model, "get_wind_distribution")
    @patch.object(service.wind_analysis_model, "get_wind_core")
    def test_core_maps_units_and_dominant_level(self, core, distribution):
        core.return_value = {
            "avg_wind": "3.25", "max_wind": "8.10", "max_wind_date": "2026-05-22",
            "observation_days": 3, "observation_records": 12,
        }
        distribution.return_value = [{"level": 3, "count": 2}, {"level": 4, "count": 1}]
        result = service.get_wind_core(province="广东", start_date="2026-05-20", end_date="2026-05-22")
        self.assertEqual(result["avgWind"], 3.25)
        self.assertEqual(result["avgWindKmh"], 11.7)
        self.assertEqual(result["dominantLevel"]["level"], 3)
        self.assertEqual(result["maxWindDate"], "2026-05-22")

    @patch.object(service.wind_analysis_model, "get_wind_distribution")
    def test_distribution_always_returns_all_levels_and_percentages_sum(self, model):
        model.return_value = [{"level": 0, "count": 2}, {"level": 3, "count": 1}]
        result = service.get_wind_distribution()
        self.assertEqual(len(result), 10)
        self.assertEqual(sum(row["count"] for row in result), 3)
        self.assertAlmostEqual(sum(row["percentage"] for row in result), 100.0)

    @patch.object(service.wind_analysis_model, "get_wind_trend")
    def test_recent_rows_keep_missing_values(self, model):
        model.return_value = [{"date": "2026-05-22", "avg_wind": None, "max_wind": "5.1"}]
        result = service.get_recent_wind(end_date="2026-05-22")
        self.assertIsNone(result[0]["avgWind"])
        self.assertEqual(result[0]["maxWind"], 5.1)
        self.assertIsNone(result[0]["level"])


if __name__ == "__main__":
    unittest.main()
