"""Location selector endpoints backed by the weather service."""

from flask import Blueprint

from ..services import weather_service
from ..utils.query_params import name_param
from ..utils.response import error_response, success_response


location_bp = Blueprint("location", __name__)


@location_bp.get("/provinces")
def provinces():
    return success_response(data=weather_service.list_provinces(), meta={})


@location_bp.get("/cities")
def cities():
    province = name_param("province", required=True)
    data = weather_service.list_cities(province=province)
    if not data:
        return error_response("province not found", http_status=404)
    return success_response(data=data, meta={})


@location_bp.get("/districts")
def districts():
    province = name_param("province", required=True)
    city = name_param("city", required=True)
    data = weather_service.list_districts(province=province, city=city)
    if not data:
        return error_response("location not found", http_status=404)
    return success_response(data=data, meta={})
