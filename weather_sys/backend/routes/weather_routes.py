"""Read-only weather endpoints backed by the existing weather service."""

from flask import Blueprint

from ..services import weather_service
from ..utils.query_params import cities_param, integer_param, weather_location_params
from ..utils.response import error_response, success_response


weather_bp = Blueprint("weather", __name__)


@weather_bp.get("/latest")
def latest_weather():
    data = weather_service.get_latest_weather(**weather_location_params())
    if data is None:
        return error_response("weather record not found", http_status=404)
    return success_response(data=data)


@weather_bp.get("/trend")
def weather_trend():
    location = weather_location_params()
    days = integer_param("days", default=7, minimum=1, maximum=90)
    data = weather_service.get_weather_trend(**location, days=days)
    # 区分不存在的位置与存在但没有有效日期记录的位置。
    if not data and weather_service.get_latest_weather(**location) is None:
        return error_response("location not found", http_status=404)
    return success_response(data=data, meta={"days": days})


@weather_bp.get("/city-comparison")
def city_comparison():
    result = weather_service.compare_cities(cities_param())
    return success_response(data=result["data"], meta=result["meta"])
