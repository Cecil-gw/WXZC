# 测试报告

> 时序倒序（最新在上）。P0-01 起按真实执行填写；早期"环境/登录/权限测试/Bug记录"是模板示例内容，与实际当前进度无关，保留作为格式参考。

---

## 2026-07-30 · P0-02 core smoke test（临时 venv）

**环境**

- OS：Windows
- Python：3.12.10（临时 venv，验证后删除）
- 依赖：按 `requirements.txt` 全量安装（Flask 3.0.3 / SQLAlchemy 2.0.30 / pydantic 2.7.1 / pydantic-settings 2.2.1 / python-jose 3.3.0 / bcrypt 4.1.2 等）

**用例与结果（6/6 PASS）**

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | config: settings loads | .env 缺省时按默认值加载；`model_dir_abs` 解析为项目根下 `data/models` 绝对路径 | PASS |
| 2 | response: success + BizException | `success` 返回 `{code:0,message,data}`；`BizException(1003,...)` 走 to_response → HTTP 403, code 1003 | PASS |
| 3 | security: bcrypt hash/verify | 正确密码 True；错密码 / 空密码 False；异常吞掉 | PASS |
| 4 | security: JWT roundtrip + tamper + expiry | 有效 token 解出 sub/role/username；篡改 → TokenInvalidError；过期（expires_seconds=-5）→ TokenInvalidError | PASS |
| 5 | database: engine + get_db outside request ctx | SQLite 相对路径归一化到 BASE_DIR；`SELECT 1` 通过；`close_db(None)` 静默不抛 | PASS |
| 6 | dependencies: login_required + role_required | 无 token → 401/1002；admin token 通过 `/me` 与 `/admin`；user token 访问 `/admin` → 403/1003；非法 token → 401 | PASS |

**Bug 记录**

- BUG-002：`sqlite:///instance/insurance.db` 相对路径依赖 CWD，非项目根启动会 `unable to open database file`。修复：`app/core/database.py` 新增 `_normalize_sqlite_url()`，将相对路径解析为 `BASE_DIR / rest` 并 `makedirs` 父目录。状态：已修复并回归通过。
- smoke test 自身：JWT 过期用 `sleep(1.2)` 受 `int(exp)` 秒边界影响不稳定，改为 `expires_seconds=-5` 直接造过期。状态：已修复。

**未覆盖**

- 蓝图与真实路由（P0-04/05 后覆盖）；
- ORM 表 CRUD（P0-03 后覆盖）；
- 使用真实 `.env` 的加载（当前仅覆盖了默认值路径）。

---

## 2026-07-30 · P0-01 项目脚手架与依赖

**环境**：Python 3.12.10 临时 venv（验证后删除）。

**用例**

| # | 用例 | 结果 |
| --- | --- | --- |
| 1 | 目录树对齐 `docs/04 §4` | PASS（`Get-ChildItem app -Recurse` 逐项核对） |
| 2 | `pip install --dry-run -r requirements.txt` | PASS（无冲突，`Would install` 输出 51 个包完整版本） |

---

## 历史模板示例（非真实测试结果）

以下内容为项目初始化时的模板占位，保留仅作格式参考：

- 登录接口 POST /auth/login：正确密码 PASS / 错误密码 PASS
- 权限：admin 可训练模型 / user 禁止训练
- BUG-001 Excel 上传失败（示例，已标记"已修复"）

---

## 2026-07-30 · P0-03 ORM models smoke test（临时 venv）

**环境**：Python 3.12.10 临时 venv（验证后删除），依赖全量安装。

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | create_all tables | 6 张表名与 `docs/04 §7` 一致（customers / email_records / experiments / operation_logs / prompt_templates / users） | PASS |
| 2 | User CRUD | insert→select→delete；username 唯一约束生效 | PASS |
| 3 | Customer CRUD | insert 12 字段→select→update predicted_prob（0.85）→delete | PASS |
| 4 | Experiment + is_best | insert 2 条→filter_by(is_best=True) 命中 correct model→批量 delete | PASS |
| 5 | EmailRecord + relationships | er.customer.gender 与 er.creator.username 关系遍历正确 | PASS |
| 6 | OperationLog + relationship | log.user.username 关系遍历正确；details JSON 存中文 | PASS |
| 7 | PromptTemplate + is_active | insert→select by is_active→update content→delete | PASS |

**Bug 记录**：无。

**未覆盖**：外键级联删除（CASCADE/SET NULL）的实际数据库行为（smoke 仅验证了 relaciones 可遍历，未验证 delete user→log 自动删）；后续 P0-04 应用工厂 + 集成测试时补。

---

## 2026-07-30 · P0-04 应用工厂 smoke test（临时 venv）

**环境**：Python 3.12.10 临时 venv（验证后删除），依赖全量安装。

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | `create_app()` 无异常 | 应用工厂完整链路：蓝图注册→`teardown`→异常处理器→`create_all`→seed | PASS |
| 2 | 6 表建表 | `inspect(engine).get_table_names()` 返回 customers/email_records/experiments/operation_logs/prompt_templates/users | PASS |
| 3 | admin seed | `admin` 用户存在，`role=admin`，`password_hash` 长度 60（bcrypt） | PASS |
| 4 | Prompt seed | 默认模板 `is_active=True`，`content` 含 `{gender}` 等占位符，长度 230 | PASS |
| 5 | `GET /` 200 | Flask test client 返回 200，`Content-Type: text/html` | PASS |
| 6 | `GET /auth/me` 404 | 蓝图已注册但路由未实现，返回 404（`code=5000`）——预期行为，P0-05 实现后消失 | PASS |

**Bug 记录**：

- BUG-003：`_seed_admin()` 在 `create_all()` 前执行，导致 `no such table: users`。修复：调整 `create_app()` 内部顺序，`create_all` 在 seed 之前；同时 `import app.models` 确保模型提前注册。状态：已修复并回归通过。

