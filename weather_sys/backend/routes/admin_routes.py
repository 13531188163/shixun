"""Server-rendered backend management page routes."""

from __future__ import annotations

import logging

from flask import Blueprint, current_app, render_template

from ..services.admin_service import get_admin_summary
from ..utils.db import ping_database


LOGGER = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/")
@admin_bp.get("/admin")
def admin_page():
    """Render a non-sensitive management page, separate from the Vue UI."""

    database_ok = True
    try:
        ping_database()
    except Exception:
        LOGGER.exception("Backend admin health check failed")
        database_ok = False

    return render_template(
        "admin.html",
        database_name=current_app.config.get("DB_NAME", "weather_db"),
        database_ok=database_ok,
        summary=get_admin_summary(),
        frontend_dev_url="http://127.0.0.1:5173/",
        frontend_build_url="/dashboard",
    )
