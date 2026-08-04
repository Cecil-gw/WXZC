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

---

## P1-05 实验记录 / 最佳模型查询 · Code Review

| 维度 | 检查项 | 结论 |
| --- | --- | --- |
| 架构 | 分层职责 | PASS。查询构造在 Model（`Experiment.paginate`），编排与上限裁剪在 Service，路由仅解析参数，与 P1-02 的 `Customer` 模式完全一致 |
| 架构 | 重复代码 | PASS。复用 `SUPPORTED_MODELS` 做白名单校验；分页响应五键结构与 `/data/customers` 同构。`_query_int` 与 `data.py::_int_arg` 语义重复但刻意不跨蓝图 import，避免 `api/v1` 内横向依赖 |
| 架构 | 循环依赖 | PASS。依赖仍单向：api → services → models → core |
| 后端 | 错误码 | PASS。1001 参数非法、1002 未认证、3002 无最佳模型，对齐 docs/03 §0.5 与 §3.3 |
| 后端 | 分页正确性 | PASS。`pages` 用上取整；空数据 pages=0；per_page 上限 200 与客户分页一致 |
| 后端 | 排序稳定性 | PASS。`created_at` 秒级精度下同批记录时间戳相同，已加 `id` 倒序兜底，避免跨页重复 |
| 后端 | 响应契约 | PASS。`/experiments` items 11 字段、`/best` 恰好 3 字段，与 docs §3.2 / §3.3 逐项核对 |
| 安全 | 权限粒度 | PASS。docs §3.2/§3.3 鉴权栏为「是」且未标注 admin（对比 §3.1 明确标注），故仅 `@login_required`；用例 19 验证普通用户可读 |
| 安全 | 输入校验 | PASS。page/per_page 非整数与越界均 1001；model_name 走白名单，不进 SQL 拼接 |
| 健壮性 | 脏数据防御 | PASS。`/best` 用 `first()` 而非 `one()`，规避 `is_best` 多条为真时抛 `MultipleResultsFound` 变 5000；`params` 反序列化失败降级 None，不打断整页 |
| 测试 | 覆盖度 | PASS。20 用例覆盖空数据、鉴权、分页边界、跨页重叠、过滤、非法参数、上限截断、选优一致性、排序、普通用户权限 |

### 结论
PASS，可进入 P1-06。

### 遗留与技术债
| 编号 | 内容 | 计划 |
| --- | --- | --- |
| DEBT-P105-1 | `params` 默认全量返回，38 万行下 ROC 点数可达数万，分页响应体偏大 | P1-08 视需要加 `?with_params=0` 开关 |
| DEBT-P105-2 | `_query_int` 与 `data.py::_int_arg` 逻辑重复两份 | 若第三处再出现，提取到 `app/utils/` 统一收口 |
| WARNING 5-C | `is_best` 仍无数据库唯一约束 | 当前靠 `train()` 先失活再激活 + `/best` 用 `first()` 双重兜底；P2 可评估加部分唯一索引 |

---

## P1-06 全量预测 · Code Review

