# Code Review 规则

检查：

## 架构

是否符合分层设计

## 后端

是否：

- 路由不写业务
- service 负责业务
- model 只负责数据

## AI

检查：

- 是否数据泄漏
- scaler 是否正确

## 安全

检查：

- JWT
- 权限
- 密码

## 测试

没有测试不能完成任务。

---

# 任务级 Review 记录

时序倒序（最新在上）。每次任务完成后，按上述五个维度勾选并给出结论。

---

## 2026-07-30 · P0-01 项目脚手架与依赖

**范围**：仅工程骨架（目录树 / requirements.txt / .env.example / .gitignore），无业务代码。

| 维度 | 结果 | 说明 |
| --- | --- | --- |
| 架构 | ✅ 通过 | 目录结构严格对齐 `docs/04_技术框架方案.md §4`（app/api/v1、core、models、schemas、services、utils、static 全部就位；data/models、instance 已建）。services/utils/schemas 补 `__init__.py` 属工程实现细节，无违规。 |
| 后端 | ✅ 通过（本轮不适用业务） | 所有 `__init__.py` 均为 0 字节占位，未提前写路由/业务/模型；未破坏"路由不写业务、service 负责业务、model 只负责数据"分层。 |
| AI | ➖ 不适用 | 本任务不涉及模型/scaler/数据流。 |
| 安全 | ✅ 通过 | `.env.example` 中 `JWT_SECRET_KEY` 为占位强提示"change-me"，`LLM_API_KEY` 留空；`.gitignore` 覆盖 `.env`、`instance/`、`data/models/`、`*.log`，防止密钥与数据入仓。 |
| 测试 | ✅ 通过（工程级验证） | 本任务无业务代码，因而无单元测试；替代性验证：Python 3.12.10 临时 venv 中 `pip install --dry-run -r requirements.txt` 无冲突，`Would install` 输出 51 个包版本齐全；验证后临时 venv 已删除。 |

**结论**：P0-01 通过审查，可标记 `[x]` 完成，继续 P0-02。

**遗留 / 备注**：

- `demo1.py`（0 字节，历史遗留）保留至 P0-04 出 `run_flask.py` 时统一清理，届时按 `AI_RULES.md` 走一次变更说明。
- 目前无自动化测试文件；`tests/` 目录待 P2-01 建立，前期先靠"每任务人工验证 + `TEST_REPORT.md` 记录"覆盖。

---

## 2026-07-30 · P0-02 基础设施层 core

**范围**：`app/core/{config,database,response,security,dependencies}.py`，共 5 个文件。仅基础设施，不含路由/模型/业务。

| 维度 | 结果 | 说明 |
| --- | --- | --- |
| 架构 | ✅ 通过 | 严格对齐 `docs/04 §6.1-6.4/§8`；模块之间仅依赖 `config` → `security/database/response` → `dependencies`；未反向依赖业务/路由。 |
| 后端 | ✅ 通过 | 五件套均为纯基础设施；`response.py` 保证统一信封；`dependencies.py` 通过 `BizException` 返回错误，不在装饰器里 jsonify。装饰器可与 `login_required` 组合，也可单独使用（`role_required` 会自动补一次登录校验）。 |
| AI | ➖ 不适用 | 本任务不涉及模型/scaler/数据流。 |
| 安全 | ✅ 通过 | 密码：直接 bcrypt（`hashpw` + `checkpw`），失败异常吞掉返回 False，避免侧信道；不使用 passlib，绕过 bcrypt 4.x 兼容坑。JWT：HS256、`sub` 存 user_id、`role/username` 附带、`exp` 严格校验、篡改/过期统一抛 `TokenInvalidError`；`decode_token` 强制要求 `sub`。RBAC：默认拒绝，无 token → 1002/401，角色不匹配 → 1003/403。配置：`.env` 中 `JWT_SECRET_KEY` 默认值明确写 "change-me"，`LLM_API_KEY` 允许空并走降级路径，均在 `.gitignore` 保护范围内。 |
| 测试 | ✅ 通过（临时验证） | 一次性 smoke test 6 用例全绿；覆盖成功/失败两侧、边界（过期/篡改/未认证/越权）。首轮暴露的 SQLite 相对路径缺陷已修，避免带病进入 P0-03/04。主项目 `tests/` 目录留到 P2-01；本次验证脚本 `work/smoke_core.py` 保留在工作区，不进仓库。 |

