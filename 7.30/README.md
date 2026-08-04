# 保险精准营销 AI 系统

> Insurance Precision Marketing · AI-Driven Customer Targeting

基于机器学习与大语言模型的保险精准营销平台：通过 Flask 提供 REST API，前端为原生 SPA（零框架依赖），内置 LR/RF/XGBoost 三算法自动选优训练 + LLM 个性化邮件生成；同时附带一套纯 MVC 教学骨架，便于初学者理解分层结构。

---

## 目录

- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [功能模块](#功能模块)
- [API 文档](#api-文档)
- [测试](#测试)
- [MVC 教学骨架](#mvc-教学骨架)
- [常见问题](#常见问题)
- [项目结构](#项目结构)

---

## 快速部署（Docker）

一键启动，无需配置 Python 环境！

### 1. 构建并启动容器

```bash
# 1. 准备环境文件
copy .env.docker .env        # Windows
cp .env.docker .env        # macOS / Linux

# 2. 编辑 .env（可选）
# 修改 JWT_SECRET_KEY 和 DEFAULT_ADMIN_PASSWORD 为安全值

# 3. 启动服务
docker-compose up -d
```

### 2. 访问服务

- 前端：<http://127.0.0.1:5000>
- 账号：`admin` / `admin123`

### 3. 常用 Docker 命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 更新代码后重新构建
docker-compose up -d --build
```

### 4. 数据持久化

- 数据库：映射到本地 `./instance/` 目录
- 模型和数据：映射到本地 `./data/` 目录
- 数据安全：删除容器不会丢失数据

---

## 技术栈

| 类别     | 技术                                        | 版本          |
| -------- | ------------------------------------------- | ------------- |
| 语言     | Python                                      | 3.12+         |
| Web 框架 | Flask                                       | 3.0+          |
| ORM      | SQLAlchemy                                  | 2.0+          |
| 认证     | PyJWT / python-jose                         | JWT（HS256）  |
| 数据处理 | pandas / openpyxl                           | —             |
| 机器学习 | scikit-learn / XGBoost / joblib             | —             |
| 大模型   | OpenAI-compatible（DashScope / 阿里云百炼） | qwen-flash 等 |
| 校验     | pydantic                                    | 2.x           |
| 数据库   | SQLite（默认）/ MySQL / PostgreSQL          | —             |
| 前端     | 原生 HTML + CSS + ES Modules（无构建步骤）  | —             |

---

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
# Windows PowerShell / CMD
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
```

编辑 `.env`，按需修改：

- `DATABASE_URL`：默认 `sqlite:///instance/insurance.db`
- `JWT_SECRET_KEY`：生产务必改为强随机字符串
- `LLM_API_KEY`：可选；未配置时邮件生成走降级模式，业务照常运行
- `LLM_API_BASE` / `LLM_MODEL`：默认阿里云 DashScope 兼容端点

### 3. 启动项目

```bash
python run_flask.py
```

默认监听 `0.0.0.0:5000`，开启 debug 热重载。

### 4. 访问系统

- 前端 SPA：<http://127.0.0.1:5000>
- API 根路径：`/api/v1/...`
- 默认管理员账号：

| 用户名  | 密码       |
| ------- | ---------- |
| `admin` | `admin123` |

> 首次启动会自动建表并 seed 管理员账号与默认 Prompt 模板。

---

## 功能模块

### 数据管理

- **Excel 上传**：`POST /api/v1/data/upload`，支持 `.xlsx / .xls`，单次上限 50MB，上传后清空旧数据再批量入库。
- **客户列表**：`GET /api/v1/data/customers`，支持分页 / 性别 / 年龄区间 / 历史投保 / 关键字过滤。
- **数据统计**：`GET /api/v1/data/statistics`，返回总量、性别分布、响应分布、年龄统计。
- **质量报告**：`GET /api/v1/data/quality`，字段缺失、重复、数据类型一览。
- **EDA 可视化**：`GET /api/v1/data/visualization/{chart_type}`，内置 4 种图（响应分布、性别×响应、年龄分布、保费分布），返回 Base64 PNG。

### 模型训练

- 自动训练 **Logistic Regression / Random Forest / XGBoost** 三种算法。
- 按 **ROC-AUC** 指标自动选优，最佳模型持久化到 `data/models/`。
- 支持自定义 `test_size` / `random_state` / 各算法超参。
- 训练完成自动记录操作日志。

相关接口：

- `POST /api/v1/model/train`（仅 admin）
- `GET /api/v1/model/experiments` 实验记录分页
- `GET /api/v1/model/best` 当前最佳

### 预测服务

- **全量预测**：`POST /api/v1/model/predict`，对全量客户打分并回写 `predicted_prob`。
- **上传文件预测**：`POST /api/v1/model/predict_upload`，对新 Excel 预测但不入库，返回逐条预测结果与统计。

### 邮件生成

- **高潜客户筛选**：`GET /api/v1/email/targets`，按分位数（默认 0.9）筛选高分客户。
- **LLM 个性化邮件**：`POST /api/v1/email/generate`，调用大模型按客户画像生成主题 + HTML 正文。
- **降级机制**：未配置 `LLM_API_KEY` 或调用失败时，单条记录标记为 `status=failed`，其余业务不受影响。
- **Prompt 模板**：`GET/PUT /api/v1/email/prompt`。
- **邮件记录 CRUD**：`GET/PUT/PATCH/DELETE /api/v1/email/records`。

### 日志审计

- `GET /api/v1/logs`（仅 admin）：分页查询操作日志，支持 `user_id` / `action` 过滤。
- 训练、预测、模型导入等关键写操作均自动入库。

---

## API 文档

完整接口定义、请求/响应示例、错误码参见：

📄 [`docs/03_API接口文档.md`](./docs/03_API接口文档.md)

产品需求、技术方案与框架方案：

- [`docs/01_PRD_产品需求文档.md`](./docs/01_PRD_产品需求文档.md)
- [`docs/02_AI技术方案.md`](./docs/02_AI技术方案.md)
- [`docs/04_技术框架方案.md`](./docs/04_技术框架方案.md)

---

## 测试

项目使用 `pytest` 进行测试：

```bash
pytest tests/ -v
```

（如暂未提供 `tests/` 目录，可参考 `insurance_mvc_starter/test_smoke.py` 中的基础用例。）

---

## MVC 教学骨架

仓库内附带一份**纯 MVC 架构的教学起步包**，适合初学者理解「Model / View / Controller」分层，独立于主项目运行。

### 启动

```bash
cd insurance_mvc_starter
python run.py
```

默认监听 `0.0.0.0:5001`。

### 特点

- 纯 MVC 分层（models / services / templates / core）。
- Jinja2 服务端渲染 + 轻量 JS 交互。
- 内置登录注册、客户管理、上传导入、仪表盘等页面。
- 依赖极少，便于阅读完整代码路径。

---

## 常见问题

### 1. bcrypt 版本兼容

Windows + Python 3.12 下若 `pip install bcrypt` 报编译错误（缺少 Rust / C 编译链），可降级安装：

```bash
pip install "bcrypt==4.1.2"
```

或直接使用预编译 wheel（`pip install bcrypt` 最新版通常已提供）。

### 2. 中文字体图表

`matplotlib` 默认 sans-serif 字体不含中文字形，图表中/英文混排会出现方块。解决方案（三选一）：

- 安装系统中文字体（如 `Microsoft YaHei` / `SimHei`）。
- 在 `app/utils/visualizer.py` 中显式指定 `matplotlib.font_manager` 的字体路径。
- 对中文标题统一用英文或拼音替代。

### 3. SQLite 锁

默认 SQLite 为单写者模型。多进程 / 多线程下并发写入可能触发 `database is locked`。建议：

- 开发阶段：保持单进程 `debug=True` 即可。
- 生产环境：切换到 MySQL / PostgreSQL（修改 `.env` 中 `DATABASE_URL`）。

### 4. LLM API Key 配置

- 在 `.env` 中填入 `LLM_API_KEY=sk-xxx`。
- 默认 `LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1`，可换成任何 OpenAI 兼容端点（本地 Ollama、Azure、百炼等）。
- 未配置时 `/email/generate` 会对每条记录标记 `failed`，不会阻塞其它业务。

### 5. 文件上传大小限制

默认 50MB（`MAX_CONTENT_LENGTH`）。如需调整，修改 `app/__init__.py` 中的 `MAX_UPLOAD_BYTES` 常量，并同步 `app.config["MAX_CONTENT_LENGTH"]`。

---

## 项目结构

```
7.30/
├── app/                               # 主后端应用
│   ├── __init__.py                   # 应用工厂（create_app）
│   ├── api/
│   │   └── v1/                       # API 路由层（5 个 Blueprint）
│   │       ├── auth.py               #   /api/v1/auth
│   │       ├── data.py               #   /api/v1/data
│   │       ├── model.py              #   /api/v1/model
│   │       ├── email.py              #   /api/v1/email
│   │       └── log.py                #   /api/v1/logs
│   ├── core/                         # 配置 / 数据库 / 鉴权 / 响应
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   ├── response.py
│   │   └── security.py
│   ├── models/                       # SQLAlchemy ORM 模型
│   │   ├── user.py
│   │   ├── customer.py
│   │   ├── experiment.py
│   │   ├── email_record.py
│   │   ├── operation_log.py
│   │   └── prompt_template.py
│   ├── schemas/                      # Pydantic 请求/响应校验
│   │   └── auth.py
│   ├── services/                     # 业务逻辑层
│   │   ├── auth_service.py
│   │   ├── data_service.py
│   │   ├── ml_service.py
│   │   ├── email_service.py
│   │   ├── llm_service.py
│   │   └── operation_log_service.py
│   ├── static/                       # 原生 SPA 前端
│   │   ├── index.html
│   │   ├── css/app.css
│   │   └── js/
│   │       ├── api.js
│   │       └── app.js
│   └── utils/
│       ├── data_processor.py
│       └── visualizer.py
├── data/
│   ├── sample_insurance.xlsx         # 示例数据集
│   └── models/                       # 训练产物（.joblib）
├── docs/
│   ├── 01_PRD_产品需求文档.md
│   ├── 02_AI技术方案.md
│   ├── 03_API接口文档.md
│   └── 04_技术框架方案.md
├── insurance_mvc_starter/            # MVC 教学骨架（独立运行，端口 5001）
│   ├── app/
│   ├── templates/
│   ├── run.py
│   └── requirements.txt
├── instance/                         # SQLite 数据库文件目录
├── scripts/
│   └── e2e_demo.py                   # 端到端演示脚本
├── tests/                            # pytest 测试
├── .dockerignore                     # Docker 构建忽略文件
├── .env.docker                       # Docker 环境变量模板
├── .env.example
├── .gitignore
├── docker-compose.yml                # Docker Compose 配置
├── Dockerfile                        # Docker 镜像构建文件
├── requirements.txt
└── run_flask.py                      # 主项目入口（端口 5000）
```

---

© Insurance AI · For educational and demonstration purposes.
