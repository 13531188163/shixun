# weatherdemo 数据字典

## 1. 范围与证据

本字典只根据 database/weather_data.sql 的 DDL、索引、AUTO_INCREMENT 值和少量 INSERT 样例生成。原始 SQL 未被修改，INSERT 行数用于规模估计；部署后的实时行数仍以 MySQL 查询为准。

数据库：weather_db

原始文件：database/weather_data.sql

## 2. 表清单

| 表名 | 作用 | SQL dump 规模估计 | 状态 |
| --- | --- | ---: | --- |
| air_quality_data | 城市空气质量快照 | 262 行 | 有数据，可用于 AQI、等级、排名和分布 |
| weather_data | 按省/市/区县记录的历史天气 | 834,971 行 | 大表，天气接口的主要来源 |
| wind_data | 另一套按城市记录的天气/风力结构 | 0 行 | 只有结构，没有业务数据；当前不作为 API 数据源 |

weather_data 的 AUTO_INCREMENT 为 1,337,960，但样例 id 不连续，不能用 AUTO_INCREMENT 推断行数。

## 3. 索引与查询约束

### air_quality_data

- 主键：id
- 普通索引：idx_city(city)、idx_province(province)、idx_aqi(aqi)

### weather_data

- 主键：id
- 普通索引：idx_province(province)、idx_city(city)、idx_district(district)、idx_month(month)、idx_year(year)

### wind_data

- 主键：id
- 普通索引：idx_city(city)、idx_year(year)、idx_month(month)

原表没有 date 复合索引，也没有业务唯一约束。正式实现必须先用省/市/区县条件缩小范围，再做日期解析、排序和 LIMIT；如需优化索引只能新增独立 migration，不能改写原始 SQL。

## 4. air_quality_data 字段

| 数据库字段 | 类型 | 是否为空 | SQL 样例 | 业务含义 | API 字段 | 是否需要转换 |
| --- | --- | --- | --- | --- | --- | --- |
| id | bigint | 否，自增 | 1 | 空气质量记录标识 | id | 否 |
| city | varchar(50) | 否 | 二连浩特、北京 | 城市名称 | city | 规范化名称 |
| province | varchar(50) | 否 | 内蒙古、北京 | 省/直辖市名称 | province | 规范化名称 |
| aqi | varchar(20) | 否 | 16、105、149 | 空气质量指数 | aqi | string → integer |
| status | varchar(50) | 是 | 优、良、轻度 | AQI 等级文本 | status | 去空白；NULL 保持 null |
| created_at | timestamp | 是，默认 CURRENT_TIMESTAMP | 2026-05-31 17:40:21 | 导入/快照时间 | createdAt | snake_case → camelCase、时间格式化 |

样例 status 的计数为：优 101、良 133、轻度 28；未在样例中发现中度、重度、严重污染。接口不能假定所有等级都有数据。

## 5. weather_data 字段

| 数据库字段 | 类型 | 是否为空 | SQL 样例 | 业务含义 | API 字段 | 是否需要转换 |
| --- | --- | --- | --- | --- | --- | --- |
| id | bigint | 否，自增 | 502989 | 天气记录标识 | id（内部可不返回） | 否 |
| province | varchar(50) | 否 | 北京市、广东省 | 省/直辖市名称 | province | 规范化名称 |
| city | varchar(50) | 否 | 北京市、广州市 | 城市名称 | city | 规范化名称 |
| district | varchar(50) | 是 | 东城区、荔湾区 | 区县名称 | district | 保留原始行政区名称 |
| year | varchar(10) | 是 | 2026年 | 年份标签 | year | 内部保留；不作为日期排序依据 |
| month | varchar(10) | 否 | 2026年3月 | 月份标签 | month | 内部保留；不作为日期排序依据 |
| date | varchar(20) | 是 | 2026-03-01 | 观测日期 | date | 按 YYYY-MM-DD 解析和验证 |
| weather | varchar(50) | 是 | 阴、晴、中雨 | 天气状况文本 | weather | 空值保持 null |
| max_temp | varchar(20) | 是 | 18.2℃、-2℃ | 日最高温度 | maxTemp | 去 ℃ 后 string → number |
| min_temp | varchar(20) | 是 | 5.6℃、-0.2℃ | 日最低温度 | minTemp | 去 ℃ 后 string → number |
| avg_wind | varchar(20) | 是 | 1.56 | 日平均风速 | avgWind | string → number |
| max_wind | varchar(20) | 是 | 9.5 | 日最大风速 | maxWind | string → number |
| total_precip | varchar(20) | 是 | 0、14.8 | 日总降水量 | precipitation | string → number；字段重命名 |
| created_at | timestamp | 是，默认 CURRENT_TIMESTAMP | 2026-05-26 12:24:48 | 数据导入时间 | createdAt（需要时） | snake_case → camelCase、时间格式化 |

### 5.1 天气字段转换重点

数据库中的温度是带单位的字符串：

    max_temp = 18.6℃
    min_temp = 8.2℃

API 必须返回：

    maxTemp = 18.6
    minTemp = 8.2

遇到 NULL、空字符串、无法解析的单位文本时，API 返回 null，不得用 0 或随机数填充。所有数值转换都必须在 service/utils 层完成。

## 6. wind_data 字段

