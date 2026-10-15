import unittest
from unittest.mock import patch

from weather_sys.backend import create_app


class RainfallRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch(
        "weather_sys.backend.routes.rainfall_routes.rainfall_service.get_rainfall_dates",
        return_value=["2026-05-22", "2026-05-21"],
    )
    def test_dates_returns_real_date_list_and_meta(self, service):
        response = self.client.get("/api/rainfall/dates?province=山东")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"], ["2026-05-22", "2026-05-21"])
        self.assertEqual(response.get_json()["meta"], {"count": 2})
        service.assert_called_once_with(province="山东", city=None, district=None)

    @patch(
        "weather_sys.backend.routes.rainfall_routes.rainfall_service.get_rainfall_core",
        return_value={
            "totalPrecip": 12.5,
            "avgPrecip": 2.5,
            "maxPrecip": 8.0,
            "maxPrecipDate": "2026-05-17",
            "rainyDays": 3,
            "observationDays": 5,
            "observationRecords": 12,
        },
    )
    def test_core_uses_camel_case_response(self, service):
        response = self.client.get(
            "/api/rainfall/core?province=山东&startDate=2026-05-01&endDate=2026-05-22"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["rainyDays"], 3)
        self.assertEqual(response.get_json()["data"]["observationDays"], 5)
        self.assertEqual(response.get_json()["data"]["observationRecords"], 12)
        service.assert_called_once_with(
            province="山东",
            city=None,
            district=None,
            start_date="2026-05-01",
            end_date="2026-05-22",
        )

    @patch(
        "weather_sys.backend.routes.rainfall_routes.rainfall_service.get_rainfall_core",
        return_value=None,
    )
    def test_core_returns_not_found_without_data(self, service):
        response = self.client.get("/api/rainfall/core")
        self.assertEqual(response.status_code, 404)
        self.assertIsNone(response.get_json()["data"])

    def test_invalid_date_range_returns_bad_request(self):
        response = self.client.get(
            "/api/rainfall/trend?startDate=2026-05-22&endDate=2026-05-01"
        )
        self.assertEqual(response.status_code, 400)

    @patch(
        "weather_sys.backend.routes.rainfall_routes.rainfall_service.get_rainfall_distribution",
        return_value=[
            {"level": "无降水", "count": 1},
            {"level": "小雨", "count": 2},
        ],
    )
    def test_distribution_returns_fixed_business_data(self, service):
        response = self.client.get("/api/rainfall/distribution?city=济南")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["meta"], {"groupBy": "rainfallLevel"})
        service.assert_called_once_with(
            province=None,
            city="济南",
            district=None,
            start_date=None,
            end_date=None,
        )


if __name__ == "__main__":
    unittest.main()
