# P1-01 任务拆分 · Excel 上传模块

> 拆分原则：每个子任务 30~90 分钟，可独立开发、独立 smoke、独立 commit。
> 拆分依据：`docs/03_API接口文档.md §2.1` + `docs/04_技术框架方案.md §5`。

## 拆分概览

| 子任务 | 范围 | 文件 | 预计工时 | 依赖 | 状态 |
| --- | --- | --- | --- | --- | --- |
| P1-01-1 | Excel 解析器 | `app/utils/data_processor.py` | 60 min | 无 | **本轮** |
| P1-01-2 | 质量报告 | `app/utils/data_processor.py` | 30 min | P1-01-1 | 待 |
| P1-01-3 | 批量入库 | `app/services/data_service.py` | 45 min | P1-01-1 | 待 |
| P1-01-4 | Service 编排 | `app/services/data_service.py` | 30 min | P1-01-1/2/3 | 待 |
| P1-01-5 | API 路由 | `app/api/v1/data.py` | 30 min | P1-01-4 | 待 |
| P1-01-6 | Smoke + 边界 | `work/smoke_p101.py` | 30 min | P1-01-5 | 待 |

合计 ~225 min（约 4 小时）。

## P1-01-1 · Excel 解析器（首子任务）

**范围**：
- `app/utils/data_processor.py`（新建）
- `app/utils/__init__.py`（保持 P0 末的 0 字节占位）

**输入**：`FileStorage`（Flask `request.files['file']`）

**输出**（标准结构）：
```
{
    "rows": list[dict],     # 合法的行（已 rename 到 ORM 字段名）
    "errors": list[dict],   # 非法行明细 [{row_index, column, value, error}]
    "valid_count": int,
    "error_count": int,
    "total_rows": int
}
```

**验收标准**：
1. 支持 `.xlsx`（openpyxl 引擎）与 `.xls`
2. 必需 12 列白名单：id/Gender/Age/Driving_License/Region_Code/Previously_Insured/Vehicle_Age/Vehicle_Damage/Annual_Premium/Policy_Sales_Channel/Vintage/Response
3. 缺列 → 抛 `BizException(1001, ...)`
4. 字段类型校验（int/float/str），单行错误不阻断整体
5. 解析失败 → `BizException(2002, ...)`
6. 非法数据收集到 `errors` 字段，不抛异常
7. 单元测试覆盖：合法 / 缺列 / 缺字段 / 类型错 / 空文件 / xls

**禁止**：
- 数据库写入
- API 路由
- Service 层（仅在 utils 层）
- bulk_insert
- quality_report（属于 P1-01-2）

## P1-01-2 · 质量报告

**范围**：`app/utils/data_processor.py::compute_quality_report()`

**输入**：`pd.DataFrame`

**输出**：`{total_rows, total_cols, missing_values, duplicates, dtypes}`

**验收**：
- 复用 P1-01-1 的解析结果（不入库）
- `dtypes` 转 str 防 JSON 序列化报错
- 单测：空 DataFrame、有缺失、有重复

## P1-01-3 · 批量入库

**范围**：`app/services/data_service.py::bulk_insert()`

**输入**：`db: Session`, `rows: list[dict]`, `batch_size: int = 5000`

**输出**：`int`（写入条数）

**验收**：
- 先 `db.query(Customer).delete()` 清空（业务主键策略，对齐 Gate Review 5-A）
- 分批 `bulk_insert_mappings(Customer, rows)`，最后 `db.commit()`
- 38 万行 / 5000 一批 = 76 次
- 单测：插入 10 行、插入 10001 行（验证分批）、Customer 表无残留

## P1-01-4 · Service 编排

**范围**：`app/services/data_service.py::DataService.upload()`

**输入**：`db: Session`, `file_storage`

**输出**：`{imported_count, quality_report}`

**验收**：
- 串联 P1-01-1 / P1-01-2 / P1-01-3
- 暂不写 OperationLog（对齐 P0 Gate Review WARNING 7-C：统一在 P1-04 之后建 `OperationLogService`）
- 单测：完整流程 + 缺列时不上 DB

## P1-01-5 · API 路由

**范围**：`app/api/v1/data.py`（占位 → 实装）

**实现**：
- `POST /data/upload` + `@login_required`
- `request.files.get('file')` 非空检查 → 1001
- 扩展名白名单（.xlsx/.xls）→ 1001
- 调 `DataService.upload(db, file)`
- 错误统一由全局 errorhandler 转 `{code, message, data}`

**单测**：HTTP 客户端级别（不写 Flask test，端到端 smoke 在 P1-01-6）

## P1-01-6 · Smoke + 边界

**范围**：`work/smoke_p101.py`

**用例**：
1. 未带 token → 1002
2. 无 file 字段 → 1001
3. 错扩展名 → 1001
4. 缺列 → 1001
5. 合法 xlsx（10 行）→ 200 / `code=0` / `imported_count=10`
6. 直查 SQLite 确认 10 行入库
7. 二次上传（清空策略）→ 旧数据被覆盖，新行数 = 新文件

## 依赖图

```
P1-01-1 ──> P1-01-2 ─┐
       └─> P1-01-3 ─┴─> P1-01-4 ─> P1-01-5 ─> P1-01-6
```

P1-01-2 与 P1-01-3 互不依赖，可并行开发；P1-01-4 串行。

## 不在本任务拆分范围

- P1-02 客户分页查询
- P1-03 统计 / 质量接口 / EDA 可视化
- 任何 P1-04+ 模型/邮件/日志功能