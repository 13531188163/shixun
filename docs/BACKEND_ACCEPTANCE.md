# WeatherDemo 后端验收报告

验收日期：2026-09-26
数据库：`weather_db`（MySQL 8.0.43）
验收范围：Phase 6 后端完整验收、只读真实数据库验证、REST API 契约冻结

## 1. 验收范围

本次验收覆盖 Flask 启动、Blueprint 注册、11 个正式 GET API、Model / Service
分层、真实 MySQL 只读请求、参数边界、错误响应、CORS、数据类型、名称归一化、
SQL 安全和大表查询风险。

本阶段没有新增业务 REST API、没有写入数据库、没有修改表结构、没有修改
`database/weather_data.sql`，也没有创建 Vue 页面。管理后台预览属于下一阶段
前端工作范围。

## 2. 后端架构

```text
MySQL weather_db
    ↓
Models / Repository（参数化只读 SQL）
    ↓
Services（业务组合、归一化、数值和日期转换）
    ↓
Routes（参数校验、Service 调用、统一响应）
    ↓
Flask REST API /api
```

启动方式：`python weather_sys/app.py`。实际启动确认无 ImportError、循环依赖、
Blueprint 冲突或重复路由；服务监听 `http://127.0.0.1:5000`。

## 3. API 清单

| Method | URL | Route | Service | Model / 数据边界 | 测试 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/api/health` | `health_check` | `ping_database` | `utils.db` | `test_health_and_errors.py`、真实请求 | PASS |
| GET | `/api/locations/provinces` | `provinces` | `list_provinces` | `weather_model.get_distinct_provinces` | `test_location_routes.py`、真实请求 | PASS |
| GET | `/api/locations/cities` | `cities` | `list_cities` | `weather_model.get_distinct_cities` | `test_location_routes.py`、真实请求 | PASS |
| GET | `/api/locations/districts` | `districts` | `list_districts` | `weather_model.get_distinct_districts` | `test_location_routes.py`、真实请求 | PASS |
| GET | `/api/weather/latest` | `latest_weather` | `get_latest_weather` | `weather_model.get_latest_weather` | `test_weather_routes.py`、真实请求 | PASS |
| GET | `/api/weather/trend` | `weather_trend` | `get_weather_trend` | `weather_model.get_weather_history_by_date` | `test_weather_routes.py`、真实请求 | PASS |
| GET | `/api/weather/city-comparison` | `city_comparison` | `compare_cities` | `weather_model.get_city_weather_latest` | `test_weather_routes.py`、真实请求 | PASS |
| GET | `/api/air-quality/latest` | `latest_air_quality` | `get_latest_air_quality` | `air_quality_model.get_latest_air_quality` | `test_air_quality_routes.py`、真实请求 | PASS |
| GET | `/api/air-quality/ranking` | `air_quality_ranking` | `get_air_quality_ranking` | `air_quality_model.get_air_quality_ranking` | `test_air_quality_routes.py`、真实请求 | PASS |
| GET | `/api/air-quality/distribution` | `air_quality_distribution` | `get_air_quality_distribution_result` | `air_quality_model.get_air_quality_distribution` | `test_air_quality_routes.py`、真实请求 | PASS |
| GET | `/api/dashboard/overview` | `dashboard_overview` | `get_dashboard_overview` | weather / AQI models | `test_dashboard_routes.py`、真实请求 | PASS |

Flask 路由、`docs/API_SPEC.md`、`docs/openapi.yaml` 均包含同样的 11 个路径，
不存在多余实现或缺失实现。

## 4. 测试环境

- Windows，Python 3，Flask 开发服务器（debug off）。
- MySQL 8.0.43，数据库 `weather_db`。
- CORS 实际允许 `http://localhost:5173` 和 `http://127.0.0.1:5173`，没有使用 `*`。
- 所有数据库验收请求均为 GET / SELECT / EXPLAIN，只读执行。

## 5. 自动测试结果

- 全部测试：49/49 通过，默认跳过 3 个需要数据库的集成测试。
- `RUN_DB_TESTS=1`：49/49 通过，包含 Model 的真实 MySQL 只读测试。
- `ruff check weather_sys tests scripts`：通过。
- `python -m compileall -q weather_sys tests scripts`：通过。
- OpenAPI YAML 解析：通过，11 个路径与 Flask 路由一致。

## 6. 真实数据库测试结果

