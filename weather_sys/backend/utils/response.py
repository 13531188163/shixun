"""Unified JSON response helpers."""

from __future__ import annotations

from typing import Any, Optional

from flask import jsonify


def success_response(
    data: Any = None,
    message: str = "success",
    http_status: int = 200,
    meta: Optional[dict] = None,
):
    """Return the standard successful response envelope."""
    payload = {
        "code": 200,
        "message": message,
        "data": data,
    }
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), http_status


def error_response(
    message: str,
    http_status: int = 400,
    data: Any = None,
    meta: Optional[dict] = None,
):
    """Return the standard error response envelope."""
    payload = {
        "code": http_status,
        "message": message,
        "data": data,
    }
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), http_status
