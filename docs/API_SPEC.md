# weatherdemo REST API 规范

> **API Status: FROZEN FOR FRONTEND DEVELOPMENT**
> Frozen on 2026-09-26 after Phase 6 backend acceptance. During Vue 3
> development, URL、HTTP Method、query parameters、response fields、JSON
> nesting and data types must remain compatible. Any required change must be
> recorded here and synchronized with `docs/openapi.yaml`, backend tests and
> frontend callers.

## 1. 契约范围

本文件是 Flask 后端和未来 Vue 3 前端共同遵守的接口契约。本阶段只设计接口，不实现路由、Model、Repository 或 Service。

- Base URL：/api
- JSON 字段：camelCase
- Python 内部字段：snake_case
- 数据库字段：保持原始 snake_case
- 日期：YYYY-MM-DD
- 时间：YYYY-MM-DD HH:mm:ss
- 成功：HTTP 200，code 为 200
- 参数错误：HTTP 400
- 资源不存在：HTTP 404
- 服务器或数据库异常：HTTP 500
- 列表统一使用 data 数组；单对象接口使用 data 对象；无数据时返回空数组或 null。
- 接口只返回业务数据，不返回 ECharts option。

### 1.1 统一成功响应

对象型接口：

    {
      "code": 200,
      "message": "success",
      "data": {}
    }

列表型接口：

    {
      "code": 200,
      "message": "success",
      "data": [],
      "meta": {}
    }

### 1.2 统一错误响应

    {
      "code": 400,
      "message": "invalid query parameter: days",
      "data": null
    }

message 可读但不得泄漏 SQL、密码或连接串。

### 1.3 数据可用状态

文档中的“数据可用状态”对应契约元信息 data_status；取值必须是以下四类之一：

- available：当前 SQL 可以直接读取或确定计算。
- partial：只能支持模块的一部分，响应不得包含缺失指标。
- unavailable：当前数据库不支持，暂不提供正式接口字段。
- future_extension：预留给未来新增真实数据源或 migration。

## 2. 数据和选择规则

1. 天气接口的 latest 按解析后的 weather_data.date 选择，不能按 created_at 或 id 冒充观测时间。
2. air_quality_data 没有观测日期；空气接口按 created_at 选择最新快照，同一城市同一时间以 id 较大者为稳定选择。
3. city、province 输入接受规范化名称和已登记的原始别名；Service 使用显式 normalize_city_name() 和地区规范化函数匹配，原始数据库不修改。
4. district 未提供时，天气接口选取该城市最新日期下按 district 字典序、id 升序的稳定代表记录，并在响应中返回实际 district；这不是城市平均值。
5. city-comparison 在每个城市使用同一代表记录规则；不得把缺失城市填成 0。
6. 数值字段在 service 层清洗：温度去除 ℃ 后转 number；风速、降水转 number；AQI 转 integer；失败或 NULL 返回 null。
7. weather_data 的 year、month 是标签，不作为日期排序主键。

## 3. System

### 3.1 健康检查

- 接口名称：健康检查
- Method：GET
- URL：/api/health
- 业务用途：确认 Flask 进程可响应，并使用参数化 SELECT 1 检查 MySQL 连接。
- Query 参数：无。
- 参数类型：无。
- 是否必填：无。
- 默认值：无。
- 参数约束：无。
- 数据来源表：无业务表；数据库连接元信息。
- 数据计算方式：application 为进程状态，database 为 SELECT 1 结果，checkedAt 为服务器检查时间。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": {
          "application": "ok",
          "database": "ok",
          "checkedAt": "2026-05-31 17:40:21"
        }
      }

- 参数错误示例：不适用。
- 无数据示例：不适用。
- HTTP Status：200；数据库不可用时 500。
- 前端对应模块：应用启动探针。
- 数据可用状态：available。

## 4. Location

### 4.1 获取省份列表

- 接口名称：获取省份列表
- Method：GET
- URL：/api/locations/provinces
- 业务用途：为省份选择器提供当前 weather_data 中可查询的规范化省份名称。
- Query 参数：无。
- 参数类型：无。
- 是否必填：无。
- 默认值：无。
- 参数约束：返回去重、排序后的字符串数组。
- 数据来源表：weather_data.province。
- 数据计算方式：SELECT DISTINCT 后显式地区名称归一化、去重、排序。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": ["北京", "上海", "广东", "浙江"],
        "meta": {}
      }

- 参数错误示例：不适用。
- 无数据示例：

      {
        "code": 200,
        "message": "success",
        "data": [],
        "meta": {}
      }

- HTTP Status：200；数据库异常 500。
- 前端对应模块：省份选择器、地图筛选器。
- 数据可用状态：available。

### 4.2 获取城市列表

