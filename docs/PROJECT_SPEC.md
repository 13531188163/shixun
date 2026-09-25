# weatherdemo 项目规范与 Phase 1 结论

## 1. 文档定位

本文件记录 weatherdemo 第一阶段的项目级决策、数据分析结论、Dashboard 能力边界和后续实现顺序。它与 AGENTS.md、DATA_DICTIONARY.md、API_SPEC.md、openapi.yaml 一起构成后续开发的约束。

本阶段只制定规则和接口契约，不创建 Flask 路由、Model、Repository、Service、Vue 页面，不安装依赖，不启动服务，不修改原始 SQL。

## 2. 系统目标

weatherdemo 是天气与空气质量数据分析及可视化系统，目标架构为：

    MySQL weather_db
        ↓
    Flask REST API（/api）
        ↓
    Vue 3 + Axios
        ↓
    ECharts Dashboard

数据库是业务事实的唯一来源。dashboard-reference.png 只用于设计参考；当图片和数据库能力冲突时，数据库优先。

## 3. 已检查的输入

| 输入 | 检查方式 | 结论 |
| --- | --- | --- |
| database/weather_data.sql | 读取 DDL、索引、AUTO_INCREMENT、少量首尾样例及按表 INSERT 计数 | 3 张表；weather_data 为大表；所有业务数值字段以字符串保存 |
| docs/reference/dashboard-reference.png | 视觉检查布局与指标卡 | 包含天气、AQI、污染物、预警、健康建议等模块，但图片不能证明数据库存在对应字段 |

SQL dump 的 INSERT 行计数（用于规模估计，不代替运行时 COUNT）：

- air_quality_data：262 行；
- weather_data：834,971 行；
- wind_data：0 行。

weather_data 的 DDL AUTO_INCREMENT 为 1,337,960，样例 id 从 502,989 到 1,337,959，说明不能用连续 id 推断实际行数。实际部署后仍应以数据库查询结果为准。

## 4. 数据源结论

### 4.1 air_quality_data

有 city、province、aqi、status、created_at。样例快照时间为 2026-05-31 17:40:21；status 样例为 优、良、轻度，计数分别为 101、133、28。aqi 在原表中是 varchar(20)，Service 必须转换为整数后再排序、统计和输出。

该表没有日期观测字段，created_at 更像导入/快照时间。因此 Air Quality API 应说明其是数据快照，不声称实时监测。

### 4.2 weather_data

有省、市、区县、年月标签、date、weather、最高/最低温、平均/最大风速、总降水和 created_at。样例包含 2026-03-01 至 2026-03-31 的天气记录，温度值带 ℃ 后缀，如 18.2℃、-2℃。

province、city 在该表中同时出现：

- 北京市 / 北京市；
- 上海市 / 上海市；
- 广东省 / 广州市、深圳市；
- 浙江省 / 杭州市。

因此查询输入和 API 输出使用规范化名称，原始值不回写数据库。东城区等区县保持原始行政区名称，不做无依据的后缀删除。

### 4.3 wind_data

表结构存在 city、year、month、date、weather、max_temp、min_temp、wind 和 created_at，但 SQL dump 没有任何 INSERT。当前公开接口不得依赖该表；风速接口数据来自 weather_data.avg_wind 和 weather_data.max_wind。未来填充 wind_data 时必须先重新评估是否需要独立接口。

## 5. 统一转换与命名决策

### 5.1 城市与地区规范化

Service/utils 层提供 normalize_city_name()，采用显式映射而不是盲目删除“市”：

| 原始值 | 规范值 |
| --- | --- |
| 北京市 | 北京 |
| 上海市 | 上海 |
| 广州市 | 广州 |
| 深圳市 | 深圳 |
| 杭州市 | 杭州 |

对 province 使用同样的显式地区映射，例如 北京市→北京、上海市→上海、广东省→广东、浙江省→浙江。自治州、地区、县、区等名称不得通过通用字符串截断处理。归一化只发生在查询比较和 response 转换，原始 SQL 不变。

### 5.2 数值与日期

- max_temp、min_temp：去除末尾 ℃ 和空白后转 number；例如 18.6℃ → 18.6。
- avg_wind、max_wind、total_precip、wind_data.wind：按可解析的小数转 number；解析失败或原值为 NULL 时输出 null，并记录数据质量日志。
- aqi：去除空白后转 integer；不能解析的值不得参与数值排序或统计。
- date：按 YYYY-MM-DD 解析和排序，API 保持 YYYY-MM-DD。
- year、month：原库包含 年、月后缀，主要用于数据源追踪；业务排序优先使用 date。
- created_at：API 使用 createdAt，格式 YYYY-MM-DD HH:mm:ss；它是入库/快照时间，不等同于观测日期。

## 6. Dashboard 页面模块映射

下表将参考图中的模块映射到当前契约。支持表示可以直接用已有字段；部分支持表示只能实现其中一部分或需要明确限制；当前数据不支持表示不得创建虚假接口字段。

