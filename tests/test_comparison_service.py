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

    @patch.object(comparison_service.air_quality_service, "get_latest_air_quality")
    @patch.object(comparison_service.comparison_model, "get_comparison_daily")
    @patch.object(comparison_service.comparison_model, "get_date_bounds", return_value={"start_date": "2026-05-01", "end_date": "2026-05-31"})
    def test_four_city_comparison_keeps_missing_aqi_as_null(self, bounds, daily, aqi):
        refs = [
            ("北京", "北京"),
            ("上海", "上海"),
            ("广东", "广州"),
            ("四川", "广安"),
        ]
        daily.return_value = [
            {
                "province": province,
                "city": city,
                "date": "2026-05-22",
                "max_temp": 25 + index,
                "min_temp": 15 + index,
                "avg_wind": 2 + index,
                "max_wind": 4 + index,
                "precip": index,
            }
            for index, (province, city) in enumerate(refs)
        ]
        aqi.side_effect = [
            {"aqi": 42, "status": "优", "createdAt": "2026-05-31 17:40:21"},
            None,
            {"aqi": 55, "status": "良", "createdAt": "2026-05-31 17:40:21"},
            None,
        ]

        result = comparison_service.compare(",".join(f"{province}::{city}" for province, city in refs))

        self.assertEqual(len(result["cities"]), 4)
        self.assertEqual(result["dataCoverage"]["commonDays"], 1)
        self.assertEqual(result["cities"][0]["aqiSnapshot"]["aqi"], 42)
        self.assertIsNone(result["cities"][1]["aqiSnapshot"]["aqi"])
        self.assertIsNone(result["cities"][3]["aqiSnapshot"]["aqi"])

    def test_more_than_four_city_refs_are_rejected(self):
        refs = ",".join(f"省{i}::城市{i}" for i in range(5))
        with self.assertRaises(ValueError):
            comparison_service._refs(refs)

    @patch.object(comparison_service.air_quality_service, "get_latest_air_quality", return_value=None)
    @patch.object(comparison_service.comparison_model, "get_comparison_daily", return_value=[])
    @patch.object(comparison_service.comparison_model, "get_date_bounds", return_value={"start_date": "2024-05-24", "end_date": "2026-05-22"})
    def test_omitted_dates_use_latest_thirty_day_window(self, bounds, daily, aqi):
        result = comparison_service.compare("北京::北京,上海::上海")
        self.assertEqual(result["weatherPeriod"], {"startDate": "2026-04-23", "endDate": "2026-05-22"})

    @patch.object(comparison_service.comparison_model, "get_comparison_locations")
    def test_locations_are_deduplicated_after_name_normalization(self, locations):
        locations.return_value = [
            {"province": "北京市", "city": "北京市"},
            {"province": "北京", "city": "北京"},
            {"province": "四川省", "city": "广安市"},
            {"province": "四川", "city": "广安"},
        ]
        self.assertEqual(
            comparison_service.get_locations(),
            [
                {"key": "北京::北京", "province": "北京", "city": "北京"},
                {"key": "四川::广安", "province": "四川", "city": "广安"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
