"""Server-rendered backend management page routes."""

from __future__ import annotations

import logging
import hmac
import os
from pathlib import Path

import yaml
from flask import Blueprint, current_app, jsonify, render_template, request

from ..services.admin_service import get_admin_summary
from ..utils.db import ping_database


LOGGER = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)
OPENAPI_PATH = Path(__file__).resolve().parents[3] / "docs" / "openapi.yaml"


@admin_bp.before_request
def admin_access_control():
    """Protect the workbench when an ADMIN_API_TOKEN is configured.

    Development remains convenient when the variable is unset; deployment
    environments can require the X-Admin-Token header without changing routes.
    """

    expected = os.getenv("ADMIN_API_TOKEN", "").strip()
    if expected and not hmac.compare_digest(request.headers.get("X-Admin-Token", ""), expected):
        return jsonify({"code": 401, "message": "admin authentication required", "data": None}), 401
    return None


@admin_bp.get("/")
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


@admin_bp.get("/admin")
def admin_workbench_page():
    """Serve the compact API workbench for the real Flask API."""

    return render_template("api_workbench.html")


@admin_bp.get("/api/docs")
def swagger_ui_page():
    """Serve the standard Swagger UI shell for the real Flask API."""

    return render_template("swagger_ui.html")


@admin_bp.get("/openapi.json")
def openapi_json():
    """Expose the repository OpenAPI 3 contract as JSON for Swagger UI."""

    try:
        document = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        LOGGER.exception("OpenAPI document could not be loaded")
        return jsonify({"code": 500, "message": "openapi document unavailable", "data": None}), 500
    response = jsonify(document)
    response.headers["Cache-Control"] = "no-cache"
    return response
