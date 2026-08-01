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

**P1-04 完成。P1 累计 smoke 60/60（10+10+7+10+10+13）全绿。下一步 P1-05：GET /model/experiments + GET /model/best。**

---

# P2 机器学习模块

- [ ] 特征工程
- [ ] Logistic Regression / RandomForest / XGBoost
- [ ] ROC-AUC 评估
- [ ] 最佳模型保存

---

# P3 LLM 模块

- [ ] Prompt 模板
- [ ] 客户画像转换
- [ ] 邮件生成
- [ ] 邮件记录保存

---

# P4 前端

- [ ] 登录页面
- [ ] 数据管理页面
- [ ] 模型管理页面
- [ ] 邮件管理页面

---

# P5 测试部署

- [ ] API 测试
- [ ] 部署文档
- [ ] README
