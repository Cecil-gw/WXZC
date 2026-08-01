"""DECISION-004 · 上传文件大小限制（50MB）Smoke Test。

用例：
1. 配置项确实是 50MB
2. 小文件（真实 xlsx，远小于 50MB）上传成功 code=0 且真正入库
3. 略小于 50MB 的请求体能通过大小闸门（不被 413 拦，落到业务层 2002 解析失败）
4. 超过 50MB 返回 code=1001 / message 含 50MB / data=null
5. 413 响应体是统一 JSON 信封（不是 werkzeug HTML）
"""
from __future__ import annotations

import io
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from app import MAX_UPLOAD_BYTES, create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402

VA = ["< 1 Year", "1-2 Year", "> 2 Years"]
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:220]) if not cond else ""))


def make_excel(n: int = 80) -> io.BytesIO:
    rnd = random.Random(11)
    rows = [{
        "id": i,
        "Gender": "Male" if i % 2 else "Female",
        "Age": rnd.randint(20, 70),
        "Driving_License": 1,
        "Region_Code": float(rnd.randint(0, 52)),
        "Previously_Insured": rnd.randint(0, 1),
        "Vehicle_Age": VA[i % 3],
        "Vehicle_Damage": "Yes" if i % 3 == 0 else "No",
        "Annual_Premium": float(rnd.randint(2600, 60000)),
        "Policy_Sales_Channel": float(rnd.randint(1, 163)),
        "Vintage": rnd.randint(10, 299),
        "Response": 1 if i % 8 == 0 else 0,
    } for i in range(1, n + 1)]
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False)
    buf.seek(0)
    return buf


def main() -> int:
    app = create_app()
    client = app.test_client()

    db = SessionLocal()
    db.query(Customer).delete()
    db.commit()
    db.close()

    token = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    ).get_json()["data"]["access_token"]
    hdr = {"Authorization": f"Bearer {token}"}

    # ---- 1. 配置值 ----
    check(
        "1 MAX_CONTENT_LENGTH == 50MB",
        app.config.get("MAX_CONTENT_LENGTH") == 50 * 1024 * 1024 == MAX_UPLOAD_BYTES,
        app.config.get("MAX_CONTENT_LENGTH"),
    )

    # ---- 2. 小于 50MB 上传成功 ----
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (make_excel(80), "small.xlsx")},
        headers=hdr,
        content_type="multipart/form-data",
    )
    b = r.get_json()
    ok = r.status_code == 200 and b.get("code") == 0 and b["data"]["imported_count"] == 80
    check("2 under-limit upload succeeds (code=0)", ok, b)

    db = SessionLocal()
    try:
        check("3 under-limit really persisted", db.query(Customer).count() == 80, db.query(Customer).count())
    finally:
        db.close()

    # ---- 4. 略小于 50MB：应通过大小闸门，被业务层判为解析失败 2002 ----
    near = io.BytesIO(b"\x00" * (49 * 1024 * 1024))
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (near, "near_limit.xlsx")},
        headers=hdr,
        content_type="multipart/form-data",
    )
    b = r.get_json()
    check(
        "4 49MB passes size gate (not 413), rejected by parser 2002",
        r.status_code != 413 and b.get("code") == 2002,
        f"status={r.status_code} body={b}",
    )

    # ---- 5. 超过 50MB -> code=1001 ----
    over = io.BytesIO(b"\x00" * (51 * 1024 * 1024))
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (over, "too_big.xlsx")},
        headers=hdr,
        content_type="multipart/form-data",
    )
    b = r.get_json()
    check("5 over-limit -> HTTP 413", r.status_code == 413, r.status_code)
    check("6 over-limit -> code=1001", b is not None and b.get("code") == 1001, b)
    check("7 over-limit -> message mentions 50MB", b is not None and "50MB" in b.get("message", ""), b)
    check("8 over-limit -> data is null", b is not None and b.get("data") is None, b)
    check(
        "9 413 body is JSON envelope (not HTML)",
        r.content_type.startswith("application/json") and set(b or {}) == {"code", "message", "data"},
        f"{r.content_type} keys={sorted((b or {}).keys())}",
    )

    # ---- 10. 超限未破坏已有数据 ----
    db = SessionLocal()
    try:
        check("10 over-limit did not wipe existing data", db.query(Customer).count() == 80, db.query(Customer).count())
    finally:
        db.close()

    p = sum(1 for _, c in results if c)
    f = len(results) - p
    print(f"\n=== upload-limit smoke: {p} passed, {f} failed / {len(results)} ===")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())