**未覆盖**：蓝图路由逻辑（P0-05~P1-14 逐步覆盖）、`BizException` 全局 errorhandler 的 HTTP 200 与非 200 响应码行为（P0-05 接口测试覆盖）。

---

## 2026-07-30 · P0-05 认证模块 smoke test（临时 venv）

**环境**：Python 3.12.10 临时 venv（验证后删除），依赖全量安装。

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | `POST /auth/login` admin/admin123 | 正常登录，返回 JWT + `token_type=bearer` + `expires_in=86400` + `user.role=admin` | PASS |
| 2 | `POST /auth/login` 错误密码 | 统一错误信息"用户名或密码错误"，`code=1002`，HTTP 401 | PASS |
| 3 | `POST /auth/register` 新用户 alice | 注册成功，`role` 强制为 `user`，返回 JWT | PASS |
| 4 | `POST /auth/register` 重复用户名 | `code=1004`，HTTP 400 | PASS |
| 5 | `GET /auth/me` 携带 admin Token | 返回 `{id, username, role}`，`role=admin` | PASS |
| 6 | `GET /auth/me` 无 Token | `code=1002`，HTTP 401 | PASS |
| 7 | `GET /auth/me` 携带 user Token | 返回 `username=alice`，`role=user` | PASS |
| 8 | `POST /auth/logout` 携带 Token | `code=0`，`data=null`，`message="已登出"` | PASS |
| 9 | `POST /auth/register` 带 `role=admin` 字段 | `role` 被忽略，实际存储为 `user` | PASS |

**Bug 记录**：

- BUG-004：`auth.py` 末尾重复的 `bp = Blueprint(...)` 导致路由丢失，`POST /auth/login` 返回 404。修复：删除末尾重复行。状态：已修复并回归通过。

## 2026-07-31 · P0-06 前端 SPA 入口 smoke test（临时 venv）

**环境**

- OS：Windows
- Python：3.13.3（系统 Python；系统只有此版本）
- 临时 venv：`.venv_p006/`，按 P0-06 smoke 最小集安装（Flask 3.1.3 / SQLAlchemy 2.0.51 / pydantic 2.13.4 / pydantic-settings 2.14.2 / python-jose 3.5.0 / bcrypt 4.3.0）；未安装数据科学栈（pandas/numpy/scikit-learn 等），因为 P0-06 不涉及。
- 验证脚本：`work/smoke_p006.py`

**用例与结果（6/6 PASS，含 1 个本轮修复项）**

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | `GET /` | 200 / `text/html; charset=utf-8` / 含 `id="login-page"` + `id="register-page"` + `id="app-page"` | PASS |
| 2 | `GET /static/css/app.css` | 200 / `text/css; charset=utf-8` / 402B | PASS |
| 2 | `GET /static/js/api.js` | 200 / `text/javascript; charset=utf-8` / 1090B | PASS |
| 2 | `GET /static/js/app.js` | 200 / `text/javascript; charset=utf-8` / 6218B | PASS |
| 3 | Bootstrap 5.3.0 CDN | HTML 含 `bootstrap@5.3.0/dist/{css,js}` 字符串 + `urllib HEAD` 实测 200 OK | PASS |
| 4 | `/favicon.ico` 控制台噪声 | `index.html` 含 `<link rel="icon" href="data:,">`，浏览器不再发请求；server route 仍 404 但无客户端触发 | PASS（按方案 A 抑制） |
| 5 | `POST /api/v1/auth/login` admin/admin123 | 200 / `code=0` / `role=admin` / `access_token` 签发 | PASS |
| 5 | `GET /api/v1/auth/me` 携带 Bearer Token | 200 / `code=0` / `username=admin` | PASS |

**Bug 记录**

- BUG-005：`GET /favicon.ico` 在后端没有路由时返回 404，浏览器自动请求会在 DevTools 控制台产生红色错误，违反 P0-06"控制台无 404"验收。修复：方案 A —— 在 `app/static/index.html` `<head>` 加 `<link rel="icon" href="data:,">`，浏览器改用 inline 空 data URI 不再发 favicon 请求。状态：已修复并回归通过。

**环境约束备注**

- `requirements.txt` 中 `pandas==2.2.2` 在 Python 3.13 上**无 wheel**（PyPI 上 3.13 仅有 pandas 2.2.3+），pip 走 meson 源码构建又缺 `vswhere.exe`。本轮 smoke 不需要 pandas，未修改 `requirements.txt`，临时 venv 也只装后端核心 6 包。**该问题需在进入 P1-01（数据上传）前按 `DECISION.md` 流程处理**（候选：把 pandas 升到 2.2.3，或锁 Python 3.12 环境）。

**未覆盖**（按 P0 阶段惯例留到对应任务）

- SPA 各功能页面（hash 路由后的具体渲染）—— P1-15 覆盖。
- 富化后的菜单项 / RBAC 实际分支 —— P1-15 覆盖。
- 浏览器真实运行（Playwright/headless）—— P2-01 阶段或更晚引入。


## 2026-07-31 · P1-01-1 Excel 解析器 单元测试（work/smoke_p101_1.py）

**环境**：Python 3.13.3（系统） + 临时 venv `.venv_q8/`（按 DECISION-002 修订后的 requirements.txt 完整安装，Flask 3.0.3 / SQLAlchemy 2.0.51 / pydantic 2.13.4 / pandas 2.3.3 / numpy 2.5.1 / openpyxl 3.1.2 / openai 1.51.0 等 38 个 wheel 全部装上）。

