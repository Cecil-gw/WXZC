"""P0 Gate Review · Tech Lead 验收报告。

目的：在进入 P1 业务开发前，对 P0（6 项）做一次架构级审查，识别会污染 P1 的设计缺陷。
口径：所有结论基于仓库当前真实代码（已逐文件读过），不基于"应该如此"。
"""

## 总评结论

| # | 检查项 | 评级 | 关键证据 |
| --- | --- | --- | --- |
| 1 | 目录结构对齐 docs/04_技术框架方案.md | PASS | app/{api/v1,core,models,schemas,services,utils,static} 全部就位，5 蓝图占位 + 6 ORM 表 + 3 个 static 资源齐全 |
| 2 | 重复代码 | PASS | AST 扫描 + 三行滑窗：无业务逻辑重复；仅 docstring/imports 标准模板重复，属工程惯例 |
| 3 | 循环依赖 | PASS | AST 全量扫描 18 个模块，0 个环 |
| 4 | Blueprint 注册 | PASS | register_blueprints() 一次挂载 5 蓝图，每个蓝图自带 url_prefix，无重复挂载、无遗漏 |
| 5 | ORM 设计 | PASS with 3 WARNING | 6 张表字段/关系/索引与 docs/04 §7 严格对齐；3 项业务约束需要 P1 阶段注意 |
| 6 | JWT 安全 | PASS | HS256 + sub/exp/role/username claim + 异常吞掉 JWTError；密钥默认值有提示 |
| 7 | 影响 P1 的设计问题 | PASS with 4 WARNING | 分层清晰、service 可复用；4 项需在 P1 各任务中"必须处理" |
| 8 | requirements 兼容 Py 3.12 & 3.13 | FAIL | Py 3.12 OK；Py 3.13 上 pandas==2.2.2 无 cp313 wheel，pip 走 meson 源码构建又缺 vswhere.exe，直接阻塞 P1-01 |
| 9 | 技术债 | WARNING | 12 项已识别，按优先级记入 P2-* 任务，不阻塞 P1 |

Gate 决议：FAIL · 暂停进入 P1。

原因：Q8 FAIL —— requirements.txt 与系统 Python 3.13 不兼容（pandas 2.2.2 无 wheel），而 P1-01（Excel 上传）必须使用 pandas。其余 8 项均为 PASS（含 7 项带 WARNING 的可接受情况）。

修复方案（解锁 P1）：

1. 最小修复（推荐）：requirements.txt 把 pandas==2.2.2 升到 pandas==2.2.3（最近一个有 cp313 wheel 的 2.2.x；API 兼容，向后兼容 2.2.2 全部 API）。
2. 或锁 Python 3.12.10 环境（与历史 P0-* smoke 一致）。
3. 或加 python_version<'3.13' 环境标记（不推荐，违背"Py 3.12 + 3.13"要求）。

按 AI_RULES.md：此 FAIL 触发"需求冲突/技术方案不确定"分支，应在 DECISION.md 写入评审记录，三选一确认后回 P0-01 修订 requirements.txt，再开 P1-01。

---

## 1. 目录结构对齐 docs/04_技术框架方案.md · PASS

对照口径：docs/04 §4 规定的目录树。

实际清单（剔除 __pycache__ / .venv / .git）：

```
app/
├── __init__.py              # create_app
├── api/
│   ├── __init__.py
│   └── v1/
│       ├── __init__.py      # register_blueprints
│       ├── auth.py          # 4 routes 实装
│       ├── data.py          # 蓝图占位
│       ├── model.py         # 蓝图占位
│       ├── email.py         # 蓝图占位
│       └── log.py           # 蓝图占位
├── core/                    # 5 件套
│   ├── config.py / database.py / response.py / security.py / dependencies.py
├── models/                  # 6 张表
│   ├── user.py / customer.py / experiment.py / email_record.py / operation_log.py / prompt_template.py
│   └── __init__.py
├── schemas/                 # Pydantic
│   └── auth.py
├── services/                # 业务层
│   └── auth_service.py
├── utils/                   # 工具层（空，P1-03 才有 visualizer）
│   └── __init__.py
└── static/                  # 前端 SPA
    ├── index.html / css/app.css / js/{api.js, app.js}
```

