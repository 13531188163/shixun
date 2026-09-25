"""Conservative city and province name normalization.

Database values remain untouched.  These helpers are used for display and
query aliases only; an unknown value is returned as-is after trimming.
"""

from __future__ import annotations

from typing import Any


CITY_ALIASES = {
    "北京市": "北京",
    "上海市": "上海",
    "天津市": "天津",
    "重庆市": "重庆",
    "广州市": "广州",
    "深圳市": "深圳",
    "杭州市": "杭州",
    "南京市": "南京",
    "武汉市": "武汉",
    "成都市": "成都",
}

PROVINCE_ALIASES = {
    "北京市": "北京",
    "上海市": "上海",
    "天津市": "天津",
    "重庆市": "重庆",
    "广东省": "广东",
    "浙江省": "浙江",
    "江苏省": "江苏",
    "四川省": "四川",
    "湖北省": "湖北",
    "河北省": "河北",
    "山东省": "山东",
    "河南省": "河南",
    "福建省": "福建",
    "湖南省": "湖南",
    "安徽省": "安徽",
    "江西省": "江西",
    "陕西省": "陕西",
    "辽宁省": "辽宁",
    "吉林省": "吉林",
    "黑龙江省": "黑龙江",
    "云南省": "云南",
    "贵州省": "贵州",
    "山西省": "山西",
    "甘肃省": "甘肃",
    "海南省": "海南",
    "青海省": "青海",
}


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_city_name(value: Any) -> str | None:
    text = _clean(value)
    return CITY_ALIASES.get(text, text) if text is not None else None


def normalize_province_name(value: Any) -> str | None:
    text = _clean(value)
    return PROVINCE_ALIASES.get(text, text) if text is not None else None


def _query_values(value: Any, aliases: dict[str, str]) -> tuple[str, ...]:
    text = _clean(value)
    if text is None:
        return ()
    canonical = aliases.get(text, text)
    values = [text]
    if canonical not in values:
        values.append(canonical)
    for raw, mapped in aliases.items():
        if mapped == canonical and raw not in values:
            values.append(raw)
    return tuple(values)


def city_query_values(value: Any) -> tuple[str, ...]:
    """Return raw/canonical city forms suitable for a parameterized ``IN``."""

    return _query_values(value, CITY_ALIASES)


def province_query_values(value: Any) -> tuple[str, ...]:
    """Return raw/canonical province forms suitable for a parameterized ``IN``."""

    return _query_values(value, PROVINCE_ALIASES)


# Descriptive aliases for callers that prefer the term "aliases".
city_aliases = city_query_values
province_aliases = province_query_values
