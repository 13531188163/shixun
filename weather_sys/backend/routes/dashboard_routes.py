"""Dashboard endpoint delegates all aggregation to its service."""

from flask import Blueprint

from ..services import dashboard_service
from ..utils.query_params import date_param, name_param, weather_location_params
from ..utils.response import error_response, success_response


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/overview")
def dashboard_overview():
    location = weather_location_params()
    selected_date = date_param()
    if selected_date is not None:
        location["date"] = selected_date
    data = dashboard_service.get_dashboard_overview(**location)
    if data is None:
        return error_response("dashboard location data not found", http_status=404)
    return success_response(data=data)


@dashboard_bp.get("/province-overview")
def province_dashboard_overview():
    province = name_param("province", required=True)
    selected_date = date_param()
    data = dashboard_service.get_province_dashboard_overview(
        province=province, date=selected_date
    )
    if data is None:
        return error_response("province dashboard data not found", http_status=404)
    return success_response(data=data)
