# 项目任务列表

> 高层任务视图。详细子任务见 `TASK_BREAKDOWN.md`（按 P0/P1 模块拆分）。
> 状态：`[x]` 已完成 · `[/]` 进行中 · `[ ]` 未开始 · `[!]` 阻塞

---

# P0 基础环境

- [x] Flask 项目结构（见 `P0-01`）
- [x] 数据库配置（见 `P0-02/03`）
- [x] JWT 认证（见 `P0-05`）
- [x] 应用工厂 + 蓝图（见 `P0-04`）
- [x] 前端 SPA 入口（见 `P0-06`）
- [x] P0 Gate Review（见 `P0_GATE_REVIEW.md`）—— Q8 已解锁（DECISION-002）

---

# P1 数据模块

## P1-01 Excel 上传（拆分见 TASK_BREAKDOWN.md）

- [x] **P1-01-1** Excel 解析器（utils/data_processor.py）· 10/10 smoke PASS
- [x] **P1-01-2** 质量报告（utils/data_processor.py）· 10/10 smoke PASS
- [x] **P1-01-3** 批量入库（services/data_service.py::bulk_insert）
- [x] **P1-01-4** Service 编排（services/data_service.py::DataService.upload）
- [x] **P1-01-5** API 路由（api/v1/data.py::POST /upload）
- [x] **P1-01-6** Smoke + 边界（work/smoke_p101.py）· 7/7 PASS

**P1-01 整体 27/27 smoke 全绿（10+10+7）**

## P1-02 客户分页查询 · [x] 已完成

- [x] P1-02-1 Customer.paginate() Model 静态方法
- [x] P1-02-2 DataService.list_customers() Service 编排
- [x] P1-02-3 GET /customers 路由 + _int_arg 辅助
- [x] P1-02-4 Smoke 10 用例（work/smoke_p102.py）· 10/10 PASS

**P1-02 完成。P1 累计 smoke 37/37（10+10+7+10）全绿。**

## P1-03 数据统计 / 质量接口 / EDA 可视化 · [x] 已完成

- [x] P1-03-1 visualizer.py 4 个 chart 函数（matplotlib Agg）
- [x] P1-03-2 DataService.statistics / quality / visualization
- [x] P1-03-3 3 个 GET 路由（/statistics / /quality / /visualization/<chart_type>）
- [x] P1-03-4 Smoke 10 用例（work/smoke_p103.py）· 10/10 PASS

**P1-03 完成。P1 累计 smoke 47/47（10+10+7+10+10）全绿。**

## P1-04 模型模块 · 特征工程与训练 · [x] 已完成

- [x] P1-04-1 operation_log_service.log（补 P0 Gate WARNING 7-C）
- [x] P1-04-2 data_processor.prepare_features（Label / Ordinal 编码 + FEATURE_NAMES）
- [x] P1-04-3 ml_service._get_model / MLService.train（stratify + scaler 防泄漏 + 不平衡处理 + ROC-AUC 选优 + joblib bundle + experiments 落库）
- [x] P1-04-4 POST /model/train（admin only）+ 操作日志
- [x] P1-04-5 Smoke 13 用例（work/smoke_p104.py）· 13/13 PASS

**P1-04 完成。P1 累计 smoke 60/60（10+10+7+10+10+13）全绿。**

## DECISION-004 上传大小限制（50MB）· [x] 已完成

- [x] `MAX_CONTENT_LENGTH = 50MB` + `RequestEntityTooLarge` 处理器返回 code=1001
- [x] Smoke 10 用例（work/smoke_upload_limit.py）· 10/10 PASS

## P1-05 模型模块 · 实验记录 / 最佳模型查询 · [x] 已完成

- [x] P1-05-1 Experiment.paginate + to_dict（params 反序列化，created_at desc + id desc 兜底）
- [x] P1-05-2 MLService.list_experiments（per_page 上限 200 + model_name 白名单）
- [x] P1-05-3 MLService.get_best（无最佳模型 → 3002，用 first() 防脏数据）
- [x] P1-05-4 GET /model/experiments + GET /model/best（仅需登录，docs §3.2/§3.3 未限 admin）
- [x] P1-05-5 Smoke 20 用例（work/smoke_p105.py）· 20/20 PASS

**P1-05 完成。P1 累计 smoke 80/80（10+10+7+10+10+13+10+20）全绿。**

## P1-06 模型模块 · 全量预测 · [x] 已完成

- [x] P1-06-1 MLService.predict（定位模型 → _load_bundle 校验 → scaler 只 transform → predict_proba → 分批回写）
- [x] P1-06-2 POST /model/predict（可选 model_name 覆盖）+ 操作日志 action=prediction
- [x] P1-06-3 Smoke 18 用例（work/smoke_p106.py）· 18/18 PASS
- [x] P1-06-4 BUG-016 修复：smoke_p104 / smoke_p106 改为自清理表，不依赖删 db 文件

**P1-06 完成。P1 累计 smoke 98/98 全绿。**

## P1-07 模型模块 · 上传数据预测 · [x] 已完成