| 数据库字段 | 类型 | 是否为空 | SQL 样例 | 业务含义 | API 字段 | 是否需要转换 |
| --- | --- | --- | --- | --- | --- | --- |
| id | bigint | 否，自增 | 无数据 | 风力记录标识 | id | 否 |
| city | varchar(50) | 否 | 无数据 | 城市名称 | city | 规范化名称 |
| year | varchar(10) | 否 | 无数据 | 年份标签 | year | 字符串标签 |
| month | varchar(10) | 否 | 无数据 | 月份标签 | month | 字符串标签 |
| date | varchar(20) | 是 | 无数据 | 观测日期 | date | 按 YYYY-MM-DD 解析 |
| weather | varchar(50) | 是 | 无数据 | 天气状况 | weather | 空值保持 null |
| max_temp | varchar(20) | 是 | 无数据 | 日最高温度 | maxTemp | 去 ℃ 后转 number |
| min_temp | varchar(20) | 是 | 无数据 | 日最低温度 | minTemp | 去 ℃ 后转 number |
| wind | varchar(50) | 是 | 无数据 | 风力/风向原始文本 | wind | 仅在有数据后定义具体拆分规则 |
| created_at | timestamp | 是，默认 CURRENT_TIMESTAMP | 无数据 | 入库时间 | createdAt | 时间格式化 |

wind_data 当前没有 INSERT，任何依赖它的 API 必须返回无数据或标记 future_extension，不能从其他字段臆造 wind 字段。

## 7. 字段映射总表

### 7.1 weather_data

| 数据库字段 | Python 内部字段 | JSON 字段 |
| --- | --- | --- |
| province | province | province |
| city | city | city |
| district | district | district |
| year | year | year |
| month | month | month |
| date | date | date |
| weather | weather | weather |
| max_temp | max_temp | maxTemp |
| min_temp | min_temp | minTemp |
| avg_wind | avg_wind | avgWind |
| max_wind | max_wind | maxWind |
| total_precip | total_precip | precipitation |
| created_at | created_at | createdAt |

### 7.2 air_quality_data

| 数据库字段 | Python 内部字段 | JSON 字段 |
| --- | --- | --- |
| id | id | id |
| city | city | city |
| province | province | province |
| aqi | aqi | aqi |
| status | status | status |
| created_at | created_at | createdAt |

### 7.3 wind_data（未来扩展）

| 数据库字段 | Python 内部字段 | JSON 字段 |
| --- | --- | --- |
| city | city | city |
| year | year | year |
| month | month | month |
| date | date | date |
| weather | weather | weather |
| max_temp | max_temp | maxTemp |
| min_temp | min_temp | minTemp |
| wind | wind | wind |
| created_at | created_at | createdAt |

## 8. 城市与地区名称规范

原始值不得修改。Service/utils 层提供 normalize_city_name() 和同类地区规范化函数，在查询比较、跨表关联和 API 输出时使用显式映射：

| 原始值 | 规范值 |
| --- | --- |
| 北京市 | 北京 |
| 上海市 | 上海 |
| 广州市 | 广州 |
| 深圳市 | 深圳 |
| 杭州市 | 杭州 |
| 广东省（province） | 广东 |
| 浙江省（province） | 浙江 |

不得盲目删除所有“市”“省”“自治区”等后缀，因为自治州、地区、县、区等行政区划可能是合法名称。未知名称保持原值并做 trim；需要新增别名时先补充本字典和 API 契约。

## 9. 数据能力矩阵

| 指标 | 数据库是否存在 | 是否可计算 | API 是否提供 | 备注 |
| --- | --- | --- | --- | --- |
| 最高温度 | 是，weather_data.max_temp | 是 | 是 | 去 ℃ 后 number |
| 最低温度 | 是，weather_data.min_temp | 是 | 是 | 去 ℃ 后 number |
| 平均风速 | 是，weather_data.avg_wind | 是 | 是 | string → number |
| 最大风速 | 是，weather_data.max_wind | 是 | 是 | string → number |
| 降水量 | 是，weather_data.total_precip | 是 | 是 | JSON 名称 precipitation |
| 天气状况 | 是，weather_data.weather | 是 | 是 | 原始中文文本 |
| AQI | 是，air_quality_data.aqi | 是 | 是 | string → integer |
| AQI 等级 | 是，air_quality_data.status | 是 | 是 | 当前样例有 优、良、轻度 |
| PM2.5 | 否 | 否 | 否 | unavailable / future_extension |
| PM10 | 否 | 否 | 否 | unavailable / future_extension |
| SO2 | 否 | 否 | 否 | unavailable / future_extension |
| NO2 | 否 | 否 | 否 | unavailable / future_extension |
| CO | 否 | 否 | 否 | unavailable / future_extension |
| O3 | 否 | 否 | 否 | unavailable / future_extension |
| 湿度 | 否 | 否 | 否 | unavailable / future_extension |
| 气压 | 否 | 否 | 否 | unavailable / future_extension |
| 能见度 | 否 | 否 | 否 | unavailable / future_extension |
| 紫外线 | 否 | 否 | 否 | unavailable / future_extension |
| 经纬度 | 否 | 否 | 否 | 只能展示城市列表，不能承诺真实地图点位 |
| 预警统计 | 否 | 否 | 否 | 没有事件、等级和时间字段 |
| 健康建议 | 否 | 否 | 否 | 需要独立规则或外部可信来源 |
| 7 天天气预报 | 否 | 否 | 否 | 现有 date 记录是历史数据 |

## 10. 统计和空值规则

- API 只返回可以从原始字段读取或明确计算出的值。
- 数值转换失败返回 null，并记录数据质量问题；不得默认填 0。
- AQI 排序先转整数；无法转整数的行不参与数值排名。
- AQI 分布按 status 原值分组；NULL status 不归入已知等级。
- latest 按解析后的 date（天气）或 created_at（空气快照）选择，不按 id 猜测时间。
- 没有记录时使用统一成功空数据（data: [] 或 data: null，按接口定义），而不是生成占位天气。