| 维度 | 检查项 | 结论 |
| --- | --- | --- |
| 架构 | 分层职责 | PASS。路由解析 model_name 并记日志，`MLService.predict` 负责定位模型 / 加载 / 预测 / 回写，特征工程仍在 utils |
| 架构 | 重复代码 | PASS。复用 `prepare_features(with_target=False)`（P1-04 预留开关）、`Customer.to_dict`、`operation_log_service.log`；`_BATCH_SIZE` 与 `data_service` 分批规模对齐 |
| 架构 | 循环依赖 | PASS。依赖仍单向 |
| AI | **scaler 一致性** | PASS。`scaler.transform` 绝不 refit；smoke 用例 12 手工复算逐行比对 max_diff<1e-9 提供了硬证据 |
| AI | 特征列顺序 | PASS。训练与预测同走 `prepare_features`，列顺序由 `FEATURE_NAMES` 固定，不会错位 |
| AI | 概率而非硬标签 | PASS。取 `predict_proba(...)[:, 1]` 正类概率，为 P1-10 分位数筛选保留排序信息 |
| 后端 | 错误码分层 | PASS。模型侧问题（无记录 / 文件丢失 / 结构异常 / 预测异常）统一 3002，无客户数据 2001，参数非法 1001，对齐 docs/03 §3.4 |
| 后端 | 批量写入 | PASS。`bulk_update_mappings` 按 5000 分批，避免大 UPDATE |
| 健壮性 | 模型文件防御 | PASS。三重检查：`model_path` 非空 → `os.path.exists` → `_load_bundle` 校验 dict 含 model+scaler。避免问题延迟到 `predict_proba` 才暴露为 500 |
| 健壮性 | 脏数据容忍 | PASS。模型定位用 `first()` 而非 `one()`，与 P1-05 一致，规避 `is_best` 多条为真 |
| 安全 | 权限 | PASS。docs §3.4 鉴权栏为「是」未标 admin，故仅 `@login_required` |
| 安全 | 输入校验 | PASS。model_name 校验类型、去空白、走 `SUPPORTED_MODELS` 白名单，不进 SQL 拼接 |
| 测试 | 覆盖度 | PASS。18 用例覆盖鉴权、参数、无模型、文件丢失、无数据、回写完整性、概率有效性、scaler 一致性、指定模型覆盖、操作日志 |
| 测试 | 可重复性 | PASS（修复后）。BUG-016 已消除，脚本自清理表，连跑两遍稳定 |

### 结论
PASS，可进入 P1-07。

### 遗留与技术债
| 编号 | 内容 | 计划 |
| --- | --- | --- |
| DEBT-P106-1 | 预测同步阻塞，38 万行耗时未实测 | 与 DEBT-P104-3（训练同步）同源，P2 一并评估异步化 |
| DEBT-P106-2 | 并发预测无锁，多请求同时回写 `predicted_prob` 结果不确定 | 教学项目单用户场景可接受；P2 若引入多用户需加行锁或任务队列 |
| BUG-016 | 已修复。根因是 Windows 文件句柄占用导致删库静默失败 | 建议排查仓库中 5 个残留 `.venv_q8` python 进程的来源 |

---

## P1-07 上传数据预测 · Code Review

| 维度 | 检查项 | 结论 |
| --- | --- | --- |
| 架构 | 分层职责 | PASS。路由做文件白名单与表单解析，Service 做模型定位 + 解析 + 预测 + 汇总，特征工程仍在 utils |
| 架构 | **重复代码消除** | PASS。开发前先把 `predict()` 内 20 余行模型定位逻辑提取为 `_resolve_experiment()`，两个预测接口共用；避免了复制粘贴产生两份待同步逻辑 |
| 架构 | 重构安全性 | PASS。提取后立即重跑 P1-06 smoke 18/18 确认 `/predict` 无回归，才继续开发 |
| 架构 | 循环依赖 | PASS。依赖仍单向：api → services → utils/models → core |
| 后端 | 不入库语义 | PASS。全程无写库操作（仅操作日志），smoke 用例 16 从行数/NULL 数/最大 id 三角度交叉验证 |
| 后端 | 错误码分层 | PASS。文件格式 1001、解析失败 2002、模型不可用 3002，对齐 docs/03 §3.5 |
| 后端 | 契约一致 | PASS。data 恰四字段，与 docs §3.5 逐项核对 |
| AI | scaler 一致性 | PASS。`scaler.transform` 不 refit，用例 17 手工复算比对提供硬证据 |
| AI | 分位数策略 | PASS。`high_potential_threshold` 用 0.9 分位数而非固定 0.5，依据 docs/02 §2.7；口径与 P1-10 高潜筛选统一 |
| AI | 排序语义 | PASS。`predictions` 按概率倒序，契合 docs/02 §2.7「要的是排序而非二分判断」 |
| 后端 | 标签列处理 | PASS。预测场景不复用 `check_required_columns`（该函数含 Response 校验、服务于入库），只校验 10 个特征列；用例 18 验证 |
| 健壮性 | id 列缺失 | PASS。有则透传、无则 1-based 行号兜底，保证 predictions 可追溯 |
| 安全 | 权限 | PASS。docs §3.5 与接口清单第 14 项均标「已登录」，故仅 `@login_required` |
| 安全 | 输入校验 | PASS。扩展名白名单、model 去空白 + `SUPPORTED_MODELS` 白名单，不进 SQL 拼接；文件体积受 DECISION-004 的 50MB 全局上限约束 |
| 测试 | 覆盖度 | PASS。23 用例覆盖鉴权、文件格式、解析失败、缺列、未知模型、响应契约、排序、statistics 自洽、分位数正确性、不入库、scaler 一致性、无标签列、无 id 列、指定模型、文件丢失、操作日志 |

