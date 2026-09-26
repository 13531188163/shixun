import unittest
from unittest.mock import patch

from weather_sys.backend import create_app


class WeatherRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch(
        "weather_sys.backend.routes.weather_routes.weather_service.get_latest_weather",
        return_value={"city": "北京", "date": "2026-05-22"},
    )
    def test_latest_success(self, service):
        response = self.client.get("/api/weather/latest?city=北京")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["data"]["city"], "北京")

    def test_latest_requires_city(self):
        response = self.client.get("/api/weather/latest")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["message"], "city is required")

    @patch("weather_sys.backend.routes.weather_routes.weather_service.get_latest_weather", return_value=None)
    def test_latest_not_found(self, service):
        response = self.client.get("/api/weather/latest?city=不存在")
        self.assertEqual(response.status_code, 404)

    @patch("weather_sys.backend.routes.weather_routes.weather_service.get_weather_trend", return_value=[{"date": "2026-05-22"}])
    def test_trend_success_and_meta(self, service):
        response = self.client.get("/api/weather/trend?city=北京&days=3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["meta"], {"days": 3})
        service.assert_called_once_with(city="北京", province=None, district=None, days=3)

    @patch("weather_sys.backend.routes.weather_routes.weather_service.get_weather_trend", return_value=[])
    @patch("weather_sys.backend.routes.weather_routes.weather_service.get_latest_weather", return_value=None)
    def test_trend_location_not_found(self, latest, trend):
        response = self.client.get("/api/weather/trend?city=不存在")
        self.assertEqual(response.status_code, 404)

    def test_trend_invalid_days(self):
        for value in ("abc", "-1", "999999"):
            response = self.client.get(f"/api/weather/trend?city=北京&days={value}")
            self.assertEqual(response.status_code, 400)

    @patch(
        "weather_sys.backend.routes.weather_routes.weather_service.compare_cities",
        return_value={"data": [{"city": "北京"}], "meta": {"requested": 1, "returned": 1}},
    )
    def test_city_comparison_success(self, service):
        response = self.client.get("/api/weather/city-comparison?cities=北京")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["meta"]["returned"], 1)

    def test_city_comparison_invalid_cities(self):
        self.assertEqual(self.client.get("/api/weather/city-comparison?cities=").status_code, 400)
        cities = ",".join([f"城市{i}" for i in range(11)])
        self.assertEqual(self.client.get(f"/api/weather/city-comparison?cities={cities}").status_code, 400)


if __name__ == "__main__":
    unittest.main()