| 页面模块 | 后端接口 | SQL 来源字段 | 状态 | 说明 |
| --- | --- | --- | --- | --- |
| 顶部天气指标卡（温度、风速、降水） | /api/weather/latest | weather_data.date、max_temp、min_temp、avg_wind、max_wind、total_precip | 支持 | 温度和数值先做字符串清洗；图片中的湿度不提供 |
| 当前天气概况 | /api/weather/latest | weather_data.city、district、date、weather、max_temp、min_temp | 支持 | latest 是历史库最新日期，不是 realtime |
| 城市温度比较 | /api/weather/city-comparison | weather_data.city、date、max_temp、min_temp | 支持 | 只返回数据库存在的城市，查询数量受限 |
| 天气趋势 | /api/weather/trend | weather_data.date、max_temp、min_temp、avg_wind、max_wind、total_precip、weather | 支持 | 历史趋势；不命名为预报 |
| 全国地图 / 城市点位 | /api/air-quality/ranking、/api/locations/* | air_quality_data.city、province、aqi、status | 部分支持 | 有城市和省份数值，但没有经纬度、边界或地图拓扑，不能承诺真实地理地图 |
| AQI 最新值 | /api/air-quality/latest | air_quality_data.city、province、aqi、status、created_at | 支持 | 按快照时间选取；没有污染物浓度明细 |
| AQI 排名 TOP10 | /api/air-quality/ranking | air_quality_data.city、province、aqi、status | 支持 | aqi 字符串转整数后排序，默认升序为较好排名 |
| 空气质量等级分布 | /api/air-quality/distribution | air_quality_data.status | 支持 | 当前样例实际出现 优、良、轻度；空 status 不计入已知等级 |
| 主要污染物浓度 | 无（Future API） | 无 PM2.5、PM10、SO2、NO2、CO、O3 字段 | 当前数据不支持 | 不能用 AQI 值冒充污染物浓度 |
| 空气质量预警 | 无（Future API） | 无预警事件、等级、时间字段 | 当前数据不支持 | 不返回图片中的预警次数或图标状态 |
| 健康与生活建议 | 无（Future API） | 无健康规则、敏感人群或建议字段 | 当前数据不支持 | 需要单独业务规则或可信外部数据源 |
| 7 天天气预报 | 无 | 只有历史 date 记录 | 当前数据不支持 | /api/weather/trend 仅提供历史记录，不得标为 forecast |
| Dashboard 首屏聚合 | /api/dashboard/overview | 委托 weather/latest 与 air-quality/latest，并统计已有记录 | 部分支持 | 只聚合 location、latestWeather、latestAirQuality、basicStatistics，不塞入历史趋势 |

## 7. API 契约总览

当前定义 11 个接口：

1. GET /api/health
2. GET /api/locations/provinces
3. GET /api/locations/cities
4. GET /api/locations/districts
5. GET /api/weather/latest
6. GET /api/weather/trend
7. GET /api/weather/city-comparison
8. GET /api/air-quality/latest
9. GET /api/air-quality/ranking
10. GET /api/air-quality/distribution
11. GET /api/dashboard/overview

所有接口均使用统一 response envelope、camelCase JSON 字段和 API_SPEC.md 中的错误语义。openapi.yaml 必须与上述清单逐项一致。

## 8. 查询性能与数据质量风险

1. weather_data 约 83 万条 INSERT，且数值和日期是字符串；趋势和 latest 查询必须先按省、市、区县缩小范围，再按规范化日期排序，不能无条件 SELECT *。
2. 现有索引覆盖 province、city、district、month、year，但没有 date 复合索引。正式实现前应通过 EXPLAIN 验证排序代价；如需新增索引，只能以 migration 文件变更。
3. weather_data 没有唯一约束来保证 city、district、date 唯一，Service 必须定义重复记录的稳定选择/聚合规则。
4. air_quality_data.aqi 是字符串，必须显式转换后排序；不得按字符顺序把 100 排在 20 前面。
5. air_quality_data 没有观测日期，created_at 只能表达导入快照时间。
6. wind_data 没有样例数据；依赖它的统计应返回无数据或标记 future_extension。
7. 城市和省份名称跨表不一致，必须在 Service/utils 归一化，不能修改原始 SQL。

## 9. Phase 1 验收标准

- AGENTS.md 覆盖开发顺序、分层、数据真实性、API 兼容性、前端边界和变更纪律。
- DATA_DICTIONARY.md 完整列出三张表的字段、类型、索引、转换和能力矩阵。
- API_SPEC.md 为 11 个接口逐一给出参数、来源、计算、示例、状态和数据可用状态。
- openapi.yaml 使用 OpenAPI 3.0.3，并覆盖 API_SPEC.md 的全部路径和核心 schema。
- 未创建 Flask、Vue、Model、Service、依赖或 SQL 改动。

下一阶段建议：用户确认本阶段契约后，进入 Phase 2，仅搭建 Flask 应用配置、统一 response/error 结构、数据库连接健康检查和测试骨架；暂不实现业务查询。
