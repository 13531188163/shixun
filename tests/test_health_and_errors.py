import unittest
from unittest.mock import patch

from weather_sys.backend import create_app
from weather_sys.backend.utils.exceptions import DatabaseUnavailableError


class HealthAndErrorRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch("weather_sys.backend.routes.health_routes.ping_database")
    def test_health_success_matches_contract(self, ping):
        response = self.client.get("/api/health")
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["code"], 200)
        self.assertEqual(payload["data"]["application"], "ok")
        self.assertEqual(payload["data"]["database"], "ok")
        self.assertRegex(payload["data"]["checkedAt"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
        ping.assert_called_once_with()

    @patch(
        "weather_sys.backend.routes.health_routes.ping_database",
        side_effect=DatabaseUnavailableError(),
    )
    def test_health_database_failure_is_sanitized_500(self, ping):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"code": 500, "message": "database unavailable", "data": None})

    def test_unknown_route_and_method_errors_are_json(self):
        not_found = self.client.get("/api/does-not-exist")
        self.assertEqual(not_found.status_code, 404)
        self.assertEqual(not_found.get_json()["data"], None)

        method_error = self.client.post("/api/health")
        self.assertEqual(method_error.status_code, 405)
        self.assertEqual(method_error.get_json()["message"], "method not allowed")
        self.assertIn("GET", method_error.headers.get("Allow", ""))

    @patch(
        "weather_sys.backend.routes.weather_routes.weather_service.get_latest_weather",
        side_effect=RuntimeError("private SQL/password must not escape"),
    )
    def test_unexpected_exception_is_sanitized(self, service):
        response = self.client.get("/api/weather/latest?city=北京")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json(), {"code": 500, "message": "internal server error", "data": None})


if __name__ == "__main__":
    unittest.main()