**用例与结果（10/10 PASS）**：

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | 合法 10 行 xlsx | valid=10, error=0, 12 字段 ORM rename 正确 | PASS |
| 2 | 缺 Response 列 | BizException(1001)，message 列出缺失列名 | PASS |
| 3 | 2/4 行类型错（age="abc"、premium="xx"） | 错误行入 errors，其余入 rows；error 详情含 row_index + column | PASS |
| 4 | Annual_Premium=None | NaN 计入 errors，error="值缺失" | PASS |
| 5 | 空文件（0 字节） | BizException(2002) "上传文件为空" | PASS |
| 6 | 仅 header 无数据行 | total=0, valid=0, error=0 | PASS |
| 7 | 损坏字节 | BizException(2002)，pandas 报 "Excel file format cannot be determined" | PASS |
| 8 | 全部行类型错（id/age/response） | valid=0, error=3 | PASS |
| 9 | id 列小写（区别于其它 CapitalCase） | 正确解析，id=42 | PASS |
| 10 | 字段类型断言 | 12 字段全部 coerce 到正确 Python 类型（int/float/str） | PASS |

**Bug 记录**：无。

**未覆盖**（按 P1-01 拆分留到对应子任务）：
- quality_report 字段生成 → P1-01-2
- DB 写入 / bulk_insert_mappings → P1-01-3
- Service 编排 / DataService.upload() → P1-01-4
- API 路由 / 鉴权 / 扩展名校验 → P1-01-5
- 端到端 HTTP 链路（admin 登录 → 上传 → 查库）→ P1-01-6
- xlrd 引擎（.xls 文件）需补 xlrd==2.0.1+ 到 requirements.txt
- BOM 前缀处理：pd.read_excel 对 BOM 头的列名可能带 \ufeff


## 2026-07-31 · P1-01 Excel 上传模块（整体收官）

**环境**：Python 3.13.3 + 临时 venv `.venv_q8/`（按 DECISION-002 修订后的 requirements.txt 全量安装：Flask 3.0.3 / SQLAlchemy 2.0.51 / pydantic 2.13.4 / pandas 2.3.3 / numpy 2.5.1 / openpyxl 3.1.2 / scikit-learn 1.9.0 / xgboost 3.3.0 等 38 个 wheel）。

**P1-01-1 单测**（work/smoke_p101_1.py · 10/10 PASS）：合法 10 行 / 缺列 / 部分行类型错 / NaN 缺失 / 空文件 / 仅 header / 损坏字节 / 全错行 / id 小写 / 字段类型。

**P1-01-2 单测**（work/smoke_p101_2.py · 10/10 PASS）：空 12 列 DataFrame / 10 行无缺失 / 部分列缺失 / 3 行重复 / dtypes 全部 str / 混合类型 / check_required_columns 通过与失败 / read_excel_to_df 端到端 / validate_rows public API。

**P1-01-6 端到端 smoke**（work/smoke_p101.py · 7/7 PASS）：无 token 1002 / 无 file 1001 / 错扩展名 1001 / 缺列 1001 / 合法 10 行 200+DB 验证 / 二次上传覆盖 / 质量报告完整字段。

**总计：27 / 27 全绿。**

**Bug 记录**：
- BUG-006：P1-01-1 case 1 性别断言写错（Male vs Female）。修复。
- BUG-007：P1-01-2 case 4 duplicates 期望值写错（3 vs 2，keep='first'）。修复。
- BUG-008：P1-01-2 empty DataFrame 列数 0。修复：_make_df 加 columns 参数。
- BUG-009：P1-01-6 case 7 Age 含 NaN → pandas 推断 float64 而非 int64。修复：换用 id 列。
- BUG-010：P1-01-6 case 7 openpyxl 把 30001.0 存为整数 → pandas 读为 int64。修复：测试接受 int/float 任一；生产代码 compute_quality_report 不受影响。

**未覆盖**（P1 后续任务）：
- /data/customers 分页查询 → P1-02
- /data/statistics / /data/quality / /data/visualization → P1-03
- 38 万行 / 5000 一批 / < 60s 性能基线 → 需真实数据集才能测
- xlrd 引擎（.xls 文件）→ 需补 xlrd 到 requirements
- BOM 前缀处理 → P1-15 前端集成时
- 文件大小限制（mimetype 检测 / magic number）→ P1-15 / P2-08


## 2026-07-31 · P1-02 客户分页查询 端到端 smoke（work/smoke_p102.py）

**环境**：Python 3.13.3 + 临时 venv `.venv_q8/`（沿用 P1-01 同一 venv）。

**用例与结果（10/10 PASS）**：

| # | 用例 | 覆盖点 | 结果 |
| --- | --- | --- | --- |
| 1 | page=1 per_page=10 | total=25, pages=3, ids=1..10, item 15 字段齐全 | PASS |
| 2 | page=2 per_page=10 | ids=11..20 | PASS |
| 3 | gender=Female | total=13, 全部 Female | PASS |
| 4 | age_min=40 | total=6 (age>=40) | PASS |
| 5 | age_max=25 | total=5 (age<=25) | PASS |
| 6 | previously_insured=1 | total=13 | PASS |
| 7 | keyword=5 | total=1, id=5 | PASS |
| 8 | per_page=500 | cap 到 200, 25 条全返回 | PASS |
| 9 | empty data | total=0, pages=0, items=[] | PASS |
| 10 | 非法参数（4 种） | 1001 | PASS |

**Bug 记录**：
- BUG-011：P1-01 收官后追加 P1-02 块时，data_service.py 出现两个 `class DataService:` 定义，第二个空类覆盖第一个含 upload 的类，导致 P1-01-6 端到端 smoke 全部 500。修复：合并为一个类。状态：已修复并回归通过（P1-01-1/2/6 + P1-02 共 37/37 全绿）。

**P1 累计 smoke**：P1-01-1 (10) + P1-01-2 (10) + P1-01-6 (7) + P1-02 (10) = **37/37 全绿**。

**未覆盖**（P1 后续任务）：
- /data/statistics / /data/quality / /data/visualization → P1-03
- 38 万行 count + 分页性能基线（当前测 25 行）→ 需真实数据集
- 索引优化（age_min/max / previously_insured 走 B-Tree 索引）→ P2 优化


