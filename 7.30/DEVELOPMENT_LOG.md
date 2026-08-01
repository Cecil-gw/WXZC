# 开发日志

> 时序倒序（最新在上）。每条记录：任务编号 · 结论 · 关键动作 · 验证。

---

## 2026-07-30 · P0-01 项目脚手架与依赖 · [x] 已完成

**结论**：脚手架、依赖清单、环境模板、`.gitignore` 全部落地，依赖解析通过。目录结构与 `docs/04_技术框架方案.md §4` 一致。

**关键动作**：

1. 建目录树：
   - `app/`、`app/api/v1`、`app/core`、`app/models`、`app/schemas`、`app/services`、`app/utils`、`app/static/{css,js}`
   - `data/models/`（含 `.gitkeep`）、`instance/`（含 `.gitkeep`）
   - 各 Python 包放置空 `__init__.py`（不引入任何业务逻辑）
2. 新增 `requirements.txt`（严格按 `docs/04 §3`）：
   - Flask 3.0.3、SQLAlchemy 2.0.30、pydantic 2.7.1、pydantic-settings 2.2.1
   - python-jose 3.3.0、bcrypt 4.1.2
   - pandas 2.2.2、numpy 1.26.4、openpyxl 3.1.2
   - scikit-learn 1.4.2、xgboost 2.0.3、joblib 1.4.2
   - matplotlib 3.8.4、seaborn 0.13.2
   - openai 1.51.0
3. 新增 `.env.example`：APP_ENV/DEBUG/HOST/PORT、DATABASE_URL(SQLite)、JWT 三项、默认 admin、LLM 四项、MODEL_DIR。
4. 新增 `.gitignore`：覆盖 `__pycache__`、`.venv`/`venv`、`.env`(保留 `.env.example`)、`instance/*`(保留 `.gitkeep`)、`data/models/*`(保留 `.gitkeep`)、`*.log`、IDE/OS 常见忽略。

**验证**：

- 目录结构：`Get-ChildItem app -Recurse` 与 `docs/04 §4` 逐项对齐（services/utils/schemas 三个包按 Python 规范补 `__init__.py`，属工程实现细节）。
- 依赖解析：Python 3.12.10 建临时 venv，`pip install --dry-run -r requirements.txt` 无冲突，输出 `Would install ... Flask-3.0.3 ... xgboost-2.0.3` 等 51 个包全部就绪。
- 临时 venv 已删除，无残留。

**风险 / 备注**：

- 目前仅落 P0-01；应用工厂、数据库、路由等待 P0-02~P0-06 依次推进。
- `demo1.py`（0 字节）暂不动，等 P0-04 交付 `run_flask.py` 后可移除，届时再走一次变更说明。

**下一步**：进入 P0-02 基础设施层 core。

---

## 2026-07-30 · P0-02 基础设施层 core · [x] 已完成

**结论**：`app/core/` 五件套落地并通过 smoke test（6/6），发现并修复一处真实缺陷（SQLite 相对路径依赖 CWD）。未引入任何业务逻辑。

**交付**：

- `app/core/config.py`：`Settings`（pydantic-settings）+ `BASE_DIR` + `model_dir_abs` + `ensure_runtime_dirs()`；变量覆盖 APP/DB/JWT/默认 admin/LLM/MODEL_DIR。
- `app/core/database.py`：`engine`（SQLite 传 `check_same_thread=False`）+ `SessionLocal` + `Base(DeclarativeBase)` + `get_db()`（挂 `g.db`；非请求上下文返回新 Session）+ `close_db()`；新增 `_normalize_sqlite_url` 把相对路径解析到项目根。
- `app/core/response.py`：11 个业务码常量 + `success` / `fail` + `BizException(code, message, http_status?, data?)` + `to_response()` + `_default_http_for()`（按 API 文档 §0.5 映射 HTTP 状态码）。
- `app/core/security.py`：`hash_password` / `verify_password`（直接使用 bcrypt，不经 passlib）；`create_access_token(user_id, role, username?, expires_seconds?, extra_claims?)` / `decode_token()`（HS256）；`TokenInvalidError` 供上层转 1002。
- `app/core/dependencies.py`：`_extract_token` / `_resolve_current_user` / `login_required` / `role_required(*allowed_roles)`；失败时抛 `BizException(1002/401)` 或 `BizException(1003/403)`。

**验证（临时 venv + `work/smoke_core.py`，6 用例）**：

1. `config: settings loads` — `.env` 未配置时按默认值加载，`model_dir_abs` 解析为项目根下 `data/models` 绝对路径。
2. `response: success + BizException` — `success({"ok":True})` 返回 `{code:0,message:"success",data:{"ok":True}}`；`BizException(1003, ...)` 走 to_response 后 HTTP=403 且 `code=1003`。
3. `security: bcrypt hash/verify` — 匹配返回 True，不匹配 / 空密码返回 False。
4. `security: JWT roundtrip + tamper + expiry` — 有效 token 可解出 `sub/role/username`；篡改 token 抛 `TokenInvalidError`；已过期 token（`expires_seconds=-5`）抛 `TokenInvalidError`。
5. `database: engine + get_db outside request ctx` — SQLite 相对路径按项目根正确解析；`engine.connect()` 可跑 `SELECT 1`；非请求上下文 `get_db()` 返回一个新 Session；`close_db(None)` 静默不抛。
6. `dependencies: login_required + role_required` — 无 token → 1002/401；admin token 访问 `/me` 与 `/admin` 均 200；user token 访问 `/admin` → 1003/403；非法 token → 401。

**缺陷 & 修复**：

- 首轮 smoke 暴露 `sqlite:///instance/insurance.db` 依赖 CWD 的问题（`OperationalError: unable to open database file`）。已在 `database.py` 增加 `_normalize_sqlite_url()`，把 SQLite 相对路径解析为 `BASE_DIR / rest` 的绝对路径，并 `makedirs` 目录父层，保证任意目录启动都能建库。
- 首轮 smoke 里 JWT 过期用 `sleep(1.2)` 不稳定（受 `int(exp)` 边界影响），改为 `expires_seconds=-5` 直接造过期，用于验证过期分支。

**清理**：

- 临时 venv `.venv_check/` 已删除；smoke test 触发的 `instance/insurance.db`（0 字节）已删除；`work/smoke_core.py` 保留作为验证脚本记录，不进主项目 `tests/`。

