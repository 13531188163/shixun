import unittest
from unittest.mock import patch

from weather_sys.backend import create_app


class ComparisonRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app().test_client()

    @patch("weather_sys.backend.routes.comparison_routes.comparison_service.compare", return_value={"cities": []})
    def test_comparison_accepts_two_to_four_city_refs(self, compare):
        response = self.client.get("/api/comparison?cities=北京::北京,上海::上海")
        self.assertEqual(response.status_code, 200)
        compare.assert_called_once_with(["北京::北京", "上海::上海"], None, None)

    def test_comparison_requires_cities(self):
        self.assertEqual(self.client.get("/api/comparison").status_code, 400)


if __name__ == "__main__":
    unittest.main()