## 2026-07-31 · P1-03 数据统计 / 质量 / EDA 可视化 端到端 smoke（work/smoke_p103.py）

**环境**：Python 3.13.3 + 临时 venv `.venv_q8/`（沿用 P1-01 同一 venv，含 matplotlib 3.11.1）。

**用例与结果（10/10 PASS）**：

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
| 10 | viz/foobar | 1001 + message 含未知类型名 | PASS |

**Bug 记录**：
- BUG-012：第二度踩到 BUG-011。DataService 末尾追加 P1-03 时新建 class 覆盖旧类。修复：彻底重写为一个类。已加自我提示。
- BUG-013：P1-03 case_2 留了两行 max 断言（50/45）。修复：删 50。
- BUG-014：P1-03 case_4 断言 missing 全 0，但 predicted_prob 默认 None → 25 次缺失。修复：分列断言。

**P1 累计 smoke**：P1-01-1 (10) + P1-01-2 (10) + P1-01-6 (7) + P1-02 (10) + P1-03 (10) = **47/47 全绿**。

**未覆盖**（P1 后续任务）：
- 38 万行 quality/visualization 性能基线（当前测 25 行）→ 需真实数据集
- 中文字体 / 美化 → P2-07
- 上传时持久化质量报告 → P2 优化（避免每次 quality 接口全表扫）

---

## P1-04 模型训练 · 测试报告

**环境**：Windows / Python 3.13.3 / `.venv_q8`（Flask 3.0.3、SQLAlchemy 2.0.51、scikit-learn 1.9.0、xgboost 3.3.0、pandas 2.3.3、numpy 2.5.1）
**入口**：`& ".venv_q8\Scripts\python.exe" work\smoke_p104.py`
**数据**：600 条合成客户，正样本约 13%，标签与 `previously_insured` / `vehicle_damage` / `age` 有真实相关性

### 用例结果（13/13 PASS）
| # | 用例 | 断言 | 结果 |
| --- | --- | --- | --- |
| 1 | 无数据训练 | code=2001 | PASS |
| 2 | 特征编码 | Male=0、`> 2 Years`=2、Yes=1、feature_names==FEATURE_NAMES | PASS |
| 3 | 非法车龄 | BizException.code=1001 | PASS |
| 4 | 普通用户 | HTTP 403 / code=1003 | PASS |
| 5 | 未带 Token | code=1002 | PASS |
| 6 | models=["svm"] | code=1001 | PASS |
| 7 | test_size=0.9 | code=1001 | PASS |
| 8 | 三模型训练 | results 含 3 个算法，best_model 在其中；耗时 1.95s | PASS |
| 9 | 指标与选优 | 5 指标齐全、AUC∈[0,1]、best=AUC 最大者、最佳 AUC>0.6 | PASS |
| 10 | 落库 | experiments=3 行、is_best 唯一、params JSON 四个 key 完整且长度一致 | PASS |
| 11 | 落盘 | ≥3 个 .joblib，每个含 model 与 scaler | PASS |
| 12 | 二次训练 | 4 行记录、is_best 仍唯一 | PASS |
| 13 | 操作日志 | operation_logs 中 model_training 2 条 | PASS |

### 回归
P1-01-1 10/10、P1-01-2 10/10、P1-01 端到端 7/7、P1-02 10/10、P1-03 10/10 —— `data_processor.py` 追加 `prepare_features` 后既有解析链路无回归。

**P1 累计 smoke：60/60（10+10+7+10+10+13）全绿。**

### Bug 记录
本轮 0 新增 Bug（编号仍至 BUG-014）。

### 未覆盖
- 38 万行真实数据集的训练耗时与 AUC 未实测。
- `params` 覆盖超参（如 `{"xgboost":{"n_estimators":50}}`）只做了类型校验，未做端到端生效断言。
- LR 的 `feature_importances` 走 `coef_` 绝对值分支，未单独断言数值合理性。

---

## P1-05 实验记录 / 最佳模型查询 · 测试报告

**环境**：Windows / Python 3.13.3 / `.venv_q8`（Flask 3.0.3、SQLAlchemy 2.0.51、scikit-learn 1.9.0、xgboost 3.3.0）
**入口**：`& ".venv_q8\Scripts\python.exe" work\smoke_p105.py`
**数据**：500 条合成客户（标签与 previously_insured / vehicle_damage / age 相关），训练两轮共产生 4 条实验记录

### 用例结果（20/20 PASS）
| # | 用例 | 断言 | 结果 |
| --- | --- | --- | --- |
| 1 | 未训练查 /best | code=3002 | PASS |
| 2 | 未训练查 /experiments | items=[]、total=0、pages=0、HTTP 200 | PASS |
| 3 | /experiments 无 Token | code=1002 | PASS |
| 4 | /best 无 Token | code=1002 | PASS |
| 5 | 训练第 1 轮（三模型） | code=0 | PASS |
| 6 | 训练第 2 轮（仅 LR） | code=0 | PASS |
| 7 | 分页首页 | per_page=3 → 3 条、total=4、pages=2、page=1 | PASS |
| 8 | 分页第 2 页 | 1 条且与首页 id 无交集 | PASS |
| 9 | items 字段 | 11 字段与 docs §3.2 一致 | PASS |
| 10 | params 可复现性 | fpr/tpr 等长且 >1 点；CM 为 2x2；importances 与 feature_names 均 10 项 | PASS |
| 11 | model_name 过滤 | total=2 且全部为 logistic_regression | PASS |
| 12 | 非法 model_name | code=1001 | PASS |
| 13 | per_page=999 | 截断为 200 | PASS |
| 14 | page=abc | code=1001 | PASS |
| 15 | page=0 | code=1001 | PASS |
| 16 | /best 结构与一致性 | 三字段恰好；experiment_id / model_name / roc_auc 与 DB is_best 行逐项相符 | PASS |
| 17 | is_best 唯一性 | 4 条记录中恰 1 条 is_best | PASS |
| 18 | /best 选优正确 | roc_auc == 全部实验最大值 | PASS |
| 19 | 普通用户权限 | 两接口均 code=0（docs 未限 admin） | PASS |
| 20 | 排序稳定性 | id 序列严格倒序 | PASS |

