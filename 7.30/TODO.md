# 开发任务清单 · 保险精准营销系统 Insurance AI

> 编写人：技术负责人（AI）
> 依据：`docs/01~04` 全套方案；同目录 `PROJECT_ANALYSIS.md`
> 状态标记：`[ ]` 待办 · `[x]` 完成 · `[/]` 进行中 · `[!]` 阻塞


## 优先级说明

- **P0** 必须完成才能运行 —— 缺一项则系统跑不起来或核心接口无法通。
- **P1** 核心业务功能 —— PRD 要求的完整闭环功能。
- **P2** 优化功能 —— 提升可用性、可运维性、可扩展性，可在核心跑通后补足。

每项任务字段：
`任务编号 · 任务名称 · 负责模块 · 依赖任务 · 验收标准`

---

## P0 · 必须完成才能运行

### P0-01 项目脚手架与依赖 `[x]`
- 完成日期：2026-07-30
- 负责模块：项目根、`requirements.txt`、`.env.example`、`.gitignore`
- 依赖任务：无
- 验收标准：
  1. `requirements.txt` 含 Flask 3.0.3 / SQLAlchemy 2.0.30 / pydantic 2.7 / pydantic-settings 2.2 / python-jose 3.3 / bcrypt 4.1 / pandas / numpy / openpyxl / scikit-learn / xgboost / joblib / matplotlib / seaborn / openai 1.51.0；
  2. `.env.example` 含 `JWT_SECRET_KEY` / `DATABASE_URL` / `LLM_API_KEY` / `LLM_API_BASE` / `LLM_MODEL` 占位；
  3. `.gitignore` 覆盖 `.env` / `instance/` / `data/models/` / `__pycache__/` / `*.joblib`；
  4. 新虚拟环境 `pip install -r requirements.txt` 无冲突。

### P0-02 基础设施层 core `[x]`
- 完成日期：2026-07-30
- 负责模块：`app/core/config.py`、`database.py`、`response.py`、`security.py`、`dependencies.py`
- 依赖任务：P0-01
- 验收标准：
  1. `settings` 从 `.env` 读取并做类型校验；
  2. `SessionLocal`、`Base`、`get_db()`（挂 `g.db`）、`close_db()` 可用；
  3. `success(data, message)` 与 `BizException(code, message, http)` 定义齐全；
  4. `hash_password` / `verify_password` 使用 bcrypt；`create_access_token` / `decode_token` 使用 HS256；
  5. `login_required` 与 `role_required("admin")` 装饰器可组合使用。

### P0-03 数据层 ORM 6 张表 `[x]`
- 完成日期：2026-07-30
- 负责模块：`app/models/user.py`、`customer.py`、`experiment.py`、`email_record.py`、`operation_log.py`、`prompt_template.py`、`__init__.py`
- 依赖任务：P0-02
- 验收标准：
  1. 字段与 `docs/03_API接口文档.md`、`docs/04_技术框架方案.md` 完全一致；
  2. 关系映射：`User 1—N OperationLog`、`Customer 1—N EmailRecord`；
  3. `Experiment.is_best` 有索引；`PromptTemplate.is_active` 有索引；`Customer.predicted_prob` 有索引；
  4. `Base.metadata.create_all(bind=engine)` 首次启动无异常并生成 SQLite 文件。

### P0-04 应用工厂与蓝图注册 `[x]`
- 完成日期：2026-07-30
- 负责模块：`app/__init__.py`、`app/api/v1/__init__.py`、`run_flask.py`、5 个占位蓝图、`app/static/index.html`
- 依赖任务：P0-02、P0-03
- 验收标准：
  1. `create_app()` 注册 5 个蓝图 + 静态文件 + `teardown_appcontext(close_db)`；
  2. 三级异常处理器（`BizException`、`HTTPException`、`Exception`）分别返回 `{code,message,data}`；
  3. 启动时自动 `create_all` + seed `admin/admin123` + seed 默认 Prompt 模板；
  4. `python run_flask.py` 监听 `0.0.0.0:5000`，`GET /` 返回 HTTP 200。

### P0-05 认证模块 `/auth` `[x]`
- 完成日期：2026-07-30
- 负责模块：`app/api/v1/auth.py`、`app/schemas/auth.py`、`app/services/auth_service.py`
- 依赖任务：P0-04
- 验收标准：
  1. `POST /auth/login` 用 `admin/admin123` 可拿到 JWT；错误密码返回 `code=1002`；
  2. `POST /auth/register` 强制 `role=user`，重复用户名 `code=1004`；
  3. `GET /auth/me` 携带 Token 返回 `{id,username,role}`；未带 Token 返回 `code=1002`；
  4. `POST /auth/logout` 返回 `{code:0,data:null}`。