### 结论
PASS，可进入 P1-08。

### 遗留与技术债
| 编号 | 内容 | 计划 |
| --- | --- | --- |
| DEBT-P107-1 | `predictions` 全量返回，38 万行上传时 JSON 约 30MB+ | docs §3.5 未定义分页，暂按文档实现；前端如遇问题可加 `top_n` |
| DEBT-P107-2 | `_HIGH_POTENTIAL_QUANTILE=0.9` 硬编码在 ml_service | P1-10 若需可配分位数，提取为参数复用此常量，不要再定义一份 |
| DEBT-P106-2 | 并发预测无锁（沿用上轮记录） | 本接口不写库，不受该问题影响；仅 `/predict` 相关 |

---

## P1-08 模型评估可视化 · Code Review

| 维度 | 检查项 | 结论 |
| --- | --- | --- |
| 架构 | 分层职责 | PASS。绘图纯函数在 utils（不依赖 Flask/DB），数据取用与分流在 Service，路由只传参 |
| 架构 | 复用 | PASS。四个新函数全部复用 `_to_base64`；沿用 P1-03 已设置的 Agg 后端；响应结构与 `/data/visualization` 一致 |
| 架构 | 侵入性 | PASS。P1-03 的 4 个 EDA 函数与 `CHART_FUNCS` 零改动，用例 23 专门回归 |
| 架构 | 命名清晰 | PASS。`MODEL_CHART_TYPES` 与数据模块 `CHART_FUNCS` 分开；两者取值域不同，混用会让错误提示误导使用者 |
| 架构 | 循环依赖 | PASS。services → utils 单向；visualizer 不反向 import service |
| AI | 数据来源正确 | PASS。全部取自 `experiments.params`，不重新训练、不加载 joblib。用例 17 断言 experiments 与 predicted_prob 未变，用例 19 断言幂等 |
| AI | 图表语义 | PASS。ROC 带随机基线与 AUC 图例；指标图强调 ROC-AUC（docs/02 §2.5 的选优依据）；混淆矩阵标行内占比（不平衡下只看绝对值会误判召回）；重要性按值排序 |
| AI | 多轮实验去重 | PASS。`_latest_per_model` 每算法只取最新一条，避免历史曲线重叠成团 |
| 后端 | 参数校验 | PASS。chart_type 白名单、model 必填判定（仅对两种单模型图）、model 白名单，均按 docs §3.6 |
| 后端 | 错误码 | PASS。参数问题 1001，数据不可用（无实验 / params 缺失或损坏）3002，对齐 docs/03 §0.5 |
| 健壮性 | 脏数据防御 | PASS。`_experiment_params` 对 params 为空、非法 JSON、非 dict 三种情况均转 3002；`feature_names` 与 `feature_importances` 长度不等也拦下。用例 21 验证损坏 params 不炸成 500 |
| 安全 | 权限 | PASS。docs §3.6 与接口清单第 15 项均标「已登录」，故仅 `@login_required`；用例 22 验证 |
| 安全 | 资源释放 | PASS。`_to_base64` 内 `plt.close(fig)`，不累积 Figure 句柄 |
| 测试 | 覆盖度 | PASS。23 用例覆盖鉴权、四种图表 × 三算法、参数校验、无数据、损坏数据、幂等、不重训、跨模块回归 |
| 测试 | 断言强度 | PASS。除 PNG magic bytes 外，另做逐像素非白占比与色彩数统计，排除「合法但空白画布」的假通过 |

