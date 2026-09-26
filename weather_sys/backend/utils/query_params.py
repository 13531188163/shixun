"""HTTP query parsing only; business conversions remain in services."""

from __future__ import annotations

import re

from flask import request

from .exceptions import AppException


def _single_value(name: str) -> str | None:
    values = request.args.getlist(name)
    if len(values) > 1:
        raise AppException(f"invalid query parameter: {name}")
    return values[0].strip() if values else None


def name_param(name: str, required: bool = False) -> str | None:
    value = _single_value(name)
    if required and not value:
        raise AppException(f"{name} is required")
    if value is None:
        return None
    if not 1 <= len(value) <= 50:
        raise AppException(f"{name} must be between 1 and 50 characters")
    return value


def integer_param(name: str, default: int, minimum: int, maximum: int) -> int:
    value = _single_value(name)
    if value is None:
        return default
    message = f"{name} must be an integer between {minimum} and {maximum}"
    if len(value) > 32 or not re.fullmatch(r"[+-]?[0-9]+", value):
        raise AppException(message)
    number = int(value)
    if not minimum <= number <= maximum:
        raise AppException(message)
    return number


def enum_param(name: str, default: str, choices: tuple[str, ...]) -> str:
    value = _single_value(name)
    if value is None:
        return default
    if value not in choices:
        raise AppException(f"{name} must be {' or '.join(choices)}")
    return value


def cities_param() -> list[str]:
    value = _single_value("cities")
    message = "cities must contain between 1 and 10 city names"
    if not value:
        raise AppException(message)
    # 最多拆出 11 项即可拒绝超限输入；别名去重交给已有 Service。
    parts = value.split(",", 10)
    if len(parts) > 10:
        raise AppException(message)
    cities = [part.strip() for part in parts]
    # OpenAPI 的 Cities pattern 要求每一项非空。
    if any(not city for city in cities):
        raise AppException(message)
    if any(len(city) > 50 for city in cities):
        raise AppException("city must be between 1 and 50 characters")
    return cities


def weather_location_params() -> dict[str, str | None]:
    return {
        "city": name_param("city", required=True),
        "province": name_param("province"),
        "district": name_param("district"),
    }
