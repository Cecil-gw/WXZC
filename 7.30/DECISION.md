# 技术决策记录

## DECISION-001

日期：

2026-07-30

问题：

为什么选择SQLite？

方案：

A:
MySQL

B:
SQLite

决定：

选择SQLite

原因：

- 教学环境快速启动
- 零配置
- 后期可迁移MySQL

影响：

## DECISION-002

日期：
2026-07-31

问题：
`requirements.txt` 钉的版本在 Python 3.13 上无 cp313 wheel，pip 走 meson 源码构建又缺 `vswhere.exe`，直接阻塞 P1-01（Excel 上传必须用 pandas）。本轮 Gate Review（见 `P0_GATE_REVIEW.md` §8）判定 Q8 FAIL，决议如何修？

方案：

A（推荐）：放宽钉版本到下一个有 cp313 wheel 的兼容范围
B：锁死 Python 3.12.10 环境，文档标注"仅支持 Py 3.12"
C：CI 矩阵测两个版本，requirements.txt 维持原样，环境约束由 runtime.txt / pyproject.toml 锁

决定：
选择 A

原因：

- 用户明确要求"兼容 Python 3.12 与 3.13"（Gate Review Q8 原题），B/C 都违背这一点
- 选 A 的改动面最小（仅 requirements.txt 一文件，7 行），P0 已通过的代码不动
- 全部升级目标版本已实测在 Py 3.13 上有 cp313 wheel（`pip download --only-binary=:all: --python-version 3.13` 验证）：
  - pandas 2.2.3+（保留 2.x 主版本，不跨 3.x）
  - numpy 2.0+（跨 1.x → 2.x，但 pandas/scikit-learn/xgboost/matplotlib 2.0+ 均已官方支持 numpy 2.x）
  - pydantic 2.10+（保留 2.x 主版本）
  - scikit-learn 1.5+（保留 1.x 主版本）
  - xgboost 2.1+（跨 2.x → 3.x 之前最新是 2.x；放宽到 2.1~3.99 兼容 2.x/3.x 均可）
  - matplotlib 3.9+（保留 3.x 主版本）
  - seaborn 0.13.2（pure-python，Py 3.12/3.13 都有 wheel，原钉版本不动）
- 主版本升级（numpy 1.x → 2.x）影响面分析：
  - pandas 2.2.3+ 官方支持 numpy 2.x
  - scikit-learn 1.5+ 官方支持 numpy 2.x
  - xgboost 2.1+ 官方支持 numpy 2.x
  - matplotlib 3.9+ 官方支持 numpy 2.x
  - 项目自身代码未使用 numpy C API 任何 1.x-only 特性（仅 `pandas.read_excel` / `numpy.array` / `np.mean` 等标准用法）
  - 不阻塞 P1（训练/预测/可视化 API 表面不变）

影响：

- 修订后 `requirements.txt` 7 行：`pandas` / `numpy` / `pydantic` / `scikit-learn` / `xgboost` / `matplotlib` 改为 `>=` 范围；`seaborn==0.13.2` 不动
- P0-01 验收标准 4（"新虚拟环境 `pip install -r requirements.txt` 无冲突"）现在在 Py 3.12 + 3.13 双版本上成立
- Q8 由 FAIL 改判 PASS；批准 P1-01
- 同步给 P0 Gate Review 添加"已解锁"备注

回归：

- 改完跑 `pip install --dry-run -r requirements.txt` 在 Py 3.13 上确认无冲突
 - 在 Py 3.12 临时 venv 上同样跑一次确认无回归
 - 不重跑全部 P0 smoke（业务代码无变更），仅验证 `create_app()` + 6 表建表 + admin seed + `/api/v1/auth/login` 仍通过

## DECISION-004

日期：
2026-08-01

问题：
Review Mode 验收清单要求「上传文件大小限制 10MB」，但 `docs/01_PRD_产品需求文档.md §170` 的性能指标写明「38 万行 Excel 上传入库 < 60 秒」，§253 验收标准第 2 条要求「上传 Excel 后 customers 表有数据」。38 万行 x 12 列的 xlsx 实际体积约 12~20MB —— 若按 10MB 设限，真实数据集会被 413 直接拒绝，反而挂掉 PRD 明文写的验收项。两个需求存在直接冲突，如何取舍？

方案：

A：不设任何上限（维持现状）
B：按验收清单设 10MB
C（推荐）：设 50MB + 注册 RequestEntityTooLarge(413) 处理器，返回统一 JSON 信封

决定：
选择 C，上限 50MB

原因：

- A 无闸门：超大文件会被完整读入内存再交给 pandas，存在内存耗尽风险；且 werkzeug 默认无上限
- B 与 PRD §170 / §253 直接冲突：38 万行真实数据集（12~20MB）会被拒，导致核心验收流程不可用
- C 兼顾两侧：50MB 对 38 万行留出 2.5~4 倍余量，同时拦住恶意超大请求
- 附带修复一个真实体验缺口：不注册 413 处理器时，超限会落入通用 `Exception` 分支返回 `code=5000`「服务器内部错误」，把客户端错误误报成服务端故障；现按 `docs/03_API接口文档.md §0.5` 归类为参数错误 1001

实现：

| 位置 | 内容 |
| --- | --- |
| `app/__init__.py` | 模块级常量 `MAX_UPLOAD_BYTES = 50 * 1024 * 1024` |
| `app/__init__.py` `create_app()` | `app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES` |
| `app/__init__.py` 异常处理器 | `@app.errorhandler(RequestEntityTooLarge)` → `fail(1001, "上传文件超过50MB限制", 413)` |

处理器注册在通用 `HTTPException` 之前。`RequestEntityTooLarge` 是 `HTTPException` 子类，Flask 按异常类特异性优先匹配，因此能精确命中而不被通用分支吞掉。

响应契约：

```json
{
    "code": 1001,
    "message": "上传文件超过50MB限制",
    "data": null
}
```

影响：

- `work/acceptance_p1_data.py` 用例 A10 的断言值从 10MB 同步改为 50MB
- 新增 `work/smoke_upload_limit.py`（10 用例，全 PASS）
- 既有 6 份 smoke（P1-01-1 / P1-01-2 / P1-01 端到端 / P1-02 / P1-03 / P1-04）零回归

遗留：

- 50MB 是按 38 万行推算的经验值，未用真实数据集实测体积；若后续数据集更大需重新评估
- `MAX_CONTENT_LENGTH` 是全局请求体上限，对所有 POST 接口生效（含未来的 `/model/import` .joblib 上传），当前无接口需要超过 50MB
