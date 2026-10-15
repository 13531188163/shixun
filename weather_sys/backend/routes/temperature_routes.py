"""Historical temperature analysis endpoints."""

from flask import Blueprint

from ..services import temperature_service
from ..utils.exceptions import AppException
from ..utils.query_params import date_param, name_param
from ..utils.response import error_response, success_response


temperature_bp = Blueprint("temperature", __name__)


def _temperature_location_params() -> dict[str, str | None]:
    return {
        "province": name_param("province"),
        "city": name_param("city"),
        "district": name_param("district"),
    }


def _temperature_params() -> dict[str, str | None]:
    start_date = date_param("startDate")
    end_date = date_param("endDate")
    if start_date and end_date and start_date > end_date:
        raise AppException("startDate must be earlier than or equal to endDate")
    return {
        **_temperature_location_params(),
        "start_date": start_date,
        "end_date": end_date,
    }


def _service_call(function, **params):
    try:
        return function(**params)
    except ValueError as exc:
        raise AppException(str(exc)) from exc


@temperature_bp.get("/dates")
def temperature_dates():
    data = _service_call(temperature_service.get_temperature_dates, **_temperature_location_params())
    return success_response(data=data, meta={"count": len(data)})


@temperature_bp.get("/average")
def temperature_average():
    data = _service_call(temperature_service.get_temperature_average, **_temperature_params())
    if data is None:
        return error_response("temperature average data not found", http_status=404)
    return success_response(data=data)


@temperature_bp.get("/extremes")
def temperature_extremes():
    data = _service_call(temperature_service.get_temperature_extremes, **_temperature_params())
    if data is None:
        return error_response("temperature extreme data not found", http_status=404)
    return success_response(data=data)


@temperature_bp.get("/trend")
def temperature_trend():
    data = _service_call(temperature_service.get_temperature_trend, **_temperature_params())
    return success_response(data=data, meta={"days": temperature_service.TREND_DAYS})


@temperature_bp.get("/monthly")
def temperature_monthly():
    data = _service_call(temperature_service.get_temperature_monthly, **_temperature_params())
    return success_response(data=data, meta={"groupBy": "month"})


@temperature_bp.get("/recent")
def temperature_recent():
    data = _service_call(temperature_service.get_recent_temperature, **_temperature_params())
    return success_response(data=data, meta={"days": temperature_service.RECENT_DAYS})
