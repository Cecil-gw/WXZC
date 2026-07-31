"""P1-01-1 Excel 解析器 · 单元测试 + Smoke test。

说明：P0 阶段未引入 pytest（P2-01 任务），本轮采用 smoke-style 断言脚本。
所有用例通过 Flask test_client 之外的纯函数测试，传入内存 FileStorage。
"""
from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.response import BizException  # noqa: E402
from app.utils.data_processor import parse_excel  # noqa: E402


class FakeFile:
    """模拟 Flask FileStorage：支持 .read() / .filename。"""

    def __init__(self, data: bytes, filename: str = "test.xlsx") -> None:
        self._data = data
        self.filename = filename

    def read(self) -> bytes:
        return self._data


def _make_xlsx(rows: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> bytes:
    """生成 xlsx 二进制。"""
    if columns is None:
        columns = [
            "id", "Gender", "Age", "Driving_License", "Region_Code",
            "Previously_Insured", "Vehicle_Age", "Vehicle_Damage",
            "Annual_Premium", "Policy_Sales_Channel", "Vintage", "Response",
        ]
    df = pd.DataFrame(rows, columns=columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return buf.getvalue()


def _valid_row(i: int) -> Dict[str, Any]:
    """生成一行合规数据。"""
    return {
        "id": i,
        "Gender": "Male" if i % 2 == 0 else "Female",
        "Age": 30 + (i % 30),
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


# -------- 用例 --------

def case_1_valid_10_rows() -> None:
    """合法 10 行 xlsx -> 全部 valid, 0 errors"""
    rows = [_valid_row(i) for i in range(1, 11)]
    xlsx = _make_xlsx(rows)
    res = parse_excel(FakeFile(xlsx))
    assert res["valid_count"] == 10, f"valid_count={res['valid_count']}"
    assert res["error_count"] == 0, f"error_count={res['error_count']}"
    assert res["total_rows"] == 10
    assert len(res["rows"]) == 10
    # ORM 字段名已 rename
    r0 = res["rows"][0]
    assert r0["id"] == 1
    assert r0["gender"] == "Female"  # i=1 -> 1%2==1 -> Female
    assert r0["age"] == 31
    assert r0["region_code"] == 28.0
    assert r0["annual_premium"] == 30001.0
    print(f"[1] valid 10 rows -> valid={res['valid_count']}, errors={res['error_count']}, total={res['total_rows']}")


def case_2_missing_column() -> None:
    """缺 'Response' 列 -> BizException(1001)"""
    cols = [
        "id", "Gender", "Age", "Driving_License", "Region_Code",
        "Previously_Insured", "Vehicle_Age", "Vehicle_Damage",
        "Annual_Premium", "Policy_Sales_Channel", "Vintage",
        # 缺 Response
    ]
    rows = [_valid_row(i) for i in range(1, 4)]
    xlsx = _make_xlsx(rows, columns=cols)
    try:
        parse_excel(FakeFile(xlsx))
    except BizException as e:
        assert e.code == 1001, f"code={e.code}"
        assert "Response" in e.message, f"message={e.message}"
        print(f"[2] missing column 'Response' -> BizException(1001): {e.message}")
        return
    raise AssertionError("expected BizException but none raised")


def case_3_partial_invalid() -> None:
    """部分行类型错（age=非数字） -> 该行进 errors，其它进 rows"""
    rows = [
        _valid_row(1),
        {**_valid_row(2), "Age": "abc"},       # 第 2 行 age 类型错
        _valid_row(3),
        {**_valid_row(4), "Annual_Premium": "xx"},  # 第 4 行 premium 类型错
    ]
    xlsx = _make_xlsx(rows)
    res = parse_excel(FakeFile(xlsx))
    assert res["valid_count"] == 2, f"valid_count={res['valid_count']}"
    assert res["error_count"] == 2, f"error_count={res['error_count']}"
    assert res["total_rows"] == 4
    # 验证错误明细
    err_indices = {e["row_index"] for e in res["errors"]}
    assert err_indices == {1, 3}, f"err_indices={err_indices}"
    err_cols = {e["column"] for e in res["errors"]}
    assert "Age" in err_cols and "Annual_Premium" in err_cols, f"err_cols={err_cols}"
    print(f"[3] partial invalid (2/4 bad) -> valid=2, errors=2, bad rows={sorted(err_indices)}")


def case_4_nan_value() -> None:
    """某行 Annual_Premium 缺失 -> 该行进 errors"""
    rows = [
        _valid_row(1),
        {**_valid_row(2), "Annual_Premium": None},  # NaN
    ]
    xlsx = _make_xlsx(rows)
    res = parse_excel(FakeFile(xlsx))
    assert res["valid_count"] == 1
    assert res["error_count"] == 1
    err = res["errors"][0]
    assert err["row_index"] == 1
    assert err["column"] == "Annual_Premium"
    assert "缺失" in err["error"] or "None" in err["value"] or err["value"] is None
    print(f"[4] NaN value -> 1 error: {err}")


def case_5_empty_file() -> None:
    """空文件 -> BizException(2002)"""
    try:
        parse_excel(FakeFile(b"", "empty.xlsx"))
    except BizException as e:
        assert e.code == 2002, f"code={e.code}"
        print(f"[5] empty file -> BizException(2002): {e.message}")
        return
    raise AssertionError("expected BizException(2002) for empty file")


def case_6_header_only() -> None:
    """仅 header 无数据行 -> valid=0, error=0, total=0"""
    xlsx = _make_xlsx([])
    res = parse_excel(FakeFile(xlsx))
    assert res["valid_count"] == 0
    assert res["error_count"] == 0
    assert res["total_rows"] == 0
    assert res["rows"] == []
    assert res["errors"] == []
    print(f"[6] header only -> total=0, valid=0, errors=0")


def case_7_corrupt_bytes() -> None:
    """非 Excel 字节 -> BizException(2002)"""
    try:
        parse_excel(FakeFile(b"not a real xlsx file", "bad.xlsx"))
    except BizException as e:
        assert e.code == 2002, f"code={e.code}"
        print(f"[7] corrupt bytes -> BizException(2002): {e.message[:60]}")
        return
    raise AssertionError("expected BizException(2002) for corrupt file")


def case_8_all_invalid() -> None:
    """全部行类型错 -> valid=0, error=N"""
    rows = [
        {**_valid_row(1), "Age": "x"},
        {**_valid_row(2), "Response": "y"},
        {**_valid_row(3), "id": "z"},
    ]
    xlsx = _make_xlsx(rows)
    res = parse_excel(FakeFile(xlsx))
    assert res["valid_count"] == 0
    assert res["error_count"] == 3
    print(f"[8] all 3 rows invalid -> valid=0, errors=3, sample error: {res['errors'][0]}")


def case_9_id_lower_case() -> None:
    """id 列是 lowercase（与其它列不同），确保大小写匹配"""
    rows = [_valid_row(42)]
    xlsx = _make_xlsx(rows)
    res = parse_excel(FakeFile(xlsx))
    assert res["valid_count"] == 1
    assert res["rows"][0]["id"] == 42
    print(f"[9] id column (lowercase) -> parsed correctly, id={res['rows'][0]['id']}")


def case_10_field_types() -> None:
    """验证各字段都被转换为正确类型"""
    row = _valid_row(1)
    xlsx = _make_xlsx([row])
    res = parse_excel(FakeFile(xlsx))
    r = res["rows"][0]
    assert isinstance(r["id"], int)
    assert isinstance(r["age"], int)
    assert isinstance(r["driving_license"], int)
    assert isinstance(r["region_code"], float)
    assert isinstance(r["annual_premium"], float)
    assert isinstance(r["gender"], str)
    assert isinstance(r["vehicle_age"], str)
    assert isinstance(r["vintage"], int)
    assert isinstance(r["response"], int)
    print(f"[10] field types -> all 12 fields coerced to correct Python type")


def main() -> int:
    cases = [
        case_1_valid_10_rows,
        case_2_missing_column,
        case_3_partial_invalid,
        case_4_nan_value,
        case_5_empty_file,
        case_6_header_only,
        case_7_corrupt_bytes,
        case_8_all_invalid,
        case_9_id_lower_case,
        case_10_field_types,
    ]
    for c in cases:
        c()
    print()
    print("=" * 60)
    print(f"P1-01-1 smoke: {len(cases)} / {len(cases)} cases passed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