真实数据库统计：

| 表 | 实际记录数 |
| --- | ---: |
| `weather_data` | 834,971 |
| `air_quality_data` | 262 |
| `wind_data` | 0 |

真实天气最新日期为 `2026-05-22`，空气质量快照时间为
`2026-05-31 17:40:21`。所有 11 个正式 API 均已通过真实 HTTP 请求验证。

已覆盖的边界请求包括：天气趋势 `days=7/14/30`、非法 days、城市比较重复/缺失/
超限输入、AQI 升降序及多个 limit、非法 limit/order、缺少参数、空字符串、不存
在地区、未知路由和错误 HTTP Method。

## 7. 数据真实性检查

- 天气温度、风速和降水返回 JSON number 或 null，不返回带单位字符串。
- AQI 返回 integer 或 null，排名使用数值排序。
- 日期统一为 `YYYY-MM-DD`，时间统一为 `YYYY-MM-DD HH:mm:ss`。
- 城市和省份使用显式别名归一化，原始数据库不修改。
- 城市比较保持请求顺序，缺失城市不填 0。
- AQI 分布 `count` 总和为 `meta.totalKnown=262`。
- Dashboard 只返回 `location`、`latestWeather`、`latestAirQuality`、
  `basicStatistics`，没有添加数据库不支持的指标。
- `wind_data` 为空时返回空结果，不伪造风向、风力等级或随机值。

## 8. 安全检查

- 后端 SQL 未发现 INSERT、UPDATE、DELETE、ALTER、DROP、TRUNCATE 等写操作。
- 用户输入均通过 DB-API 参数传递；`order` 只接受 `asc` / `desc` 白名单值。
- 查询使用显式字段，不使用无条件 `SELECT *`。
- 错误响应不会返回密码、连接串、SQL、`.env` 内容或 Python 堆栈。
- `.env`、缓存目录和日志规则已加入 `.gitignore`，未进入 Git。

## 9. 性能风险

`weather_data` 是约 83 万行的大表。真实 `EXPLAIN` 结果显示地点过滤会使用
现有 `idx_province`，但日期字符串解析和排序仍产生 filesort；地点列表会产生
temporary。AQI 排名因 `aqi` 是字符串并需要数值转换，当前对 262 行执行 filesort，
规模较小时可接受。

代码已经通过地点条件、显式字段、`LIMIT` 和数据库端聚合控制结果集大小，没有把
整张天气表读入 Python。

## 10. 已知限制

- `latest` 表示历史库中按日期可获得的最新记录，不代表实时天气或未来预报。
- `weather_data.date`、温度和 AQI 等字段在源表中是字符串，排序和转换有额外成本。
- 当前没有独立的经纬度、地图边界、污染物浓度、湿度、气压、能见度、紫外线、预警
  事件或健康建议数据。
- Phase 6 按冻结契约实现 AQI 分布字段 `status` 和 `count`；验收清单中出现的
  `level` / `percentage` 不属于当前 `API_SPEC.md` / `openapi.yaml` 契约，前端应
  以冻结契约为准。

## 11. 不支持的数据

当前数据库不支持以下正式指标或业务：

- PM2.5、PM10、SO2、NO2、CO、O3；
- 湿度、气压、能见度、紫外线；
- 气象预警、健康建议；
- 经纬度、行政区边界和真实地图拓扑；
- 未来天气预测和真实实时气象；
- `wind_data` 当前为空，不提供其派生业务数据。

## 12. 推荐索引

本阶段没有执行任何 `ALTER TABLE`。建议经过线上 `EXPLAIN` 和负载测量后，以独立
migration 评估：

1. `weather_data(province, city, district, date, id)`，支持地点过滤和最新记录选择；
2. 如果调用经常省略 province，再单独比较 `weather_data(city, district, date, id)`，
   不建议未经测量同时添加；
3. `air_quality_data(city, created_at, id)`，支持城市最新快照；
4. AQI 高频排名可评估数值化生成列及索引，但必须先处理历史非数字值。

## 13. API 契约冻结

`docs/API_SPEC.md` 已增加：

> API Status: FROZEN FOR FRONTEND DEVELOPMENT

冻结后，URL、Method、Query 参数、Response 字段、JSON 层级和字段类型不得直接
破坏性修改。任何兼容性变更都必须同步 API_SPEC、OpenAPI、后端测试和前端调用。
