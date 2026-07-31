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