结论：100% 对齐。

- 优点：schemas/ / services/ / utils/ 都补了 __init__.py，符合 Python 包约定。
- 注意点：utils/ 当前为空目录，P1-03 必须建 data_processor.py / visualizer.py（已在 TODO.md 标记）。

---

## 2. 重复代码 · PASS

扫描方法：AST 全量扫描 + 三行滑窗找跨文件重复块（去除 docstring / imports / 空行后）。

唯一被识别的"重复"：

1. `from __future__ import annotations` —— 6 个 models 全有，Python 惯例。
2. `from datetime import datetime` / `from typing import Optional` —— 标准库 import。
3. `created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)` —— 出现在 Customer/EmailRecord/PromptTemplate。
4. `updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)` —— 同上三表。
5. `Boolean, nullable=False, default=False, index=True` —— Experiment.is_best / PromptTemplate.is_active。

判定：上述重复均为模型字段样板（timestamp / boolean flag），不是业务逻辑。P1 阶段如重复 ≥5 处可考虑抽 TimestampMixin / FlagMixin，目前 3 处抽离属过度设计。接受。

零业务逻辑重复：

- 路由层 → 服务层调用，每个 blueprint 仅 import 自己的 service（目前仅 auth_service）。
- 没有"两个函数干同一件事"的情况。

---

## 3. 循环依赖 · PASS

扫描方法：AST 解析 app/**/*.py 的 import / from ... import，构建有向图，DFS 找环。

全量 import 关系（剔除外置包）：

```
app.api.v1.__init__     → {auth, data, email, log, model}
app.api.v1.auth         → {core.database, core.dependencies, core.response, schemas.auth, services.auth_service}
app.app (__init__)      → {api.v1, core.config, core.database, core.response, core.security, models, models.prompt_template, models.user}
app.core.database       → {core.config}
app.core.dependencies   → {core.response, core.security}
app.core.security       → {core.config}
app.models.__init__     → {customer, email_record, experiment, operation_log, prompt_template, user}
app.models.*（6 个）    → {core.database}（仅）
app.services.auth_service → {core.config, core.response, core.security, models.user}
```

结论：拓扑方向严格自上而下，0 个环。

- app.__init__ 同时 import core.* 与 models.* 是预期（应用工厂在启动时统一注册）。
- models/__init__.py 导入顺序按"无 FK → 有 FK"排列（user/customer/prompt_template → experiment/email_record/operation_log），避免 SQLAlchemy 字符串解析时反向引用报错。

---

## 4. Blueprint 注册 · PASS

5 个 Blueprint 一览：

| Blueprint | 名称 | url_prefix | 实装路由 | 备注 |
| --- | --- | --- | --- | --- |
| app/api/v1/auth.py | auth | /api/v1/auth | /login POST、/register POST、/me GET、/logout POST | P0-05 完整实现 |
| app/api/v1/data.py | data | /api/v1/data | 无（占位） | P1-01~03 填充 |
| app/api/v1/model.py | model | /api/v1/model | 无（占位） | P1-04~09 填充 |
| app/api/v1/email.py | email | /api/v1/email | 无（占位） | P1-10~13 填充 |
| app/api/v1/log.py | log | /api/v1/logs | 无（占位） | P1-14 填充 |

注册入口：app/api/v1/__init__.py::register_blueprints(app) 一次性挂载，调用顺序 auth → data → model → email → log。

评估：

1. 无重复挂载：每个 bp 名字唯一（auth/data/model/email/log），url_prefix 唯一。
2. 无遗漏：5 个业务模块全覆盖（对照 docs/03 §7 29 个接口清单）。
3. 命名一致性：log 蓝图用 /api/v1/logs（复数），与 API 文档 §5.1 一致；其他蓝图均为单数形式（/auth//data//model//email），符合 REST 资源命名。这点不构成 WARNING —— logs 是 "log entries" 复数语义保留。
4. 占位蓝图的设计：data/model/email/log 4 个蓝图只 import 不写路由，create_app() 启动后未注册路由的路径会走全局 404 → code=5000（已在 P0-04 smoke 验证 /auth/me 404 行为）。这种"占位蓝图"的写法在 P1 阶段填路由时不会引入"挂载顺序"或"导入顺序"问题。

