import unittest
from unittest.mock import patch

from weather_sys.backend import create_app


class LocationRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch("weather_sys.backend.routes.location_routes.weather_service.list_provinces", return_value=["北京"])
    def test_provinces_success(self, service):
        response = self.client.get("/api/locations/provinces")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"code": 200, "message": "success", "data": ["北京"], "meta": {}})

    def test_cities_requires_province(self):
        response = self.client.get("/api/locations/cities")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["message"], "province is required")

    @patch("weather_sys.backend.routes.location_routes.weather_service.list_cities", return_value=[])
    def test_cities_missing_province_returns_404(self, service):
        response = self.client.get("/api/locations/cities?province=不存在")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["message"], "province not found")

    @patch("weather_sys.backend.routes.location_routes.weather_service.list_districts", return_value=["东城区"])
    def test_districts_success(self, service):
        response = self.client.get("/api/locations/districts?province=北京&city=北京")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"], ["东城区"])


if __name__ == "__main__":
    unittest.main()
