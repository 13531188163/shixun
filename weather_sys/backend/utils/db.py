"""On-demand PyMySQL connection helpers."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

import pymysql
from pymysql.cursors import DictCursor
from flask import has_app_context, current_app

from ..config import Settings, settings
from .exceptions import DatabaseUnavailableError

LOGGER = logging.getLogger(__name__)


def _active_settings() -> Settings:
    """Use app configuration when available, with module settings as fallback."""
    if has_app_context():
        return Settings(
            db_host=current_app.config["DB_HOST"],
            db_port=current_app.config["DB_PORT"],
            db_user=current_app.config["DB_USER"],
            db_password=current_app.config["DB_PASSWORD"],
            db_name=current_app.config["DB_NAME"],
            flask_host=settings.flask_host,
            flask_port=settings.flask_port,
            flask_debug=settings.flask_debug,
            cors_origins=settings.cors_origins,
        )
    return settings


def get_connection():
    """Open a new MySQL connection using centralized settings."""
    active_settings = _active_settings()
    try:
        return pymysql.connect(
            host=active_settings.db_host,
            port=active_settings.db_port,
            user=active_settings.db_user,
            password=active_settings.db_password,
            database=active_settings.db_name,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=True,
            connect_timeout=5,
            read_timeout=5,
            write_timeout=5,
        )
    except pymysql.MySQLError as exc:
        LOGGER.error(
            "MySQL connection failed for host=%s port=%s database=%s",
            active_settings.db_host,
            active_settings.db_port,
            active_settings.db_name,
        )
        raise DatabaseUnavailableError() from exc


@contextmanager
def connection_scope() -> Generator:
    """Yield one connection and always close it after use."""
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()


def ping_database() -> None:
    """Run the minimal database health query and close cursor/connection."""
    try:
        with connection_scope() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
                result = cursor.fetchone()
                if not result or result.get("ok") != 1:
                    raise DatabaseUnavailableError()
    except DatabaseUnavailableError:
        raise
    except pymysql.MySQLError as exc:
        LOGGER.error("MySQL health query failed")
        raise DatabaseUnavailableError() from exc