### 回归
P1-01-1 10/10、P1-01-2 10/10、P1-01 端到端 7/7、P1-02 10/10、P1-03 10/10、P1-04 13/13、上传限制 10/10 全部通过。

**累计 smoke：80/80（10+10+7+10+10+13+10+20）全绿。**
**验收脚本 `work/acceptance_p1_data.py`：34/37**（余 3 项 `uploaded_by` / `customers.py` 复数命名 / `Customer.bulk_create` 为已确认保留的 docs 冲突项）。

### Bug 记录
本轮 0 新增 Bug（编号仍至 BUG-015）。

**排序缺陷的提前规避**：SQLite `func.now()` 精度到秒，同一次训练写入的 3 条记录 `created_at` 完全相同。若仅按 `created_at` 单列倒序，分页边界记录会漂移并出现跨页重复。实现时已加 `id` 倒序兜底，用例 8（跨页无重叠）与用例 20（全局有序）专门覆盖此风险。

### 未覆盖
- 单页超过 200 条实验记录的翻页压力未测（当前最多 4 条）。
- `params` 在 38 万行数据下的 ROC 点数膨胀（数万点）对响应体积的影响未实测。
- `is_best` 存在多条 `True` 的脏数据场景未构造（`/best` 已用 `first()` 而非 `one()` 做防御）。

---

## P1-06 全量预测 · 测试报告

**环境**：Windows / Python 3.13.3 / `.venv_q8`
**入口**：`& ".venv_q8\Scripts\python.exe" work\smoke_p106.py`
**数据**：400 条合成客户，训练三模型后预测

### 用例结果（18/18 PASS）
| # | 用例 | 断言 | 结果 |
| --- | --- | --- | --- |
| 1 | 未训练即预测 | code=3002 | PASS |
| 2 | 无 Token | code=1002 | PASS |
| 3 | model_name="  " | code=1001 | PASS |
| 4 | model_name=123 | code=1001 | PASS |
| 5 | model_name="svm" | code=1001 | PASS |
| 6 | 训练 | code=0 | PASS |
| 7 | 预测前状态 | predicted_prob 全 NULL（400 行） | PASS |
| 8 | 缺省预测 | model_name==best_model、predicted_count=400、data 恰两字段 | PASS |
| 9 | 回写完整性 | 无 NULL 残留 | PASS |
| 10 | 概率范围 | 全部 ∈ [0,1] | PASS |
| 11 | 概率有效性 | 不同值 >10 个（非常量输出） | PASS |
| 12 | **scaler 复用** | 手工 `model.predict_proba(scaler.transform(X))` 与库中值逐行比对 max_diff<1e-9 | PASS |
| 13 | 指定模型 | model_name=logistic_regression 生效 | PASS |
| 14 | 覆盖回写 | 回写值与指定模型的输出逐行一致 | PASS |
| 15 | 未训练的模型名 | code=3002 | PASS |
| 16 | 模型文件丢失 | code=3002 | PASS |
| 17 | 无客户数据 | code=2001 | PASS |
| 18 | 操作日志 | operation_logs 中 prediction 2 条 | PASS |

用例 12 是本轮最关键的断言：它证明预测期复用了训练时持久化的 scaler 而非重新 fit，正是 docs/02 §2.6 反复强调的一致性约束。

### 回归
P1-01-1 10/10、P1-01-2 10/10、P1-01 端到端 7/7、P1-02 10/10、P1-03 10/10、P1-04 13/13、P1-05 20/20、上传限制 10/10 全部通过。

**累计 smoke：98/98（10+10+7+10+10+13+20+18+10）全绿。**
**验收脚本：34/37**（余 3 项为已确认保留的 docs 冲突项）。

### Bug 记录
**BUG-016 · 测试可重复性缺陷（已修复）**
- 现象：`smoke_p104` 用例 13、`smoke_p106` 用例 18 的日志计数断言间歇性失败，实测值从 2 逐轮涨到 4、6、7。
- 根因：两个脚本依赖外部 `Remove-Item instance\insurance.db` 重置状态。Windows 下该文件被 5 个残留 `.venv_q8` python 进程持有句柄，删除操作因 `-ErrorAction SilentlyContinue` 静默失败，`operation_logs` 于是跨轮累积。
- 修复：脚本启动时自行 `delete()` 所用表（含按 action 过滤清理 `operation_logs`），不再依赖删文件。
- 验证：连续运行两遍均 13/13 与 18/18。
- 影响面：仅测试脚本，生产代码无涉。

### 未覆盖
- 38 万行规模的预测耗时与回写性能未实测。
- 模型文件存在但内容损坏（非 joblib 格式）的场景未构造，`_load_bundle` 已做异常捕获与结构校验。
- 并发预测（多请求同时回写同一批 `predicted_prob`）未测。

---

## P1-07 上传数据预测 · 测试报告

**环境**：Windows / Python 3.13.3 / `.venv_q8`
**入口**：`& ".venv_q8\Scripts\python.exe" work\smoke_p107.py`
**数据**：库内 400 条训练数据 + 上传批次 30 条（id 9001~9030，与库内 id 1~400 不重叠，便于验证不入库）

