"""Small, deterministic conversions for values read from the source tables.

The dump stores most measurements as strings (for example ``"4.3℃"`` and
``"2 m/s"``).  Conversion failures deliberately return ``None`` so a bad
source value is not silently presented as zero.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any


_MISSING = {"", "--", "n/a", "na", "null", "none"}
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


def _number_from_text(value: Any, units: tuple[str, ...] = ()) -> int | float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        # NaN and infinity are not useful measurements.
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return None
        if number != number or number in (float("inf"), float("-inf")):
            return None
        return int(value) if number.is_integer() else number

    text = str(value).strip()
    if text.lower() in _MISSING:
        return None
    for unit in sorted(units, key=len, reverse=True):
        if text.lower().endswith(unit.lower()):
            text = text[: -len(unit)].strip()
            break
    if not _NUMBER_RE.fullmatch(text):
        return None
    try:
        number = float(text)
    except ValueError:
        return None
    return int(number) if number.is_integer() and "." not in text else number


def parse_numeric_value(value: Any) -> int | float | None:
    """Parse a numeric value and the measurement suffixes used by the dump."""

    return _number_from_text(value, ("℃", "°C", "°c", "m/s", "m／s", "米/秒", "毫米", "mm", "MM"))


def parse_temperature(value: Any) -> int | float | None:
    """Parse Celsius values such as ``"18.6℃"`` or ``"-2 °C"``."""

    return _number_from_text(value, ("℃", "°C", "°c", "C", "c"))


def parse_wind_speed(value: Any) -> int | float | None:
    """Parse wind speed values, normally stored in metres per second."""

    return _number_from_text(value, ("m/s", "m／s", "米/秒"))


def parse_precipitation(value: Any) -> int | float | None:
    """Parse precipitation amounts in millimetres."""

    return _number_from_text(value, ("毫米", "mm", "MM"))


def parse_aqi(value: Any) -> int | None:
    """Parse AQI, which is represented as an integer string in the dump."""

    number = _number_from_text(value)
    if number is None:
        return None
    if isinstance(number, float) and not number.is_integer():
        return None
    return int(number)


def format_date(value: Any) -> str | None:
    """Return a date as ``YYYY-MM-DD`` or ``None`` when it cannot be parsed."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    text = str(value).strip()
    if text.lower() in _MISSING:
        return None
    for pattern in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, pattern).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Accommodate ISO datetime values with a T separator and optional offset.
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return None
