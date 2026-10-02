# WeatherDemo

一个基于 Python Flask、Vue 3、ECharts 和 MySQL 的前后端分离天气数据分析项目。当前首页是正式的天气与空气质量可视化大屏，数据全部来自已冻结的 REST API，可按省份、城市、区县切换查看真实记录。

## 项目简介

本项目面向天气数据查询与分析场景，使用已有 SQL 数据文件初始化 MySQL 数据库，由 Flask 后端提供 REST API，并在 Vue 前端使用 ECharts 图表和响应式深色大屏布局进行可视化展示。

系统首页采用天气监控大屏形式，所有展示字段均来自数据库已有数据或可复现的聚合计算。

## 核心功能

* 天气与空气质量数据监控大屏
* 省、市、区县三级真实数据联动
* 最高温、最低温历史趋势和城市温度比较
* 平均风速、最大风速和降水量指标卡
* 空气质量 AQI 概况、低值城市 TOP10 和等级分布
* Dashboard 概览统计与加载、空态、错误态

## 技术栈

### 前端

* Vue 3
* Vue Router
* Apache ECharts
* Vite 6
* JavaScript、HTML、CSS

### 后端

* Python 3
* Flask、Flask-CORS
* PyMySQL、python-dotenv
* MySQL

## 功能页面

|页面路径|页面名称|功能|
|-|-|-|
|`/`|天气与空气质量可视化大屏|天气概况、历史趋势、城市温度比较、AQI 概况、排名和等级分布|

## 项目结构

```text
weatherdemo/
├── AGENTS.md, README.md, requirements.txt, .env.example
├── database/weather_data.sql       # 原始业务数据资产（只读）
├── docs/                           # 规范、API、验收报告和截图
└── weather_sys/
    ├── app.py                      # Flask 后端启动入口
    ├── backend/{config,models,routes,services,utils}/
    └── font/weather_font/          # Vue 3 + Vite 前端工程
        └── public/maps/china.json  # 中国行政区边界展示资源
```

## 环境要求

* Python 3.x
* Node.js 与 npm
* MySQL 8.x

## 快速启动

### 1\. 克隆仓库

```bash
git clone https://github.com/13531188163/shixun
cd weatherdemo
```

### 2\. 导入 SQL 数据文件

通过 MySQL 命令行导入项目内的只读原始数据文件。若数据库尚未创建，可先执行：

```sql
CREATE DATABASE weather_db
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

导入数据：

```bash
mysql -u root -p weather_db < database/weather_data.sql
```

也可以使用 MySQL Workbench、Navicat 等数据库工具打开 SQL 文件并执行。

> 建议将数据库地址、用户名和密码改为环境变量，不要将真实密码提交到公开仓库。

### 3\. 启动后端

```bash
cd weatherdemo
python -m venv .venv
```

Windows：

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python weather_sys/app.py
```

macOS／Linux：

```bash
source .venv/bin/activate
pip install -r requirements.txt
python weather_sys/app.py
```

后端默认运行在：`http://127.0.0.1:5000`

### 4\. 启动前端

打开另一个终端：

```bash
cd weather_sys/font/weather_font
npm install
npm run dev
```

前端默认运行在：`http://localhost:5173`

## 主要 API

|接口|功能|
|-|-|
|`/api/health`|应用和数据库健康检查|
|`/api/locations/*`|省份、城市、区县列表|
|`/api/weather/latest`、`trend`、`city-comparison`|天气最新记录、历史趋势、城市比较|
|`/api/air-quality/latest`、`ranking`、`distribution`|AQI 最新记录、排名、等级分布|
|`/api/dashboard/overview`|Dashboard 首屏聚合数据|

## 开发协作

* 主分支：`main`
* 开发分支：`develop`
* 功能分支：`feature/功能名称`
* 修复分支：`fix/问题名称`
* 提交信息建议采用：`类型: 简要说明`

示例：

```text
feat: 完成温度趋势接口
fix: 修复城市筛选后图表未刷新的问题
docs: 补充数据库初始化说明
test: 添加天气统计接口测试
```

## 注意事项

1. 项目内原有虚拟环境可能来自 Windows，不建议直接复用，应在本机重新创建。
2. 导入 SQL 文件前，请确认目标数据库名称与 `backend/config.py` 中的配置一致。
3. `latest` 表示数据库观测日期可获得的最新记录，不是实时气象 API；项目数据用于课程实训和功能演示。

## Git 仓库

* 仓库地址：https://github.com/13531188163/shixun

## Phase 10 交付说明

本项目已经完成最终联调验收，实际链路为：MySQL 真实历史数据 → Flask REST API → Vue 3 → ECharts Dashboard。首页支持省份、城市、区县三级联动，天气概览、7 日趋势、城市温度比较、AQI 概况、排名和等级分布，并包含加载态、空态和错误态。

### 实际目录

```text
weatherdemo/
├── AGENTS.md
├── README.md
├── requirements.txt
├── .env.example
├── database/weather_data.sql       # 原始业务数据资产（只读）
├── docs/                           # 规范、API、验收报告和截图
└── weather_sys/
    ├── app.py                      # Flask 启动入口
    ├── backend/{config,models,routes,services,utils}/
    └── font/weather_font/          # Vue 3 + Vite 前端
```

### 数据库与环境变量

数据库为 `weather_db`，原始数据文件为 `database/weather_data.sql`，请先启动 MySQL，再执行 `mysql -u root -p weather_db < database/weather_data.sql`（已有数据库时无需重复导入）。根目录 `.env.example` 包含 `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`、Flask 端口和 CORS 配置；真实 `.env` 已忽略，不应提交。

### 推荐启动方式

后端在项目根目录执行 `python -m venv .venv`、激活虚拟环境、`pip install -r requirements.txt`，然后运行 `python weather_sys/app.py`，地址为 `http://127.0.0.1:5000`。另开终端进入 `weather_sys/font/weather_font`，运行 `npm install` 和 `npm run dev`，页面地址为 `http://localhost:5173`。

### API 与数据限制

所有接口使用 `/api` 前缀，统一返回 `code/message/data`，完整契约见 `docs/API_SPEC.md` 和 `docs/openapi.yaml`。`latest` 是数据库观测日期字段可得到的最新记录，不代表实时气象服务。中心区域使用本地中国行政区边界资源并高亮当前省份；数据库没有经纬度字段，因此不伪造城市地图点位。数据库未提供 PM2.5、PM10、SO2、NO2、CO、O3、湿度、气压、紫外线、能见度、预警和健康建议字段，系统没有伪造这些指标。

最终截图：[docs/screenshots/dashboard-final.png](docs/screenshots/dashboard-final.png)。完整验收结果见 [docs/PROJECT_ACCEPTANCE.md](docs/PROJECT_ACCEPTANCE.md)。
