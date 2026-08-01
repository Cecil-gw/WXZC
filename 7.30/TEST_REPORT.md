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
