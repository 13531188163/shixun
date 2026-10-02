"""Static, non-sensitive information for the backend management page."""

from __future__ import annotations


def get_admin_summary() -> dict[str, list[dict[str, str]]]:
    """Return the backend registry without exposing database rows."""

    return {
        "tables": [
            {
                "name": "weather_data",
                "label": "历史天气",
                "description": "按省、市、区县保存的历史天气观测记录。",
                "api": "/api/weather/latest、/api/weather/trend、/api/weather/dates",
            },
            {
                "name": "air_quality_data",
                "label": "空气质量快照",
                "description": "城市 AQI 快照；原表没有历史观测日期字段。",
                "api": "/api/air-quality/latest、/api/air-quality/ranking",
            },
            {
                "name": "wind_data",
                "label": "风力扩展表",
                "description": "预留的风力数据结构，目前不作为正式数据源。",
                "api": "暂无正式数据接口",
            },
        ],
        "routes": [
            {"path": "/api/health", "description": "应用与数据库健康检查"},
            {"path": "/api/locations/*", "description": "省份、城市、区县列表"},
            {"path": "/api/weather/*", "description": "历史天气查询"},
            {"path": "/api/air-quality/*", "description": "AQI 快照与统计"},
            {"path": "/api/dashboard/overview", "description": "Dashboard 聚合数据"},
        ],
    }