### 用例结果（23/23 PASS）
| # | 用例 | 断言 | 结果 |
| --- | --- | --- | --- |
| 1 | 未训练即预测 | code=3002 | PASS |
| 2 | 无 Token | code=1002 | PASS |
| 3 | 训练 | code=0 | PASS |
| 4 | 未上传文件 | code=1001 | PASS |
| 5 | .txt 扩展名 | code=1001 | PASS |
| 6 | 损坏 Excel | code=2002 | PASS |
| 7 | 缺 Vehicle_Age 列 | code=1001 | PASS |
| 8 | model=svm | code=1001 | PASS |
| 9 | 响应结构 | data 恰 {model_name,total_count,statistics,predictions}；model_name==best_model；total_count=30 | PASS |
| 10 | predictions 元素 | 长度 30，字段恰 {id, predicted_prob} | PASS |
| 11 | 概率有效性 | 全部 ∈[0,1]，不同值 >5 | PASS |
| 12 | 排序 | 严格按 predicted_prob 倒序 | PASS |
| 13 | id 透传 | 返回 id 集合 == {9001..9030} | PASS |
| 14 | statistics 自洽 | 六字段齐全；min≤mean≤max；min/max 与 predictions 吻合；1≤high_potential_count≤30 | PASS |
| 15 | 分位数阈值 | high_potential_threshold == 全精度概率的 np.quantile(0.9)，误差 <1e-9 | PASS |
| 16 | **不入库** | customers 行数 400、predicted_prob NULL 数 400、最大 id 400 三项均未变 | PASS |
| 17 | scaler 复用 | 与手工 `predict_proba(scaler.transform(X))` 逐行比对 max_diff<1e-6 | PASS |
| 18 | 无标签列 | 不含 Response 时仍 code=0、total_count=8 | PASS |
| 19 | 无 id 列 | 返回 id 为 1-based 行号 [1..6] | PASS |
| 20 | 指定模型 | model=logistic_regression 生效 | PASS |
| 21 | model 空白串 | code=1001 | PASS |
| 22 | 模型文件丢失 | code=3002 | PASS |
| 23 | 操作日志 | prediction 日志 4 条（每次成功一条） | PASS |

用例 16 是本轮核心断言：docs/03 §3.5 明确「不入库，不覆盖训练数据」，故从三个角度交叉验证库内数据完全未受影响。

### 回归
P1-01-1 10/10、P1-01-2 10/10、P1-01 端到端 7/7、P1-02 10/10、P1-03 10/10、P1-04 13/13、P1-05 20/20、P1-06 18/18、上传限制 10/10 全部通过。

`_resolve_experiment` 重构后单独重跑 P1-06 确认 18/18，验证提取共用逻辑未影响 `/predict`。

**累计 smoke：121/121（10+10+7+10+10+13+20+18+23+10）全绿。**
**验收脚本：34/37**（余 3 项为已确认保留的 docs 冲突项）。

### Bug 记录
本轮 0 生产代码缺陷（编号仍至 BUG-016）。

**测试脚本自身修正**：case 15 起初在已 `round(6)` 的 predictions 上重算 0.9 分位数，与服务端"先算分位数再舍入"顺序不同，产生 1e-6 偏差导致误报（api=0.968156 vs expect=0.968157）。已改为在全精度概率数组上比对并加注释说明。属断言不严谨，非实现问题。

### 未覆盖
- 上传 38 万行的响应体积与耗时未实测（`predictions` 全量返回，估算 JSON 约 30MB+）。
- Excel 含额外无关列时的容忍度未专门断言（`prepare_features` 只取 FEATURE_NAMES，理论上多余列被忽略）。
- 上传批次全部为同一取值导致概率完全相同时，`high_potential_count` 会等于总数的边界未构造。

---

## P1-08 模型评估可视化 · 测试报告

**环境**：Windows / Python 3.13.3 / `.venv_q8`（matplotlib 3.11.1，Agg 后端）
**入口**：`& ".venv_q8\Scripts\python.exe" work\smoke_p108.py`
**数据**：400 条合成客户，训练一次产生 3 条实验；全部图表由 `experiments.params` 复原

### 用例结果（23/23 PASS）
| # | 用例 | 断言 | 结果 |
| --- | --- | --- | --- |
| 1 | 无实验时 roc_curve | code=3002 | PASS |
| 2 | 无实验时 confusion_matrix | code=3002 | PASS |
| 3 | 无 Token | code=1002 | PASS |
| 4 | 训练 | code=0 | PASS |
| 5 | chart_type=nope | code=1001 | PASS |
| 6 | confusion_matrix 缺 model | code=1001 | PASS |
| 7 | feature_importance 缺 model | code=1001 | PASS |
| 8 | model=svm | code=1001 | PASS |
| 9 | roc_curve | data 恰三字段、format=png、base64 解码为合法 PNG 且 >3KB | PASS |
| 10 | metrics_comparison | 同上 | PASS |
| 11-13 | confusion_matrix × LR/RF/XGB | 均返回真 PNG | PASS |
| 14-16 | feature_importance × LR/RF/XGB | 均返回真 PNG | PASS |
| 17 | **不重新训练** | 调用 8 次图表后 experiments 仍 3 条、predicted_prob 仍 400 个 NULL | PASS |
| 18 | 图像差异性 | 5 个不同图表产出 5 张互不相同的 base64 | PASS |
| 19 | 幂等性 | 同一请求两次返回完全相同的 base64 | PASS |
| 20 | 删除 RF 实验后取其图 | code=3002 | PASS |
| 21 | params 置为 `"{not-json"` | code=3002（非 500） | PASS |
| 22 | 普通用户 | code=0（docs §3.6 未限 admin） | PASS |
| 23 | **P1-03 回归** | 4 个 EDA 图表接口仍全部 code=0 | PASS |

### 图像内容核验（超出 magic bytes 的额外验证）
仅校验 PNG 头部无法排除「合法但空白的画布」。额外导出四张图用 `matplotlib.image` 逐像素统计：

| 图表 | 尺寸 | 非白像素占比 | 不同颜色数 | 判读 |
| --- | --- | --- | --- | --- |
| roc_curve | 625x508 | 6.59% | 490 | 多条曲线叠加 + 基线虚线 |
| metrics_comparison | 613x450 | 42.28% | 276 | 柱体填充完整 |
| confusion_matrix | 511x439 | 34.24% | 1272 | 热力图渐变 + colorbar |
| feature_importance | 759x407 | 5.35% | 260 | 10 条横向条形 |

