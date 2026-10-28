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
| 全国地图 / 城市点位 | /api/air-quality/ranking、/api/locations/* | air_quality_data.city、province、aqi、status | 部分支持 | 前端内置公开中国行政区边界并高亮当前省份；数据库没有经纬度，暂不绘制城市地理点位 |
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

## 10. Phase 6 完成后的接口冻结规则

Phase 6 后端验收已完成，REST API 契约已冻结，状态记录在
`docs/API_SPEC.md` 和 `docs/BACKEND_ACCEPTANCE.md` 中。进入 Vue 3 前端开发
后，原则上不得破坏性修改以下内容：

- URL 和 HTTP Method；
- Query 参数名称、是否必填、默认值和取值范围；
- Response 字段、JSON 层级和字段命名；
- 字段数据类型、空值语义和 HTTP 状态码。

如果确实需要修改 API，必须同步更新 `API_SPEC.md`、`openapi.yaml`、后端
测试和前端调用，并在文档中记录变更原因和兼容影响。

## 11. 开发环境配置指导

可直接交给组员执行的独立版本见 [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md)。

本节是 weatherdemo 的本地环境配置指引，目标是让新成员在不修改业务代码和原始数据的前提下，完成 MySQL、Flask、Vue 3 和 ECharts 的安装、配置与启动。命令以 Windows PowerShell 为主；Linux/macOS 使用对应的 `python3`、`source` 和 `cp` 命令即可。

### 11.1 推荐版本与职责

| 技术 | 推荐版本 | 用途 |
| --- | --- | --- |
| Python | 3.11 或 3.12 | Flask 后端和测试 |
| MySQL | 8.0.x（验收环境为 8.0.43） | 唯一业务数据源 |
| Node.js | 20 LTS | Vue/Vite 前端构建与开发服务器 |
| npm | 随 Node.js 安装，建议 10.x 或更高 | 安装 `package-lock.json` 中锁定的前端依赖 |
| Git | 当前稳定版 | 代码和文档版本管理 |
| 浏览器 | Chrome、Edge 或 Firefox | Dashboard 验证 |

ECharts、Vue Router、Axios 和 Element Plus 已在
`weather_sys/font/weather_font/package.json` 中声明，不需要单独下载安装。后端依赖以根目录
`requirements.txt` 为准，不要为了运行本项目额外安装 Pandas、SQLAlchemy 或其他未声明依赖。

### 11.2 环境文件和端口

配置文件只提交示例，不提交真实密码、令牌或个人环境文件：

```text
weatherdemo/
├── .env.example                         # 后端和数据库示例配置
├── .env                                  # 本机复制生成，不提交
├── database/weather_data.sql.gz          # Git 跟踪的压缩原始数据资产
├── database/weather_data.sql             # 从压缩包恢复，本机只读
└── weather_sys/font/weather_font/
    ├── .env.example                      # Vite 示例配置
    └── .env                              # 前端本机配置，不提交
```

| 服务 | 默认地址 | 说明 |
| --- | --- | --- |
| MySQL | `127.0.0.1:3306` | 数据库服务 |
| Flask API | `http://127.0.0.1:5000` | `/api/*` 接口和后端管理页 |
| Vite | `http://localhost:5173` | Vue 开发服务器和 Dashboard |

后端和前端在本地开发时分开运行。Vite 将 `/api` 代理到 `127.0.0.1:5000`，Vue 不得直接连接 MySQL。

### 11.3 MySQL 配置与数据导入

1. 安装 MySQL 8.0 并启动 MySQL 服务，确认客户端可执行：

   ```powershell
   mysql --version
   ```

2. 使用 root 或数据库管理员创建数据库。字符集必须保持 `utf8mb4`：

   ```sql
   CREATE DATABASE IF NOT EXISTS weather_db
     DEFAULT CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   ```

3. 原始 SQL 约 163 MiB，超过 GitHub 普通文件限制，因此 `database/weather_data.sql`
   按 `.gitignore` 排除；Git 跟踪的 `database/weather_data.sql.gz` 是同一文件的压缩副本。
   如果本地还没有 SQL 文件，先在项目根目录恢复：

   ```powershell
   python -c "import gzip,shutil; shutil.copyfileobj(gzip.open('database/weather_data.sql.gz','rb'), open('database/weather_data.sql','wb'))"
   ```

   原始 SQL 只能导入，禁止直接编辑。

   在 CMD 或 Git Bash 中执行：

   ```bash
   mysql -u root -p --default-character-set=utf8mb4 weather_db < database/weather_data.sql
   mysql -u root -p weather_db < database/migrations/20261014_weather_temperature_indexes.sql
   ```

   PowerShell 不接受某些版本中的 `<` 重定向语法时，请打开 CMD/Git Bash 执行以上命令，或调用本机 MySQL `bin` 目录下的 `mysql.exe`。

4. 应用运行时建议使用只读账号，而不是 root。以下语句应由管理员执行，并将密码替换为本机随机密码：

   ```sql
   CREATE USER IF NOT EXISTS 'weather_app'@'127.0.0.1'
     IDENTIFIED BY 'replace_with_local_password';
   GRANT SELECT ON weather_db.* TO 'weather_app'@'127.0.0.1';
   FLUSH PRIVILEGES;
   ```

   如果 `DB_HOST` 使用 `localhost`，需要为 `weather_app@localhost` 单独建立授权；MySQL 会区分 `localhost` 和 `127.0.0.1`。

5. 导入后只做只读校验，不要使用 `DROP`、`TRUNCATE` 或全表 `DELETE`：

   ```sql
   USE weather_db;
   SHOW TABLES;
   SELECT COUNT(*) AS weather_count FROM weather_data;
   SELECT COUNT(*) AS air_quality_count FROM air_quality_data;
   SELECT MAX(date) AS latest_date FROM weather_data;
   ```

   `database/migrations/20261014_weather_temperature_indexes.sql` 是独立性能迁移，不属于原始 dump。已有数据库重复执行前，应先检查索引是否存在。

### 11.4 Flask 后端配置

在项目根目录执行：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

编辑根目录 `.env`，至少填写以下配置：

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=weather_app
DB_PASSWORD=replace_with_local_password
DB_NAME=weather_db
DB_READ_TIMEOUT=30

FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# 本地可以留空；共享环境和部署环境应设置随机令牌。
ADMIN_API_TOKEN=
```

启动后端：

```powershell
python weather_sys/app.py
```

另开终端检查健康接口：

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
```

预期结果是 HTTP 200，响应中的 `code` 为 `200`，并且 `data.application` 与 `data.database` 均为 `ok`。如果数据库不可用，接口应返回统一的错误结构，而不是泄漏密码、连接串或 SQL 细节。

### 11.5 Vue 3、Vite 和 ECharts 配置

打开第二个终端：

```powershell
cd weather_sys/font/weather_font
Copy-Item .env.example .env
node --version
npm --version
npm ci
npm run dev
```

前端 `.env` 默认保持：

```dotenv
VITE_API_BASE_URL=/api
```

浏览器打开 `http://localhost:5173`。如果后端不是 `127.0.0.1:5000`，需要同步修改
`vite.config.js` 中的 `/api` 代理目标；生产环境应由反向代理提供同源 `/api`，不要在组件中写死数据库地址。

构建生产前端：

```powershell
npm run build
npm run preview
```

`npm ci` 会严格使用 `package-lock.json`。只有在明确升级依赖时才使用 `npm install`，并提交对应的 lockfile 变更。

### 11.6 推荐启动顺序与验证

每次新环境按以下顺序操作：

1. 启动 MySQL，确认 `weather_db`、三张表和性能迁移存在。
2. 激活 `.venv`，启动 Flask，确认 `/api/health` 返回数据库可用。
3. 安装并启动 Vue/Vite，打开 Dashboard。
4. 在页面中选择省份、城市、区县和观测日期，确认数据来自接口而非前端固定值。

代码验证可以使用：

```powershell
python -m unittest discover -s tests -v
cd weather_sys/font/weather_font
npm run test:map
npm run test:comparison
npm run test:dashboard
npm run build
```

### 11.7 常见故障处理

| 现象 | 优先检查 |
| --- | --- |
| `Can't connect to MySQL server` | MySQL 服务是否启动、`DB_HOST`/`DB_PORT` 是否正确、防火墙和端口占用 |
| `Access denied for user` | `.env` 用户名密码、MySQL 用户 host 是否与 `DB_HOST` 匹配、授权是否执行 |
| `/api/health` 返回 500 | 后端日志、数据库名、三张表和迁移索引是否存在 |
| 页面请求 `/api` 失败 | Flask 是否运行在 5000 端口、Vite 代理目标是否正确、CORS 是否包含 5173 |
| `npm` 或 `node` 不是命令 | 安装 Node.js LTS，重新打开终端并确认 PATH；不要混用损坏的全局 npm 路径 |
| 导入 SQL 找不到文件 | 从仓库中的 `database/weather_data.sql.gz` 恢复 `database/weather_data.sql`；不要用空表或假数据替代 |

所有环境配置都必须继续遵守：原始 SQL 只读、真实数据优先、`.env` 不提交、前端不直连 MySQL、`latest` 表示历史库按观测日期取得的最新记录而不是实时天气。
