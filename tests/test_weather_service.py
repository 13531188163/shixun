"""Unit tests for the Phase 4 weather service."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from weather_sys.backend.services import weather_service


def _weather_row(row_id: int, date_value: str, city: str = "北京市", district: str = "东城区") -> dict:
    return {
        "id": row_id,
        "province": "北京市",
        "city": city,
        "district": district,
        "date": date_value,
        "weather": "晴",
        "max_temp": "18.6℃",
        "min_temp": "-2℃",
        "avg_wind": "1.25",
        "max_wind": "5.6",
        "total_precip": "0",
    }


class WeatherServiceTests(unittest.TestCase):
    @patch("weather_sys.backend.services.weather_service.weather_model.get_latest_weather")
    def test_latest_maps_fields_and_units(self, model_call) -> None:
        model_call.return_value = _weather_row(1, "2026-05-22")
        result = weather_service.get_latest_weather(city="北京")
        self.assertEqual(result["province"], "北京")
        self.assertEqual(result["city"], "北京")
        self.assertEqual(result["maxTemp"], 18.6)
        self.assertEqual(result["minTemp"], -2)
        self.assertEqual(result["precipitation"], 0)

    @patch("weather_sys.backend.services.weather_service.weather_model.get_weather_history_by_date")
    def test_trend_returns_dates_in_ascending_order(self, model_call) -> None:
        model_call.return_value = [
            _weather_row(3, "2026-05-22"),
            _weather_row(2, "2026-05-21"),
            _weather_row(1, "2026-05-20"),
        ]
        result = weather_service.get_weather_trend(city="北京", days=3)
        self.assertEqual([row["date"] for row in result], ["2026-05-20", "2026-05-21", "2026-05-22"])
        model_call.assert_called_once_with(city="北京", province=None, district=None, days=3)

    @patch("weather_sys.backend.services.weather_service.weather_model.get_distinct_provinces")
    def test_location_list_normalizes_deduplicates_and_sorts(self, model_call) -> None:
        model_call.return_value = [
            {"province": "广东省"},
            {"province": "北京市"},
            {"province": "北京"},
        ]
        self.assertEqual(weather_service.list_provinces(), ["北京", "广东"])

    @patch("weather_sys.backend.services.weather_service.weather_model.get_city_weather_latest")
    def test_comparison_keeps_requested_order_and_counts_missing(self, model_call) -> None:
        model_call.return_value = [_weather_row(1, "2026-05-22", city="北京市")]
        result = weather_service.compare_cities("北京,上海")
        self.assertEqual(result["meta"], {"requested": 2, "returned": 1})
        self.assertEqual(result["data"][0]["city"], "北京")

    def test_invalid_days_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            weather_service.get_weather_trend(city="北京", days=0)


if __name__ == "__main__":
    unittest.main()
