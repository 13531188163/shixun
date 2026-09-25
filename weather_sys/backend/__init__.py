"""Flask application factory for weatherdemo."""

from __future__ import annotations

import logging
from typing import Optional

from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .config import Settings, settings
from .routes.health_routes import health_bp
from .utils.exceptions import AppException
from .utils.response import error_response

LOGGER = logging.getLogger(__name__)


def create_app(app_settings: Optional[Settings] = None) -> Flask:
    """Create and configure a Flask application without opening a DB connection."""
    active_settings = app_settings or settings

    app = Flask(__name__)
    app.config.from_mapping(
        FLASK_HOST=active_settings.flask_host,
        FLASK_PORT=active_settings.flask_port,
        FLASK_DEBUG=active_settings.flask_debug,
        DB_HOST=active_settings.db_host,
        DB_PORT=active_settings.db_port,
        DB_USER=active_settings.db_user,
        DB_PASSWORD=active_settings.db_password,
        DB_NAME=active_settings.db_name,
    )

    CORS(
        app,
        resources={r"/api/*": {"origins": list(active_settings.cors_origins)}},
    )

    app.register_blueprint(health_bp, url_prefix="/api")
    _register_error_handlers(app)
    return app


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppException)
    def handle_app_exception(error: AppException):
        LOGGER.warning("Application error: %s", error.message)
        return error_response(
            message=error.message,
            http_status=error.status_code,
            data=error.data,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        status_code = error.code or 500
        messages = {
            400: "bad request",
            404: "resource not found",
            405: "method not allowed",
            500: "internal server error",
        }
        message = messages.get(status_code, "request failed")
        return error_response(message=message, http_status=status_code)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        LOGGER.exception("Unhandled application exception: %s", error)
        return error_response(
            message="internal server error",
            http_status=500,
        )
