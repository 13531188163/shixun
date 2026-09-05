# 天气数据可视化与预测系统

一个基于 Python Flask、Vue 3、ECharts 和 MySQL 的前后端分离天气数据分析项目。系统提供天气数据存储、查询、统计分析和可视化展示，可按省份、城市、区县及年份查看温度、风力、降水、天气类型和空气质量数据。

## 项目简介

本项目面向天气数据查询与分析场景，使用已有 SQL 数据文件初始化 MySQL 数据库，由 Flask 后端提供 REST API，并在 Vue 前端使用 ECharts 图表和中国地图进行可视化展示。

系统首页采用天气监控大屏形式，另外提供温度、风力、降水、天气类型和空气质量等专题分析页面。

## 核心功能

* 全国天气数据监控大屏
* 省、市、区县和年份多级筛选
* 最高温、最低温及月度温度趋势分析
* 平均风速、最大风速和风力等级分析
* 累计降水、降水天数和降水趋势分析
* 晴、阴、雨、雪等天气类型分布统计
* 全国省份平均气温地图
* 空气质量 AQI、城市排名和省份分布
* 基于近期历史数据的简单天气预测

## 技术栈

### 前端

* Vue 3
* Vue Router
* ECharts 6
* Vite 8
* JavaScript、HTML、CSS

### 后端

* Python 3
* Flask、Flask-CORS
* Pandas、NumPy
* SQLAlchemy、PyMySQL
* MySQL

## 功能页面

|页面路径|页面名称|功能|
|-|-|-|
|`/`|天气监控大屏|综合指标、气温地图、温度、风力、降水和天气分布|
|`/temperature`|温度分析|温度统计、趋势及预测|
|`/wind`|风力分析|风速趋势、等级和风能指标|
|`/precipitation`|降水分析|降水统计、趋势和等级|
|`/weather`|天气分析|天气类型数量及占比|
|`/air-quality`|空气质量|AQI、城市排名和省份分布|

## 项目结构

```text
weatherdemo/
├── weather\_sys/
│   ├── app.py                     # Flask 后端启动入口
│   ├── backend/
│   │   ├── config.py              # 数据库配置
│   │   ├── models/                # 数据访问层
│   │   ├── routes/                # REST API 路由
│   │   ├── services/              # 天气与空气质量业务逻辑
│   │   └── utils/                 # 数据库连接工具
│   ├── font/weather\_font/         # Vue 前端项目
│   └── weather\_data.sql           # 数据库初始化脚本（文件名以实际为准）
├── 项目启动书.md
└── README.md
```

## 环境要求

* Python 3.10 或更高版本
* Node.js 20.19 或更高版本
* MySQL 8.x

## 快速启动

### 1\. 克隆仓库

```bash
git clone https://github.com/13531188163/shixun
cd weatherdemo
```

### 2\. 导入 SQL 数据文件

请将已有 SQL 文件放在便于访问的位置，然后通过 MySQL 命令行导入。若 SQL 文件中未包含建库语句，可先创建数据库：

```sql
CREATE DATABASE weather\_db
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4\_unicode\_ci;
```

导入已有 SQL 文件：

```bash
mysql -u root -p weather\_db < <数据库脚本>.sql
```

也可以使用 MySQL Workbench、Navicat 等数据库工具打开 SQL 文件并执行。

> 建议将数据库地址、用户名和密码改为环境变量，不要将真实密码提交到公开仓库。

### 3\. 启动后端

```bash
cd weather\_sys
python -m venv .venv
```

Windows：

```powershell
.venv\\Scripts\\activate
pip install -r backend/requirements.txt
python app.py
```

macOS／Linux：

```bash
source .venv/bin/activate
pip install -r backend/requirements.txt
python app.py
```

后端默认运行在：`http://127.0.0.1:5000`

### 4\. 启动前端

打开另一个终端：

```bash
cd weather\_sys/font/weather\_font
npm install
npm run dev
```

前端默认运行在：`http://127.0.0.1:3000`

## 主要 API

|接口前缀|功能|
|-|-|
|`/api/weather/\*`|天气筛选、统计、趋势、地图及预测|
|`/api/air-quality/\*`|空气质量、城市排名及省份分布|

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
3. 当前预测结果基于近期历史数据的统计值，仅供课程实训和功能演示使用。

## Git 仓库

* 仓库地址：https://github.com/13531188163/shixun