- [x] P1-07-1 重构：提取 _resolve_experiment（/predict 与 /predict_upload 共用模型定位），重跑 P1-06 确认无回归
- [x] P1-07-2 _prob_statistics（0.9 分位数高潜阈值，依据 docs/02 §2.7）
- [x] P1-07-3 MLService.predict_upload（不入库；不要求 Response 列；id 缺失用行号兜底；按概率倒序）
- [x] P1-07-4 POST /model/predict_upload（扩展名白名单 + 可选 model 表单字段）+ 操作日志
- [x] P1-07-5 Smoke 23 用例（work/smoke_p107.py）· 23/23 PASS

**P1-07 完成。P1 累计 smoke 121/121 全绿。**

## P1-08 模型模块 · 评估可视化 · [x] 已完成

- [x] P1-08-1 visualizer 追加 4 个评估图函数（roc_curve / metrics_comparison / confusion_matrix / feature_importance），P1-03 的 EDA 函数零改动
- [x] P1-08-2 MLService.visualization + _latest_per_model（每算法取最新）+ _experiment_params（损坏 params 转 3002）
- [x] P1-08-3 GET /model/visualization/<chart_type>（model 参数对两种单模型图必填）
- [x] P1-08-4 Smoke 23 用例（work/smoke_p108.py）· 23/23 PASS，含逐像素图像内容核验

**P1-08 完成。P1 累计 smoke 144/144（10+10+7+10+10+13+20+18+23+23+10）全绿。**

## P1-09 模型模块 · 导入导出 · [x] 已完成

- [x] P1-09-1 MLService.export_model（SUPPORTED_MODELS 白名单 + os.path.commonpath 二次路径归属校验）
- [x] P1-09-2 _infer_model_name + _ESTIMATOR_CLASS_MAP（落盘名由 bundle 内 estimator 类名推断，不采用上传文件名）
- [x] P1-09-3 MLService.import_model（临时文件先校验 bundle 结构，os.replace 覆盖，finally 清理；坏文件不污染已有模型）
- [x] P1-09-4 GET /model/export/<model_name>（send_file 二进制流）+ POST /model/import（记 model_import 日志），两者仅 admin
- [x] P1-09-5 Smoke 25 用例（work/smoke_p109.py）· 25/25 PASS，连跑两遍幂等

**P1-09 完成。P1 累计 smoke 169/169 全绿。P1 模型模块（P1-04~P1-09）全部收口。**

## P1-10 邮件模块 · 高潜客户筛选 · [x] 已完成

- [x] P1-10-1 Customer.predicted_probs（只取概率列供分位数计算）+ paginate_by_prob（阈值过滤 + 概率倒序、id 兜底）+ to_target_dict（docs §4.1 的五字段）
- [x] P1-10-2 新建 app/services/email_service.py，EmailService.targets 复用 ml_service._HIGH_POTENTIAL_QUANTILE（DEBT-P107-2，不另定义默认值）
- [x] P1-10-3 GET /email/targets（percentile 开区间 (0,1) 校验 + _float_arg 拦 nan/inf）
- [x] P1-10-4 Smoke 23 用例（work/smoke_p110.py）· 23/23 PASS，含阈值与 np.quantile 精确比对（1e-9）
- [x] P1-10-5 集成校验（work/smoke_p110_integration.py）：train → predict → targets 全链路 PASS

**P1-10 完成。P1 累计 smoke 192/192（10+10+7+10+10+13+20+18+23+23+25+23+10）全绿。下一步 P1-11：POST /email/generate 邮件生成（docs/03 §4.2，未配置 LLM_API_KEY 时 status=failed）。**

---

# P2 机器学习模块

> 本板块四项已在 P1-04 / P1-05 落地，此处补齐勾选并标注实现位置。

- [x] 特征工程 —— `app/utils/data_processor.py::prepare_features`（Label / Ordinal 编码 + FEATURE_NAMES）· P1-04
- [x] Logistic Regression / RandomForest / XGBoost —— `app/services/ml_service.py::_get_model`（class_weight / scale_pos_weight 不平衡处理）· P1-04
- [x] ROC-AUC 评估 —— `ml_service.train` 用 `roc_auc_score` 选优；`experiments.params` 存 ROC/CM/特征重要性 · P1-04 + P1-05
- [x] 最佳模型保存 —— `joblib.dump({"model","scaler"})` 落盘 + `is_best` 唯一标记；`GET /model/best` 可查 · P1-04 + P1-05

---

# P3 LLM 模块

- [x] Prompt 模板（P1-12 邮件模板管理）
- [x] 客户画像转换（P1-11 naturalize() 反编码）
- [x] 邮件生成（P1-11 LLMService + 降级策略）
- [x] 邮件记录保存（P1-13 EmailRecord CRUD）

---

# P4 前端

- [x] 登录页面（P1-15 SPA + MVC 骨架）
- [x] 数据管理页面（P1-15 客户列表/上传/统计/质量）
- [x] 模型管理页面（P1-15 训练/实验/评估/导入导出）
- [x] 邮件管理页面（P1-15 邮件中心 + 生成/记录/模板）

---

# P5 测试部署

- [x] API 测试（P2-01 pytest 36/36 全绿 + work/ 下 340+ smoke）
- [x] 部署文档（P2-02 README.md）
- [x] README（P2-02 README.md）