结论：接受。

---

## 5. ORM 设计 · PASS with 3 WARNING

字段 / 关系 / 索引 与 docs/04 §7 比对：

| 表 | 主键 | 业务字段 | 关系 | 索引 | 与文档一致 |
| --- | --- | --- | --- | --- | --- |
| users | id auto | username/role/created_at + password_hash | operation_logs / email_records | username unique | OK |
| customers | id 业务 auto-inc=False | 12 业务字段 + predicted_prob | email_records | predicted_prob | OK（predicted_prob 有 index） |
| experiments | id auto | model_name/4 指标 + params/model_path/is_best | — | is_best / model_name | OK |
| email_records | id auto | customer_id(FK)/subject/content/status/created_by(FK) | customer / creator | customer_id / status / created_by | OK（FK ondelete: customer CASCADE, creator SET NULL） |
| operation_logs | id auto | user_id(FK)/action/details | user | user_id / action / created_at | OK（FK ondelete: user CASCADE） |
| prompt_templates | id auto | name/content/is_active | — | is_active | OK |

优点：

1. 字段顺序、类型、可空性、默认值全部对齐 API 文档。
2. Customer.predicted_prob / Experiment.is_best / PromptTemplate.is_active 三个高频过滤字段都建了索引。
3. FK ondelete 策略分层合理：审计日志（OperationLog）跟随用户级联删除；邮件记录（EmailRecord）保留但 creator 置空。
4. __repr__ 输出不含敏感信息（password_hash 缺席）。

WARNING 5-A：Customer.id 业务主键 + autoincrement=False 决定"上传必须先清空旧数据"。

- 影响：P1-01 的上传逻辑必须显式 DELETE FROM customers 后再 bulk_insert_mappings，否则第二批数据若 ID 重复会主键冲突。
- 已在 P0-03 dev log 中标注"覆盖策略"；P1-01 实现时必须沿用。

WARNING 5-B：Customer.region_code 与 policy_sales_channel 用 Float 而非 Integer。

- 影响：Kaggle 原数据集这两列是整数（区域码 / 渠道码），Float 存储会引入 .0 后缀与精度隐患（虽然实测 < 2^53 不会丢精度，但 ORM 层取回时类型不对）。
- 建议：P1-01 落库前 astype(int) 转一下，或在 P1-03 改 schema 为 Integer（需走 DECISION 流程）。

WARNING 5-C：PromptTemplate.is_active 无唯一约束。

- 影响：理论上 db.add() 两条 is_active=True 的模板不会被数据库拒绝。_seed_prompt_template() 与 P1-12 的 PUT /email/prompt 必须业务层保证唯一（更新前 UPDATE ... SET is_active=False）。
- 建议：P1-12 实现时新增事务内"先全量失活、再激活新模板"的两步写法；P2-08（数据校验加固）阶段可加唯一 partial index。

---

## 6. JWT 安全 · PASS

实现位置：app/core/security.py + app/core/dependencies.py。

审计清单：

| 风险 | 现状 | 评级 |
| --- | --- | --- |
| 算法 | HS256，配置化（settings.JWT_ALGORITHM），未硬编码 | OK |
| 密钥 | settings.JWT_SECRET_KEY 默认 "change-me-please-use-a-long-random-string"，.env.example 明确写"生产必须替换"；.gitignore 覆盖 .env | OK |
| Claims | 含 sub（user_id 字符串化）、iat、exp、role、username | OK |
| 过期 | JWT_EXPIRE_SECONDS=86400（24h）写死默认；可配 | OK |
| 异常处理 | JWTError → TokenInvalidError → BizException(1002, 401)，不泄露内部错误 | OK |
| 类型校验 | decode_token 强制要求 sub，否则 TokenInvalidError | OK |
| python-jose 字节 | 显式 if isinstance(token, bytes): token.decode("utf-8")，避免 jose 3.x 返回 bytes 时的兼容坑 | OK |
| 用户名枚举 | AuthService.login 失败统一返回"用户名或密码错误"，不区分"用户不存在"和"密码错" | OK |
| 越权注册 admin | RegisterRequest 无 role 字段；AuthService.register 硬编码 role="user" | OK |
| 密码哈希 | 直接 bcrypt.hashpw / checkpw，不经过 passlib，避开 4.x 兼容坑 | OK |
| Token 泄露 | 无 refresh token / 黑名单（JWT 无状态），仅依赖 24h 过期 + 客户端丢弃 | OK（P2-06 可加黑名单） |

