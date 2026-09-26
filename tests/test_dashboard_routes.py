import unittest
from unittest.mock import patch

from weather_sys.backend import create_app


class DashboardRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch(
        "weather_sys.backend.routes.dashboard_routes.dashboard_service.get_dashboard_overview",
        return_value={"location": {"city": "北京"}},
    )
    def test_overview_success(self, service):
        response = self.client.get("/api/dashboard/overview?city=北京")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["location"]["city"], "北京")

    def test_overview_requires_city(self):
        self.assertEqual(self.client.get("/api/dashboard/overview").status_code, 400)

    @patch("weather_sys.backend.routes.dashboard_routes.dashboard_service.get_dashboard_overview", return_value=None)
    def test_overview_not_found(self, service):
        response = self.client.get("/api/dashboard/overview?city=不存在")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
