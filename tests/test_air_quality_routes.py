import unittest
from unittest.mock import patch

from weather_sys.backend import create_app


class AirQualityRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch(
        "weather_sys.backend.routes.air_quality_routes.air_quality_service.get_latest_air_quality",
        return_value={"city": "北京", "aqi": 105},
    )
    def test_latest_success(self, service):
        response = self.client.get("/api/air-quality/latest?city=北京")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["aqi"], 105)

    def test_latest_requires_city(self):
        self.assertEqual(self.client.get("/api/air-quality/latest").status_code, 400)

    @patch("weather_sys.backend.routes.air_quality_routes.air_quality_service.get_air_quality_ranking", return_value=[])
    def test_ranking_success_and_defaults(self, service):
        response = self.client.get("/api/air-quality/ranking")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["meta"], {"limit": 10, "order": "asc"})
        service.assert_called_once_with(limit=10, order="asc")

    def test_ranking_invalid_parameters(self):
        for query in ("limit=abc", "limit=-1", "order=invalid"):
            self.assertEqual(self.client.get(f"/api/air-quality/ranking?{query}").status_code, 400)

    @patch(
        "weather_sys.backend.routes.air_quality_routes.air_quality_service.get_air_quality_distribution_result",
        return_value={
            "data": [{"status": "优", "count": 2}, {"status": "良", "count": 1}],
            "meta": {"totalKnown": 3},
        },
    )
    def test_distribution_success_and_total(self, service):
        response = self.client.get("/api/air-quality/distribution")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["meta"], {"totalKnown": 3})


if __name__ == "__main__":
    unittest.main()
