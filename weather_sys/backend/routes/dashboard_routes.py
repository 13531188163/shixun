"""Dashboard endpoint delegates all aggregation to its service."""

from flask import Blueprint

from ..services import dashboard_service
from ..utils.query_params import weather_location_params
from ..utils.response import error_response, success_response


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/overview")
def dashboard_overview():
    data = dashboard_service.get_dashboard_overview(**weather_location_params())
    if data is None:
        return error_response("dashboard location data not found", http_status=404)
    return success_response(data=data)