四张图均有实质内容，非空白。核验用临时目录 `work/charts_p108/` 已清理。

### 回归
P1-01-1 10/10、P1-01-2 10/10、P1-01 端到端 7/7、P1-02 10/10、P1-03 10/10、P1-04 13/13、P1-05 20/20、P1-06 18/18、P1-07 23/23、上传限制 10/10 全部通过。

**累计 smoke：144/144（10+10+7+10+10+13+20+18+23+23+10）全绿。**
**验收脚本：34/37**（余 3 项为已确认保留的 docs 冲突项）。

### Bug 记录
本轮 0 新增 Bug（编号仍至 BUG-016）。

### 未覆盖
- 中文标题渲染未测（当前全英文标签，matplotlib 默认字体无中文字形，属 P2-07 范围）。
- 38 万行训练产生的数万点 ROC 曲线绘图耗时与内存未实测。
- `feature_importances` 与 `feature_names` 长度不一致的脏数据场景未构造（Service 已做长度校验并抛 3002）。
- 图表视觉美观度未做人工评审，仅做了像素级非空与色彩多样性的自动核验。

---

## P1-09 模型导入 / 导出 · 测试报告

**环境**：Windows / Python 3.13.3 / `.venv_q8`（joblib 1.5.2，scikit-learn / xgboost 同 P1-04）
**入口**：`& ".venv_q8\Scripts\python.exe" work\smoke_p109.py`
**数据**：400 条合成客户，训练一次产生 3 个 joblib 文件
**状态重置**：脚本启动时自行 `delete()` customers / experiments / operation_logs 并清空 `MODEL_DIR`，不依赖删 db 文件（BUG-016 教训）

### 用例结果（25/25 PASS）
| # | 用例 | 断言 | 结果 |
| --- | --- | --- | --- |
| 1 | 训练前导出 | code=3002 | PASS |
| 2 | 导出无 Token | code=1002 | PASS |
| 3 | 导入无 Token | code=1002 | PASS |
| 4 | 普通用户导出 | HTTP 403 / code=1003 | PASS |
| 5 | 普通用户导入 | HTTP 403 / code=1003 | PASS |
| 6 | 训练 | code=0（全程只训练这一次） | PASS |
| 7 | 导出 logistic_regression | HTTP 200、`Content-Disposition: attachment`、body 非空 | PASS |
| 8 | 导出字节流可用性 | 落盘后 `joblib.load` 成功且含 model+scaler 双键 | PASS |
| 9 | 三算法导出 | LR / RF / XGB 均 HTTP 200 且字节流合法 | PASS |
| 10 | 穿越 `..%2f..%2f.env` | 非 200，且 `.env` 未被读出 | PASS |
| 11 | 穿越 `....//....//.env` | 同上 | PASS |
| 12 | 穿越 `%2e%2e%2f.env` | 同上 | PASS |
| 13 | 导出 `unknown_model` | code=1001 | PASS |
| 14 | 导入不带 file | code=1001 | PASS |
| 15 | 导入 `a.txt` | code=1001 | PASS |
| 16 | 导入伪造 `.joblib`（内容为随机字节） | code=1001（非 500） | PASS |
| 17 | 导入只含 model 无 scaler 的 bundle | code=1001 | PASS |
| 18 | 导入 `DecisionTreeClassifier` bundle | code=1001（不在白名单） | PASS |
| 19 | **失败导入的副作用** | 用例 15-18 之后 `MODEL_DIR` 无 `.import_tmp_*` 文件，且原 LR 模型仍可加载预测 | PASS |
| 20 | 导出→导入往返 | code=0，data 恰 `{model_name, path}` 两字段 | PASS |
| 21 | **落盘名推断** | 上传文件名改为 `evil_name.joblib`，落盘仍为 `logistic_regression.joblib` | PASS |
| 22 | 落盘位置 | `os.path.commonpath` 确认目标在 `MODEL_DIR` 内 | PASS |
| 23 | 导入后可用性 | 紧接 `POST /model/predict` 返回 code=0 且回写 400 行 | PASS |
| 24 | 操作日志 | `operation_logs` 中 `model_import` 恰 1 条（只记成功那次） | PASS |
| 25 | 临时文件终态 | 全部用例结束后 `MODEL_DIR` 无 `.import_tmp_*` 残留 | PASS |

### 安全用例说明
目录穿越三组用例覆盖了不同的编码层次：`..%2f` 测 URL 解码后拼接、`....//` 测朴素的「去掉 `../`」式过滤能否被绕过、`%2e%2e%2f` 测点号本身被编码的情形。三者均在 `SUPPORTED_MODELS` 白名单处即被拦下，`commonpath` 复核是第二道防线。断言不只看状态码，还确认响应体里不含 `.env` 的内容特征，避免「返回了 200 但其实是另一个文件」的漏检。

### 幂等性
P1-09 smoke 连续运行两遍，两次均 25/25，`operation_logs` 计数断言稳定为 1，无跨轮累积。

### 回归
P0-06 6/6、P1-01-1 10/10、P1-01-2 10/10、P1-01 端到端 7/7、P1-02 10/10、P1-03 10/10、P1-04 13/13、P1-05 20/20、P1-06 18/18、P1-07 23/23、P1-08 23/23、上传限制 10/10 全部通过。

**累计 smoke：169/169（10+10+7+10+10+13+20+18+23+23+25+10）全绿。**
**验收脚本：34/37**（余 3 项为已确认保留的 docs 冲突项：`uploaded_by` 字段、`customers.py` 复数命名、`Customer.bulk_create`）。

### Bug 记录
本轮 0 新增 Bug（编号仍至 BUG-016）。

