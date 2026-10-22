import unittest
from unittest.mock import patch

from weather_sys.backend import create_app


class AdminWeatherRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    @patch(
        "weather_sys.backend.routes.admin_routes.weather_service.list_weather_records",
        return_value={"rows": [], "page": 1, "pageSize": 50, "total": 0, "pages": 0},
    )
    def test_empty_keyword_is_omitted_from_service_filter(self, service):
        response = self.client.get("/api/admin/weather-records?province=上海&keyword=")
        self.assertEqual(response.status_code, 200)
        service.assert_called_once_with(
            province="上海",
            city=None,
            district=None,
            date=None,
            keyword=None,
            page=1,
            page_size=50,
        )


if __name__ == "__main__":
    unittest.main()
