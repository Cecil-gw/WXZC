# 项目分析报告 · 保险精准营销系统 Insurance AI

> 版本：v2（接管后重审）
> 编写人：技术负责人（AI）
> 编写日期：2026-07-30
> 依据：`AI_RULES.md`、`PROJECT_CONTEXT.md`、`TODO.md`、`docs/01~04`
> 快照对象：`D:\wx26.7.14\7.30\`


## 1. 当前项目状态

### 1.1 仓库物理状态（对 `D:\wx26.7.14\7.30\` 逐项清点）

- 根目录文件：
  - `AI_RULES.md`（1.1KB）· 协作与变更规则
  - `PROJECT_CONTEXT.md`（0.8KB）· 项目上下文
  - `TASKS.md`（0.8KB）· 粗粒度任务清单（P0~P5，未按 PRD 校准）
  - `DECISION.md`（0.3KB）· 记录 DECISION-001 采用 SQLite
  - `DEVELOPMENT_LOG.md`（19B）· 空模板
  - `CODE_REVIEW.md`（0.2KB）· 空模板
  - `TEST_REPORT.md`（0.4KB）· 示例内容（伪造 PASS，非真实产出）
  - `demo1.py`（0B）· 空占位
  - `PROJECT_ANALYSIS.md`（15KB，v1）· 本次将被 v2 覆盖
  - `TODO.md`（14.7KB）· 上一轮拆分的 P0/P1/P2 34 项任务
- 子目录：
  - `docs/`：01_PRD / 02_AI 技术方案 / 03_API 接口文档 / 04_技术框架方案 · **全部齐全并三方评审通过**
  - `data/`：空
  - `output/`：空
- 不存在的关键路径（对比 `docs/04_技术框架方案.md` 第 4 节目录树）：
  - `run_flask.py` / `requirements.txt` / `.env.example` / `.gitignore`
  - `app/`（`__init__.py` / `api/v1/*` / `core/*` / `models/*` / `schemas/*` / `services/*` / `utils/*` / `static/*`）
  - `data/models/`（`.joblib` 存放）· `instance/insurance.db`（SQLite）
  - `insurance_mvc_starter/`（教学骨架）
  - `tests/`、`README.md`

### 1.2 完成度定量评估

| 层级 | 权重 | 完成度 | 说明 |
| --- | ---: | ---: | --- |
| 需求 & 技术方案文档 | 20% | 95% | 4 份主文档评审通过；缺 `05_3天课程逐字稿.md` 与 README |
| 流程规范文档 | 5% | 40% | AI_RULES/PROJECT_CONTEXT/TASKS/DECISION 骨架已建；DEVELOPMENT_LOG/CODE_REVIEW/TEST_REPORT 未真实使用 |
| 目录结构 | 5% | 0% | 主项目目录树完全未落地 |
| 后端源码（core/models/services/api） | 35% | 0% | 未起 |
| 前端 SPA | 15% | 0% | 未起 |
| 数据 & 模型产物 | 5% | 0% | 无示例数据集、无 `.joblib` |
| 教学骨架 `insurance_mvc_starter/` | 5% | 0% | 未起 |
| 测试 & CI | 5% | 0% | 无 pytest、无用例、无 CI |
| 部署产物 | 5% | 0% | 无 README / Dockerfile / 启动脚本 |
| **加权合计** | 100% | **≈ 21%** | 主要由文档撑起，工程实体为 0 |

### 1.3 目录结构符合性判断

结论：**当前目录结构不符合 `docs/04_技术框架方案.md`**，具体差异如下：

- 缺失主项目根 `app/` 及其全部子目录（api/core/models/schemas/services/utils/static）；
- 缺失应用工厂、启动脚本、依赖清单、环境变量模板；
- 缺失教学骨架 `insurance_mvc_starter/`；
- `data/` 应存 `models/` 与示例 Excel，目前为空；
- 未初始化 `instance/`（SQLite 存放位置）。

好的一面：docs 目录、根目录流程文档命名规范；上一轮补写的 `PROJECT_ANALYSIS.md` / `TODO.md` 与 `AI_RULES.md` 同层，符合流程文档惯例。

### 1.4 TODO 合理性审查

对上一轮 `TODO.md`（P0-01 ~ P2-12，共 34 项）逐条核对 PRD/技术方案，整体覆盖完整，但有下列需要修订的地方（见本报告 `4. 风险点` 与 `5. 下一步开发计划`）：

- 遗漏项：
  1. **教学骨架 `insurance_mvc_starter/` 的启动脚本 & 独立 requirements**：TODO 只列了 P1-16，颗粒度偏粗，应单独拆一个 P0 级子任务（因为教学 Day 1 强依赖它）。
  2. **`data/models/` 目录 & `MODEL_DIR` 绝对路径**：在 P0-04 或 P1-04 中未明确"启动时自动创建 `data/models/`"这一步，Windows 下常见 404 隐患。
  3. **matplotlib Agg 后端强制切换 & 中文字体**：在 P1-03/P1-08 只提图表 API，未强制"进程启动即 `matplotlib.use('Agg')`"，容易在 Web Worker 里卡死；中文字体只放到 P2-07，若示例数据/教学场景需要中文轴标签则应前置。
  4. **登录失败限速、密码强度校验**：非功能安全需求，PRD 第 4 节含"防撞库枚举"，TODO 只覆盖了统一错误信息，未涉及限速。
  5. **CORS/静态资源相对路径**：单页应用 hash 路由 + 后端同源，未列 CORS 配置注意点。
- 需要收敛的项：
  6. **P2-05 异步化 & P2-09 OpenAPI** 与 3 天实训节奏冲突，建议标注为"课后扩展"，避免核心里程碑被拉长。
  7. **P2-10 Docker/生产化** 同上，MVP 完成后再纳入。
- 需要修正的字段：
  8. `TODO.md` 中"依赖关系速览"里 `P1-14` 缺一条上游依赖（`P1-04` 训练要记 `OperationLog`，`P1-14` 依赖训练动作产生日志），应显式添加。

上述条目在下文"下一步开发计划"里合并为具体的 TODO 修订建议（未修改文件本体，等你确认后再改）。


## 2. 已完成模块

按"能被下一步直接复用"的口径统计，只有文档与流程骨架可复用；代码/数据/前端/测试全为 0。

### 2.1 需求 & 技术方案（可作为契约直接消费）

- `docs/01_PRD_产品需求文档.md`：目标、角色/权限、7 大功能模块、非功能指标、数据字段、业务码、8 条验收标准、3 天里程碑，全部齐全。
- `docs/02_AI技术方案.md`：ML 两条链路（三算法 + 不平衡处理 + ROC-AUC + `predict_proba` + 分位数筛选 + scaler 一致性）与 LLM 两条链路（OpenAI 兼容协议 + Prompt 四要素 + Markdown 清理 + 降级）。
- `docs/03_API接口文档.md`：29 个接口契约（统一 `{code,message,data}`、鉴权约定、分页约定、错误码表）。
- `docs/04_技术框架方案.md`：五层分层、目录结构、6 张 ORM 表、关键设计（应用工厂、`teardown_appcontext`、`BizException`、RBAC 装饰器、三级异常处理）、扩展点、部署方案。

### 2.2 流程 & 规则骨架

- `AI_RULES.md`：变更前必须说明"原因/影响/方案"；禁止随意改目录结构、删模块、改 API 返回格式；遇冲突需先落 `DECISION.md`。
- `PROJECT_CONTEXT.md`：项目定位、技术栈、核心模块索引。
- `DECISION.md`：DECISION-001 已确认 SQLite（后期可平滑迁 MySQL）。
- `TODO.md`：上一轮拆好的 P0/P1/P2 34 项任务，含依赖速览。
- `PROJECT_ANALYSIS.md`（v1）：前一版分析报告，本次由 v2 覆盖。

### 2.3 尚未落地但已在方案里"半成品"式定义好的资产

以下内容在文档中已经写明具体实现细节，编码阶段可直接照抄成型：

- 应用工厂 `create_app()` 伪代码（04 文档 §6.1）
- 请求级 Session（04 文档 §6.2）
- 统一响应 + `BizException`（04 文档 §6.3、01 文档 §7）
- RBAC 装饰器（04 文档 §6.4）
- 特征工程 + `stratify=y` + `fit_transform` 只在训练集（02 文档 §2.3）
- 三算法工厂与不平衡处理参数（02 文档 §2.4）
- `joblib.dump({"model","scaler"})` + 预测复用 scaler（02 文档 §2.6）
- 分位数筛选 top 10%（02 文档 §2.7）
- LLM 调用 + Markdown 清理 + 降级（02 文档 §3.4）
- Prompt 模板 DB 化（02 文档 §3.5）

### 2.4 结论

代码交付物：**0**。文档交付物：**约 95% 完成**。项目处于"设计冻结、施工未开工"状态。


## 3. 缺失模块

以"从零到能跑通 PRD 8 条验收标准"为目标，逐层列出缺项：

### 3.1 基础设施

- `run_flask.py`、`requirements.txt`、`.env.example`、`.gitignore`
- `app/__init__.py`（`create_app`：蓝图注册 + `teardown_appcontext` + 三级异常处理器 + 启动 `create_all` + seed admin + seed Prompt）
- `app/core/`：`config.py`（pydantic-settings 读 .env）、`database.py`（engine/Session/Base/`get_db`/`close_db`）、`response.py`（`success` + `BizException`）、`security.py`（bcrypt + JWT）、`dependencies.py`（`login_required` + `role_required`）

### 3.2 数据层（6 张 ORM 表）

- `User` / `Customer` / `Experiment` / `EmailRecord` / `OperationLog` / `PromptTemplate`
- 关键索引：`Customer.predicted_prob`、`Experiment.is_best`、`PromptTemplate.is_active`
- 关系：`User 1—N OperationLog`、`Customer 1—N EmailRecord`

### 3.3 业务层 Services

- `DataService`：Excel 解析、字段映射、分批 5000 条 `bulk_insert_mappings`、统计/质量/EDA
- `MLService`：编码（Label/Ordinal/Standard）、`stratify` 拆分、`_get_model` 工厂（LR/RF/XGB + 不平衡处理）、指标、`is_best` 更新、模型持久化、`predict_all`（回写）、`predict_upload`（不入库）、导入导出
- `LLMService`：OpenAI 客户端惰性初始化、`generate_email` + Markdown 清理 + 失败降级
- `EmailService`：分位阈值筛选、批量生成、Prompt 模板 CRUD、记录 CRUD + 批量删除 + 状态标记

### 3.4 表现层 Blueprint（对齐 API 文档 29 个接口）

- `/api/v1/auth`（4）：login / register / me / logout
- `/api/v1/data`（5）：upload / customers / statistics / quality / visualization
- `/api/v1/model`（8）：train / experiments / best / predict / predict_upload / visualization / export / import
- `/api/v1/email`（10）：targets / generate / prompt(GET/PUT) / records(GET) / records/{id}(GET/PUT/PATCH/DELETE) / records(DELETE 批量)
- `/api/v1/logs`（1）：操作日志
- `/`（1）：前端 SPA 入口
- `app/schemas/`：Pydantic 请求体校验

### 3.5 工具层

- `utils/data_processor.py`：`encode_features`、`build_feature_matrix`、`reverse_encode`（LLM 反编码）
- `utils/visualizer.py`：EDA 4 图 + 模型评估 4 图；进程启动即 `matplotlib.use("Agg")`；中文字体或英文标签兜底

### 3.6 前端 SPA

- `static/index.html`、`static/css/app.css`、`static/js/api.js`、`static/js/app.js`
- hash 路由 + Bootstrap 5 布局 + 登录/数据/模型/邮件/日志页面
- RBAC 菜单：admin 11 项，user 7 项；请求自动注入 `Authorization`

### 3.7 数据与产物

- `data/sample_insurance.xlsx`（示例数据，方便开箱即跑与教学）
- `data/models/`（joblib 存放）
- `instance/insurance.db`（首次启动自动生成）

### 3.8 教学骨架

- `insurance_mvc_starter/`（纯 MVC 三层），Day 1 用；应有独立启动脚本

### 3.9 质量保障 & 交付

- `tests/`：pytest 覆盖认证/上传/训练/预测/邮件/权限
- `README.md`：一分钟启动 + 常见问题（bcrypt/passlib、matplotlib 中文字体、SQLite 锁、LLM Key）
- `DEVELOPMENT_LOG.md` / `TEST_REPORT.md`：按真实执行填写
- 可选：`.github/workflows/ci.yml`、`Dockerfile`


## 4. 风险点

风险按"影响×概率"排序，标注**技术/业务/交付**类型。

| ID | 类别 | 风险 | 触发条件 | 影响 | 对策（提前防御） |
| --- | --- | --- | --- | --- | --- |
| R1 | 技术 | 数据严重不平衡（正:负 ≈ 13:87），直接建模偏向多数类 | 未处理不平衡就训练 | ROC-AUC 掉到 0.5 左右，营销无效 | LR/RF `class_weight="balanced"`；XGB `scale_pos_weight`；`stratify=y` |
| R2 | 技术 | 训练/预测 `scaler` 不一致，特征分布偏移 | 预测时重新 `fit` 或漏加载 scaler | 预测概率不可信 | `joblib.dump({"model","scaler"})`；预测只 `transform` |
| R3 | 技术 | 38 万行 Excel 上传超时/锁库 | 单事务一次性 insert | 上传功能不可用 | 分批 5000 条 `bulk_insert_mappings`；每批 commit |
| R4 | 技术 | LLM API Key 未配置或服务抖动 | 缺 `LLM_API_KEY` 或网络失败 | 邮件功能失败 | `client=None` 兜底；单条失败不影响整体，`status=failed` |
| R5 | 技术 | LLM 输出带 Markdown 包裹（```json） | 大模型输出格式漂移 | JSON 解析失败 | 正则清理 + try/except 降级 |
| R6 | 安全 | 越权注册 admin | 注册接口接收 role | 权限漏洞 | 注册接口不接收 role；服务端硬编码 `user`；`role_required` 装饰器 |
| R7 | 安全 | 撞库/枚举用户名 | 错误信息区分"用户名不存在/密码错误" | 账号被暴力破解 | 统一"用户名或密码错误"；后续加登录限速（P2） |
| R8 | 技术 | matplotlib 主线程渲染 & 中文字体 | 未切 Agg / 未装字体 | 可视化接口挂/中文乱码 | 进程启动即 `matplotlib.use("Agg")`；中文字体前置或使用英文标签 |
| R9 | 技术 | Windows 相对路径 bug（`send_file` 404） | 用相对路径 | 模型导出下载失败 | `MODEL_DIR = os.path.abspath(...)`；启动时 `os.makedirs(exist_ok=True)` |
| R10 | 技术 | SQLite 并发写锁 | 训练 + 日志并发写 | 请求超时 | 训练串行化；短事务；生产切 PG/MySQL |
| R11 | 交付 | 依赖冲突（bcrypt 4.x + passlib） | 使用 passlib 包裹 bcrypt | 环境搭建失败 | 直接使用 bcrypt；锁死 `requirements.txt` |
| R12 | 交付 | 3 天实训节奏紧 | 教学 + 编码并行 | 教学目标不达标 | 主项目分层、骨架 MVC 双线；把 P2-05/09/10 移到"课后扩展" |
| R13 | 业务 | 前后端字段命名不一致（大小写、驼峰） | 未按 API 文档统一 | 前端渲染错、联调返工 | 契约驱动：所有 Schema 与响应对齐 `docs/03`；PR 走 API diff |
| R14 | 安全 | `.env` / `.joblib` / SQLite 被提交入仓 | 未配置 `.gitignore` | 密钥泄露 / 数据泄漏 | `.gitignore` 覆盖 `.env`、`instance/`、`data/models/` |
| R15 | 技术 | 前端相对路径 & CORS | 静态资源与 API 前缀混用 | 页面 404 或跨域失败 | Flask 静态与 API 同源；`api.js` 走相对前缀 `/api/v1` |
| R16 | 交付 | `TASKS.md` 与新 `TODO.md` 存在两套优先级 | 未合并 | 团队理解冲突 | 由 `TODO.md` 作为唯一事实；`TASKS.md` 保留为课程节奏视图，标注"以 TODO.md 为准" |
| R17 | 业务 | 上传/邮件生成同步阻塞 | 单请求跑长任务 | 前端超时 | 训练/批量生成留后台任务扩展点；接口先返摘要 |
| R18 | 交付 | 教学骨架 `insurance_mvc_starter/` 未启动 | Day 1 讲解无骨架 | 教学脱节 | 提前一天完成骨架（P0 阶段并行推进）|


## 5. 下一步开发计划

### 5.1 三条主线（并行推进）

- **主线 A · 主项目脚手架**：把 `app/` 目录树立起来并跑通"启动 → 登录 → SPA 空壳"。
- **主线 B · 教学骨架**：`insurance_mvc_starter/` 独立可跑，覆盖 Day 1 RBAC 登录 + Excel 上传。
- **主线 C · 数据与规范**：准备示例数据、锁定依赖、初始化 `.gitignore` / `.env.example` / `README`。

### 5.2 里程碑与验收（对齐 PRD 3 天节奏）

| 里程碑 | 时长 | 目标 | 关键交付物 | 验收（可直接跑的动作） |
| --- | --- | --- | --- | --- |
| M0 | 0.5d | 脚手架就绪 | `run_flask.py` / `requirements.txt` / `.env.example` / `app/__init__.py` / `app/core/*` / `app/models/*` / 首次启动建表 + seed admin + seed Prompt | `python run_flask.py` 起服，`GET /` 200，SQLite 文件生成 |
| M1 | 1d | 认证 + 数据闭环 + 教学骨架 | `/auth/*`、`/data/*`（upload/customers/statistics/quality/visualization）、`insurance_mvc_starter/` | admin 登录、上传示例 Excel、统计接口通、教学骨架独立可跑 |
| M2 | 1d | ML 闭环 | `/model/train`、`/model/experiments`、`/model/best`、`/model/predict`、`/model/predict_upload`、`/model/visualization`、导入导出 | 训练三算法，`is_best` 唯一为真；全量预测回写 `predicted_prob` |
| M3 | 0.5d | LLM 邮件 + 日志 | `/email/targets`、`/email/generate`、`/email/prompt`、`/email/records/*`、`/logs` | 未配 Key 时 status=failed；配 Key 时可生成 |
| M4 | 0.5d | 前端 SPA + 全链路联调 | `static/index.html`、`api.js`、`app.js`、CSS；RBAC 菜单 | PRD §8 八条验收全部通过 |
| M5 | 0.5d | 硬化 & 交付 | `tests/` 关键路径覆盖、`README.md`、真实 `TEST_REPORT.md`、`.gitignore` | `pytest -q` 全绿；README 一分钟启动 |

> M0/M1 起步阶段 Owner 建议 1 人前后端全栈；M2 前后端分工；M3~M4 联调阶段合流。

### 5.3 立即启动的 7 步动作（按顺序执行）

1. `TODO.md` 修订（不动业务代码）：吸收本报告 §1.4 的 8 条修订建议，主要是"data/models 自动创建 & 绝对路径"、"matplotlib Agg 前置"、"登录限速前置为 P1"、"P2-05/09/10 标注为课后扩展"、"P1-14 依赖显式补全"、"教学骨架单列 P0 子任务"。
2. 落地根目录基础文件：`requirements.txt` / `.env.example` / `.gitignore` / `README.md`（占位版）。
3. 创建 `app/` 目录树 + `app/core/*` 五件套 + `app/__init__.py`（应用工厂）+ `run_flask.py`。
4. 建 `app/models/*` 6 张表 + `Base.metadata.create_all`，首次启动 seed `admin/admin123` 与默认 Prompt。
5. 完成 `/auth/*` 与 `GET /`（SPA 空壳），跑通 M0 验收。
6. 拉起 `insurance_mvc_starter/` 教学骨架（与 M1 并行）。
7. 按 M1→M2→M3→M4→M5 顺序推进，每完成一项：更新 `TODO.md` 状态、`DEVELOPMENT_LOG.md` 追加一行、`TEST_REPORT.md` 记录接口测试结果。

### 5.4 编码前需要你确认的 3 件事

1. **LLM 供应商与模型**：默认按 02 文档 = qwen-flash（OpenAI 兼容协议），API Key 是否已有？没有则 M3 阶段以"降级 status=failed"验收，不阻断交付。
2. **示例数据集来源**：是否采用公开 Health Insurance Cross Sell Prediction 数据？可先放 1000 行样本；如你有真实内部脱敏数据请给出路径。
3. **是否保留 `TASKS.md` 与新 `TODO.md` 并存**：建议保留 `TASKS.md` 作为"教学节奏视图"，在文件头显式声明"以 TODO.md 为准"；如你希望合并，我把 `TASKS.md` 内容并入 `TODO.md` 后删除。

### 5.5 本轮不做的事（明确边界）

- 不修改任何业务代码（当前也没有）。
- 不改动 `docs/01~04` 四份评审通过的文档。
- 不动 `AI_RULES.md` / `PROJECT_CONTEXT.md` / `DECISION.md` 的既有条款。
- `TODO.md` 的修订建议只列在本报告中，等你确认后再改文件。

---

> 完成本报告后进入等待状态。请在你决定的时刻下达"开始 M0"或"先修订 TODO"等指令，我按 `AI_RULES.md` 的流程推进。
