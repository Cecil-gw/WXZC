"""P1-01-2 质量报告 · 单元测试 + Smoke test。"""
from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.response import BizException  # noqa: E402
from app.utils.data_processor import (  # noqa: E402
    check_required_columns,
    compute_quality_report,
    parse_excel,
    read_excel_to_df,
    validate_rows,
)


# -------- 工具 --------

def _valid_row(i: int) -> Dict[str, Any]:
    return {
        "id": i,
        "Gender": "Male" if i % 2 == 0 else "Female",
        "Age": 30 + i,
        "Driving_License": 1,
        "Region_Code": 28.0,
        "Previously_Insured": 0,
        "Vehicle_Age": "1-2 Year",
        "Vehicle_Damage": "Yes",
        "Annual_Premium": 30000.0 + i,
        "Policy_Sales_Channel": 152.0,
        "Vintage": 100 + i,
        "Response": 0,
    }


_COLUMNS = list(_valid_row(1).keys())


def _make_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    """造一个 12 列的 DataFrame（含 header）。"""
    return pd.DataFrame(rows, columns=_COLUMNS)


# -------- 用例 --------

def case_1_empty_dataframe() -> None:
    """空 DataFrame（仅 header 12 列） -> total=0, all missing=0, dup=0"""
    df = _make_df([])
    rep = compute_quality_report(df)
    assert rep["total_rows"] == 0
    assert rep["total_cols"] == 12
    assert all(v == 0 for v in rep["missing_values"].values())
    assert rep["duplicates"] == 0
    assert len(rep["dtypes"]) == 12
    print(f"[1] empty 12-col DataFrame -> total=0, cols=12, all missing=0, dup=0")


def case_2_no_missing() -> None:
    """10 行全齐 -> missing 全 0, dup=0"""
    rows = [_valid_row(i) for i in range(1, 11)]
    df = _make_df(rows)
    rep = compute_quality_report(df)
    assert rep["total_rows"] == 10
    assert rep["total_cols"] == 12
    assert all(v == 0 for v in rep["missing_values"].values())
    assert rep["duplicates"] == 0
    print(f"[2] 10 valid rows -> total=10, all missing=0, dup=0")


def case_3_with_missing() -> None:
    """部分列缺失 -> missing_values 准确"""
    rows = [
        _valid_row(1),
        {**_valid_row(2), "Age": None, "Vehicle_Damage": None},
        _valid_row(3),
        {**_valid_row(4), "Annual_Premium": None},
    ]
    df = _make_df(rows)
    rep = compute_quality_report(df)
    assert rep["total_rows"] == 4
    assert rep["missing_values"]["Age"] == 1
    assert rep["missing_values"]["Vehicle_Damage"] == 1
    assert rep["missing_values"]["Annual_Premium"] == 1
    assert rep["missing_values"]["Gender"] == 0
    print(f"[3] 3 cells missing across 2 rows -> missing per col OK")


def case_4_with_duplicates() -> None:
    """3 行完全重复 -> duplicates=3（保留首行）"""
    row = _valid_row(1)
    rows = [row, _valid_row(2), row, _valid_row(3), row]
    df = _make_df(rows)
    rep = compute_quality_report(df)
    assert rep["total_rows"] == 5
    assert rep["duplicates"] == 2  # keep first: 位置 0 不算，位置 2/4 算
    print(f"[4] row1 at 3 positions (0/2/4) -> dup=2 (keep=first)")


def case_5_dtypes_are_strings() -> None:
    """dtypes 全部 str（JSON 友好）"""
    rows = [_valid_row(i) for i in range(1, 4)]
    df = _make_df(rows)
    rep = compute_quality_report(df)
    for col, dt in rep["dtypes"].items():
        assert isinstance(dt, str), f"dtypes[{col}] is {type(dt).__name__}, expected str"
    assert "int" in rep["dtypes"]["Age"]
    assert "float" in rep["dtypes"]["Annual_Premium"]
    assert "object" in rep["dtypes"]["Gender"]
    print(f"[5] dtypes all str, sample=int{int}/{float}/{object}")


def case_6_mixed_types() -> None:
    """混合 int/float/str 列 -> dtypes 反映各列实际类型"""
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "Gender": ["M", "F", "M"],
        "Age": [20, 30, 40],
        "Driving_License": [1, 1, 0],
        "Region_Code": [28.0, 35.0, 12.0],
        "Previously_Insured": [0, 1, 0],
        "Vehicle_Age": ["< 1 Year", "1-2 Year", "> 2 Years"],
        "Vehicle_Damage": ["Yes", "No", "Yes"],
        "Annual_Premium": [30000.0, 40000.0, 50000.0],
        "Policy_Sales_Channel": [152.0, 26.0, 124.0],
        "Vintage": [100, 200, 300],
        "Response": [0, 1, 0],
    })
    rep = compute_quality_report(df)
    assert "int" in rep["dtypes"]["id"]
    assert "object" in rep["dtypes"]["Gender"]
    assert "float" in rep["dtypes"]["Region_Code"]
    print(f"[6] mixed types -> int+object+float all captured")


def case_7_check_required_columns_pass() -> None:
    """完整 12 列 -> check 不抛异常"""
    df = _make_df([_valid_row(1)])
    check_required_columns(df)
    print("[7] check_required_columns(完整 12 列) -> no exception")


def case_8_check_required_columns_fail() -> None:
    """缺 'Response' -> BizException(1001)"""
    df = pd.DataFrame({c: [1] for c in _valid_row(1).keys() if c != "Response"})
    try:
        check_required_columns(df)
    except BizException as e:
        assert e.code == 1001
        assert "Response" in e.message
        print(f"[8] check_required_columns(缺 Response) -> BizException(1001)")
        return
    raise AssertionError("expected BizException")


def case_9_read_excel_to_df_integration() -> None:
    """read_excel_to_df 端到端：FileStorage -> DataFrame"""
    rows = [_valid_row(i) for i in range(1, 4)]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        _make_df(rows).to_excel(writer, index=False, sheet_name="Sheet1")

    class FakeFile:
        def read(self):
            return buf.getvalue()
        filename = "test.xlsx"

    df = read_excel_to_df(FakeFile())
    assert len(df) == 3
    assert list(df.columns)[:3] == ["id", "Gender", "Age"]
    print(f"[9] read_excel_to_df -> {len(df)} rows, first 3 cols={list(df.columns)[:3]}")


def case_10_validate_rows_public() -> None:
    """validate_rows (P1-01-4 用的 public API) 返回 rows+errors"""
    rows = [_valid_row(1), {**_valid_row(2), "Age": "abc"}, _valid_row(3)]
    df = _make_df(rows)
    res = validate_rows(df)
    assert res["valid_count"] == 2
    assert res["error_count"] == 1
    assert res["errors"][0]["row_index"] == 1
    assert res["errors"][0]["column"] == "Age"
    print(f"[10] validate_rows (public API) -> valid=2, errors=1, err on row 1 col Age")


def main() -> int:
    cases = [
        case_1_empty_dataframe,
        case_2_no_missing,
        case_3_with_missing,
        case_4_with_duplicates,
        case_5_dtypes_are_strings,
        case_6_mixed_types,
        case_7_check_required_columns_pass,
        case_8_check_required_columns_fail,
        case_9_read_excel_to_df_integration,
        case_10_validate_rows_public,
    ]
    for c in cases:
        c()
    print()
    print("=" * 60)
    print(f"P1-01-2 smoke: {len(cases)} / {len(cases)} cases passed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
