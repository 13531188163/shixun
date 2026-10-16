from flask import Blueprint

from ..services import comparison_service
from ..utils.query_params import cities_param, date_param
from ..utils.response import error_response, success_response

comparison_bp = Blueprint("comparison", __name__)


@comparison_bp.get("/locations")
def locations():
    return success_response(data=comparison_service.get_locations(), meta={})


@comparison_bp.get("")
def comparison():
    cities = cities_param()
    start_date = date_param("startDate")
    end_date = date_param("endDate")
    try:
        data = comparison_service.compare(cities, start_date, end_date)
    except ValueError as exc:
        return error_response(str(exc), http_status=400)
    return success_response(data=data)