### 结论
PASS，可进入 P1-09。

### 遗留与技术债
| 编号 | 内容 | 计划 |
| --- | --- | --- |
| DEBT-P108-1 | 图表标签全英文，matplotlib 默认字体无中文字形 | TODO.md P2-07「中文字体与图表美化」已规划，不提前处理 |
| DEBT-P108-2 | 38 万行下 ROC 数万点的绘图耗时与内存未实测 | 与 DEBT-P105-1（params 体积）同源，一并在大数据量验证时评估 |
| DEBT-P108-3 | `metrics_comparison` 图宽按模型数线性放大 | 当前 3 个算法无问题；若扩展算法数需检查画布是否溢出 |

---

## P1-09 模型导入 / 导出 · Code Review

| 维度 | 检查项 | 结论 |
| --- | --- | --- |
| 架构 | 分层职责 | PASS。`export_model` 只返回路径信息，`send_file` 留在路由层；Service 不产生 HTTP 响应对象 |
| 架构 | 复用 | PASS。导入校验完全走 P1-06 的 `_load_bundle`，未另写结构检查；`SUPPORTED_MODELS`、`settings.model_dir_abs`、`operation_log_service` 全部沿用 |
| 架构 | 侵入性 | PASS。无既有函数被修改，纯追加；`ml_service.py` 改前改后核对结构，`class MLService` 仍唯一、8 方法齐全（规避 BUG-011/012） |
| 架构 | 循环依赖 | PASS。services → utils / models 单向，未新增反向引用 |
| 安全 | 路径穿越（导出） | PASS。`model_name` 先过 `SUPPORTED_MODELS` 白名单，再用 `os.path.commonpath` 复核绝对路径归属 `MODEL_DIR`。用例 10-12 三种编码变体均拦下 |
| 安全 | 路径穿越（导入） | PASS。落盘名由 `_infer_model_name` 从 estimator 类名推断，根本不取用户上传的文件名 —— 比清洗文件名更彻底。用例 21 用 `evil_name.joblib` 验证 |
| 安全 | 反序列化风险 | WARNING。joblib 底层是 pickle，加载不可信文件等价于任意代码执行。当前靠「仅 admin」+ 白名单落盘缓解，但无法根除。教学项目可接受，登记为 DEBT-P109-1 |
| 安全 | 权限 | PASS。docs/03 §3.7 / §3.8 鉴权栏均写「仅 admin」，故加 `@role_required("admin")`。用例 4-5 验证普通用户 403 / 1003 |
| 安全 | 审计 | PASS。导入记 `action="model_import"` 并附 `source_filename`，可追溯是谁上传了什么文件。用例 24 确认只记成功那次，失败不留噪声日志 |
| 健壮性 | 不信任扩展名 | PASS。先写临时文件真正 `joblib.load` 校验 bundle 结构，通过后才覆盖。用例 16 用随机字节的假 `.joblib` 验证返回 1001 而非 500 |
| 健壮性 | 坏文件不污染 | PASS。临时文件 + `os.replace` 保证要么完整替换要么原文件不动。用例 19 在四次失败导入后确认原模型仍可预测 |
| 健壮性 | 临时文件清理 | PASS。`finally` 块统一清理，且用 `os.path.exists` 保护，成功路径（文件已被 replace 移走）不会二次删除报错。用例 25 确认终态无残留 |
| 健壮性 | 跨平台 | PASS。用 `os.replace` 而非 `os.rename`（后者在 Windows 覆盖已存在文件会抛 `FileExistsError`）；`uuid4().hex` 做临时名避免并发碰撞 |
| 后端 | 错误码 | PASS。导入失败统一 1001（语义为「用户上传了不合格文件」），导出文件缺失 3002（语义为「模型尚未训练」）。`_load_bundle` 内部的 3002 在导入路径被显式转成 1001，两个调用方各得其所 |
| 后端 | 响应结构 | PASS。导入返回 `{model_name, path}` 与 docs §3.8 一致；导出为二进制流带 `Content-Disposition: attachment` |
| 测试 | 覆盖度 | PASS。25 用例覆盖鉴权 / 越权、三种穿越编码、四类非法文件、副作用检查、往返一致性、落盘名推断、导入后可预测、日志、临时文件终态 |
| 测试 | 断言强度 | PASS。导出不只看 200，还把字节流落盘 `joblib.load` 确认可用；穿越用例额外确认响应体不含 `.env` 内容特征，避免「200 但返回了别的文件」漏检 |
| 测试 | 幂等 | PASS。连跑两遍均 25/25，脚本自清理三张表与 `MODEL_DIR`，不依赖删 db 文件 |

