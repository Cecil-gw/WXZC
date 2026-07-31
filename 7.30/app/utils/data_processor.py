"""Excel 解析 + 列校验 + 行级类型校验 + 质量报告。

设计要点：
- 纯函数（无 Flask / DB 依赖），输入 FileStorage / DataFrame，输出结构化结果；
- 单行类型校验失败不阻断整体，错误收集到 errors 列表；
- 缺失必需列 / 解析失败抛 BizException；
- 质量报告 dtypes 转 str 防 JSON 序列化报错。

P1-01 拆分：
- P1-01-1 提供 parse_excel(file_storage) + read_excel_to_df + check_required_columns + validate_rows
- P1-01-2 新增 compute_quality_report(df)
- P1-01-3 消费 rows 写入 DB（本模块不涉及）
- P1-01-4 Service 编排本模块 + DB 写入
"""

from __future__ import annotations

import io
from typing import Any, Dict, List, Type

import pandas as pd

from app.core.response import (
    CODE_EXCEL_PARSE_ERROR,
    CODE_PARAM_ERROR,
    BizException,
)


# 必需 12 列（与 docs/03 §2.1 + docs/01 §5.1 + docs/04 §7 一致）
REQUIRED_COLUMNS: List[str] = [
    "id",
    "Gender",
    "Age",
    "Driving_License",
    "Region_Code",
    "Previously_Insured",
    "Vehicle_Age",
    "Vehicle_Damage",
    "Annual_Premium",
    "Policy_Sales_Channel",
    "Vintage",
    "Response",
]

# Excel 列名 -> ORM 字段名（"id" 保持小写，identity，不进映射）
COLUMN_RENAME: Dict[str, str] = {
    "Gender": "gender",
    "Age": "age",
    "Driving_License": "driving_license",
    "Region_Code": "region_code",
    "Previously_Insured": "previously_insured",
    "Vehicle_Age": "vehicle_age",
    "Vehicle_Damage": "vehicle_damage",
    "Annual_Premium": "annual_premium",
    "Policy_Sales_Channel": "policy_sales_channel",
    "Vintage": "vintage",
    "Response": "response",
}

# 字段类型：int / float / str（用于逐行校验）
_FIELD_TYPES: Dict[str, Type[Any]] = {
    "id": int,
    "gender": str,
    "age": int,
    "driving_license": int,
    "region_code": float,
    "previously_insured": int,
    "vehicle_age": str,
    "vehicle_damage": str,
    "annual_premium": float,
    "policy_sales_channel": float,
    "vintage": int,
    "response": int,
}


# ====================================================================
# 公开 API：解析 / 列校验 / 行校验 / 质量报告
# ====================================================================

def parse_excel(file_storage: Any) -> Dict[str, Any]:
    """解析上传的 Excel 文件，做列校验与字段类型校验。

    Parameters
    ----------
    file_storage : FileStorage
        Flask ``request.files['file']`` 对象。

    Returns
    -------
    dict
        ``{rows, errors, valid_count, error_count, total_rows}``

    Raises
    ------
    BizException
        - ``code=2002``：Excel 解析失败（文件损坏 / 空文件 / 非 xlsx/xls）
        - ``code=1001``：缺少必需列
    """
    df = read_excel_to_df(file_storage)
    check_required_columns(df)
    return validate_rows(df)


def read_excel_to_df(file_storage: Any) -> pd.DataFrame:
    """从 FileStorage 读取为 DataFrame。解析失败抛 BizException(2002)。

    公开 API，供 P1-01-4 Service 编排使用（与 parse_excel 共享 IO 步骤）。
    """
    try:
        data = file_storage.read()
        if not data:
            raise BizException(CODE_EXCEL_PARSE_ERROR, "上传文件为空", 400)
        # pandas 根据文件头自动选 engine（xlsx -> openpyxl，xls -> xlrd）
        return pd.read_excel(io.BytesIO(data))
    except BizException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise BizException(CODE_EXCEL_PARSE_ERROR, f"Excel 解析失败: {exc}", 400) from exc


