"""Flask application factory for weatherdemo."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from flask import Flask, Response, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from .config import Settings, settings
from .routes.air_quality_routes import air_quality_bp
from .routes.admin_routes import admin_bp
from .routes.dashboard_routes import dashboard_bp
from .routes.health_routes import health_bp
from .routes.location_routes import location_bp
from .routes.weather_routes import weather_bp
from .utils.exceptions import AppException
from .utils.response import error_response

LOGGER = logging.getLogger(__name__)
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "font" / "weather_font" / "dist"


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
    app.register_blueprint(admin_bp)
    app.register_blueprint(location_bp, url_prefix="/api/locations")
    app.register_blueprint(weather_bp, url_prefix="/api/weather")
    app.register_blueprint(air_quality_bp, url_prefix="/api/air-quality")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    _register_frontend_dashboard(app)
    _register_error_handlers(app)
    return app


def _register_frontend_dashboard(app: Flask) -> None:
    """Expose an optional built Vue Dashboard under a distinct path.

    The Flask root is reserved for the backend management page.  The Vite
    development server remains the preferred frontend workflow, while a
    production bundle can be opened at ``/dashboard`` after ``npm run build``.
    """

    setup_page = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>WeatherDemo 后端已启动</title>
<style>body{font-family:system-ui,"Microsoft YaHei",sans-serif;background:#061a36;color:#eaf6ff;max-width:760px;margin:12vh auto;padding:32px}a{color:#65d7ff}code{color:#9fe8ff}</style></head>
<body><h1>WeatherDemo 后端已启动</h1><p>Flask API 已在运行，但尚未找到前端生产构建文件。</p>
<p>构建版需要先在另一个终端执行：<code>cd weather_sys/font/weather_font</code>、<code>npm install</code>、<code>npm run build</code>，然后刷新本页；开发预览需要运行 <code>npm run dev</code> 后打开 <a href="http://localhost:5173">http://localhost:5173</a>。</p>
<p>健康检查：<a href="/api/health">/api/health</a></p></body></html>"""

    @app.get("/dashboard")
    def frontend_preview():
        index_file = FRONTEND_DIST / "index.html"
        if index_file.is_file():
            return send_from_directory(FRONTEND_DIST, "index.html")
        return Response(setup_page, status=200, mimetype="text/html")

    @app.get("/assets/<path:filename>")
    def frontend_assets(filename: str):
        mimetype = "application/javascript" if filename.endswith(".js") else None
        return send_from_directory(FRONTEND_DIST / "assets", filename, mimetype=mimetype)

    @app.get("/maps/<path:filename>")
    def frontend_maps(filename: str):
        return send_from_directory(FRONTEND_DIST / "maps", filename)

    @app.get("/favicon.svg")
    def frontend_favicon():
        return send_from_directory(FRONTEND_DIST, "favicon.svg")


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
        response, status = error_response(message=message, http_status=status_code)
        if status_code == 405 and error.valid_methods:
            response.headers["Allow"] = ", ".join(sorted(error.valid_methods))
        return response, status

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception):
        LOGGER.exception("Unhandled application exception: %s", error)
        return error_response(
            message="internal server error",
            http_status=500,
        )