- ### P0-06 前端 SPA 入口 `[x]`
- 完成日期：2026-07-31
- 负责模块：`app/static/index.html`
- 依赖任务：P0-04
- 验收标准：
  1. `GET /` 返回可渲染的 HTML；
  2. 控制台无 404（含浏览器默认的 `/favicon.ico` 请求）；
  3. Bootstrap 5 CDN 或本地资源可加载。
- 说明：`app/static/{css/app.css,js/api.js,js/app.js}` 已存在并作为 P1-15 的脚手架；P0-06 本身只动 `index.html`，其余文件保持"P0-06 占位，P1-15 富化"原状。P1-15 时再富化各功能页面。


---

## P1 · 核心业务功能

### P1-01 数据模块 · Excel 上传
- 负责模块：`app/api/v1/data.py`、`app/services/data_service.py`、`app/utils/data_processor.py`
- 依赖任务：P0-03、P0-05
- 验收标准：
  1. `POST /data/upload` 接收 `.xlsx/.xls`，字段校验通过后清空旧数据；
  2. 分批 5000 条 `bulk_insert_mappings`；
  3. 38 万行导入 < 60s（本地基线）；
  4. 返回 `imported_count` 与 `quality_report`（rows/cols/missing/duplicates/dtypes）；
  5. 未上传文件 → `code=1001`；解析失败 → `code=2002`。

### P1-02 数据模块 · 客户分页查询
- 负责模块：`app/api/v1/data.py`、`app/services/data_service.py`
- 依赖任务：P1-01
- 验收标准：
  1. `GET /data/customers` 支持 `page/per_page/gender/age_min/age_max/previously_insured/keyword`；
  2. 返回统一分页结构 `{items,total,page,per_page,pages}`；
  3. `items` 元素含全字段 + `predicted_prob`；
  4. `per_page` 上限做保护（≤200）。

### P1-03 数据模块 · 统计/质量/EDA
- 负责模块：`app/api/v1/data.py`、`app/services/data_service.py`、`app/utils/visualizer.py`
- 依赖任务：P1-01
- 验收标准：
  1. `GET /data/statistics` 返回 total / gender_distribution / response_distribution / age_stats；
  2. `GET /data/quality` 与上传时保持一致；
  3. `GET /data/visualization/{chart_type}` 支持 4 种图表，返回 base64 PNG，`format=png`；
  4. 未知 chart_type → `code=1001`；后端强制 `matplotlib.use("Agg")` 且无内存/句柄泄漏。

### P1-04 模型模块 · 特征工程与训练
- 负责模块：`app/services/ml_service.py`、`app/utils/data_processor.py`
- 依赖任务：P1-01
- 验收标准：
  1. 编码策略：Gender/Vehicle_Damage=Label，Vehicle_Age=Ordinal，其余数值 StandardScaler；
  2. `train_test_split(stratify=y)`；scaler 只 fit 训练集；
  3. `_get_model` 支持 `logistic_regression / random_forest / xgboost`，不平衡处理正确；
  4. `POST /model/train`（仅 admin）返回 `best_model` 与 3 模型 metrics；写入 3 条 `experiments`；`is_best` 唯一为真；
  5. 训练时长 < 60s（38 万行、默认参数、单机）。

### P1-05 模型模块 · 实验记录/最佳模型查询
- 负责模块：`app/api/v1/model.py`、`app/services/ml_service.py`
- 依赖任务：P1-04
- 验收标准：
  1. `GET /model/experiments` 分页 + `model_name` 过滤；
  2. `GET /model/best` 无最佳模型时 `code=3002`；
  3. `experiments.params`（JSON）含 ROC/CM/特征重要性可复现的数据。

### P1-06 模型模块 · 全量预测
- 负责模块：`app/api/v1/model.py`、`app/services/ml_service.py`
- 依赖任务：P1-04、P1-05
- 验收标准：
  1. `POST /model/predict` 加载最佳模型（可传 `model_name` 覆盖）；
  2. 复用 joblib 中的 scaler；
  3. 全量客户 `predict_proba` 并回写 `customers.predicted_prob`；
  4. 返回 `{model_name, predicted_count}`；无最佳模型 → `code=3002`。

