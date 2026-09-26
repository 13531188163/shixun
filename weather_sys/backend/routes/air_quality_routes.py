"""AQI endpoints backed by the existing air-quality service."""

from flask import Blueprint

from ..services import air_quality_service
from ..utils.query_params import enum_param, integer_param, name_param
from ..utils.response import error_response, success_response


air_quality_bp = Blueprint("air_quality", __name__)


@air_quality_bp.get("/latest")
def latest_air_quality():
    city = name_param("city", required=True)
    data = air_quality_service.get_latest_air_quality(city=city)
    if data is None:
        return error_response("air quality record not found", http_status=404)
    return success_response(data=data)


@air_quality_bp.get("/ranking")
def air_quality_ranking():
    limit = integer_param("limit", default=10, minimum=1, maximum=100)
    order = enum_param("order", default="asc", choices=("asc", "desc"))
    data = air_quality_service.get_air_quality_ranking(limit=limit, order=order)
    return success_response(data=data, meta={"limit": limit, "order": order})


@air_quality_bp.get("/distribution")
def air_quality_distribution():
    result = air_quality_service.get_air_quality_distribution_result()
    return success_response(data=result["data"], meta=result["meta"])
