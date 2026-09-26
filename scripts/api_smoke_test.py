"""Read-only smoke test for every public weatherdemo GET API.

The script discovers a usable location from the running service, then calls
each documented endpoint through HTTP.  It only sends GET requests and never
writes to MySQL.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass
class ApiResult:
    status: int
    payload: dict[str, Any]


class SmokeFailure(RuntimeError):
    """Raised when an API smoke assertion fails."""


def _request(base_url: str, path: str) -> ApiResult:
    request = Request(f"{base_url.rstrip('/')}{path}", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=20) as response:
            status = response.status
            body = response.read()
    except HTTPError as error:
        status = error.code
        body = error.read()
    except URLError as error:
        raise SmokeFailure(f"request failed for {path}: {error.reason}") from error

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SmokeFailure(f"{path} returned non-JSON data (HTTP {status})") from error
    if not isinstance(payload, dict):
        raise SmokeFailure(f"{path} returned a non-object envelope")
    for key in ("code", "message", "data"):
        if key not in payload:
            raise SmokeFailure(f"{path} response is missing {key}")
    return ApiResult(status=status, payload=payload)


def _assert_status(result: ApiResult, path: str, expected: set[int]) -> None:
    if result.status not in expected or result.payload.get("code") != result.status:
        raise SmokeFailure(
            f"{path} returned HTTP {result.status}/code {result.payload.get('code')}; "
            f"expected one of {sorted(expected)}"
        )


def _query(path: str, **params: str | int) -> str:
    return f"{path}?{urlencode(params)}"


def _discover_location(base_url: str) -> tuple[str, str, str | None, list[str]]:
    provinces_path = "/api/locations/provinces"
    result = _request(base_url, provinces_path)
    _assert_status(result, provinces_path, {200})
    provinces = result.payload["data"]
    if not isinstance(provinces, list) or not provinces:
        raise SmokeFailure("provinces returned no usable locations")
    if len(provinces) != len(set(provinces)) or any(not isinstance(item, str) for item in provinces):
        raise SmokeFailure("provinces contains duplicates or non-string values")

    for province in provinces:
        cities_path = _query("/api/locations/cities", province=province)
        cities_result = _request(base_url, cities_path)
        if cities_result.status != 200 or not isinstance(cities_result.payload.get("data"), list):
            continue
        cities = [city for city in cities_result.payload["data"] if isinstance(city, str) and city]
        for city in cities[:20]:
            districts_path = _query(
                "/api/locations/districts", province=province, city=city
            )
            districts_result = _request(base_url, districts_path)
            if districts_result.status == 200 and isinstance(districts_result.payload.get("data"), list):
                districts = districts_result.payload["data"]
                district = districts[0] if districts else None
                return province, city, district, cities[:3]
            if districts_result.status == 404:
                return province, city, None, cities[:3]
    raise SmokeFailure("could not discover a usable province/city location")


def _check(name: str, callback) -> None:
    callback()
    print(f"PASS {name}")


def run(base_url: str) -> int:
    province, city, district, comparison_cities = _discover_location(base_url)
    latest_params = {"province": province, "city": city}
    if district:
        latest_params["district"] = district

    health_path = "/api/health"
    health = _request(base_url, health_path)
    _assert_status(health, health_path, {200})
    health_data = health.payload["data"]
    if not isinstance(health_data, dict) or health_data.get("database") != "ok":
        raise SmokeFailure("health did not report database=ok")
    print("PASS GET /api/health")

    provinces_path = "/api/locations/provinces"
    _check("GET /api/locations/provinces", lambda: _assert_status(_request(base_url, provinces_path), provinces_path, {200}))

    cities_path = _query("/api/locations/cities", province=province)
    _check("GET /api/locations/cities", lambda: _assert_status(_request(base_url, cities_path), cities_path, {200}))

    districts_path = _query("/api/locations/districts", province=province, city=city)
    _check(
        "GET /api/locations/districts",
        lambda: _assert_status(_request(base_url, districts_path), districts_path, {200, 404}),
    )

    latest_path = _query("/api/weather/latest", **latest_params)
    _check("GET /api/weather/latest", lambda: _assert_status(_request(base_url, latest_path), latest_path, {200}))

    trend_path = _query("/api/weather/trend", **latest_params, days=7)
    _check("GET /api/weather/trend", lambda: _assert_status(_request(base_url, trend_path), trend_path, {200}))

    comparison_path = _query("/api/weather/city-comparison", cities=",".join(comparison_cities))
    _check(
        "GET /api/weather/city-comparison",
        lambda: _assert_status(_request(base_url, comparison_path), comparison_path, {200}),
    )

    ranking_path = "/api/air-quality/ranking"
    ranking = _request(base_url, ranking_path)
    _assert_status(ranking, ranking_path, {200})
    ranking_data = ranking.payload["data"]
    if not isinstance(ranking_data, list) or not ranking_data:
        raise SmokeFailure("air-quality ranking returned no usable city")
    aqi_city = ranking_data[0].get("city")
    if not isinstance(aqi_city, str) or not aqi_city:
        raise SmokeFailure("air-quality ranking returned an invalid city")
    print("PASS GET /api/air-quality/ranking")

    aqi_latest_path = _query("/api/air-quality/latest", city=aqi_city)
    _check(
        "GET /api/air-quality/latest",
        lambda: _assert_status(_request(base_url, aqi_latest_path), aqi_latest_path, {200}),
    )

    distribution_path = "/api/air-quality/distribution"
    _check(
        "GET /api/air-quality/distribution",
        lambda: _assert_status(_request(base_url, distribution_path), distribution_path, {200}),
    )

    dashboard_path = _query("/api/dashboard/overview", **latest_params)
    _check(
        "GET /api/dashboard/overview",
        lambda: _assert_status(_request(base_url, dashboard_path), dashboard_path, {200}),
    )

    print("PASS all documented GET APIs (11)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-url",
        default=os.getenv("API_BASE_URL", "http://127.0.0.1:5000"),
        help="running Flask base URL (default: %(default)s)",
    )
    args = parser.parse_args()
    try:
        return run(args.base_url)
    except SmokeFailure as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