微观察（非阻塞）：

- dependencies.py::_resolve_current_user 直接从 JWT claim 读 role/username，不查库——这是设计选择（性能优先）。如果用户表改了 role 而 token 还没过期，旧 token 仍带旧 role 直到过期。这是 JWT 无状态特性的固有 trade-off，不属于漏洞。
- verify_password 吞掉所有异常返回 False —— 好的实践，避免侧信道。

结论：满足 docs/04 §8 全部安全条款。

---

## 7. 影响 P1 的设计问题 · PASS with 4 WARNING

逐项审视"如果我现在写 P1 路由，会不会被现有设计绊倒"。

WARNING 7-A：utils/visualizer.py 尚未建立 + matplotlib.use("Agg") 未在 P0 阶段强制。

- 风险：P1-03（GET /data/visualization/{chart_type}）会因 matplotlib 默认尝试 TkAgg 后端，在 Windows headless 环境 / Docker 容器里崩溃。
- 必做：P1-03 第一行 import matplotlib; matplotlib.use("Agg")（写在 import pyplot 之前）。
- 已记录：TODO.md P1-03 验收标准已含此项。

WARNING 7-B：生产数据库驱动（pymysql / psycopg）未列在 requirements.txt。

- 风险：docs/04 §10 描述"生产切 MySQL/PG 只改 DATABASE_URL"，但 SQLAlchemy 用 mysql+pymysql:// 时需要 pymysql 包、postgresql+psycopg:// 需要 psycopg 包。当前 requirements.txt 不含。P2-10 部署文档阶段会暴露。
- 必做：P2-10 / 真要切生产数据库时再加；P0 阶段用 SQLite 不阻塞。

WARNING 7-C：缺少 OperationLog 写入辅助函数。

- 风险：P1-04（训练）、P1-06（预测）、P1-09（导入模型）、P1-11（生成邮件）、P1-13（更新/标记/删除邮件）等所有"关键动作"都需要写 OperationLog，但目前 6 张表里没有 OperationLogService。
- 必做：P1-04 开工前在 app/services/ 新建 operation_log_service.py（log(user_id, action, details=None)），供后续 service 调用。建议在 P0 收官时一并补上，否则每个 P1 service 都会重复实现 db.add(OperationLog(...)); db.commit()。

WARNING 7-D：缺少 g.current_user 类型声明。

- 风险：dependencies.py 把 dict 挂到 g.current_user，业务层用 g.current_user["id"] 取值时类型检查器（mypy/pyright）会抱怨；编辑器无补全。
- 必做：可选优化。在 app/core/dependencies.py 顶部加：
  ```python
  from flask import g
  if TYPE_CHECKING:
      class CurrentUser(TypedDict):
          id: int
          username: Optional[str]
          role: str
  ```
  并声明 g.current_user: CurrentUser。P0 不阻塞，P2-03（CI + 类型检查）阶段处理。

其他 PASS 项：

- 路由层调 service / service 调 model 的分层严格保持；P1 路由可以直接套 @login_required / @role_required("admin")。
- BizException 体系齐全（1001/1002/1003/1004/2001/2002/3001/3002/4001/5000），P1 各模块按需抛即可。
- 统一响应 {code, message, data} 已在 P0-02 落地，P1 路由不需要再处理响应格式。
- get_db() / close_db() 已在 app.core.database 导出，P1 service 接收 db: Session 即可。
- Pydantic schema 范式已建立（app/schemas/auth.py），P1-01 起按模块新增 data.py / model.py / email.py / log.py 即可。

---

## 8. requirements 兼容 Py 3.12 & 3.13 · FAIL

