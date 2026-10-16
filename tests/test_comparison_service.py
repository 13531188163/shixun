import unittest
from unittest.mock import patch

from weather_sys.backend.services import comparison_service


class ComparisonServiceTests(unittest.TestCase):
    @patch.object(comparison_service.air_quality_service, "get_latest_air_quality", return_value=None)
    @patch.object(comparison_service.comparison_model, "get_comparison_daily")
    @patch.object(comparison_service.comparison_model, "get_date_bounds", return_value={"start_date": "2026-03-01", "end_date": "2026-05-31"})
    def test_common_dates_and_metrics_are_returned(self, bounds, daily, aqi):
        daily.return_value = [
            {"province": "北京市", "city": "北京市", "date": "2026-05-01", "max_temp": 20, "min_temp": 10, "avg_wind": 2, "max_wind": 4, "precip": 1},
            {"province": "上海市", "city": "上海市", "date": "2026-05-01", "max_temp": 24, "min_temp": 14, "avg_wind": 3, "max_wind": 5, "precip": 2},
            {"province": "北京市", "city": "北京市", "date": "2026-05-02", "max_temp": 22, "min_temp": 12, "avg_wind": 2, "max_wind": 4, "precip": 0},
        ]
        result = comparison_service.compare("北京::北京,上海::上海")
        self.assertEqual(result["comparableDates"], ["2026-05-01"])
        self.assertEqual(result["dataCoverage"]["commonDays"], 1)
        self.assertEqual(result["cities"][0]["weatherMetrics"]["validDays"], 2)
        self.assertEqual(result["cities"][0]["weatherMetrics"]["totalPrecip"], 1.0)

    def test_duplicate_and_invalid_city_counts_are_rejected(self):
        with self.assertRaises(ValueError):
            comparison_service._refs("北京::北京,北京::北京")
        with self.assertRaises(ValueError):
            comparison_service._refs("北京::北京")


if __name__ == "__main__":
    unittest.main()
