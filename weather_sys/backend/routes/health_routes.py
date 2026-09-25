"""Health check blueprint."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint

from ..utils.db import ping_database
from ..utils.exceptions import DatabaseUnavailableError
from ..utils.response import error_response, success_response

health_bp = Blueprint("health", __name__)


def _health_payload(database_status: str, application_status: str = "ok") -> dict:
    return {
        "service": "weatherdemo-api",
        "status": "ok" if database_status == "connected" else "degraded",
        "application": application_status,
        "database": database_status,
        "databaseStatus": "ok" if database_status == "connected" else "error",
        "checkedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@health_bp.get("/health")
def health_check():
    """Check Flask availability and execute a lightweight MySQL query."""
    try:
        ping_database()
    except DatabaseUnavailableError:
        return error_response(
            message="database unavailable",
            http_status=503,
            data=_health_payload("disconnected", application_status="ok"),
        )

    return success_response(data=_health_payload("connected"))
