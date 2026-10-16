import unittest
from unittest.mock import patch

from weather_sys.backend.models.air_quality_model import _latest_snapshot_sql
from weather_sys.backend.services import air_quality_service as service


class AirQualityAnalysisTests(unittest.TestCase):
    def test_numeric_aqi_levels(self):
        self.assertEqual(service.classify_aqi(50), "优")
        self.assertEqual(service.classify_aqi(51), "良")
        self.assertEqual(service.classify_aqi(100), "良")
        self.assertEqual(service.classify_aqi(101), "轻度污染")
        self.assertEqual(service.classify_aqi(300), "重度污染")
        self.assertEqual(service.classify_aqi(301), "严重污染")

    def test_latest_snapshot_query_deduplicates_city(self):
        sql, params = _latest_snapshot_sql(province="广东")
        self.assertIn("NOT EXISTS", sql)
        self.assertIn("newer.created_at > a.created_at", sql)
        self.assertIn("newer.id > a.id", sql)
        self.assertIn("a.province IN", sql)
        self.assertEqual(len(params), 2)

    @patch.object(service.air_quality_model, "get_air_quality_level_distribution")
    def test_level_distribution_is_fixed_and_sums_to_city_count(self, model):
        model.return_value = [{"level": "优", "count": 2}, {"level": "轻度污染", "count": 1}]
        result = service.get_air_quality_level_distribution()
        self.assertEqual(len(result), 6)
        self.assertEqual(sum(row["count"] for row in result), 3)
        self.assertAlmostEqual(sum(row["percentage"] for row in result), 100.0)

    @patch.object(service.air_quality_model, "get_air_quality_overview")
    def test_overview_maps_snapshot_metrics(self, model):
        model.return_value = {
            "city_count": 3, "average_aqi": "82.5", "good_city_count": 2,
            "polluted_city_count": 1, "latest_snapshot": "2026-05-31 17:40:21",
        }
        result = service.get_air_quality_overview()
        self.assertEqual(result["cityCount"], 3)
        self.assertEqual(result["averageAqi"], 82.5)
        self.assertEqual(result["goodCityCount"], 2)
        self.assertEqual(result["pollutedCityCount"], 1)


if __name__ == "__main__":
    unittest.main()
