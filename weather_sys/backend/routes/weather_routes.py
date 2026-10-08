"""Read-only weather endpoints backed by the existing weather service."""

from flask import Blueprint

from ..services import weather_service
from ..utils.query_params import date_param, cities_param, integer_param, weather_location_params
from ..utils.response import error_response, success_response


weather_bp = Blueprint("weather", __name__)


@weather_bp.get("/latest")
def latest_weather():
    location = weather_location_params()
    selected_date = date_param()
    if selected_date is not None:
        location["date"] = selected_date
    data = weather_service.get_latest_weather(**location)
    if data is None:
        return error_response("weather record not found", http_status=404)
    return success_response(data=data)


@weather_bp.get("/dates")
def weather_dates():
    """List fixed observation dates available for a selected location."""

    data = weather_service.list_weather_dates(**weather_location_params())
    return success_response(data=data, meta={"count": len(data)})


@weather_bp.get("/trend")
def weather_trend():
    location = weather_location_params()
    selected_date = date_param()
    if selected_date is not None:
        location["date"] = selected_date
    days = integer_param("days", default=7, minimum=1, maximum=90)
    data = weather_service.get_weather_trend(**location, days=days)
    # 区分不存在的位置与存在但没有有效日期记录的位置。
    if not data and weather_service.get_latest_weather(**location) is None:
        return error_response("location not found", http_status=404)
    return success_response(data=data, meta={"days": days})


@weather_bp.get("/city-comparison")
def city_comparison():
    selected_date = date_param()
    params = {"date": selected_date} if selected_date is not None else {}
    result = weather_service.compare_cities(cities_param(), **params)
    return success_response(data=result["data"], meta=result["meta"])
