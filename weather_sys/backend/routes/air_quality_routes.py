"""AQI endpoints backed by the existing air-quality service."""

from flask import Blueprint

from ..services import air_quality_service
from ..utils.query_params import enum_param, integer_param, name_param
from ..utils.response import error_response, success_response


air_quality_bp = Blueprint("air_quality", __name__)


def _service_call(function, **params):
    try:
        return function(**params)
    except ValueError as exc:
        from ..utils.exceptions import AppException
        raise AppException(str(exc)) from exc


@air_quality_bp.get("/latest")
def latest_air_quality():
    city = name_param("city", required=True)
    province = name_param("province")
    params = {"city": city}
    if province is not None:
        params["province"] = province
    data = air_quality_service.get_latest_air_quality(**params)
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


@air_quality_bp.get("/overview")
def air_quality_overview():
    data = _service_call(
        air_quality_service.get_air_quality_overview,
        province=name_param("province"),
    )
    return success_response(data=data)


@air_quality_bp.get("/provinces")
def air_quality_provinces():
    data = _service_call(air_quality_service.get_air_quality_province_summaries)
    return success_response(data=data, meta={"count": len(data)})


@air_quality_bp.get("/cities")
def air_quality_cities():
    data = _service_call(
        air_quality_service.get_air_quality_city_rows,
        province=name_param("province"),
    )
    return success_response(data=data, meta={"count": len(data)})


@air_quality_bp.get("/levels")
def air_quality_levels():
    data = _service_call(
        air_quality_service.get_air_quality_level_distribution,
        province=name_param("province"),
    )
    return success_response(data=data, meta={"totalKnown": sum(item["count"] for item in data)})