**结论**：P0-02 通过审查，可标记 `[x]` 完成，继续 P0-03。

**遗留 / 备注**：

- `settings` 目前以模块级单例创建；如未来需要在测试里替换配置（例如切内存 SQLite），可加一个 `override_settings(**kwargs)` 辅助函数，届时再实现。
- `get_db()` 在非请求上下文返回新 Session 便于 CLI / 脚本使用，调用方需自行 `close()`；已在 docstring 注明。
- SQLite 相对路径归一化仅对 `sqlite://` 生效，MySQL/PG 保持透传；`ensure_runtime_dirs` 会在 P0-04 应用工厂中调用，本任务不主动创建目录。

---

## 2026-07-30 · P0-03 数据层 ORM 6 张表

**范围**：`app/models/{user,customer,experiment,email_record,operation_log,prompt_template}.py` + `__init__.py`，共 7 个文件。仅数据层，不含业务/路由。

| 维度 | 结果 | 说明 |
| --- | --- | --- |
| 架构 | ✅ 通过 | 严格对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md`；`Base` 统一继承自 `app.core.database.Base`；`__init__.py` 按无 FK→有 FK 顺序导入，避免 `create_all` 时字符串解析开销。 |
| 后端 | ✅ 通过 | 模型只包含表结构定义（`Mapped` + `mapped_column` + `relationship`），不写任何业务逻辑；`ondelete` 策略：`OperationLog.user_id`=CASCADE（用户删则日志清理），`EmailRecord.created_by`=SET NULL（用户删但邮件保留，creator 变空）。 |
| AI | ✅ 通过 | 为 ML 链路预留：`Customer.predicted_prob` 有索引用于排序查询；`Experiment.params` 以 Text 存 JSON（ROC/CM/特征重要性），供可视化接口反序列化复原；`Experiment.is_best` 有索引，保证 `/model/best` 查询快速。 |
| 安全 | ✅ 通过 | 密码存 `password_hash`（bcrypt 哈希），不存明文；`role` 默认 `user`，新建用户不能自选角色；`User.password_hash` 不在 `__repr__` 中泄露。 |
| 测试 | ✅ 通过（临时验证） | 7 用例全绿：`create_all` 建表名一致、User CRUD + 唯一约束、Customer 12 字段 + predicted_prob 更新、Experiment is_best 索引查询、EmailRecord 双关系遍历、OperationLog 关系 + JSON details、PromptTemplate is_active 查询。临时 venv 与产物已清理。 |

**结论**：P0-03 通过审查，可标记 `[x]` 完成，继续 P0-04。

**遗留 / 备注**：

- `PromptTemplate.is_active` 未建唯一约束，由业务层保证同一时刻仅一条 `is_active=True`；如需强制约束可后续加。
- `EmailRecord.created_by` SET NULL 策略：用户删账号后邮件记录保留但 `created_by` 为空，`GET /email/records` 需处理 `created_by_username` 为 None 的情况（P1-13 实现时处理）。
- `Customer.id` 使用数据集原始 ID（`autoincrement=False`），上传时先清空旧数据再 `bulk_insert_mappings` 覆盖，与 P1-01 的覆盖策略一致。

---

## 2026-07-30 · P0-04 应用工厂与蓝图注册

**范围**：`app/__init__.py`（`create_app`）+ `run_flask.py` + `app/api/v1/__init__.py` + 5 占位蓝图 + `app/static/index.html` + 删除 `demo1.py`。

| 维度 | 结果 | 说明 |
| --- | --- | --- |
| 架构 | ✅ 通过 | 严格对齐 `docs/04 §6.1`：应用工厂延迟创建 Flask 实例；蓝图注册按 auth/data/model/email/log 五模块；`teardown_appcontext` 自动关闭 Session；三级异常处理器从具体到宽泛；`create_all` 在 `app.app_context()` 内执行。 |
| 后端 | ✅ 通过 | 占位蓝图仅定义 `Blueprint` 对象，不写业务逻辑；`create_app` 内部流程清晰（目录→蓝图→钩子→异常→seed）；`run_flask.py` 从 `settings` 读取配置，与代码解耦。 |
| AI | ➖ 不适用 | 本任务不涉及模型/scaler/数据流。 |
| 安全 | ✅ 通过 | `_seed_admin` 仅首次创建，不重复；密码使用 `hash_password`（bcrypt）存储，不存明文；`_seed_prompt_template` 仅首次创建，不重复。 |
| 测试 | ✅ 通过（临时验证） | 临时 venv 验证：6 表建表、admin 用户 seed（bcrypt 哈希 60 位）、Prompt 模板 seed（含占位符）、`GET /` 200、`/auth/me` 404（code=5000，路由未实现正确行为）。 |

**结论**：P0-04 通过审查，可标记 `[x]` 完成，继续 P0-05。

**遗留 / 备注**：

- `GET /` 当前返回 `app/static/index.html`（最小占位），P0-06 富化为完整 SPA 入口。
- `/auth/me` 返回 404（code=5000）是预期行为——蓝图已注册，路由未实现，P0-05 实现后消失。
- `_seed_admin` 与 `_seed_prompt_template` 在 `create_app` 内用 `SessionLocal` 而非 `get_db()`，因为不在请求上下文中。
- `create_app` 无参数，测试环境多实例切换可后续加 `config_overrides` 参数。

---

## 2026-07-30 · P0-05 认证模块 `/auth`

**范围**：`app/schemas/auth.py` + `app/services/auth_service.py` + `app/api/v1/auth.py`（重写），共 3 个文件。

| 维度 | 结果 | 说明 |
| --- | --- | --- |
| 架构 | ✅ 通过 | 严格遵守分层：路由只做参数校验 + 调 service；service 只做业务编排 + 调模型；schema 只做请求体定义；`AuthService` 纯函数不依赖 Flask。 |
| 后端 | ✅ 通过 | 路由不写业务逻辑（`AuthService.login/register` 封装）；Pydantic 校验统一经 `_validate` 转 `BizException(1001)`；`/register` 不接收 role，`RegisterRequest` 无 role 字段但 Pydantic `extra="ignore"` 模式下多余字段被忽略（实测 role 字段被静默丢弃）。 |
| AI | ➖ 不适用 | 本任务不涉及模型/scaler/数据流。 |
| 安全 | ✅ 通过 | 密码：bcrypt 哈希存储，登录失败统一"用户名或密码错误"（防用户名枚举）；JWT：`create_access_token` 含 `sub`/`role`/`username`/`exp`；`/me` 与 `/logout` 均 `@login_required`；`/register` role 硬编码 `user`，Pydantic 不接收 role 字段。 |
| 测试 | ✅ 通过（临时验证） | 9 用例全绿：登录成功/失败、注册/重名、`/me` 带/无 Token、user token `/me`、logout、role 越权注册。 |

**结论**：P0-05 通过审查，可标记 `[x]` 完成，继续 P0-06。

**遗留 / 备注**：

- `RegisterRequest` 未显式设置 `model_config = ConfigDict(extra="forbid")`，因此多余字段（如 `role`）被静默忽略而非报错。当前行为符合 PRD 需求（role 硬编码 user），但若要严格拒绝未知字段（如前端误传 `role` 时给出明确提示），可后续加 `extra="forbid"`。
## 2026-07-31 · P0-06 前端 SPA 入口

**范围**：仅 `app/static/index.html`（最小化修改：在 `<head>` 增加 1 行 `<link rel="icon" href="data:,">`）。未触及 `app/static/css/app.css` / `js/api.js` / `js/app.js`（P1-15 范围）。

| 维度 | 结果 | 说明 |
| --- | --- | --- |
| 架构 | ✅ 通过 | 严格对齐 `docs/04 §4` 目录约定（`app/static/{index.html,css/,js/}`），入口由 `app/__init__.py` 中 `GET /` 路由 `send_static_file("index.html")` 提供。Bootstrap 5.3.0 通过 jsDelivr CDN 加载，无构建步骤，符合"前端 SPA + hash 路由"约定。P0-06 范围仅 `index.html`；其余 3 个静态文件已存在但归 P1-15 富化范围。 |
| 后端 | ✅ 通过 | 本轮零后端改动；前端逻辑（fetch 封装、token 注入、登录/注册/退出、菜单渲染、hash 路由）位于 `app/static/js/app.js` + `api.js`，P0-06 仅保证"不 404"，具体业务 P1-15 富化。 |
| AI | ➖ 不适用 | 本任务不涉及模型/数据流。 |
| 安全 | ✅ 通过 | `api.js` 在响应 `code=1002`（token 失效）时自动 `clearToken()`，避免脏 token 残留；登录错误信息统一从后端 `message` 字段读取，不在前端硬编码；favicon 抑制采用 inline `data:,` 不引入任何外部域，无 CSP 风险。本轮未涉及 cookie / session，纯 JWT。 |
| 测试 | ✅ 通过（临时验证） | `work/smoke_p006.py` 6 用例全绿：GET / 200 + 3 个本地资源 200 + Bootstrap CDN 实测 200 + favicon 噪声抑制 + 端到端登录（admin/admin123 → /me）。临时 venv + smoke 产物已清理。 |

**结论**：P0-06 通过审查，可标记 `[x]` 完成，**P0 全部 6 项收官**。

**遗留 / 备注**：

- `app/static/{css/app.css, js/api.js, js/app.js}` 文件已存在但**内容属于 P1-15 范畴**（api.js 已实现 token 注入；app.js 已实现登录/注册/退出/菜单/hash 路由）。P1-15 时按 PRD 8 条验收全链路富化（admin 11 项、user 7 项菜单，以及各功能页面的实际渲染）。当前 admin 15 项 / user 11 项是占位菜单，最终 RBAC 数量以 P1-15 为准。
- 浏览器真实渲染（Playwright 截图）覆盖留到 P2-01 或 P1-15 联调阶段。
- 环境约束（Py3.13 与 `pandas==2.2.2` wheel 不兼容）需在进入 P1-01 前按 `DECISION.md` 流程处理。
- favicon 当前用 inline `data:,` 抑制；如未来要正式品牌图标，把 `data:,` 替换为 `/static/favicon.ico` 真实路径即可。


## 2026-07-31 · P1-02 客户分页查询

**范围**：`app/models/customer.py`（追加 paginate / to_dict） + `app/services/data_service.py`（追加 list_customers + 合并 DataService） + `app/api/v1/data.py`（追加 GET /customers + _int_arg） + `work/smoke_p102.py`（10 用例 smoke）。

| 维度 | 结果 | 说明 |
| --- | --- | --- |
| 架构 | ✅ 通过 | 严格分层：Model 只做查询+序列化；Service 做编排（含 per_page cap + pages 计算）；API 只做参数解析与委托。三个类/函数职责单一，无跨层调用 |
| 后端 | ✅ 通过 | 路由不写业务（_int_arg 只做类型转换 + 抛 BizException）；DataService.list_customers 纯业务编排；Customer.paginate 是纯查询；Customer.to_dict 是纯序列化 |
| AI | ➖ 不适用 | 本任务不涉及模型/scaler/数据流 |
| 安全 | ✅ 通过 | @login_required 装饰器强制鉴权；参数类型校验防注入；per_page 上限 cap 防 DoS；keyword 是 id 精确匹配（数字字符串），无 SQL 注入风险（走 ORM 参数化） |
| 测试 | ✅ 通过（端到端 10/10） | 10 用例覆盖：分页 / 6 种过滤 / per_page cap / 空数据 / 4 种非法参数；P1 累计 37/37 smoke 全绿 |

**结论**：P1-02 通过审查，可标记 `[x]` 完成，继续 P1-03。

**遗留 / 备注**：
- 全表 count() + offset/limit 在 38 万行数据量下可接受（P1 性能基线要求）；如未来 >100 万行建议 keyset 分页（WHERE id > last_id），P2 优化项
- age_min / age_max / previously_insured 过滤未走索引（小数据量无必要，大数据量场景可加 B-Tree 索引）
- gender / keyword 走自然索引（gender 低基数不加索引；keyword 是 id 主键精确匹配自动命中）
- Customer.to_dict() 返回 15 字段（12 业务 + predicted_prob + created_at + updated_at），与 API 文档 §2.2 "items 元素含全字段" 一致
- BUG-011 已修：上一轮误重定义 DataService 类导致 P1-01-6 smoke 全部 500；已合并为一个类并回归通过


## 2026-07-31 · P1-03 数据统计 / 质量 / EDA 可视化

**范围**：`app/utils/visualizer.py`（新建，4 个 chart） + `app/services/data_service.py`（追加 3 方法 + 重写合并类） + `app/api/v1/data.py`（追加 3 路由） + `work/smoke_p103.py`（10 用例）。

| 维度 | 结果 | 说明 |
| --- | --- | --- |
| 架构 | ✅ 通过 | 三层职责清晰：visualizer.py（纯可视化，无 Flask/DB） + DataService（编排 + 业务） + API（参数解析 + 委托）。matplotlib Agg 后端在 utils 层第一行 import，Web 层不感知 |
| 后端 | ✅ 通过 | visualizer 纯函数（输入 DataFrame，输出 base64 str）；Service 用聚合查询而非全表加载（statistics）；quality/visualization 全表加载走 pandas；API 仅做委托 |
| AI | ➖ 不适用 | 本任务不涉及模型训练；EDA 图表仅展示数据分布 |
| 安全 | ✅ 通过 | @login_required 全覆盖；未知 chart_type 拒绝 1001；matplotlib Agg 无交互式后端风险；base64 字符串前端渲染不执行 JS |
| 测试 | ✅ 通过（端到端 10/10） | 10 用例覆盖：鉴权 / 2 种数据规模 / 4 种图表（PNG magic bytes 校验）/ 未知类型 / 空数据；P1 累计 47/47 smoke 全绿 |

**结论**：P1-03 通过审查，可标记 `[x]` 完成，继续 P1-04。

**遗留 / 备注**：
- BUG-012 已修：第二度踩到 BUG-011，已彻底重写 data_service.py 把全部方法合并到唯一类
- matplotlib Agg 后端在 Windows / Linux / Docker 均安全（已对齐 Gate WARNING 7-A）
- 中文字体未配置（按 Gate WARNING 7-D，当前标题/标签全英文）
- visualizer 输出 PNG 17-20KB，base64 字符串 ~24KB，单接口响应 < 30KB
- quality / visualization 全表加载在 38 万行下预计 5-10s；如需 P1 性能基线达标（PRD < 60s 训练时间），需真实数据集压测

---

## P1-04 模型训练 · Code Review

| 维度 | 检查项 | 结论 |
| --- | --- | --- |
| 架构 | 分层是否清晰 | PASS。API 只解析参数，MLService 做编排，data_processor 做纯特征工程，无跨层调用 |
| 架构 | 是否重复实现 | PASS。复用 `Customer.to_dict` / `COLUMN_RENAME` / `BizException` / `role_required`，未新建平行工具 |
| 架构 | 循环依赖 | PASS。依赖单向：api → services → utils/models → core |
| 后端 | 错误码一致性 | PASS。1001 参数、1002 未认证、1003 越权、2001 无数据、3001 训练失败，全部对齐 docs/03 §0.5 |
| 后端 | 事务安全 | PASS。`is_best` 全量失活与新记录插入在同一 `commit`；日志写入独立且失败静默 |
| 后端 | 响应格式 | PASS。统一 `success()` 信封，`{best_model, results}` 对齐 docs/03 §3.1 |
| AI | 编码策略 | PASS。Label / Ordinal / 不处理三类严格按 docs/02 §2.2 表格 |
| AI | 数据泄漏 | PASS。scaler 只 fit 训练集；`stratify=y` 保证分层 |
| AI | 不平衡处理 | PASS。LR/RF `class_weight="balanced"`，XGB `scale_pos_weight` 只按训练集统计（不用测试集，避免泄漏） |
| AI | 预测一致性 | PASS。`joblib.dump({"model","scaler"})` 同 bundle 落盘 |
| 安全 | 权限 | PASS。`/train` 双装饰器 admin-only，smoke 用例 4/5 覆盖 |
| 安全 | 输入校验 | PASS。models 元素类型、test_size 区间 [0.05,0.5]、random_state 整数、params 结构均校验；`isinstance(raw, bool)` 排除 True/False 混入数字参数 |
| 测试 | 覆盖度 | PASS。13 用例覆盖正常/越权/未认证/非法参数/无数据/落库/落盘/重训/日志 |

### 结论
PASS，可进入 P1-05。

### 遗留与技术债
| 编号 | 内容 | 计划 |
| --- | --- | --- |
| DEBT-P104-1 | 38 万行真实数据训练耗时未实测 | 拿到真实数据集后补一次性能验证 |
| DEBT-P104-2 | `params` 覆盖超参未做生效断言 | P1-05 顺带补 1 条用例 |
| DEBT-P104-3 | 训练为同步阻塞请求，大数据量下 HTTP 可能超时 | 教学项目暂不引入任务队列，P2 视情况评估 |
| WARNING 5-C | `PromptTemplate.is_active` 无唯一约束 | P1-12 必须事务内先全量失活再激活（本轮 `is_best` 已采用同一模式，可直接照搬） |
