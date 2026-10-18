"""Unit tests for the Phase 4 dashboard composition service."""

from __future__ import annotations

import unittest
from datetime import date, datetime
from unittest.mock import patch

from weather_sys.backend.services import dashboard_service


class DashboardServiceTests(unittest.TestCase):
    @patch("weather_sys.backend.services.dashboard_service.air_quality_model.get_air_quality_statistics")
    @patch("weather_sys.backend.services.dashboard_service.weather_model.get_weather_statistics")
    @patch("weather_sys.backend.services.dashboard_service.get_latest_air_quality")
    @patch("weather_sys.backend.services.dashboard_service.get_latest_weather")
    def test_overview_composes_source_backed_values(
        self,
        latest_weather,
        latest_air_quality,
        weather_statistics,
        air_quality_statistics,
    ) -> None:
        latest_weather.return_value = {
            "province": "北京",
            "city": "北京",
            "district": "东城区",
            "date": "2026-05-22",
            "weather": "晴",
            "maxTemp": 20,
            "minTemp": 10,
            "avgWind": 1.2,
            "maxWind": 4,
            "precipitation": 0,
        }
        latest_air_quality.return_value = {
            "city": "北京",
            "province": "北京",
            "aqi": 105,
            "status": "轻度",
            "createdAt": "2026-05-31 17:40:21",
        }
        weather_statistics.return_value = {
            "record_count": 834971,
            "latest_date": date(2026, 5, 22),
        }
        air_quality_statistics.return_value = {
            "record_count": 262,
            "latest_snapshot": datetime(2026, 5, 31, 17, 40, 21),
        }

        result = dashboard_service.get_dashboard_overview(city="北京")

        self.assertEqual(result["location"]["district"], "东城区")
        self.assertEqual(result["basicStatistics"]["weatherRecordCount"], 834971)
        self.assertEqual(result["basicStatistics"]["weatherLatestDate"], "2026-05-22")
        self.assertEqual(result["basicStatistics"]["airQualitySnapshotAt"], "2026-05-31 17:40:21")
        latest_air_quality.assert_called_once_with(city="北京", province="北京")

    @patch("weather_sys.backend.services.dashboard_service.get_latest_weather", return_value=None)
    def test_missing_weather_location_returns_none(self, latest_weather) -> None:
        self.assertIsNone(dashboard_service.get_dashboard_overview(city="不存在"))
        latest_weather.assert_called_once()

    @patch("weather_sys.backend.services.dashboard_service.get_air_quality_overview")
    @patch("weather_sys.backend.services.dashboard_service.air_quality_model.get_air_quality_statistics")
    @patch("weather_sys.backend.services.dashboard_service.weather_model.get_weather_statistics")
    @patch("weather_sys.backend.services.dashboard_service.get_national_weather_overview")
    def test_national_overview_keeps_country_scope(
        self,
        national_weather,
        weather_statistics,
        air_quality_statistics,
        air_quality_overview,
    ) -> None:
        national_weather.return_value = {
            "scope": "country",
            "date": "2026-05-22",
            "weather": "全国多种天气",
            "maxTemp": 22,
            "minTemp": 8,
            "avgWind": 2.1,
            "maxWind": 12,
            "precipitation": 1.2,
            "recordCount": 100,
        }
        weather_statistics.return_value = {"record_count": 1000, "latest_date": date(2026, 5, 22)}
        air_quality_statistics.return_value = {"record_count": 262, "latest_snapshot": None}
        air_quality_overview.return_value = {"cityCount": 262, "averageAqi": 72}

        result = dashboard_service.get_national_dashboard_overview(date="2026-05-22")

        self.assertEqual(result["location"]["scope"], "country")
        self.assertIsNone(result["latestAirQuality"])
        self.assertEqual(result["airQualitySummary"]["cityCount"], 262)
        national_weather.assert_called_once_with(date="2026-05-22")


if __name__ == "__main__":
    unittest.main()