- 接口名称：获取城市列表
- Method：GET
- URL：/api/locations/cities
- 业务用途：按省份提供规范化城市列表。
- Query 参数：province。
- 参数类型：string。
- 是否必填：是。
- 默认值：无。
- 参数约束：长度 1-50；接受规范化值和已登记原始别名；不存在的省份返回 404。
- 数据来源表：weather_data.province、weather_data.city。
- 数据计算方式：按归一化 province 过滤，DISTINCT city，归一化后去重排序。
- 成功示例：GET /api/locations/cities?province=北京

      {
        "code": 200,
        "message": "success",
        "data": ["北京"],
        "meta": {}
      }

- 参数错误示例：

      {
        "code": 400,
        "message": "province is required",
        "data": null
      }

- 无数据示例：

      {
        "code": 404,
        "message": "province not found",
        "data": null
      }

- HTTP Status：200、400、404、500。
- 前端对应模块：城市选择器。
- 数据可用状态：available。

### 4.3 获取区县列表

- 接口名称：获取区县列表
- Method：GET
- URL：/api/locations/districts
- 业务用途：按省份和城市提供区县列表。
- Query 参数：province、city。
- 参数类型：string、string。
- 是否必填：均必填。
- 默认值：无。
- 参数约束：长度 1-50；接受规范化值和已登记原始别名；区县保持原始行政区名称。
- 数据来源表：weather_data.province、weather_data.city、weather_data.district。
- 数据计算方式：按规范化省份和城市过滤，对非 NULL district 去重排序。
- 成功示例：GET /api/locations/districts?province=北京&city=北京

      {
        "code": 200,
        "message": "success",
        "data": ["东城区", "西城区", "朝阳区", "丰台区", "石景山区", "海淀区", "门头沟区", "房山区", "通州区", "顺义区", "昌平区", "大兴区", "怀柔区", "平谷区", "密云区", "延庆区"],
        "meta": {}
      }

- 参数错误示例：

      {
        "code": 400,
        "message": "city is required",
        "data": null
      }

- 无数据示例：

      {
        "code": 404,
        "message": "location not found",
        "data": null
      }

- HTTP Status：200、400、404、500。
- 前端对应模块：区县选择器。
- 数据可用状态：available。

## 5. Weather

### 5.1 获取最新天气记录

- 接口名称：获取最新天气
- Method：GET
- URL：/api/weather/latest
- 业务用途：获取指定城市（可选区县）按 date 可获得的最新天气记录。
- Query 参数：province、city、district。
- 参数类型：string、string、string。
- 是否必填：province 否；city 是；district 否。
- 默认值：province 由 city 反查；district 不提供时使用稳定代表记录。
- 参数约束：名称长度 1-50；city 必须存在；district 若提供必须属于该城市。
- 数据来源表：weather_data。
- 数据计算方式：按位置过滤，解析 date 后倒序取最新日期；district 缺省时按 district、id 稳定选择一条原始记录；转换天气数值和城市名称。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": {
          "province": "北京",
          "city": "北京",
          "district": "东城区",
          "date": "2026-03-31",
          "weather": "阴",
          "maxTemp": 18.2,
          "minTemp": 5.6,
          "avgWind": 1.56,
          "maxWind": 9.5,
          "precipitation": 0
        }
      }

- 参数错误示例：

      {
        "code": 400,
        "message": "city is required",
        "data": null
      }

- 无数据示例：

      {
        "code": 404,
        "message": "weather record not found",
        "data": null
      }

- HTTP Status：200、400、404、500。
- 前端对应模块：当前天气概况、顶部温度/风速/降水卡片。
- 数据可用状态：available。

### 5.2 获取天气趋势

- 接口名称：获取天气趋势
- Method：GET
- URL：/api/weather/trend
- 业务用途：获取历史最高温、最低温、风速和降水趋势，供 ECharts 映射。
- Query 参数：province、city、district、days。
- 参数类型：string、string、string、integer。
- 是否必填：province 否；city 是；district 否；days 否。
- 默认值：days=7；province 由 city 反查；district 缺省使用每个日期的稳定代表记录。
- 参数约束：days 为 1-90 整数；名称长度 1-50；必须按 date 限制查询范围。
- 数据来源表：weather_data。
- 数据计算方式：筛选位置后按解析 date 取最近 days 个可用日期，升序返回；每个日期选 district、id 稳定代表记录；转换天气数值。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": [
          {"date": "2026-03-29", "weather": "阴", "maxTemp": 22.3, "minTemp": 7.6, "avgWind": 1.89, "maxWind": 13.7, "precipitation": 0.1},
          {"date": "2026-03-30", "weather": "晴", "maxTemp": 17, "minTemp": 5.7, "avgWind": 1.67, "maxWind": 6, "precipitation": 0},
          {"date": "2026-03-31", "weather": "阴", "maxTemp": 18.2, "minTemp": 5.6, "avgWind": 1.56, "maxWind": 9.5, "precipitation": 0}
        ],
        "meta": {"days": 3}
      }