### 结论
PASS。P1 模型模块（P1-04~P1-09）六项全部收口，可进入 P1-10 邮件模块。

### 遗留与技术债
| 编号 | 内容 | 计划 |
| --- | --- | --- |
| DEBT-P109-1 | joblib 底层为 pickle，导入任意文件等价任意代码执行 | 现靠「仅 admin」+ 审计日志缓解。若将来开放给非管理员，须改用 ONNX / 自定义序列化格式或沙箱加载 |
| DEBT-P109-2 | 导入不校验模型特征数与当前 `FEATURE_NAMES` 是否匹配 | 错误推迟到 `/predict` 的 `scaler.transform` 暴露。docs §3.8 未要求，如遇实际问题可在 `import_model` 加 `n_features_in_` 比对 |
| DEBT-P109-3 | 导入模型不写 `experiments` 记录，不参与 `is_best` 选优 | docs 未定义导入模型的实验归属，保持最小实现；用它预测需显式传 `model_name` |
| DEBT-P107-2 | `_HIGH_POTENTIAL_QUANTILE=0.9` 硬编码（沿用上轮记录） | **P1-10 直接复用此常量**，需可配时提取为参数，不要再定义第二份 |

---

## P1-10 高潜客户筛选 · Code Review

| 维度 | 检查项 | 结论 |
| --- | --- | --- |
| 架构 | 分层职责 | PASS。查询构造（过滤 / 排序 / 分页）在 Model，阈值计算与参数归一在 Service，路由只解析参数。与 P1-02 `/data/customers` 的分层完全对称 |
| 架构 | 新建 Service 的必要性 | PASS。docs/04 §4 目录规划里明确列有 `email_service.py`，本轮按图落位，不是临时起意新增文件 |
| 架构 | 复用 | PASS。默认分位数直接 import `ml_service._HIGH_POTENTIAL_QUANTILE`，未另定义第二份（DEBT-P107-2 的明确要求）；`_MAX_PER_PAGE`、`_int_arg` 与 data 模块同值同实现 |
| 架构 | 侵入性 | PASS。`customer.py` 纯追加三个方法，既有 `paginate` / `to_dict` 零改动（P1-02 smoke 10/10 回归确认）；`api/v1/__init__.py` 无需改动，email 蓝图 P0-04 已注册 |
| 架构 | 循环依赖 | PASS。`email_service` → `ml_service` 单向。`ml_service` 不反向引用 email_service，导入链无环（`create_app` 成功启动即验证） |
| 架构 | 默认值单点 | PASS。路由读到 percentile 为 None 时不传参，让 Service 签名默认值生效。避免路由与 Service 各写一份 0.9，将来改分位数只需改一处 |
| AI | 筛选策略 | PASS。严格按 docs/02 §2.7 用 `np.quantile` 分位数，非固定阈值。用例 6 与 `np.quantile` 比对到 1e-9，用例 16 用单调性交叉验证参数确实生效 —— 两者合起来排除「参数被忽略、实际用硬编码阈值」的假通过 |
| AI | NULL 语义 | PASS。分位数计算与结果过滤两处均排除 NULL。若把未预测行当 0 参与计算会拉低阈值，让名单混入未预测客户。用例 20 专门构造半 NULL 场景验证 |
| AI | 排序稳定性 | PASS。`predicted_prob desc, id asc` 双键排序。概率相同时若无 id 兜底，翻页可能重复或漏掉记录。用例 13 断言两页 id 集合无交集 |
| 后端 | 参数校验 | PASS。percentile 取开区间 (0,1)：`0` 使阈值落到最小值等于不筛选，`1` 语义含糊，两端均 1001 且错误信息写明「不含端点」 |
| 后端 | 浮点边界 | PASS。`_float_arg` 显式拦 nan / inf。nan 与任何值比较均为 False，本例恰好落进 1001 分支属侥幸而非设计，在入口挡下才不依赖下游比较顺序 |
| 后端 | 响应结构 | PASS。docs §4.1 要求 `{threshold, total, customers}`，与项目通用分页结构 `{items,...}` 不同，此处以文档契约为准。用例 5 断言键集合精确匹配 |
| 后端 | 字段裁剪 | PASS。新增 `to_target_dict()` 只吐 docs 规定的五字段，不复用 `to_dict()`（后者会多吐 vintage / response / created_at 等无关数据） |
| 后端 | 错误码 | PASS。参数问题 1001，无预测数据 3002（语义为「模型产物不可用」，与 `/predict` 一致）。错误信息给出可执行的下一步（提示先调 `POST /model/predict`） |
| 性能 | 查询开销 | PASS。`predicted_probs()` 只查概率单列而非整行 ORM 实例，38 万行时省下大量内存。不过全量读入内存仍是隐患，登记 DEBT-P110-1 |
| 安全 | 权限 | PASS。docs §4 开头统一声明「本模块所有接口需登录」且 §4.1 鉴权栏只写「是」，故仅 `@login_required` 不加角色限制。用例 21 验证普通用户可读 |
| 安全 | 副作用 | PASS。纯只读，不写库不记日志。用例 23 断言调用前后 customers 与 operation_logs 行数不变。高频只读接口记审计会迅速淹没 operation_logs |
| 测试 | 覆盖度 | PASS。23 用例覆盖鉴权、空数据、全 NULL、半 NULL、阈值精度、单调性、排序、翻页、分页上限、七种非法 percentile、四种非法分页、幂等、只读 |
| 测试 | 断言强度 | PASS。用可精确复算的均匀分布概率（i/400）替代随机数据，使阈值可做 1e-9 级比对；另有独立集成脚本在真实 XGBoost 概率分布上复验 |

### 结论
PASS，可进入 P1-11。

### 遗留与技术债
| 编号 | 内容 | 计划 |
| --- | --- | --- |
| DEBT-P110-1 | `predicted_probs()` 全量读概率入内存算分位数（38 万行约 3MB，可接受；再上一量级需改造） | 若数据规模继续增长，改用 SQL 侧近似分位数或抽样估计 |
| DEBT-P110-2 | 阈值每次请求重算，无缓存 | 同批预测的阈值固定，理论可缓存；当前无缓存层，重算成本低于引入一致性风险 |
| DEBT-P107-2 | `_HIGH_POTENTIAL_QUANTILE=0.9` 硬编码在 ml_service | **本轮已复用而非重复定义**。若将来需要按环境配置，提取到 `settings` 即可单点生效 |
| WARNING 5-C | `PromptTemplate.is_active` 无唯一约束 | **P1-12 必须在事务内先全量失活再激活**，可照搬 `train()` 里 `is_best` 的写法 |