### P1-07 模型模块 · 上传数据预测
- 负责模块：`app/api/v1/model.py`、`app/services/ml_service.py`
- 依赖任务：P1-04
- 验收标准：
  1. `POST /model/predict_upload` 接收 Excel + 可选 `model` 字段；
  2. 不入库，仅返回 `{model_name,total_count,statistics,predictions}`；
  3. 解析失败 → `code=2002`；格式错 → `code=1001`。

### P1-08 模型模块 · 评估可视化
- 负责模块：`app/api/v1/model.py`、`app/utils/visualizer.py`
- 依赖任务：P1-05
- 验收标准：`GET /model/visualization/{chart_type}` 支持 roc_curve / metrics_comparison / confusion_matrix / feature_importance；confusion_matrix 与 feature_importance 要求 `model` 参数；均返回 base64 PNG。

### P1-09 模型模块 · 导入/导出
- 负责模块：`app/api/v1/model.py`、`app/services/ml_service.py`
- 依赖任务：P1-04
- 验收标准：
  1. `GET /model/export/{model_name}`（仅 admin）返回 `.joblib` 二进制流；
  2. `POST /model/import`（仅 admin）接收 `.joblib`；非 joblib 返回 `code=1001`；
  3. 路径 `MODEL_DIR` 使用绝对路径，Windows 与 Linux 均可。

### P1-10 邮件模块 · 高潜筛选
- 负责模块：`app/api/v1/email.py`、`app/services/email_service.py`
- 依赖任务：P1-06
- 验收标准：
  1. `GET /email/targets?percentile=0.9` 返回 `{threshold,total,customers[]}`；
  2. 无预测数据 → `code=3002`；
  3. 支持分页。

### P1-11 邮件模块 · LLM 生成
- 负责模块：`app/services/llm_service.py`、`app/services/email_service.py`
- 依赖任务：P0-04（Prompt seed）、P1-10
- 验收标准：
  1. `POST /email/generate` 支持 `customer_ids` 或 `limit`；
  2. 未配 `LLM_API_KEY` 时 `status=failed`，`generated_count/failed_count` 计数正确；
  3. 客户画像反编码为自然语言喂给 LLM；
  4. Markdown 包裹被清理，JSON 解析成功；
  5. 单客户失败不影响其它。

### P1-12 邮件模块 · Prompt 模板管理
- 负责模块：`app/api/v1/email.py`、`app/services/email_service.py`
- 依赖任务：P0-04
- 验收标准：
  1. `GET /email/prompt` 返回当前 `is_active=True` 模板；
  2. `PUT /email/prompt` 校验 `content` 含占位符（如 `{gender}`/`{age}`）；
  3. 更新后立即生效于后续 `/email/generate`。

### P1-13 邮件模块 · 记录 CRUD
- 负责模块：`app/api/v1/email.py`、`app/services/email_service.py`
- 依赖任务：P1-11
- 验收标准：
  1. `GET /email/records` 分页 + `status` 过滤；user 只看自己，admin 看全部；
  2. `GET /email/records/{id}` 含完整正文；不存在 `code=2001`；
  3. `PUT/PATCH/DELETE /email/records/{id}` 与批量 `DELETE /email/records` 全部实现；
  4. 关键动作写 `OperationLog`。

### P1-14 日志模块
- 负责模块：`app/api/v1/log.py`、`app/services/*`
- 依赖任务：P0-04
- 验收标准：
  1. `GET /logs`（仅 admin）分页 + `user_id/action` 过滤；
  2. `action` 覆盖 model_training / prediction / model_import / email_generation / email_update / email_mark / email_delete；
  3. 普通用户访问 → `code=1003`。

### P1-15 前端 SPA 主体
- 负责模块：`app/static/js/api.js`、`app.js`、`css/app.css`、`index.html`
- 依赖任务：P0-05、P1-01~P1-14
- 验收标准：
  1. hash 路由 + 登录页 + 主界面容器；
  2. RBAC 菜单：admin 11 项，user 7 项；
  3. 所有请求自动注入 `Authorization`，统一处理 `{code,message,data}`；
  4. 走通 PRD 8 条验收全链路。

### P1-16 示例数据集与教学骨架
- 负责模块：`data/sample_insurance.xlsx`、`insurance_mvc_starter/`
- 依赖任务：P0-04
- 验收标准：
  1. `data/sample_insurance.xlsx` 含符合字段规范的示例数据（建议 ≥1000 行，可从公开集截取）；
  2. `insurance_mvc_starter/`（纯 MVC）可独立启动，覆盖 RBAC 登录 + Excel 上传；
  3. 与主项目共享同一 `.env` 规范。


---

## P2 · 优化功能

