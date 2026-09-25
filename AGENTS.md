# weatherdemo 项目开发规则

## 1. Project Overview

项目名称：weatherdemo

项目定位：天气与空气质量数据分析及可视化系统。

目标链路：

MySQL（真实数据源） → Flask REST API → Vue 3 → ECharts 数据可视化大屏

database/weather_data.sql 是项目当前唯一的业务数据资产。docs/reference/dashboard-reference.png 只用于参考布局、颜色、图表和交互密度，不是数据库字段或业务事实的来源。任何情况下都不得为了还原参考图而伪造数据库不存在的数据。

当前阶段只建立项目规范、数据字典和 API 契约，不编写后端业务实现或前端页面。

## 2. Development Order

后续开发必须按以下顺序推进：

1. Phase 1：项目规范和 API 契约
2. Phase 2：Flask 后端基础框架
3. Phase 3：数据库 Models / Repository
4. Phase 4：Service 业务层
5. Phase 5：REST API Routes
6. Phase 6：后端接口测试
7. Phase 7：接口结构冻结
8. Phase 8：Vue 3 前端基础框架
9. Phase 9：Dashboard 页面布局
10. Phase 10：ECharts 图表
11. Phase 11：前后端联调
12. Phase 12：UI 优化与响应式适配

未经用户明确要求，不得跨阶段同时大规模修改前后端。

## 3. Backend Architecture Rules

目标后端结构：

    weather_sys/
    ├── app.py
    └── backend/
        ├── config.py
        ├── models/
        ├── routes/
        ├── services/
        └── utils/

- routes 只负责请求参数获取、参数校验、调用 service 和返回统一 response。
- services 负责业务逻辑、数据组合、数据计算和字段转换。
- models / repository 只负责数据库查询与持久化边界。
- utils 负责公共工具、城市/地区名称标准化、数据格式转换和 response 工具。
- 禁止在 route 中直接编写大量 SQL。
- 配置和业务代码分离；数据库连接信息从环境变量或配置注入。
- 不得把真实数据库密码写死在代码中，不得提交 .env；必须提供 .env.example。

## 4. Database Rules

- 数据库名称：weather_db。
- 原始 SQL：database/weather_data.sql。
- database/weather_data.sql 是只读原始数据资产，禁止直接修改。
- 若未来需要新增 index、view、table 或 migration，必须创建独立 migration 文件，不得改写原始 dump。
- 除非用户明确授权，禁止 DELETE 全表、DROP 原始数据表或 TRUNCATE 原始数据表。
- 所有 SQL 必须使用参数化查询，禁止拼接用户输入。
- 面向大表查询必须指定字段，尽可能使用已有索引，并通过 WHERE 和合理的 LIMIT 限制范围。
- 禁止对大表进行无条件 SELECT *。
- weather_data.date、year、month 在原库中是字符串；查询和排序必须先确认格式，不能把字符串排序误当作日期排序。
- latest 表示数据库中按观测日期字段可获得的最新记录，不表示实时气象 API；接口和文档不得使用 realtime 误导使用者。

## 5. Data Authenticity Rules

这是最高优先级规则。

只能使用：

1. SQL 中已有的数据；
2. 可以由已有字段确定计算的数据。

不得生成数据库中不存在且无法计算的数据。当前 SQL 未提供 PM2.5、PM10、SO2、NO2、CO、O3、湿度、气压、紫外线、能见度、预警和健康建议等字段，因此 API 不得伪造这些值。参考图需要但数据库缺失的指标必须在 docs/API_SPEC.md 和相关文档中标为 unavailable 或 future_extension。

前端不得使用 Math.random() 或固定假数据冒充正式业务数据。

## 6. API Rules

- 所有 API 使用 /api 前缀。
- 成功响应统一为：

      {
        "code": 200,
        "message": "success",
        "data": {}
      }

- 列表接口可以使用 data: []，需要分页或附加信息时再提供 meta: {}。
- 参数错误：HTTP 400，data: null。
- 资源不存在：HTTP 404，data: null。
- 未处理的服务器或数据库异常：HTTP 500，data: null。
- 日期统一为 YYYY-MM-DD。
- 时间统一为 YYYY-MM-DD HH:mm:ss。
- API JSON 字段统一使用 camelCase；Python 内部变量使用 snake_case；数据库字段保持原始 snake_case。
- Service 层负责 snake_case 到 camelCase、单位清洗和数值类型转换。
- 接口不得返回 ECharts option；只返回业务数据，图表配置由前端负责。

## 7. API Compatibility Rules

某接口被 Vue 使用后，不得随意修改 URL、删除字段、重命名字段、改变字段类型或改变 response JSON 层级。若必须修改，顺序必须是：

1. 先更新 docs/API_SPEC.md；
2. 再更新 docs/openapi.yaml；
3. 最后修改后端实现和测试。

接口结构冻结（Phase 7）前，仍应把每次契约变更记录在文档中。

## 8. Frontend Rules

当前阶段不创建前端。后续前端必须遵守：

- Vue 不得直接访问 MySQL，只能调用 Flask API。
- Axios 请求统一放在 src/api/。
- ECharts 配置与数据获取尽量分离。
- 页面组件不得直接硬编码大量业务数据。
- 不得使用 Math.random() 模拟正式业务数据。

## 9. UI Reference Rules

docs/reference/dashboard-reference.png 可作为布局、颜色、科技感、卡片样式、地图位置和图表类型的设计参考。它不是业务字段的真实依据。图片与数据库冲突时，数据库真实数据优先；数据库不支持的模块必须显示为未提供、待扩展或不实现。

## 10. Code Quality and Security

- 函数职责单一，避免重复代码。
- 必要位置添加中文注释，不写无意义注释。
- 所有 API 参数必须验证类型、范围、长度和枚举值。
- 捕获并记录数据库异常，同时向客户端返回统一错误结构，不泄漏密码、连接串或 SQL 细节。
- 所有统计逻辑必须说明数据来源、过滤条件、聚合方式和空值处理。
- 不提交真实密码、令牌、.env 或导出的个人数据。
- 新增查询必须考虑索引、扫描范围、排序字段和大表性能。

## 11. Change Discipline

每次修改前必须先阅读与改动范围对应的规范：

- 任意 weatherdemo 改动：先阅读本文件。
- 修改 API：先阅读 docs/API_SPEC.md 和 docs/openapi.yaml。
- 修改数据库相关代码：先阅读 docs/DATA_DICTIONARY.md。
- 修改 Dashboard：同时参考 docs/reference/dashboard-reference.png 和 docs/PROJECT_SPEC.md。

每完成一个阶段，交付说明必须列出：

- 创建文件；
- 修改文件；
- 完成内容；
- 测试方式；
- 尚未完成内容；
- 下一阶段建议。

禁止在一次任务中进行无关的大范围重构。

## 12. Phase 1 Boundary

Phase 1 只允许创建或更新以下规范文件：

- AGENTS.md
- docs/PROJECT_SPEC.md
- docs/DATA_DICTIONARY.md
- docs/API_SPEC.md
- docs/openapi.yaml

Phase 1 禁止创建 Flask Route、Model、Service、Vue 页面，禁止安装依赖、启动开发服务器、修改原始 SQL 或生成虚假天气数据。完成本阶段后必须等待用户确认，再进入 Phase 2。
