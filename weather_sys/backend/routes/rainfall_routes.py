"""Historical rainfall analysis endpoints."""

from flask import Blueprint

from ..services import rainfall_service
from ..utils.exceptions import AppException
from ..utils.query_params import date_param, name_param
from ..utils.response import error_response, success_response


rainfall_bp = Blueprint("rainfall", __name__)


def _location_params() -> dict[str, str | None]:
    return {
        "province": name_param("province"),
        "city": name_param("city"),
        "district": name_param("district"),
    }


def _rainfall_params() -> dict[str, str | None]:
    start_date = date_param("startDate")
    end_date = date_param("endDate")
    if start_date and end_date and start_date > end_date:
        raise AppException("startDate must be earlier than or equal to endDate")
    return {
        **_location_params(),
        "start_date": start_date,
        "end_date": end_date,
    }


def _service_call(function, **params):
    try:
        return function(**params)
    except ValueError as exc:
        raise AppException(str(exc)) from exc


@rainfall_bp.get("/dates")
def rainfall_dates():
    data = _service_call(rainfall_service.get_rainfall_dates, **_location_params())
    return success_response(data=data, meta={"count": len(data)})


@rainfall_bp.get("/core")
def rainfall_core():
    data = _service_call(rainfall_service.get_rainfall_core, **_rainfall_params())
    if data is None:
        return error_response("rainfall core data not found", http_status=404)
    return success_response(data=data)


@rainfall_bp.get("/recent")
def rainfall_recent():
    data = _service_call(rainfall_service.get_recent_rainfall, **_rainfall_params())
    return success_response(data=data, meta={"days": rainfall_service.RECENT_DAYS})


@rainfall_bp.get("/trend")
def rainfall_trend():
    data = _service_call(rainfall_service.get_rainfall_trend, **_rainfall_params())
    return success_response(data=data, meta={"days": rainfall_service.TREND_DAYS})


@rainfall_bp.get("/distribution")
def rainfall_distribution():
    data = _service_call(rainfall_service.get_rainfall_distribution, **_rainfall_params())
    return success_response(data=data, meta={"groupBy": "rainfallLevel"})