- 参数错误示例：

      {
        "code": 400,
        "message": "days must be an integer between 1 and 90",
        "data": null
      }

- 无数据示例：

      {
        "code": 200,
        "message": "success",
        "data": [],
        "meta": {"days": 7}
      }

- HTTP Status：200、400、404、500。位置存在但日期范围无记录时返回 200 空数组。
- 前端对应模块：天气趋势图、历史风速/降水图。
- 数据可用状态：available（历史趋势，不是预报）。

### 5.3 城市天气比较

- 接口名称：城市天气比较
- Method：GET
- URL：/api/weather/city-comparison
- 业务用途：返回多个城市最新代表天气，用于最高温/最低温柱状图。
- Query 参数：cities。
- 参数类型：string。
- 是否必填：是。
- 默认值：无。
- 参数约束：逗号分隔 1-10 个城市；每个名称长度 1-50；去重；不存在城市不补零。
- 数据来源表：weather_data。
- 数据计算方式：每个城市按 latest 规则选取同一代表记录，转换 JSON 字段；返回顺序与输入顺序一致。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": [
          {"province": "北京", "city": "北京", "district": "东城区", "date": "2026-03-31", "weather": "阴", "maxTemp": 18.2, "minTemp": 5.6},
          {"province": "上海", "city": "上海", "district": "黄浦区", "date": "2026-03-31", "weather": "中雨", "maxTemp": 16.7, "minTemp": 10.6},
          {"province": "广东", "city": "广州", "district": "荔湾区", "date": "2026-03-31", "weather": "小阵雨", "maxTemp": 29.3, "minTemp": 19.9},
          {"province": "广东", "city": "深圳", "district": "罗湖区", "date": "2026-03-31", "weather": "中阵雨", "maxTemp": 28.3, "minTemp": 22},
          {"province": "浙江", "city": "杭州", "district": "上城区", "date": "2026-03-31", "weather": "中雨", "maxTemp": 17.6, "minTemp": 11.8}
        ],
        "meta": {"requested": 5, "returned": 5}
      }

- 参数错误示例：

      {
        "code": 400,
        "message": "cities must contain between 1 and 10 city names",
        "data": null
      }

- 无数据示例：

      {
        "code": 200,
        "message": "success",
        "data": [],
        "meta": {"requested": 1, "returned": 0}
      }

- HTTP Status：200、400、500。部分或全部城市无数据时仍返回 200 空数组或已匹配城市，
  并在 meta 报告 requested / returned 数量；不存在城市不补零。
- 前端对应模块：主要城市天气对比柱状图。
- 数据可用状态：available。

## 6. Air Quality

### 6.1 获取最新空气质量

- 接口名称：获取城市最新空气质量
- Method：GET
- URL：/api/air-quality/latest
- 业务用途：返回指定城市在 air_quality_data 中可获得的最新 AQI 快照。
- Query 参数：city。
- 参数类型：string。
- 是否必填：是。
- 默认值：无。
- 参数约束：长度 1-50；接受规范化城市名和已登记原始别名。
- 数据来源表：air_quality_data。
- 数据计算方式：按规范化 city 过滤，按 created_at 倒序、id 倒序取一条；aqi 转 integer；created_at 仅代表快照时间。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": {
          "city": "北京",
          "province": "北京",
          "aqi": 105,
          "status": "轻度",
          "createdAt": "2026-05-31 17:40:21"
        }
      }

- 参数错误示例：

      {
        "code": 400,
        "message": "city is required",
        "data": null
      }

- 无数据示例：

      {
        "code": 404,
        "message": "air quality record not found",
        "data": null
      }

- HTTP Status：200、400、404、500。
- 前端对应模块：AQI 指标卡、空气质量概况。
- 数据可用状态：available（AQI 与等级）；污染物明细 unavailable。

### 6.2 空气质量排名

- 接口名称：空气质量排名
- Method：GET
- URL：/api/air-quality/ranking
- 业务用途：提供空气质量 AQI 排名，供 TOP10 表格使用。
- Query 参数：limit、order。
- 参数类型：integer、string。
- 是否必填：均否。
- 默认值：limit=10；order=asc。
- 参数约束：limit 为 1-100 整数；order 只能是 asc 或 desc；asc 表示 AQI 从低到高。
- 数据来源表：air_quality_data.city、province、aqi、status。
- 数据计算方式：aqi 转整数后排序并 LIMIT；无法转换的 aqi 不参与排名；并列按 city、id 稳定排序。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": [
          {"rank": 1, "city": "二连浩特", "province": "内蒙古", "aqi": 16, "status": "优"},
          {"rank": 2, "city": "香格里拉", "province": "云南", "aqi": 19, "status": "优"},
          {"rank": 3, "city": "三亚", "province": "海南", "aqi": 19, "status": "优"}
        ],
        "meta": {"limit": 3, "order": "asc"}
      }