检查方法：对每条钉版本查询 PyPI 是否有 cp312 / cp313 wheel。

| 包 | 钉版本 | Py 3.12 wheel | Py 3.13 wheel | 评级 |
| --- | --- | --- | --- | --- |
| Flask | 3.0.3 | OK | OK | OK |
| pydantic | 2.7.1 | OK | FAIL（pydantic-core 2.18.2 无 cp313 wheel） | Py3.13 FAIL |
| pydantic-settings | 2.2.1 | OK | OK | OK |
| SQLAlchemy | 2.0.30 | OK | OK | OK |
| python-jose | 3.3.0 | OK | OK | OK |
| bcrypt | 4.1.2 | OK | OK | OK |
| pandas | 2.2.2 | OK | FAIL（PyPI 上 2.2.2 无 cp313 wheel；2.2.3 才有） | Py3.13 FAIL |
| numpy | 1.26.4 | OK | FAIL（numpy 1.26 系列最高 cp312） | Py3.13 FAIL |
| openpyxl | 3.1.2 | OK | OK | OK |
| scikit-learn | 1.4.2 | OK | FAIL | Py3.13 FAIL |
| xgboost | 2.0.3 | OK | FAIL | Py3.13 FAIL |
| joblib | 1.4.2 | OK | OK | OK |
| matplotlib | 3.8.4 | OK | FAIL | Py3.13 FAIL |
| seaborn | 0.13.2 | OK | FAIL | Py3.13 FAIL |
| openai | 1.51.0 | OK | OK | OK |

Py 3.12 兼容性：全部 OK。

Py 3.13 兼容性：7 个包无 cp313 wheel。

- 其中 pandas / numpy 是 P1-01（Excel 上传）必用，直接阻塞 P1-01。
- scikit-learn / xgboost / matplotlib / seaborn 阻塞 P1-04（训练）和 P1-03（可视化）。

根因：所有钉版本都发布于 2024-Q1 前后，当时 Py 3.13 还未稳定；后续 Py 3.13 发布后（2024-10），这些包只在补丁版本里补了 cp313 wheel（如 pandas 2.2.3、numpy 2.0+、scikit-learn 1.5+）。

P0 阶段的影响：

- P0-06 smoke 在 Py 3.13 上只装了后端 6 个核心包就过——但 P0-* 历史 smoke（P0-02~05）按 dev log 都是 Py 3.12.10 venv，依赖装得下。
- 当前系统 Python 切换到了 3.13，P1 阶段如果不处理 requirements，P1-01 一开工就会卡在 pip install。

修复方案（按优先级）：

1. 推荐：放宽到下一个补丁版本，API 兼容：
   ```
   pandas==2.2.2 → pandas>=2.2.3,<3
   numpy==1.26.4 → numpy>=1.26.4,<2
   scikit-learn==1.4.2 → scikit-learn>=1.4,<1.6
   xgboost==2.0.3 → xgboost>=2.0,<3
   matplotlib==3.8.4 → matplotlib>=3.8,<4
   seaborn==0.13.2 → seaborn>=0.13,<0.14
   pydantic==2.7.1 → pydantic>=2.7,<3
   ```
2. 或锁定 Py 3.12.10 环境（牺牲 Py 3.13 支持）。
3. 或加 python_version < '3.13' 标记（不推荐——用户明确要求兼容 Py 3.12 + 3.13）。

结论：FAIL —— 阻塞 P1-01 开工。

按 AI_RULES.md "技术方案不确定" 分支，写入 DECISION.md 走评审；定稿后回 P0-01 修订 requirements.txt，再批准 P1-01。

---

## 9. 技术债 · WARNING（汇总）

按严重度排序，全部已在对应 P2-* 任务里登记，不在 P1 范围：

