"""Unit tests for Phase 4 air-quality and optional wind services."""

from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import patch

from weather_sys.backend.services import air_quality_service, wind_service


class AirQualityServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.row = {
            "id": 3,
            "city": "北京市",
            "province": "北京市",
            "aqi": "105",
            "status": " 轻度 ",
            "created_at": datetime(2026, 5, 31, 17, 40, 21),
        }

    @patch("weather_sys.backend.services.air_quality_service.air_quality_model.get_latest_air_quality")
    def test_latest_converts_contract_fields(self, model_call) -> None:
        model_call.return_value = self.row
        self.assertEqual(
            air_quality_service.get_latest_air_quality("北京"),
            {
                "city": "北京",
                "province": "北京",
                "aqi": 105,
                "status": "轻度",
                "createdAt": "2026-05-31 17:40:21",
            },
        )

    @patch("weather_sys.backend.services.air_quality_service.air_quality_model.get_air_quality_ranking")
    def test_ranking_adds_rank_and_excludes_snapshot_time(self, model_call) -> None:
        model_call.return_value = [self.row]
        result = air_quality_service.get_air_quality_ranking()
        self.assertEqual(result[0], {"rank": 1, "city": "北京", "province": "北京", "aqi": 105, "status": "轻度"})

    def test_invalid_parameters_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            air_quality_service.get_latest_air_quality("")
        with self.assertRaises(ValueError):
            air_quality_service.get_air_quality_ranking(order="sideways")


class WindServiceTests(unittest.TestCase):
    @patch("weather_sys.backend.services.wind_service.wind_model.has_wind_data", return_value=False)
    def test_empty_wind_table_is_reported_without_synthetic_data(self, model_call) -> None:
        self.assertFalse(wind_service.has_wind_data())
        model_call.assert_called_once_with()

    @patch("weather_sys.backend.services.wind_service.wind_model.get_wind_data", return_value=[])
    def test_empty_wind_rows_return_empty_list(self, model_call) -> None:
        self.assertEqual(wind_service.get_wind_data(limit=5), [])
        model_call.assert_called_once_with(city=None, limit=5)

    @patch("weather_sys.backend.services.wind_service.wind_model.get_latest_wind", return_value=None)
    def test_missing_latest_wind_returns_none(self, model_call) -> None:
        self.assertIsNone(wind_service.get_latest_wind("北京"))


if __name__ == "__main__":
    unittest.main()