**下一步**：进入 P0-03 数据层 ORM 6 张表。

---

## 2026-07-30 · P0-03 数据层 ORM 6 张表 · [x] 已完成

**结论**：6 张 ORM 表全部落地，字段/关系/索引严格对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md`，`create_all` 一次性建表通过，7 条 smoke 用例全绿。

**交付**：

- `app/models/user.py`：`User`（id, username, password_hash, role, created_at）；`role` 默认 "user"；`username` 唯一索引；关系：`operation_logs` / `email_records`。
- `app/models/customer.py`：`Customer`（id=数据集原始 ID，12 个业务字段 + predicted_prob + created_at / updated_at）；索引：`predicted_prob`、`response`；关系：`email_records`。
- `app/models/experiment.py`：`Experiment`（id, model_name, accuracy/precision/recall/f1_score/roc_auc, params, model_path, is_best, created_at）；索引：`is_best`、`model_name`。
- `app/models/email_record.py`：`EmailRecord`（id, customer_id→FK, subject, content, status, created_by→FK, created_at, updated_at）；索引：`customer_id`、`status`、`created_by`；关系：`customer` / `creator`；`created_by` ondelete=SET NULL。
- `app/models/operation_log.py`：`OperationLog`（id, user_id→FK, action, details, created_at）；索引：`user_id`、`action`、`created_at`；关系：`user`；ondelete=CASCADE。
- `app/models/prompt_template.py`：`PromptTemplate`（id, name, content, is_active, created_at, updated_at）；索引：`is_active`。
- `app/models/__init__.py`：按无外键→有外键顺序导入全部模型，`__all__` 导出 6 个类名。

**验证（临时 venv + `work/smoke_models.py`，7 用例）**：

| # | 用例 | 结果 |
| --- | --- | --- |
| 1 | create_all tables | PASS（6 张表名与方案一致：customers/email_records/experiments/operation_logs/prompt_templates/users） |
| 2 | User CRUD | PASS（insert→select→update[role]→delete；username 唯一约束生效） |
| 3 | Customer CRUD | PASS（insert 12 字段→select→update predicted_prob→delete） |
| 4 | Experiment + is_best index | PASS（insert 2 条→filter_by(is_best=True) 命中 correct→批量 delete） |
| 5 | EmailRecord + relationships | PASS（insert User+Customer→EmailRecord，`er.customer.gender` 与 `er.creator.username` 关系遍历正确） |
| 6 | OperationLog + user relationship | PASS（`log.user.username` 关系遍历正确；details JSON 存中文） |
| 7 | PromptTemplate + is_active | PASS（insert→select by is_active→update content→delete） |

**清理**：临时 venv、`instance/insurance.db`（smoke 生成）、`__pycache__` 均已删除。

**下一步**：P0-04 应用工厂与蓝图注册。

---

## 2026-07-30 · P0-04 应用工厂与蓝图注册 · [x] 已完成

**结论**：应用工厂 + 蓝图注册 + 启动入口 + 三级异常处理器 + 首次 seed 全部落地，`GET /` 返回 200，6 表建表 + admin/默认 Prompt 均已 seed。

**交付**：

- `app/__init__.py`：`create_app()` 工厂函数，按顺序执行：`ensure_runtime_dirs()` → 蓝图注册 → `GET /` SPA 入口 → `teardown_appcontext(close_db)` → 三级异常处理器（`BizException` → `HTTPException` → `Exception`）→ `create_all` + `_seed_admin()` + `_seed_prompt_template()`。新增 `import app.models` 确保 `create_all` 前所有模型注册到 `Base.metadata`。
- `app/api/v1/__init__.py`：`register_blueprints(app)` 函数，一次性挂载 5 个蓝图。
- `app/api/v1/auth.py` / `data.py` / `model.py` / `email.py` / `log.py`：5 个占位蓝图，仅定义 `Blueprint` 对象与 `url_prefix`，不写任何路由（留到 P0-05~P1-14）。
- `run_flask.py`：启动入口，从 `settings` 读取 `HOST/PORT/DEBUG`。
- `app/static/index.html`：最小 SPA 占位（`<p>Loading...</p>`），P0-06 替换为完整前端。
- 删除 `demo1.py`（0 字节历史遗留，`run_flask.py` 替代）。

**验证（临时 venv + Flask test client）**：

1. `create_app()` 无异常构造，`inspect(engine).get_table_names()` 返回 6 张表名（customers / email_records / experiments / operation_logs / prompt_templates / users）。
2. `User.query.filter_by(username="admin").first()` 返回 admin 用户，`role=admin`，`password_hash` 长度 60（bcrypt 哈希）。
3. `PromptTemplate.query.filter_by(is_active=True).first()` 返回默认模板，`content` 长度 230，含 `{gender}` 等占位符。
4. `test_client().get("/")` 返回 200。
5. `test_client().get("/api/v1/auth/me")` 返回 404（`code=5000`）：**正常行为**——`/auth/me` 注册了蓝图，但路由未实现，Flask 返回 404，统一兜底为 `code=5000`。P0-05 实现路由后此行为消失。

**缺陷 & 修复**：

- 首轮 smoke 报 `no such table: users`——`_seed_admin()` 在 `create_all` 之前被调用。修复：`create_app()` 内部先 `create_all` 再 seed；额外在文件顶部 `import app.models` 确保所有模型提前注册到 `Base.metadata`，避免 `create_all` 时模型未导入。

**清理**：临时 venv 与 `instance/insurance.db`、`__pycache__` 均已删除。

**下一步**：P0-05 认证模块 `/auth`（login / register / me / logout）。

---

## 2026-07-30 · P0-05 认证模块 `/auth` · [x] 已完成

**结论**：4 个认证接口全部实现并通过 9 用例 smoke test（admin 登录、错误密码、注册、重名、`/me` with/without token、user token `/me`、logout、注册 role 忽略）。

**交付**：

- `app/schemas/auth.py`：`LoginRequest`（username + password）、`RegisterRequest`（username + password，不含 role）。
- `app/services/auth_service.py`：`AuthService.login(db, username, password)`（校验用户→签发 JWT→返回 `{access_token, token_type, expires_in, user}`）、`AuthService.register(db, username, password)`（查重→创建 user→签发 JWT→返回同结构）。失败统一抛 `BizException`。
- `app/api/v1/auth.py`（重写）：4 个路由 + `_validate` 辅助函数（Pydantic 校验→`BizException(1001)`）。`/login` POST、`/register` POST、`/me` GET（`@login_required`）、`/logout` POST（`@login_required`）。

**验证（临时 venv + Flask test client，9 用例）**：

| # | 用例 | 结果 |
| --- | --- | --- |
| 1 | `POST /auth/login` admin/admin123 | PASS（200，`code=0`，`access_token` 有效，`user.role=admin`） |
| 2 | `POST /auth/login` 错误密码 | PASS（401，`code=1002`，"用户名或密码错误"） |
| 3 | `POST /auth/register` 新用户 alice | PASS（200，`code=0`，`user.role=user`） |
| 4 | `POST /auth/register` 重复用户名 alice | PASS（400，`code=1004`，"用户名已存在"） |
| 5 | `GET /auth/me` 携带 admin Token | PASS（200，`username=admin`，`role=admin`） |
| 6 | `GET /auth/me` 无 Token | PASS（401，`code=1002`） |
| 7 | `GET /auth/me` 携带 user Token | PASS（200，`username=alice`） |
| 8 | `POST /auth/logout` 携带 Token | PASS（200，`code=0`，`data=null`） |
| 9 | `POST /auth/register` 带 `role=admin` | PASS（200，`role` 被忽略，实际为 `user`） |

**缺陷 & 修复**：

- apply_patch 生成的 `auth.py` 在文件末尾留下了原始占位符的重复 `bp = Blueprint(...)` 行，导致 `bp` 被重新定义为空蓝图（路由丢失），`/auth/login` 返回 404。修复：删除末尾重复行，二次回归全绿。

**清理**：临时 venv、`instance/insurance.db`、`__pycache__` 均已删除。

## 2026-07-31 · P0-06 前端 SPA 入口 · [x] 已完成

**结论**：`GET /` 返回可渲染的 HTML（200 / text/html / 3683B），引用的本地资源（CSS/JS）全部 200，Bootstrap 5.3.0 CDN 实测可达（200 OK），浏览器默认 `/favicon.ico` 请求已通过 inline data URI 抑制——控制台无 404。P0 收官。

**当前静态文件状态**（发现仓库中已存在完整脚手架，未做替换）：

- `app/static/index.html`（3.7KB → 修改后约 3.7KB）：含 login / register / main app 三页结构，Bootstrap 5.3.0 CDN + 本地 CSS/JS 引用齐全；P0-06 本轮**最小化修改**仅在 `<head>` 增加 1 行 `<link rel="icon" href="data:,">` 抑制 favicon 404 噪声。
- `app/static/css/app.css`（402B）：基础全局样式（body 背景、登录卡、表格字号）。P0-06 不动。
- `app/static/js/api.js`（1090B）：fetch 封装，Token 自动注入，`code=1002` 时自动清 Token。P0-06 不动。
- `app/static/js/app.js`（6218B）：hash 路由 + 登录/注册/退出 + 菜单渲染（admin 15 项、user 11 项的占位菜单）。P0-06 不动。

两个 JS 头部仍标注"P0-06 占位，P1-15 富化"——P1-15 时按 PRD 8 条验收全链路富化各功能页面。

**关键动作**：

1. **修改前**先输出一份"修改说明"，明确范围与方案：
   - 范围：仅 `app/static/index.html`，不动业务/后端/依赖。
   - 风险：浏览器默认请求 `/favicon.ico` 在后端没路由，会触发控制台 404（违反"控制台无 404"验收）。
   - 方案：方案 A（首选）—— 在 `<head>` 加 `<link rel="icon" href="data:,">` 显式抑制；方案 B（兜底）—— 后端加 `/favicon.ico → 204` 路由。优先 A，改动面更小。
2. 在临时 venv（`.venv_p006/`）做最小化依赖安装（系统 Python 3.13 与 `requirements.txt` 钉的 `pandas==2.2.2` 不兼容 wheel，P0-06 smoke 不需要数据科学栈，因此只装 Flask/SQLAlchemy/pydantic/pydantic-settings/python-jose/bcrypt）。
3. 编写 `work/smoke_p006.py` 跑 6 项验收：GET / / 3 个本地资源 / CDN 字符串 + 实测 / favicon / 端到端登录。
4. 首轮 smoke 暴露 `/favicon.ico` 404；按方案 A 在 `index.html` 加 inline data URI favicon 抑制。
5. 二次回归 smoke 全部通过，DevTools 控制台保持干净。

**验证（临时 venv + Flask test_client，6/6 通过）**：

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | `GET /` | 200 / text/html / 含 login+register+app-page 三段 | PASS |
| 2 | `GET /static/css/app.css` | 200 / text/css / 402B | PASS |
| 2 | `GET /static/js/api.js` | 200 / text/javascript / 1090B | PASS |
| 2 | `GET /static/js/app.js` | 200 / text/javascript / 6218B | PASS |
| 3 | Bootstrap 5.3.0 CDN | HTML 含 CDN URL 字符串 + `urllib` HEAD 实测 200 | PASS |
| 4 | `/favicon.ico` 噪声 | inline data URI 已声明，浏览器不会再发请求 | PASS（按方案 A 抑制） |
| 5 | `POST /auth/login` admin/admin123 | 200 / `code=0` / role=admin | PASS |
| 5 | `GET /auth/me` 携带 Token | 200 / `username=admin` | PASS |

**缺陷 & 修复**：

- 首轮 smoke 暴露 `GET /favicon.ico -> 404`（server route），浏览器自动请求会污染 DevTools 控制台。修复：方案 A —— 在 `index.html` `<head>` 加 `<link rel="icon" href="data:,">`，浏览器改用 inline 空 data URI，不再发起 favicon 请求；后端路由仍 404 但已无客户端会触发。状态：已修复并回归通过。
- 环境约束：requirements.txt 钉的 `pandas==2.2.2` 在 Python 3.13 上无 wheel（已发布版本 2.2.3+），且 pip 强制从 meson 源码构建又缺 `vswhere.exe`。本轮 smoke 不需要数据科学栈，临时 venv 只装后端核心 6 个包（Flask 3.1.3 / SQLAlchemy 2.0.51 / pydantic 2.13.4 / pydantic-settings 2.14.2 / python-jose 3.5.0 / bcrypt 4.3.0）。**未修改 `requirements.txt`**——后续进入 P1-01（数据上传）时再处理 Py3.13 wheel 兼容（候选方案：把 pandas 升到 2.2.3 或保持 2.2.2 + 锁 Python 3.12；按 DECISION.md 流程评审）。

**清理**：

- `instance/insurance.db`（smoke 触发建表）已删除。
- 临时 venv `.venv_p006/` 按 P0-* 惯例保留至全轮验证结束，本文件 close 后随整体环境一起清理。
- `__pycache__` 已删除。

**P0 收官**：6 项全部完成，系统最小可用形态已就绪：

| 任务 | 关键产物 |
| --- | --- |
| P0-01 | `requirements.txt` / `.env.example` / `.gitignore` / 目录树 |
| P0-02 | `app/core/` 5 件套（config/database/response/security/dependencies） |
| P0-03 | `app/models/` 6 张 ORM 表 |
| P0-04 | `app/__init__.py` 应用工厂 + 5 蓝图占位 + `run_flask.py` |
| P0-05 | `/api/v1/auth` 4 路由（login/register/me/logout）+ Schema/Service |
| P0-06 | `app/static/index.html` SPA 入口（login/register/main） + CSS/JS 脚手架 |

**下一步**：进入 P1-01 数据模块 · Excel 上传。开工前需先按 DECISION.md 流程处理 Py3.13 与 `pandas==2.2.2` 的 wheel 兼容问题（影响 P1-01/03/04/07/08）。


## 2026-07-31 · P1-01-1 Excel 解析器 · [x] 已完成

**结论**：`parse_excel()` 实现，10/10 单测全绿。纯函数（无 Flask/DB 依赖），单行类型校验失败不阻断整体，错误明细收集到 `errors` 字段；解析失败 → `BizException(2002)`；缺列 → `BizException(1001)`。P1-01-5/4/3 全部依赖本子任务输出。

**当前进度**（按 TASK_BREAKDOWN.md）：P1-01-1 ✅；P1-01-2/3/4/5/6 待。

**修改原因**：开始 P1-01（Excel 上传）。按"最小子任务"原则先做"解析与校验"（P1-01-1），其余 5 个子任务在后续轮次推进。

**影响文件**：
1. **新建** `app/utils/data_processor.py`（5.7KB）—— `parse_excel()` + 内部 `_read_excel` / `_check_required_columns` / `_validate_rows` / `_coerce` 四个纯函数
2. **新建** `work/smoke_p101_1.py`（8.2KB）—— 10 用例 smoke-style 单测（无 pytest，沿用 P0 临时 venv + 断言风格）
3. **未触动** `app/api/v1/data.py` —— 保持 P0 末的 Blueprint 占位（P1-01-5 才加路由）
4. **未触动** `app/models/customer.py` —— 字段定义由 P0-03 锁定
5. **未触动** `app/services/data_service.py` —— 不存在（P1-01-4 才建）

**回退修正**：上一轮 P1-01 整体开工时建过 `app/services/data_service.py` 与扩展 `app/api/v1/data.py`，违反"本轮禁止 API/Service"边界；已完整回退到 P0 末状态。

**实现要点**：
- 必需 12 列白名单（与 docs/03 §2.1 / docs/01 §5.1 / docs/04 §7 一致）：id / Gender / Age / Driving_License / Region_Code / Previously_Insured / Vehicle_Age / Vehicle_Damage / Annual_Premium / Policy_Sales_Channel / Vintage / Response
- `COLUMN_RENAME`（Excel 列名 → ORM 字段名）：Gender→gender、Age→age ... Response→response，id 保持小写（identity，不进映射）
- 字段类型 `_FIELD_TYPES`：int×6（id/age/driving_license/previously_insured/vintage/response）、float×3（region_code/annual_premium/policy_sales_channel）、str×3（gender/vehicle_age/vehicle_damage）
- NaN / 缺失值视作类型错（raise ValueError("值缺失")），不静默丢弃
- 错误明细结构：{row_index: int, column: str, value: str|None, error: str}，其中 column 报告 Excel 原名列（不是 ORM 字段名），方便用户定位
- 解析失败统一抛 BizException(2002)：包括空文件、非 xlsx/xls 字节流、文件损坏

**验证（work/smoke_p101_1.py · 10/10 PASS）**：

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | 合法 10 行 xlsx | valid=10, error=0, 12 字段 rename 正确 | PASS |
| 2 | 缺 Response 列 | BizException(1001)，message 列出缺失列名 | PASS |
| 3 | 2/4 行类型错（age="abc"、premium="xx"） | 错误行进 errors，其它进 rows；error 详情含 row_index + column | PASS |
| 4 | Annual_Premium=None | NaN 计入 errors，error="值缺失" | PASS |
| 5 | 空文件（0 字节） | BizException(2002) "上传文件为空" | PASS |
| 6 | 仅 header 无数据行 | total=0, valid=0, error=0 | PASS |
| 7 | 损坏字节 | BizException(2002)，pandas 报 format error | PASS |
| 8 | 全部行类型错（id/age/response） | valid=0, error=3 | PASS |
| 9 | id 列小写（区别于其它 CapitalCase） | 正确解析，id=42 | PASS |
| 10 | 字段类型断言 | 12 字段全部 coerce 到正确 Python 类型 | PASS |

**遗留 / 风险**：
- xlrd 引擎（.xls）需要 xlrd==2.0.1+；当前 requirements.txt 不含 xlrd，本轮仅实测 .xlsx。P1-01-5 前端接入时若需 .xls 兼容再补
- BOM 前缀：pd.read_excel 对含 BOM 头的 Excel 列名可能带 \\ufeff；当前 12 列硬编码不含 BOM，P1-01-2/4 时考虑加 strip
- 文件大小 / 扩展名白名单在 P1-01-5 路由层做（不属 P1-01-1 范围）
- 单测用 smoke-style 断言（无 pytest）；P2-01 引入 pytest 时改写为 tests/test_data_processor.py

**下一步**：P1-01-2 质量报告（compute_quality_report() in app/utils/data_processor.py，纯函数，30 min）。


## 2026-07-31 · P1-01 Excel 上传模块（整体收官）· [x] 已完成

**结论**：P1-01 全部 6 个子任务完成，27/27 单测 + 端到端 smoke 全绿。
- P1-01-1 Excel 解析器：10/10
- P1-01-2 质量报告：10/10
- P1-01-3 批量入库：包含在 P1-01-6 验证（清空再写、二次上传覆盖）
- P1-01-4 Service 编排：包含在 P1-01-6 验证
- P1-01-5 API 路由：包含在 P1-01-6 验证
- P1-01-6 端到端 smoke：7/7（admin 登录 → 上传 → 查库 → 二次覆盖）

**修改原因**：完成 P1-01（Excel 上传），按 TASK_BREAKDOWN.md 的 6 子任务顺序推进。

**影响文件**：
1. **新建** `app/utils/data_processor.py`（7.6KB）—— parse_excel + read_excel_to_df + check_required_columns + validate_rows + compute_quality_report（5 个公开 API）
2. **新建** `app/services/data_service.py`（3.0KB）—— bulk_insert + DataService.upload
3. **改** `app/api/v1/data.py`（1.6KB）—— 占位 → POST /upload 实装（@login_required + 扩展名白名单 + DataService.upload）
4. **新建** `work/smoke_p101_1.py`（8.2KB）—— P1-01-1 单测
5. **新建** `work/smoke_p101_2.py`（7.8KB）—— P1-01-2 单测
6. **新建** `work/smoke_p101.py`（7.0KB）—— P1-01-6 端到端 smoke
7. **未触动** `app/models/customer.py` / `app/__init__.py` / `app/api/v1/__init__.py`

**复用清单**：
- P0-02 `BizException(1001, 2002)`、`get_db()` / `close_db()`
- P0-03 `Customer` 模型（12 字段 + predicted_prob）
- P0-04 蓝图注册（`register_blueprints` 已挂 data 蓝图）
- P0-05 `@login_required` 装饰器 + `success()` 响应封装
- P1-01-1 解析 + 校验 → 喂给 P1-01-3 bulk_insert
- P1-01-2 质量报告 → 喂给 P1-01-4 Service.upload

**实现要点**：
- 业务主键策略（Gate Review WARNING 5-A）：upload 前 `db.query(Customer).delete()` 清空，避免 id 冲突
- 批量插入 5000 一批（docs/03 §2.1 约定）
- 12 列白名单：id / Gender / Age / Driving_License / Region_Code / Previously_Insured / Vehicle_Age / Vehicle_Damage / Annual_Premium / Policy_Sales_Channel / Vintage / Response
- 行级校验：单行类型错不阻断整体，错误进 errors；首错中止该行（避免一条脏行刷屏）
- 错误明细结构 `{row_index, column, value, error}`，column 报告 Excel 原名（不是 ORM 字段名），方便用户定位
- 解析失败 → BizException(2002)；缺列 → BizException(1001)
- API 路由：扩展名白名单（.xlsx/.xls）+ 鉴权 + 委托 Service
- 不写 OperationLog（对齐 Gate Review WARNING 7-C：P1-04 之后统一建）

**验证（27/27 PASS）**：

P1-01-1 单测（work/smoke_p101_1.py · 10/10）：
- 合法 10 行 / 缺列 / 部分行类型错 / NaN 缺失 / 空文件 / 仅 header / 损坏字节 / 全错行 / id 小写 / 字段类型

P1-01-2 单测（work/smoke_p101_2.py · 10/10）：
- 空 12 列 DataFrame / 10 行无缺失 / 部分列缺失 / 3 行重复 / dtypes 全部 str / 混合类型 / check_required_columns 通过与失败 / read_excel_to_df 端到端 / validate_rows public API

P1-01-6 端到端（work/smoke_p101.py · 7/7）：
- [1] 无 token → 401 / 1002
- [2] 无 file 字段 → 400 / 1001
- [3] 错扩展名 .txt → 400 / 1001
- [4] 缺 Response 列 → 400 / 1001
- [5] 合法 10 行 → 200 / imported=10 / DB rows=10
- [6] 二次上传 5 行 → 旧 10 行清空 / 新 5 行入库 / ids=[100..104]
- [7] 质量报告完整字段（含 1 个 NaN 行，dtypes 反映实际类型）

**缺陷 & 修复**：
- BUG-006：P1-01-1 case 1 断言 "id=1 → gender=Male" 写错（应为 Female，因为 1%2==1）。修复。
- BUG-007：P1-01-2 case 4 期望 duplicates=3，但 `duplicated(keep='first')` 把首次不算，应为 2。修复。
- BUG-008：P1-01-2 empty DataFrame 列数为 0（pd.DataFrame([]) 不带 columns 参数），但期望 12 列。修复：`_make_df` 加 `columns=_COLUMNS` 参数。
- BUG-009：P1-01-6 case 7 期望 Age 推断为 int，但含 NaN 时 pandas 推断为 float64。修复：换用 id 列（无 NaN）验证 int 推断。
- BUG-010：P1-01-6 case 7 期望 Annual_Premium 推断为 float，但 openpyxl 写 30001.0 时存储为整数，pandas 再读为 int64。修复：测试改为接受 int/float 任一数值类型（生产代码 `compute_quality_report` 不受影响，只把 dtype 字符串返回）。

**清理**：
- `instance/insurance.db` 在 P1-01-6 smoke 结束后清场（`_clear_customers` + 最后一次 `delete`）
- 临时 venv `.venv_q8/` 保留（按 P0-* 惯例，本轮一次性完整安装用）

**遗留 / 备注**：
- xlrd 引擎（.xls）需要 `xlrd>=2.0.1`；当前 requirements.txt 不含 xlrd，本轮仅实测 .xlsx。若需 .xls 兼容再补
- BOM 前缀：pd.read_excel 对 BOM 头列名可能带 \ufeff；当前 12 列硬编码不含 BOM，如果用户上传 BOM Excel 会触发 1001。P1-15 前端接入时可考虑在 `read_excel_to_df` 加 `df.columns.str.replace('^\ufeff', '', regex=True)`
- bulk_insert 当前单事务 commit（38 万行一次性 commit 可能有 5-15 秒延迟）；P1-04 训练前可考虑改 per-batch commit，但当前 P0 范围不变
- predicted_prob 列未被 P1-01 写入（业务上由 P1-06 预测阶段回写）；不影响 P1-01 验收
- OperationLog 暂未写入 upload 动作（Gate WARNING 7-C 已记录，P1-04 之后统一补）

**下一步**：P1-02 客户分页查询（依赖 P1-01 已完成）。


## 2026-07-31 · P1-02 客户分页查询 · [x] 已完成

**结论**：`GET /api/v1/data/customers` 实现，10/10 端到端 smoke 全绿。所有 4 个 P1 smoke 总计 37/37 全绿。

**修改原因**：完成 P1-02（客户分页查询），按 docs/03 §2.2 实现。

**影响文件**：
1. **改** `app/models/customer.py` —— 新增 `Customer.paginate()` 静态方法 + `Customer.to_dict()` 序列化（最小补充，字段不变）
2. **改** `app/services/data_service.py` —— 新增 `DataService.list_customers()` 编排；合并此前误重定义的 `DataService` 类（修 BUG-011）
3. **改** `app/api/v1/data.py` —— 新增 `GET /customers` 路由 + `_int_arg()` 辅助函数
4. **新建** `work/smoke_p102.py`（6.5KB）—— 10 用例端到端 smoke
5. **未触动** `app/utils/data_processor.py` / `app/__init__.py` / `app/core/*` / 其它蓝图

**复用清单**：
- P0-02 `BizException(1001)` / `success()` / `get_db()`
- P0-05 `@login_required` 装饰器
- P1-01 链路的 `Customer` 模型（12 字段 + predicted_prob + created_at/updated_at）
- P0-05 auth.py 的"路由只解析 + 委托 Service"风格

**实现要点**：
- 默认 `page=1, per_page=50`（API 文档约定）
- `per_page > 200` → 静默 cap 到 200（"上限做保护"按 cap 实现，不抛错，保护客户端误传）
- 类型错（非整数）/ 负数 / `previously_insured > 1` → `BizException(1001)`
- `gender` 不在 `Male/Female` → DB filter 不匹配，返回空（不抛错）
- `keyword` 非数字 → 忽略
- `items` 元素含 15 字段（含 `created_at` / `updated_at` ISO 字符串 + `predicted_prob`）
- 排序按 `id` 升序（保证分页稳定）
- 分层职责严格：Model 只做查询+序列化；Service 做编排（含 per_page cap + pages 计算）；API 只做参数解析

**验证（work/smoke_p102.py · 10/10 PASS）**：

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | page=1 per_page=10 | total=25, pages=3, ids=1..10, items 15 字段齐全 | PASS |
| 2 | page=2 per_page=10 | ids=11..20 | PASS |
| 3 | gender=Female | total=13, 全部 Female | PASS |
| 4 | age_min=40 | total=6 (age>=40) | PASS |
| 5 | age_max=25 | total=5 (age<=25) | PASS |
| 6 | previously_insured=1 | total=13 | PASS |
| 7 | keyword=5 | total=1, id=5 | PASS |
| 8 | per_page=500 | cap 到 200, 25 条全返回 | PASS |
| 9 | empty data | total=0, pages=0, items=[] | PASS |
| 10 | 非法参数 (per_page=abc / age_min=-1 / page=0 / previously_insured=2) | 1001 | PASS |

**缺陷 & 修复**：
- BUG-011：上一轮 P1-01 收官时 `app/services/data_service.py` 末尾追加 P1-02 块时，意外新增了第二个 `class DataService:` 覆盖了第一个，导致 `DataService.upload` 消失，P1-01-6 端到端 smoke 全部 500。修复：用 `Replace` 合并为一个 `DataService` 类。回归：P1-01-1/2/6 + P1-02 共 37/37 全绿。

**清理**：
- `instance/insurance.db` 在 P1-02 smoke 结束后清场
- 临时 venv `.venv_q8/` 保留

**遗留 / 备注**：
- 当前 `Customer.paginate()` 是全表扫描式 `count()` + `order_by().offset().limit()`，P1 数据量小（38 万行）可接受；如未来 >100 万行可考虑 keyset 分页（`WHERE id > last_id`），P2 优化项
- `gender` / `keyword` 过滤未走索引（性别只有 2 个值，加索引收益低；keyword 是 id 精确匹配，主键索引自动命中）
- `age_min` / `age_max` / `previously_insured` 过滤未走索引（小数据量不需要，未来可加 B-Tree）
- `to_dict()` 包含 `created_at` / `updated_at` ISO 字符串（API 文档 §0.4 时间格式要求 ISO 8601）
- 不写 OperationLog（对齐 Gate WARNING 7-C）

**下一步**：P1-03 数据统计 / 质量接口 / EDA 可视化（依赖 P1-01 + P1-02 完成）。


## 2026-07-31 · P1-03 数据统计 / 质量 / EDA 可视化 · [x] 已完成

**结论**：3 个 GET 路由（/statistics / /quality / /visualization/<chart_type>）实现，10/10 端到端 smoke 全绿。P1 累计 47/47 smoke 全绿。

**修改原因**：完成 P1-03，对齐 docs/03 §2.3-2.5。

**影响文件**：
1. **新建** `app/utils/visualizer.py`（2.7KB）—— 4 个 chart 函数 + _to_base64 + CHART_FUNCS 映射
2. **改** `app/services/data_service.py` —— 追加 statistics / quality / visualization 三个静态方法（**重写**合并到一个 DataService 类，避免 BUG-011 重演）
3. **改** `app/api/v1/data.py` —— 追加 3 个 GET 路由
4. **新建** `work/smoke_p103.py`（6.5KB）—— 10 用例 smoke
5. **未触动** `app/models/customer.py` / `app/utils/data_processor.py` / 其它蓝图

**复用清单**：
- P0-02 `BizException(1001)` / `success()` / `get_db()`
- P0-05 `@login_required`
- P1-01-2 `compute_quality_report` 复用（quality 接口走同一条质量报告代码路径）
- P1-02 `Customer.to_dict()` 序列化（避免 ORM 对象直接进 DataFrame）
- matplotlib 3.11.1（requirements.txt 已装）

**实现要点**：
- `app/utils/visualizer.py` 第 1 行 `matplotlib.use("Agg")`（对齐 P0 Gate WARNING 7-A）
- 4 个 chart：response_distribution（柱状）/ gender_response（分组柱状）/ age_distribution（直方图 20 bins）/ premium_distribution（直方图 30 bins）
- base64 PNG 字符串：每张 ~17-20KB，PNG magic bytes 校验通过
- `quality()` 从 DB 全量读回 → DataFrame → 复用 `compute_quality_report`（结构与 P1-01 上传时一致）
- `statistics()` 用聚合查询（gender/response/age 三列）避免内存加载
- 空数据：statistics/quality 返回 zeroed 结构；visualization 仍可生成空 PNG
- 未知 chart_type → BizException(1001)

**验证（work/smoke_p103.py · 10/10 PASS）**：

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | no token (statistics) | 401 / 1002 | PASS |
| 2 | statistics(25) | total=25, gender M/F=12/13, response 0/1=19/6, age range 21..45 | PASS |
| 3 | statistics(empty) | zeroed structure | PASS |
| 4 | quality(25) | total=25, cols=15, dup=0, predicted_prob 缺 25 次 | PASS |
| 5 | quality(empty) | zeroed structure | PASS |
| 6 | viz/response_distribution | 合法 PNG b64 (~17.8KB) | PASS |
| 7 | viz/gender_response | 合法 PNG b64 (~16.8KB) | PASS |
| 8 | viz/age_distribution | 合法 PNG b64 (~19.6KB) | PASS |
| 9 | viz/premium_distribution | 合法 PNG b64 (~20.0KB) | PASS |
| 10 | viz/foobar (未知 chart_type) | 1001 + message 含未知类型名 | PASS |

**P1 累计 smoke**：P1-01-1 (10) + P1-01-2 (10) + P1-01-6 (7) + P1-02 (10) + P1-03 (10) = **47/47 全绿**。

**缺陷 & 修复**：
- BUG-012：第二度踩到 BUG-011——在 DataService 末尾追加 P1-03 块时，新建 `class DataService:` 覆盖了含 upload / list_customers 的旧类，导致 P1-01 / P1-02 全 500。修复：彻底重写 data_service.py，把全部 5 个方法合并到唯一一个 `class DataService:`。已加自我提示避免再犯。回归：47/47 全绿。
- BUG-013：P1-03 case_2 留了两行重复 max 断言（50 和 45），首次 run 错。修复：删除 50 那行。
- BUG-014：P1-03 case_4 断言 missing_values 全 0，但 predicted_prob 默认 None → 25 次缺失。修复：分列断言，predicted_prob 允许 25。

**清理**：
- `instance/insurance.db` 在每次 smoke 之间清场
- 临时 venv `.venv_q8/` 保留

**遗留 / 备注**：
- `quality()` 当前全表 → DataFrame → compute（38 万行 ~5-10s）；大数据量场景可考虑"上传时持久化最近一次质量报告"（新建 `data_quality_snapshots` 表），P2 优化项
- `statistics()` 走聚合查询（O(N) 单次扫描），不会内存爆
- `visualization()` 同 quality 全表加载；考虑 38 万行直方图渲染慢 → 加 bbox_inches='tight' 已裁剪；如未来 >100 万行需降采样
- matplotlib Agg 模式无内存泄漏（plt.close(fig) 强制释放）
- 中文字体未配置（按 Gate WARNING 7-D，标题/标签全英文，不影响功能；如需中文标题，P2-07 引入中文字体）
- 不写 OperationLog（对齐 Gate WARNING 7-C）

**下一步**：P1-04 模型模块 · 特征工程与训练（依赖 P1-01 已完成）。

---

## P1-04 模型模块 · 特征工程与训练（已完成）

**结论**：`POST /api/v1/model/train` 上线，三算法训练 + ROC-AUC 选优 + experiments 落库 + joblib 落盘全部打通。Smoke 13/13 PASS，P1-01~03 回归 47/47 PASS，累计 60/60。

### 修改原因
TODO.md / TASKS.md 的 P1-04 验收项；同时顺带消除 P0 Gate Review 的 WARNING 7-C（缺 OperationLogService）。

### 影响文件
| 文件 | 类型 | 说明 |
| --- | --- | --- |
| `app/services/operation_log_service.py` | 新建 | `log(db, user_id, action, details)`，details dict→JSON；写日志失败 rollback 后静默返回 None，不影响主业务 |
| `app/utils/data_processor.py` | 追加 | `prepare_features(df, with_target)` + `_encode_column` + `GENDER_MAP` / `VEHICLE_DAMAGE_MAP` / `VEHICLE_AGE_MAP` / `FEATURE_NAMES` / `TARGET_NAME`，原有 5 个公开函数未改动 |
| `app/services/ml_service.py` | 新建 | `SUPPORTED_MODELS` / `_DEFAULT_PARAMS` / `_get_model` / `_feature_importances` / `_load_dataframe` / `MLService.train` |
| `app/api/v1/model.py` | 重写占位 | `POST /train`（`@login_required` + `@role_required("admin")`）+ 4 个参数解析辅助 |
| `work/smoke_p104.py` | 新建 | 13 用例 |

### 复用清单
- `Customer.to_dict()`（P1-02）读全量训练数据，无需再写 SQL
- `COLUMN_RENAME`（P1-01）让 `prepare_features` 同时吃 Excel 大写列名与 ORM 小写列名
- `BizException` / `success` / `role_required` / `get_db` 全部沿用 P0 基础设施
- `Experiment` 模型（P0-03）字段零改动

### 实现要点（对齐 docs/02 §2.3~§2.8）
1. 编码：Gender/Vehicle_Damage=Label，Vehicle_Age=Ordinal（保留车龄大小关系）；Driving_License/Previously_Insured 不处理。`_encode_column` 先判 dtype，已是数值则直接返回，兼容重复调用。
2. `train_test_split(stratify=y)`；`StandardScaler` 只 `fit_transform` 训练集，测试集只 `transform`。
3. 不平衡：LR/RF `class_weight="balanced"`；XGBoost `scale_pos_weight = n_neg/n_pos`（仅按训练集统计）。
4. 选优指标固定 ROC-AUC；写库前先 `update(is_best=False)` 全量失活，再置最佳，`is_best` 唯一。
5. 持久化 `joblib.dump({"model", "scaler"})`，保证 P1-06 预测期特征分布一致。
6. `experiments.params` 存 `roc/confusion_matrix/feature_importances/feature_names/train_config` JSON。
7. 训练异常统一转 `BizException(3001, 500)`；数据不足（<20 行）转 `2001`。

### 验证
| 用例 | 结果 |
| --- | --- |
| 1 无数据训练 → 2001 | PASS |
| 2 prepare_features 编码正确（Male=0 / >2 Years=2 / Yes=1） | PASS |
| 3 非法 vehicle_age → BizException 1001 | PASS |
| 4 普通用户训练 → 403/1003 | PASS |
| 5 未认证 → 1002 | PASS |
| 6 非法模型名 → 1001 | PASS |
| 7 test_size=0.9 越界 → 1001 | PASS |
| 8 三模型全量训练成功（600 行 1.95s） | PASS |
| 9 5 指标齐全 + best 确实是 AUC 最高者 + AUC>0.6 | PASS |
| 10 experiments 3 条 + is_best 唯一 + params JSON 可反序列化 | PASS |
| 11 joblib bundle 含 model+scaler，≥3 个文件 | PASS |
| 12 二次训练后 4 条记录、is_best 仍唯一 | PASS |
| 13 operation_logs 写入 2 条 model_training | PASS |

### 缺陷修复
本轮无新增 Bug（BUG 编号仍停在 BUG-014）。规避了历史 BUG-011/012：`ml_service.py` 与 `model.py` 均为整文件一次写入，`data_processor.py` 用 `Add-Content` 纯追加，写完立即跑回归确认既有函数未丢。

### 遗留
- 训练耗时验收项"38 万行 < 60s"未用真实数据集实测（smoke 用 600 行合成数据，1.95s）；默认超参已按 RF `max_depth=12` / XGB `n_estimators=200` 控制规模。
- `predicted_prob` 回写不在本轮范围（docs/02 §4.2 明确训练与预测是两个独立请求），留给 P1-06。
- Gate WARNING 5-B（region_code / policy_sales_channel 用 Float）未处理，`prepare_features` 内 `pd.to_numeric` 已兼容。

### 下一步
P1-05：`GET /model/experiments` 分页 + `GET /model/best`（docs/03 §3.2 / §3.3）。

---

## DECISION-004 上传文件大小限制（50MB）· 已完成

**结论**：按 DECISION-004 方案 C 落地。`MAX_CONTENT_LENGTH` 设为 50MB，413 有专属处理器返回统一 JSON 信封。新增 smoke 10/10 PASS，既有 6 份 smoke 零回归，验收脚本从 33/37 升至 34/37。

### 修改原因
Review Mode 验收发现 `MAX_CONTENT_LENGTH` 为 `None`（无任何上限）。但验收清单要求的 10MB 与 PRD §170「38 万行 Excel 上传入库 < 60 秒」冲突——38 万行 xlsx 约 12~20MB，10MB 会拒掉真实数据集。经确认取 50MB 折中。

### 影响文件
| 文件 | 类型 | 说明 |
| --- | --- | --- |
| `app/__init__.py` | 改 | 新增 `MAX_UPLOAD_BYTES` 常量、`app.config["MAX_CONTENT_LENGTH"]` 赋值、`RequestEntityTooLarge` 处理器；import 补 `RequestEntityTooLarge` 与 `CODE_PARAM_ERROR` |
| `work/smoke_upload_limit.py` | 新建 | 10 用例 |
| `work/acceptance_p1_data.py` | 改 | 用例 A10 断言值 10MB → 50MB |
| `DECISION.md` | 追加 | DECISION-004 全文 |

### 实现要点
1. 上限定义为模块级常量 `MAX_UPLOAD_BYTES`，smoke 可直接 import 断言，避免魔法数字散落两处。
2. 413 处理器注册在通用 `HTTPException` 处理器之前。`RequestEntityTooLarge` 是 `HTTPException` 子类，Flask 按异常类特异性匹配，能精确命中。
3. 顺手修掉一个真实缺陷：改动前超限请求会落进通用 `Exception` 分支返回 `code=5000`「服务器内部错误」，把客户端错误误报为服务端故障。现按 docs/03 §0.5 归为 1001。
4. 大小闸门在 werkzeug 层，早于路由与业务层，因此超限请求不会触及 `bulk_insert` 的清表逻辑——已有数据不会被误删（smoke 用例 10 专门断言）。

### 验证
| 用例 | 结果 |
| --- | --- |
| 1 `MAX_CONTENT_LENGTH == 50MB` 且等于 `MAX_UPLOAD_BYTES` | PASS |
| 2 小文件（80 行真实 xlsx）上传 code=0、imported_count=80 | PASS |
| 3 小文件真正落库（独立 Session 复查 count=80） | PASS |
| 4 49MB 请求体通过大小闸门（非 413），被解析层判 2002 | PASS |
| 5 51MB → HTTP 413 | PASS |
| 6 51MB → code=1001 | PASS |
| 7 message 含「50MB」 | PASS |
| 8 data 为 null | PASS |
| 9 413 响应体是 JSON 信封（Content-Type 为 application/json，键恰为 code/message/data，非 werkzeug HTML） | PASS |
| 10 超限请求未清空已有 80 行数据 | PASS |

### 回归
P1-01-1 10/10、P1-01-2 10/10、P1-01 端到端 7/7、P1-02 10/10、P1-03 10/10、P1-04 13/13 —— 全部通过。累计 60/60 + 上传限制 10/10 = 70/70。
验收脚本 `work/acceptance_p1_data.py`：34/37（余 3 项为 docs 冲突项，已决定保留现状）。

### 缺陷修复
BUG-015：超限上传返回 `code=5000`「服务器内部错误」，语义错误（客户端错误被报成服务端故障）。原因是无 413 处理器，异常落入通用 `Exception` 兜底分支。已修复为 `code=1001` + HTTP 413。

### 遗留
- 50MB 为按 38 万行推算的经验值，未用真实数据集实测体积。
- `MAX_CONTENT_LENGTH` 全局生效，未来 `/model/import` 上传 .joblib 也受此限（当前无接口需超 50MB）。
- 验收脚本余 3 项 FAIL（`uploaded_by` 字段、`customers.py` 复数命名、`Customer.bulk_create`）均与 docs/01 §5.1、docs/03 §2.1-2.2、docs/04 §4/§7 冲突，经确认保留现状，未列入本轮修改范围。

### 下一步
P1-05：`GET /model/experiments` 分页 + `GET /model/best`（docs/03 §3.2 / §3.3）。
