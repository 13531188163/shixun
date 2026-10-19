"""Contract tests for the Swagger UI and OpenAPI document endpoints."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

from weather_sys.backend import create_app


class OpenApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        cls.document = yaml.safe_load(
            (Path(__file__).parents[1] / "docs" / "openapi.yaml").read_text(encoding="utf-8")
        )

    def test_swagger_and_openapi_entries_are_available(self):
        swagger = self.client.get("/api/docs")
        admin = self.client.get("/admin")
        self.assertEqual(swagger.status_code, 200)
        self.assertIn(b"swagger-ui", swagger.data)
        self.assertEqual(admin.status_code, 200)
        # A production frontend build is served at /admin; a small status page
        # remains only as a pre-build fallback.
        self.assertTrue(
            b'id="app"' in admin.data
            or "后端管理台".encode() in admin.data
            or b"WeatherDemo API" in admin.data
        )
        response = self.client.get("/openapi.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["openapi"], "3.0.3")

    def test_every_api_route_is_documented(self):
        actual = set()
        for rule in self.app.url_map.iter_rules():
            if rule.endpoint.startswith(("static", "frontend_")):
                continue
            if rule.endpoint.startswith("admin.") and not rule.rule.startswith("/api/admin/"):
                continue
            if "<" in rule.rule or not rule.rule.startswith("/api/"):
                continue
            for method in rule.methods - {"HEAD", "OPTIONS"}:
                actual.add((rule.rule, method))
        documented = {
            (path, method.upper())
            for path, operations in self.document["paths"].items()
            for method in operations
            if method.lower() in {"get", "post", "put", "patch", "delete"}
        }
        self.assertEqual(actual, documented)


if __name__ == "__main__":
    unittest.main()
