"""P1-01-6 端到端 smoke test · Excel 上传全链路。"""
from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402


# -------- 工具 --------

def _valid_row(i: int) -> Dict[str, Any]:
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


def _make_xlsx(rows: List[Dict[str, Any]], columns: List[str] = None) -> bytes:
    if columns is None:
        columns = list(_valid_row(1).keys())
    df = pd.DataFrame(rows, columns=columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    return buf.getvalue()


def _admin_token(client) -> str:
    """login as admin -> token"""
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, f"login status {r.status_code}"
    return r.get_json()["data"]["access_token"]


def _count_customers() -> int:
    """直查 DB 行数"""
    db = SessionLocal()
    try:
        return db.query(Customer).count()
    finally:
        db.close()


def _clear_customers() -> None:
    """清空 customers（每个用例前后清理，确保隔离）"""
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()


# -------- 用例 --------

def case_1_unauthorized(client) -> None:
    """无 token -> 1002"""
    xlsx = _make_xlsx([_valid_row(1)])
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (io.BytesIO(xlsx), "test.xlsx")},
        content_type="multipart/form-data",
    )
    assert r.status_code == 401, f"status={r.status_code}"
    assert r.get_json()["code"] == 1002
    print(f"[1] no token -> 401 / code=1002")


def case_2_no_file_field(client, token) -> None:
    """无 file 字段 -> 1001"""
    r = client.post(
        "/api/v1/data/upload",
        data={},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400, f"status={r.status_code}"
    assert r.get_json()["code"] == 1001
    print(f"[2] no file field -> 400 / code=1001")


def case_3_wrong_extension(client, token) -> None:
    """错扩展名 (.txt) -> 1001"""
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (io.BytesIO(b"hello"), "test.txt")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400, f"status={r.status_code}"
    assert r.get_json()["code"] == 1001
    print(f"[3] wrong extension .txt -> 400 / code=1001")


def case_4_missing_column(client, token) -> None:
    """缺列 -> 1001"""
    cols = [c for c in _valid_row(1).keys() if c != "Response"]
    xlsx = _make_xlsx([_valid_row(1)], columns=cols)
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (io.BytesIO(xlsx), "test.xlsx")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400, f"status={r.status_code}"
    assert r.get_json()["code"] == 1001
    assert "Response" in r.get_json()["message"]
    print(f"[4] missing column 'Response' -> 400 / code=1001 / msg 列名齐全")


def case_5_valid_10_rows(client, token) -> None:
    """合法 10 行 xlsx -> 200 / imported_count=10 / DB 10 行"""
    _clear_customers()
    rows = [_valid_row(i) for i in range(1, 11)]
    xlsx = _make_xlsx(rows)
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (io.BytesIO(xlsx), "insurance.xlsx")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, f"status={r.status_code}: {r.get_data(as_text=True)}"
    body = r.get_json()
    assert body["code"] == 0
    assert body["data"]["imported_count"] == 10
    qr = body["data"]["quality_report"]
    assert qr["total_rows"] == 10
    assert qr["total_cols"] == 12
    assert qr["duplicates"] == 0
    assert all(v == 0 for v in qr["missing_values"].values())
    # 验证 DB
    assert _count_customers() == 10
    print(f"[5] valid 10 rows -> 200 / imported=10 / DB rows=10 / quality OK")


def case_6_clear_strategy(client, token) -> None:
    """二次上传（5 行）-> 旧 10 行被清空，新 5 行入库"""
    assert _count_customers() == 10  # 上一轮留的
    rows = [_valid_row(i) for i in range(100, 105)]  # 5 行不同 id
    xlsx = _make_xlsx(rows)
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (io.BytesIO(xlsx), "v2.xlsx")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.get_json()
    assert body["data"]["imported_count"] == 5
    assert _count_customers() == 5  # 旧 10 行被清空
    # 验证全是新 id
    db = SessionLocal()
    try:
        ids = sorted(c.id for c in db.query(Customer).all())
        assert ids == [100, 101, 102, 103, 104], f"ids={ids}"
    finally:
        db.close()
    print(f"[6] second upload (5 rows) -> 旧 10 行清空, 新 5 行入库, ids=[100..104]")


def case_7_quality_report_complete(client, token) -> None:
    """质量报告字段完整：total_rows/cols/missing_values/duplicates/dtypes"""
    _clear_customers()
    rows = [_valid_row(i) for i in range(1, 6)]
    # 加 1 个有缺失的行
    rows.append({**_valid_row(6), "Age": None})
    xlsx = _make_xlsx(rows)
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (io.BytesIO(xlsx), "test.xlsx")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = r.get_json()
    qr = body["data"]["quality_report"]
    assert qr["total_rows"] == 6
    assert qr["total_cols"] == 12
    assert qr["missing_values"]["Age"] == 1
    assert qr["missing_values"]["Gender"] == 0
    # 数值列 openpyxl 往返后可能是 int 或 float（取决于是否有小数位）
    # 接受 int* / float* / Int* / Float* 任一
    for col in ("id", "Annual_Premium", "Age", "Vintage", "Response"):
        dt = qr["dtypes"][col]
        assert any(s in dt for s in ("int", "float")), f"dtypes[{col}]={dt} 期望数值类型"
    assert qr["dtypes"]["Gender"] == "object"  # str 列 pandas 用 object dtype
    print(f"[7] quality_report 完整，含 missing/duplicates/dtypes 5 个子字段")


def main() -> int:
    app = create_app()
    client = app.test_client()
    token = _admin_token(client)

    _clear_customers()  # 起点：DB 空

    cases = [
        ("unauthorized", lambda: case_1_unauthorized(client)),
        ("no_file",      lambda: case_2_no_file_field(client, token)),
        ("wrong_ext",    lambda: case_3_wrong_extension(client, token)),
        ("missing_col",  lambda: case_4_missing_column(client, token)),
        ("valid_10",     lambda: case_5_valid_10_rows(client, token)),
        ("clear_v2",     lambda: case_6_clear_strategy(client, token)),
        ("quality_full", lambda: case_7_quality_report_complete(client, token)),
    ]
    for name, fn in cases:
        fn()

    _clear_customers()  # 测试结束清场

    print()
    print("=" * 60)
    print(f"P1-01-6 end-to-end smoke: {len(cases)} / {len(cases)} cases passed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())