### P2-01 测试用例（pytest）
- 负责模块：`tests/`
- 依赖任务：P0-05、P1-*
- 验收标准：
  1. 覆盖认证（登录/注册/权限）、数据上传、训练、预测、邮件生成、日志；
  2. `pytest -q` 全绿；关键路径断言 `code=0` 与业务字段；
  3. 测试用 SQLite 内存库或临时文件，跑完清理。

### P2-02 README 与部署文档
- 负责模块：`README.md`
- 依赖任务：P0-01
- 验收标准：
  1. 一分钟启动指令、默认账号、`.env` 说明；
  2. Windows / macOS / Linux 均可跑；
  3. 常见问题（bcrypt/passlib 冲突、中文字体、SQLite 锁、LLM Key）。

### P2-03 CI 与代码质量
- 负责模块：`.github/workflows/ci.yml`、`pyproject.toml`
- 依赖任务：P2-01
- 验收标准：PR 自动跑 `ruff` + `pytest`；失败阻断合并。

### P2-04 结构化日志
- 负责模块：`app/core/logging.py`
- 依赖任务：P0-02
- 验收标准：
  1. `dictConfig` 或 `logging.yaml` 加载；
  2. 请求 ID 注入（`before_request` 生成 UUID）；
  3. 错误堆栈只入日志不入响应。

### P2-05 训练/生成异步化扩展点
- 负责模块：`app/services/*`
- 依赖任务：P1-04、P1-11
- 验收标准：
  1. 预留 `run_in_background(fn, *args)` 接口，可换 Celery/RQ；
  2. 长任务返回 `task_id`，`GET /tasks/{id}` 查询进度（可先假实现）。

### P2-06 缓存与限流
- 负责模块：`app/core/*`
- 依赖任务：P0-04
- 验收标准：`GET /data/statistics`、`GET /model/best`、`GET /email/prompt` 结果缓存 60s；登录/生成邮件加速率限。

### P2-07 中文字体与图表美化
- 负责模块：`app/utils/visualizer.py`
- 依赖任务：P1-03、P1-08
- 验收标准：图表中文不乱码；ROC 图带 AUC 数值；混淆矩阵含类别标签。

### P2-08 数据校验加固
- 负责模块：`app/schemas/*`
- 依赖任务：P0-05
- 验收标准：
  1. Pydantic 校验所有请求体；错误返回 `code=1001` 且列出字段；
  2. Excel 表头缺失/多余字段友好提示；
  3. 上传大小与列类型白名单。

### P2-09 API 文档与 OpenAPI
- 负责模块：`docs/openapi.json` 或 flask-smorest 集成
- 依赖任务：P1-15
- 验收标准：自动生成 OpenAPI，前后端与文档三端对齐。

### P2-10 生产化配置
- 负责模块：`Dockerfile`、`docker-compose.yml`、`gunicorn`
- 依赖任务：P0-04
- 验收标准：
  1. `docker compose up` 可跑；
  2. 生产切 PostgreSQL 只改 `DATABASE_URL`；
  3. 静态资源可选走 Nginx。

### P2-11 05 教学逐字稿完善
- 负责模块：`docs/05_3天课程逐字稿.md`
- 依赖任务：M1~M4 主体完成
- 验收标准：Day1/2/3 三段逐字稿完整，覆盖关键设计点与常见踩坑。

### P2-12 演示数据与端到端脚本
- 负责模块：`scripts/e2e_demo.py`
- 依赖任务：P1-15
- 验收标准：一条命令跑通"登录 → 上传 → 训练 → 预测 → 生成邮件"，输出结果摘要。

---

## 依赖关系速览

```
P0-01 → P0-02 → P0-03 → P0-04 → P0-05 → P0-06
                                    ↓
                       P1-01 → P1-02
                            ↘
                             P1-03
                             P1-04 → P1-05 → P1-06 → P1-10 → P1-11 → P1-13
                                            ↘ P1-07     ↘ P1-12
                                            ↘ P1-08
                                            ↘ P1-09
                                    P1-14
                                    P1-15（依赖 P1-01~P1-14）
                                    P1-16
                                    ↓
                       P2-* 全部
```

## 状态视图

- 已完成：P0-01（2026-07-30）、P0-02（2026-07-30）、P0-03（2026-07-30）、P0-04（2026-07-30）、P0-05（2026-07-30）、P0-06（2026-07-31）
- 进行中：无
- 下一步：P1-01 数据模块 · Excel 上传
- 说明：每完成一项在本文件把状态改为 `[x]`，并同步在 `DEVELOPMENT_LOG.md` 追加一条日志。