def check_required_columns(df: pd.DataFrame) -> None:
    """校验 12 个必需列齐全。缺失抛 BizException(1001)。

    公开 API，供 P1-01-4 Service 在拿到 df 后独立校验（不必走 parse_excel 全流程）。
    """
    actual = set(df.columns)
    missing = [c for c in REQUIRED_COLUMNS if c not in actual]
    if missing:
        raise BizException(
            CODE_PARAM_ERROR,
            f"Excel 缺少必需列: {', '.join(missing)}",
            400,
        )


def validate_rows(df: pd.DataFrame) -> Dict[str, Any]:
    """逐行做字段类型校验（公开 API，供 P1-01-4 Service 复用）。

    Parameters
    ----------
    df : pd.DataFrame
        已重命名或未重命名的 DataFrame（内部统一 rename 到 ORM 字段名）。

    Returns
    -------
    dict
        ``{rows, errors, valid_count, error_count, total_rows}``
    """
    # 重命名到 ORM 字段名，方便统一按 _FIELD_TYPES 访问
    df_renamed = df.rename(columns=COLUMN_RENAME)
    # 反向映射：ORM 字段名 -> Excel 列名（错误信息里报告 Excel 原名列，方便用户定位）
    reverse_rename = {v: k for k, v in COLUMN_RENAME.items()}

    rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for row_idx, row in df_renamed.iterrows():
        row_dict: Dict[str, Any] = {}
        first_error: Dict[str, Any] = None
        for orm_field, target_type in _FIELD_TYPES.items():
            value = row.get(orm_field)
            try:
                if pd.isna(value):
                    raise ValueError("值缺失")
                converted = _coerce(value, target_type)
            except (ValueError, TypeError) as exc:
                first_error = {
                    "row_index": int(row_idx),
                    "column": reverse_rename.get(orm_field, orm_field),
                    "value": None if pd.isna(value) else str(value),
                    "error": f"类型/值错误: {exc}",
                }
                break
            row_dict[orm_field] = converted

        if first_error is not None:
            errors.append(first_error)
        else:
            rows.append(row_dict)

    return {
        "rows": rows,
        "errors": errors,
        "valid_count": len(rows),
        "error_count": len(errors),
        "total_rows": int(len(df_renamed)),
    }


def compute_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """生成数据质量报告（与 docs/03 §2.1 quality_report 字段对齐）。

    Parameters
    ----------
    df : pd.DataFrame
        原始 DataFrame（来自 pd.read_excel，列名用 Excel 原名 Gender/Annual_Premium 等，
        不必 rename）。

    Returns
    -------
    dict
        ``{
            "total_rows": int,
            "total_cols": int,
            "missing_values": {col: int count},
            "duplicates": int,
            "dtypes": {col: str},   # 全部转 str 防 JSON 序列化报错
        }``
    """
    missing_values = {col: int(df[col].isna().sum()) for col in df.columns}
    # pandas df.duplicated 默认 keep=first，全 NaN 行不计入重复
    duplicates = int(df.duplicated().sum())
    # pandas dtype 是 np.dtype 对象，JSON 不能直接序列化；统一转 str
    dtypes = {col: str(df[col].dtype) for col in df.columns}
    return {
        "total_rows": int(len(df)),
        "total_cols": int(len(df.columns)),
        "missing_values": missing_values,
        "duplicates": duplicates,
        "dtypes": dtypes,
    }


# ====================================================================
# 内部
# ====================================================================

def _coerce(value: Any, target_type: Type[Any]) -> Any:
    """把 value 转换为 target_type。失败抛 ValueError / TypeError。"""
    if target_type is int:
        return int(value)
    if target_type is float:
        return float(value)
    if target_type is str:
        return str(value)
    raise TypeError(f"unsupported target type: {target_type}")