### 未覆盖
- 未测导入特征数与当前 `FEATURE_NAMES` 不匹配的模型（错误会推迟到 `/predict` 才暴露，见开发日志遗留项）。
- 未测超大 joblib 文件（>50MB）导入是否触发 `MAX_CONTENT_LENGTH` 的 413 → code=1001；理论上会走 DECISION-004 的处理器，但未构造该规模的模型文件。
- 未测并发导入同一模型名的竞态。`os.replace` 本身原子，但两个请求交错时最终落盘的是哪一个不确定。教学场景无并发要求。
- 未测磁盘写满时 `file_storage.save` 失败的路径。

---

## P1-10 高潜客户筛选 · 测试报告

**环境**：Windows / Python 3.13.3 / `.venv_q8`（numpy 2.x）
**入口**：`& ".venv_q8\Scripts\python.exe" work\smoke_p110.py`
**数据**：400 条合成客户，`predicted_prob = i/400`（i=1..400）—— 概率在 (0,1] 上均匀分布，使分位数可手工精确复算
**状态重置**：脚本启动时自行 `delete()` customers / experiments / operation_logs，不依赖删 db 文件（BUG-016 教训）

### 用例结果（23/23 PASS）
| # | 用例 | 断言 | 结果 |
| --- | --- | --- | --- |
| 1 | 无 Token | code=1002 | PASS |
| 2 | 空表 | code=3002 | PASS |
| 3 | 有客户、概率全 NULL | code=3002 | PASS |
| 4 | 默认调用 | code=0 | PASS |
| 5 | 响应结构 | data 键恰为 `{threshold,total,customers}`（docs §4.1，非项目通用分页结构） | PASS |
| 6 | **阈值正确性** | 返回 threshold 与 `np.quantile(probs,0.9)` 差值 <1e-9 | PASS |
| 7 | 命中数 | total 等于手工统计 `sum(p >= threshold)`，含边界 | PASS |
| 8 | 默认分页 | per_page 默认 20，返回 20 条 | PASS |
| 9 | 字段裁剪 | customers 键恰为 id/gender/age/annual_premium/predicted_prob | PASS |
| 10 | 排序 | predicted_prob 降序 | PASS |
| 11 | 排序正确性 | 首条等于全表最大概率 | PASS |
| 12 | 过滤正确性 | 每条均 >= threshold | PASS |
| 13 | 翻页 | page=2 与 page=1 的 id 集合无交集，且首条概率 <= page=1 末条 | PASS |
| 14 | total 稳定 | 跨页 total 恒定 | PASS |
| 15 | percentile=0.5 | 阈值低于 0.9 时的阈值，命中数更多 | PASS |
| 16 | **单调性** | percentile 取 0.99→0.9→0.5→0.1，total 单调递增 | PASS |
| 17 | 分页上限 | per_page=999 实际返回 <=200 | PASS |
| 18 | percentile 非法值 | `0` / `1` / `-0.5` / `1.5` / `abc` / `nan` / `inf` 全部 code=1001 | PASS |
| 19 | 分页非法值 | `page=abc` / `page=0` / `per_page=0` / `per_page=xyz` 全部 code=1001 | PASS |
| 20 | **NULL 隔离** | 将 id<=200 置 NULL 后，阈值等于剩余 200 行的中位数，结果中无 NULL | PASS |
| 21 | 普通用户 | code=0（docs §4 未限 admin） | PASS |
| 22 | 幂等 | 同一请求两次返回完全相同的 data | PASS |
| 23 | **只读** | 调用前后 customers 与 operation_logs 行数不变 | PASS |

### 阈值断言的强度说明
只断言"返回了某个 0~1 之间的 threshold"无法证明用的是分位数 —— 固定阈值 0.5 也能通过。因此本轮用可精确复算的均匀分布概率（`i/400`），把返回值与 `np.quantile` 比对到 1e-9；再用单调性用例（16）交叉验证 percentile 参数真的在起作用。两者合起来才能排除"参数被忽略、实际用了硬编码阈值"这种假通过。

### 集成校验（独立脚本）
`work/smoke_p110_integration.py`：seed 400 行 → train → predict → targets。

| 步骤 | 结果 |
| --- | --- |
| `POST /model/train` | code=0 |
| `POST /model/predict` | code=0，`{model_name: xgboost, predicted_count: 400}` |
| `GET /email/targets` | code=0，threshold=0.9625437915、total=40（正好 top 10%） |
| top3 概率 | 0.9961 / 0.9940 / 0.9934（降序，符合预期） |

确认接口在真实 XGBoost 输出的概率分布（偏两端）上同样给出正确的 top 10%。

### 幂等性
P1-10 smoke 连续运行两遍，两次均 23/23，无跨轮状态污染。

### 回归
P0-06 6/6、P1-01-1 10/10、P1-01-2 10/10、P1-01 端到端 7/7、P1-02 10/10、P1-03 10/10、P1-04 13/13、P1-05 20/20、P1-06 18/18、P1-07 23/23、P1-08 23/23、P1-09 25/25、上传限制 10/10 全部通过。

**累计 smoke：192/192（10+10+7+10+10+13+20+18+23+23+25+23+10）全绿。**
**验收脚本：34/37**（余 3 项为已确认保留的 docs 冲突项）。

### Bug 记录
本轮 0 新增 Bug（编号仍至 BUG-016）。

### 未覆盖
- 未在 38 万行规模下实测 `predicted_probs()` 的内存与耗时（见 DEBT-P110-1）。
- 未测所有客户概率完全相同的极端情形。此时分位数等于该值，全部客户都会命中，`total` 等于总数 —— 数学上正确但业务上"top 10%"失去意义。合成数据难以自然产生，实际预测也几乎不可能。
- 未测 `predicted_prob` 恰好等于阈值的浮点边界密集场景（当前用例 12 的 `>=` 断言留了 1e-12 容差）。
- 未测并发调用（纯只读，无竞态风险）。