| # | 技术债 | 影响 | 对应 P2 任务 | 阻塞 P1？ |
| --- | --- | --- | --- | --- |
| TD-01 | requirements.txt Py 3.13 不兼容 | 阻塞 P1-01 | 本 Gate 决议 | FAIL 阻塞 |
| TD-02 | g.current_user 无类型声明 | 编辑器/类型检查不友好 | P2-03 | 否 |
| TD-03 | 无 OperationLogService，每个 P1 service 重复 db.add(OperationLog); db.commit() | 代码冗余 | 应在 P1-04 之前补 | 否（WARNING 7-C） |
| TD-04 | matplotlib.use("Agg") 未在 P0 阶段预设 | P1-03 Windows headless 崩 | P1-03 必加 | 否（WARNING 7-A） |
| TD-05 | MySQL/PostgreSQL 驱动未列 requirements | 切生产时缺包 | P2-10 | 否 |
| TD-06 | 登录接口无防爆破限速 | 安全 | P2-06 | 否 |
| TD-07 | 无结构化日志 / 请求 ID 注入 | 排障能力 | P2-04 | 否 |
| TD-08 | 邮件 LLM 调用未走异步 | 长任务阻塞请求线程 | P2-05 | 否（教学项目可接受） |
| TD-09 | GET /data/statistics 等热点接口无缓存 | 性能 | P2-06 | 否 |
| TD-10 | password_hash 列宽 256 偏大 | 浪费存储 | 无需处理 | 否 |
| TD-11 | 无 pytest 测试套件 | 回归靠人 | P2-01 | 否 |
| TD-12 | 前端占位文件（api.js / app.js）含 P1-15 内容 | 早期泄漏未来代码 | 接受（脚手架性质） | 否 |

---

## Gate 决议

当前状态：FAIL · 暂停 P1。

唯一阻塞项：Q8（requirements.txt Py 3.13 不兼容）。

解锁步骤（约 5 分钟工作量）：

1. 在 DECISION.md 记录本 Gate Review 决议（决议项：requirements.txt Py 3.13 兼容方案）。
2. 三选一：
   - 方案 A（推荐）：把 pandas==2.2.2 / numpy==1.26.4 / scikit-learn==1.4.2 / xgboost==2.0.3 / matplotlib==3.8.4 / seaborn==0.13.2 / pydantic==2.7.1 放宽到兼容范围（如 pandas>=2.2.3,<3），保证 Py 3.12 + 3.13 都有 wheel。
   - 方案 B：钉死 Python 3.12.10，README 标注"仅支持 Py 3.12"。
   - 方案 C：CI 矩阵测两个版本，requirements.txt 维持原样，环境约束由 runtime.txt / pyproject.toml 锁。
3. 改完跑一次 pip install --dry-run -r requirements.txt 在 Py 3.13 上确认无冲突。
4. 更新 DEVELOPMENT_LOG.md / TODO.md 状态视图；将 Q8 改判 PASS；批准 P1-01。

Q1-Q7、Q9 全部 PASS（含 WARNING），技术债已识别且有归属，P0 主体质量过关。仅 Q8 阻断 P1 入口。

---

## 附录 A：P0 验证产物清单

| 产物 | 路径 | 状态 |
| --- | --- | --- |
| 目录树 | app/{api/v1,core,models,schemas,services,utils,static} | OK 100% 对齐 |
| Core 5 件套 | app/core/{config,database,response,security,dependencies}.py | OK |
| 6 ORM 表 | app/models/{user,customer,experiment,email_record,operation_log,prompt_template}.py | OK |
| 应用工厂 | app/__init__.py + run_flask.py | OK |
| 5 蓝图 | app/api/v1/{auth,data,model,email,log}.py | OK |
| 4 认证接口 | /api/v1/auth/{login,register,me,logout} | OK 9/9 smoke |
| SPA 入口 | app/static/{index.html,css/app.css,js/{api,app}.js} | OK 6/6 smoke |
| Bootstrap 5 CDN | https://cdn.jsdelivr.net/npm/bootstrap@5.3.0 | OK 实测 200 |

## 附录 B：评审参考

- docs/04_技术框架方案.md §4 目录 / §6 关键设计 / §7 数据模型 / §8 安全设计
- docs/03_API接口文档.md §0 通用约定 / §1 认证 / §0.5 业务码
- docs/01_PRD_产品需求文档.md §5.1 数据字段
- AI_RULES.md 修改规则 / 测试规则 / 问题分支
- TODO.md 任务依赖图