- 参数错误示例：

      {
        "code": 400,
        "message": "order must be asc or desc",
        "data": null
      }

- 无数据示例：

      {
        "code": 200,
        "message": "success",
        "data": [],
        "meta": {"limit": 10, "order": "asc"}
      }

- HTTP Status：200、400、500。
- 前端对应模块：城市空气质量 TOP10。
- 数据可用状态：available。

### 6.3 空气质量等级分布

- 接口名称：空气质量等级分布
- Method：GET
- URL：/api/air-quality/distribution
- 业务用途：统计当前空气质量快照中各 status 等级的城市数量。
- Query 参数：无。
- 参数类型：无。
- 是否必填：无。
- 默认值：无。
- 参数约束：按 status 原值分组；NULL status 不计入已知等级。
- 数据来源表：air_quality_data.status。
- 数据计算方式：GROUP BY status、COUNT(*)；按 优、良、轻度、中度、重度、严重污染 顺序输出实际存在的等级。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": [
          {"status": "优", "count": 101},
          {"status": "良", "count": 133},
          {"status": "轻度", "count": 28}
        ],
        "meta": {"totalKnown": 262}
      }

- 参数错误示例：不适用。
- 无数据示例：

      {
        "code": 200,
        "message": "success",
        "data": [],
        "meta": {"totalKnown": 0}
      }

- HTTP Status：200、500。
- 前端对应模块：空气质量等级分布环图/饼图。
- 数据可用状态：available。

## 7. Dashboard

### 7.1 Dashboard 首屏概览

- 接口名称：Dashboard 概览
- Method：GET
- URL：/api/dashboard/overview
- 业务用途：一次返回首屏需要的当前位置、最新天气、最新空气质量和基础统计；不包含完整历史趋势。
- Query 参数：province、city、district。
- 参数类型：string、string、string。
- 是否必填：province 否；city 是；district 否。
- 默认值：province 由 city 反查；district 遵循 weather/latest 的稳定代表记录规则。
- 参数约束：名称长度 1-50；city 必须存在；basicStatistics 只能包含已有表可计算的统计。
- 数据来源表：weather_data、air_quality_data。
- 数据计算方式：复用 weather/latest 规则；通过规范化 city 关联 air_quality_data；basicStatistics 返回记录数、天气最新日期和空气快照时间，不展开历史趋势。
- 成功示例：

      {
        "code": 200,
        "message": "success",
        "data": {
          "location": {"province": "北京", "city": "北京", "district": "东城区"},
          "latestWeather": {
            "province": "北京",
            "city": "北京",
            "district": "东城区",
            "date": "2026-03-31",
            "weather": "阴",
            "maxTemp": 18.2,
            "minTemp": 5.6,
            "avgWind": 1.56,
            "maxWind": 9.5,
            "precipitation": 0
          },
          "latestAirQuality": {
            "city": "北京",
            "province": "北京",
            "aqi": 105,
            "status": "轻度",
            "createdAt": "2026-05-31 17:40:21"
          },
          "basicStatistics": {
            "weatherRecordCount": 834971,
            "airQualityRecordCount": 262,
            "weatherLatestDate": "2026-03-31",
            "airQualitySnapshotAt": "2026-05-31 17:40:21"
          }
        }
      }

- 参数错误示例：

      {
        "code": 400,
        "message": "city is required",
        "data": null
      }

- 无数据示例：

      {
        "code": 404,
        "message": "dashboard location data not found",
        "data": null
      }

- HTTP Status：200、400、404、500。
- 前端对应模块：Dashboard 首屏聚合；趋势、排名和分布仍调用独立接口。
- 数据可用状态：partial。天气、AQI、基础数量可用；湿度、污染物、预警和健康建议不可用。

## 8. 当前不提供的指标

以下参考图指标在 database/weather_data.sql 中没有可读取或可确定计算的字段，本阶段不定义正式响应字段：

- PM2.5、PM10、SO2、NO2、CO、O3；
- 相对湿度、气压、能见度、紫外线；
- 预警事件、预警次数、预警等级；
- 健康建议、运动建议、穿衣建议；
- 经纬度、行政区边界和真实全国地图拓扑；
- 未来 7 天预报；
- 实时气象值。

引入新的可信数据源后，必须先更新 DATA_DICTIONARY.md、API_SPEC.md 和 openapi.yaml，再实现后端与前端。
