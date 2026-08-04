"""Excel 解析工具层（工具/Util 层）。

归属：app/utils/data_processor.py —— 纯函数式 Excel 解析与校验。

思路：
- 纯函数（无 Flask/DB 依赖），输入 FileStorage/DataFrame，输出结构化结果；
- 必需列校验 + 列名映射（Excel 大写列名 → ORM 小写字段）；
- 逐行类型校验，单行失败不阻断整体，错误收集到 errors 列表；
- 质量报告：缺失值、重复行、数据类型统计。
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


# 必需列（Excel 原始列名，大写）
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

# Excel 列名 → ORM 字段名映射
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

# 字段类型校验
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


def parse_excel(file_storage: Any) -> Dict[str, Any]:
    """解析上传的 Excel 文件，返回校验后的数据。

    Returns
    -------
    dict
        {df, valid_rows, errors, valid_count, error_count, total_rows}
    """
    df = _read_excel_to_df(file_storage)
    check_required_columns(df)
    validation = validate_rows(df)
    return {
        "df": df,
        "valid_rows": validation["valid_rows"],
        "errors": validation["errors"],
        "valid_count": validation["valid_count"],
        "error_count": validation["error_count"],
        "total_rows": validation["total_rows"],
    }


def check_required_columns(df: pd.DataFrame) -> None:
    """校验 12 个必需列齐全。缺失抛 BizException(1001)。"""
    actual = set(df.columns)
    missing = [c for c in REQUIRED_COLUMNS if c not in actual]
    if missing:
        raise BizException(
            CODE_PARAM_ERROR,
            f"Excel 缺少必需列: {', '.join(missing)}",
            400,
        )


def validate_rows(df: pd.DataFrame) -> Dict[str, Any]:
    """逐行做字段类型校验。

    Returns
    -------
    dict
        {valid_rows, errors, valid_count, error_count, total_rows}
    """
    df_renamed = df.rename(columns=COLUMN_RENAME)
    reverse_rename = {v: k for k, v in COLUMN_RENAME.items()}

    valid_rows: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for row_idx, row in df_renamed.iterrows():
        row_dict: Dict[str, Any] = {}
        first_error = None
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
            valid_rows.append(row_dict)

    return {
        "valid_rows": valid_rows,
        "errors": errors,
        "valid_count": len(valid_rows),
        "error_count": len(errors),
        "total_rows": int(len(df_renamed)),
    }


def compute_quality_report(df: pd.DataFrame) -> Dict[str, Any]:
    """生成数据质量报告。

    Returns
    -------
    dict
        {total_rows, total_cols, missing_values, duplicates, dtypes}
    """
    missing_values = {col: int(df[col].isna().sum()) for col in df.columns}
    duplicates = int(df.duplicated().sum())
    dtypes = {col: str(df[col].dtype) for col in df.columns}
    return {
        "total_rows": int(len(df)),
        "total_cols": int(len(df.columns)),
        "missing_values": missing_values,
        "duplicates": duplicates,
        "dtypes": dtypes,
    }


# ====================================================================
# 内部辅助函数
# ====================================================================

def _read_excel_to_df(file_storage: Any) -> pd.DataFrame:
    """从 FileStorage 读取为 DataFrame。解析失败抛 BizException(2002)。"""
    try:
        data = file_storage.read()
        if not data:
            raise BizException(CODE_EXCEL_PARSE_ERROR, "上传文件为空", 400)
        return pd.read_excel(io.BytesIO(data))
    except BizException:
        raise
    except Exception as exc:
        raise BizException(CODE_EXCEL_PARSE_ERROR, f"Excel 解析失败: {exc}", 400) from exc


def _coerce(value: Any, target_type: Type[Any]) -> Any:
    """把 value 转换为 target_type。失败抛 ValueError/TypeError。"""
    if target_type is int:
        return int(value)
    if target_type is float:
        return float(value)
    if target_type is str:
        return str(value)
    raise TypeError(f"unsupported target type: {target_type}")