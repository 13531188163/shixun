# WeatherDemo 环境配置指导

本文用于指导新成员在本地配置和启动 WeatherDemo。项目链路为：

```text
MySQL weather_db → Flask REST API → Vue 3/Vite → ECharts Dashboard
```

本文只描述环境配置和启动，不修改原始数据库文件，也不使用虚假业务数据。

## 1. 推荐软件

| 软件 | 推荐版本 | 用途 |
| --- | --- | --- |
| Python | 3.11 或 3.12 | Flask 后端、测试 |
| MySQL | 8.0.x | 业务数据库 |
| Node.js | 20 LTS | Vue/Vite 开发和构建 |
| npm | 随 Node.js 安装，建议 10.x 或更高 | 前端依赖管理 |
| Git | 当前稳定版 | 代码版本管理 |
| 浏览器 | Chrome、Edge 或 Firefox | 页面验证 |

ECharts、Vue Router、Axios 和 Element Plus 已写入前端 `package.json`，不用单独安装。后端依赖以根目录 `requirements.txt` 为准。

## 2. 端口和目录

| 服务 | 默认地址 | 说明 |
| --- | --- | --- |
| MySQL | `127.0.0.1:3306` | 数据库服务 |
| Flask | `http://127.0.0.1:5000` | REST API 和后端管理页 |
| Vite | `http://localhost:5173` | Vue 开发服务器 |

关键文件：

```text
weatherdemo/
├── .env.example
├── .env                              # 本机配置，不提交
├── requirements.txt
├── database/weather_data.sql.gz      # Git 跟踪的压缩原始数据资产
├── database/weather_data.sql         # 从上面的压缩包恢复，本机只读
├── database/migrations/              # 独立性能迁移
└── weather_sys/font/weather_font/
    ├── package.json
    ├── package-lock.json
    ├── .env.example
    └── vite.config.js
```

原始 SQL 文件约 163 MiB，超过 GitHub 普通文件的大小限制，因此
`database/weather_data.sql` 按 `.gitignore` 排除；仓库现在跟踪了同一文件的
`database/weather_data.sql.gz` 压缩副本（约 14 MiB）。Git clone 后先从压缩包恢复
原始 SQL，再导入数据库。压缩包内的数据与当前工作区原始文件 SHA-256
`0edf9c9f1cca42c852be47225c580233f7ae6b4a41d383af5adf200ee6077fa3` 一致。
不能用空表、随机数或固定样例替代它。

## 3. 配置 MySQL

### 3.1 检查 MySQL

安装并启动 MySQL 8.0，确认客户端可用：

```bash
mysql --version
```

### 3.2 创建数据库

使用 root 或数据库管理员执行：

```sql
CREATE DATABASE IF NOT EXISTS weather_db
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### 3.3 导入原始数据和迁移

如果 `database/weather_data.sql` 尚不存在，先在项目根目录恢复 Git 中的压缩数据资产：

```powershell
python -c "import gzip,shutil; shutil.copyfileobj(gzip.open('database/weather_data.sql.gz','rb'), open('database/weather_data.sql','wb'))"
```

恢复后，在 CMD 或 Git Bash 中执行导入：

```bash
mysql -u root -p --default-character-set=utf8mb4 weather_db < database/weather_data.sql
mysql -u root -p weather_db < database/migrations/20261014_weather_temperature_indexes.sql
```

PowerShell 某些版本不支持 `<` 重定向语法时，请使用 CMD/Git Bash，或直接调用 MySQL 安装目录下的 `mysql.exe`。

原始 dump 是只读数据资产，禁止直接编辑；新增索引必须使用独立 migration 文件。

### 3.4 创建后端运行账号

本地临时开发可以使用 root，但团队共享环境建议使用只读账号。管理员执行：

```sql
CREATE USER IF NOT EXISTS 'weather_app'@'127.0.0.1'
  IDENTIFIED BY 'replace_with_local_password';
GRANT SELECT ON weather_db.* TO 'weather_app'@'127.0.0.1';
FLUSH PRIVILEGES;
```

如果 `.env` 中的 `DB_HOST` 使用 `localhost`，需要为 `weather_app@localhost` 单独授权。

### 3.5 只读校验

```sql
USE weather_db;
SHOW TABLES;
SELECT COUNT(*) AS weather_count FROM weather_data;
SELECT COUNT(*) AS air_quality_count FROM air_quality_data;
SELECT MAX(date) AS latest_date FROM weather_data;
```

预期存在 `weather_data`、`air_quality_data` 和 `wind_data` 三张表。`wind_data` 当前可以没有业务记录。

## 4. 配置并启动 Flask

在项目根目录执行以下 Windows PowerShell 命令：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

如果 PowerShell 阻止虚拟环境脚本，可只对当前终端执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

编辑根目录 `.env`：

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

# 本地可留空；共享环境应设置随机令牌。
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

预期 HTTP 状态为 `200`，响应中的 `code` 为 `200`，并且数据库状态为 `ok`。

## 5. 配置并启动 Vue 3

打开第二个终端：

```powershell
cd weather_sys/font/weather_font
Copy-Item .env.example .env
node --version
npm --version
npm ci
npm run dev
```

前端 `.env` 默认使用：

```dotenv
VITE_API_BASE_URL=/api
```

浏览器打开 `http://localhost:5173`。Vite 会根据 `vite.config.js` 将 `/api` 转发到 `http://127.0.0.1:5000`。Vue 页面只能调用 Flask API，不能直接连接 MySQL。

## 6. 构建和验证

生产构建：

```powershell
npm run build
npm run preview
```

后端测试：

```powershell
cd ..\..\..
python -m unittest discover -s tests -v
```

前端测试：

```powershell
cd weather_sys/font/weather_font
npm run test:map
npm run test:comparison
npm run test:dashboard
```

推荐启动顺序：

1. 启动 MySQL并完成数据库导入。
2. 启动 Flask并确认 `/api/health` 正常。
3. 启动 Vite并打开 Dashboard。
4. 选择省份、城市、区县和观测日期，确认页面数据来自 API。

## 7. 常见问题

| 现象 | 检查项 |
| --- | --- |
| `Can't connect to MySQL server` | MySQL 服务、`DB_HOST`、`DB_PORT` 和端口占用 |
| `Access denied for user` | `.env` 密码、MySQL 用户 host 和授权语句 |
| `/api/health` 返回 500 | 数据库名、三张表、迁移索引和后端日志 |
| 页面请求 `/api` 失败 | Flask 是否运行在 5000 端口、Vite 代理目标是否正确、CORS 是否包含 5173 |
| `npm` 或 `node` 不是命令 | 安装 Node.js 20 LTS，重新打开终端并检查 PATH |
| 找不到 `weather_data.sql` | 先从仓库中的 `database/weather_data.sql.gz` 恢复，不要创建假数据 |

## 8. 安全和数据规则

- `.env`、数据库密码和 `ADMIN_API_TOKEN` 不提交到 Git。
- 生产环境将 `FLASK_DEBUG` 设置为 `false`。
- root 只用于数据库初始化，应用运行使用最小权限账号。
- 不执行全表 `DELETE`、`DROP` 或 `TRUNCATE`。
- `latest` 表示历史数据库按观测日期得到的最新记录，不表示实时天气。
- 数据库不存在的 PM2.5、湿度、气压、预警等指标不得在页面中伪造。
