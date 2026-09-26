"""Health check blueprint."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint

from ..utils.db import ping_database
from ..utils.response import success_response

health_bp = Blueprint("health", __name__)


def _health_payload() -> dict:
    return {
        "application": "ok",
        "database": "ok",
        "checkedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


@health_bp.get("/health")
def health_check():
    """Check Flask availability and execute a lightweight MySQL query."""
    ping_database()
    return success_response(data=_health_payload())
