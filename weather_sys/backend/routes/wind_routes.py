"""Historical wind analysis endpoints."""

from flask import Blueprint

from ..services import wind_analysis_service
from ..utils.exceptions import AppException
from ..utils.query_params import date_param, name_param
from ..utils.response import error_response, success_response

wind_bp = Blueprint("wind_analysis", __name__)


def _params():
    start = date_param("startDate"); end = date_param("endDate")
    if start and end and start > end:
        raise AppException("startDate must be earlier than or equal to endDate")
    return {"province": name_param("province"), "city": name_param("city"), "district": name_param("district"), "start_date": start, "end_date": end}


def _location():
    return {"province": name_param("province"), "city": name_param("city"), "district": name_param("district")}


def _call(function, **params):
    try:
        return function(**params)
    except ValueError as exc:
        raise AppException(str(exc)) from exc


@wind_bp.get("/dates")
def wind_dates():
    data = _call(wind_analysis_service.get_wind_dates, **_location())
    return success_response(data=data, meta={"count": len(data)})


@wind_bp.get("/core")
def wind_core():
    data = _call(wind_analysis_service.get_wind_core, **_params())
    if data is None:
        return error_response("wind core data not found", http_status=404)
    return success_response(data=data)


@wind_bp.get("/trend")
def wind_trend():
    data = _call(wind_analysis_service.get_wind_trend, **_params())
    return success_response(data=data, meta={"days": wind_analysis_service.TREND_DAYS})


@wind_bp.get("/distribution")
def wind_distribution():
    data = _call(wind_analysis_service.get_wind_distribution, **_params())
    return success_response(data=data, meta={"groupBy": "beaufortLevel"})


@wind_bp.get("/recent")
def wind_recent():
    data = _call(wind_analysis_service.get_recent_wind, **_params())
    return success_response(data=data, meta={"days": wind_analysis_service.RECENT_DAYS})
