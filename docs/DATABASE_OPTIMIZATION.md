# 数据库查询优化建议

本文件记录 Phase 3 对现有 `weather_db` 结构的只读检查结果。本文只给出
迁移建议，不执行 `ALTER TABLE`，也不修改 `database/weather_data.sql` 或线上表。

## 当前索引（只读核验）

| 表 | 已有索引 | 观察 |
| --- | --- | --- |
| `weather_data` | `PRIMARY(id)`、`idx_province(province)`、`idx_city(city)`、`idx_district(district)`、`idx_month(month)`、`idx_year(year)` | 没有 `date` 索引或地点+日期复合索引 |
| `air_quality_data` | `PRIMARY(id)`、`idx_city(city)`、`idx_province(province)`、`idx_aqi(aqi)` | `created_at` 没有索引；`aqi` 是字符串，普通字符串索引不能替代数值排序 |
| `wind_data` | `PRIMARY(id)`、`idx_city(city)`、`idx_year(year)`、`idx_month(month)` | 当前表为空，先不增加索引 |

## 建议的后续 migration（等待确认）

1. `weather_data` 的常用 latest/history 查询通常按省、市、区县筛选并按
   `date` 倒序。可评估 `(province, city, district, date, id)` 复合索引；如果
   调用场景经常缺少省份，再用实际 `EXPLAIN` 评估 `(city, district, date, id)`。
   两者不应未经测量同时添加。
2. `air_quality_data` 的城市最新快照可评估 `(city, created_at, id)`；如果
   省份筛选占主流，另行用 `EXPLAIN` 比较以省份开头的复合索引。
3. AQI 排名当前使用 `TRIM(aqi) REGEXP` 加 `CAST(... AS UNSIGNED)`，这是因为
   源字段是 `VARCHAR`。若排名成为高频请求，应在单独 migration 中评估数值化
   生成列及其索引，并先处理非数字历史值。

## 当前代码的性能边界

- Model 查询只选择显式字段，不使用无条件 `SELECT *`。
- 地点查询先使用已有的省、市、区县索引条件；latest/history 始终带有
  `ORDER BY` 和 `LIMIT`。
- 地区下拉列表的 `DISTINCT` 查询只负责取有界原始值，归一化和排序放在
  Service 层，避免在 83 万行表上强制全量 filesort。
- 列表查询有硬上限，避免把约 83 万条天气数据读入 Python。
- 日期字段在原表中是字符串；现阶段只能在已筛选的小范围内用
  `STR_TO_DATE` 排序。新增索引前必须用真实数据和 `EXPLAIN` 验证收益。
