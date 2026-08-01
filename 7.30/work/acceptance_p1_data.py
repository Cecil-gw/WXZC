"""独立验收脚本（Review Mode）：不复用既有 smoke，真实 Excel 走 HTTP 全链路。"""
from __future__ import annotations

import base64
import io
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
VA = ["< 1 Year", "1-2 Year", "> 2 Years"]

results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond), extra))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:200]) if not cond else ""))


def make_excel(n=120) -> io.BytesIO:
    """构造含全部 12 个原始大写列名的 xlsx。"""
    rnd = random.Random(3)
    rows = []
    for i in range(1, n + 1):
        rows.append({
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
        })
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False)
    buf.seek(0)
    return buf


def main() -> int:
    app = create_app()
    client = app.test_client()

    # 清库
    db = SessionLocal()
    db.query(Customer).delete()
    db.commit()
    db.close()

    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = r.get_json()["data"]["access_token"]
    hdr = {"Authorization": f"Bearer {token}"}

    # ---------- A. 上传 ----------
    buf = make_excel(120)
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (buf, "acceptance.xlsx")},
        headers=hdr,
        content_type="multipart/form-data",
    )
    body = r.get_json()
    check("A1 upload HTTP 200", r.status_code == 200, r.status_code)
    check("A2 upload code==0", body.get("code") == 0, body)
    d = body.get("data") or {}
    check("A3 imported_count==120", d.get("imported_count") == 120, d.get("imported_count"))
    q = d.get("quality_report") or {}
    check(
        "A4 quality_report schema (docs 2.1)",
        {"total_rows", "total_cols", "missing_values", "duplicates", "dtypes"} <= set(q),
        list(q.keys()),
    )

    # DB 真实写入 + snake_case 转换
    db = SessionLocal()
    try:
        cnt = db.query(Customer).count()
        one = db.query(Customer).filter(Customer.id == 1).first()
        check("A5 DB really persisted 120 rows", cnt == 120, cnt)
        check(
            "A6 snake_case fields populated",
            one is not None
            and one.gender in ("Male", "Female")
            and isinstance(one.annual_premium, float)
            and isinstance(one.policy_sales_channel, float)
            and one.vehicle_age in VA,
            None if one is None else (one.gender, one.annual_premium, one.vehicle_age),
        )
        check("A7 uploaded_by column exists", hasattr(Customer, "uploaded_by"), "Customer has NO uploaded_by attr")
    finally:
        db.close()

    # 上传非法扩展名
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (io.BytesIO(b"abc"), "x.txt")},
        headers=hdr,
        content_type="multipart/form-data",
    )
    check("A8 .txt rejected -> 1001", r.get_json().get("code") == 1001, r.get_json())

    # 损坏 xlsx -> 2002
    r = client.post(
        "/api/v1/data/upload",
        data={"file": (io.BytesIO(b"not-an-excel"), "broken.xlsx")},
        headers=hdr,
        content_type="multipart/form-data",
    )
    check("A9 broken xlsx -> 2002", r.get_json().get("code") == 2002, r.get_json())

    # 10MB 限制
    # DECISION-004 方案 C：上限定为 50MB（10MB 与 PRD §170 的 38 万行导入目标冲突）
    check(
        "A10 MAX_CONTENT_LENGTH == 50MB (DECISION-004)",
        app.config.get("MAX_CONTENT_LENGTH") == 50 * 1024 * 1024,
        f"actual={app.config.get('MAX_CONTENT_LENGTH')}",
    )

    # 重新上传恢复数据（A9 已清空? 验证覆盖策略未破坏数据）
    db = SessionLocal()
    if db.query(Customer).count() != 120:
        db.close()
        buf = make_excel(120)
        client.post("/api/v1/data/upload", data={"file": (buf, "re.xlsx")}, headers=hdr,
                    content_type="multipart/form-data")
    else:
        db.close()

    # ---------- B. customers ----------
    r = client.get("/api/v1/data/customers?page=1&per_page=10", headers=hdr)
    b = r.get_json()
    dd = b.get("data") or {}
    check("B1 customers HTTP200 code0", r.status_code == 200 and b.get("code") == 0, b)
    check(
        "B2 pagination schema",
        {"items", "total", "page", "per_page", "pages"} <= set(dd) and len(dd.get("items", [])) == 10 and dd["total"] == 120,
        {k: dd.get(k) for k in ("total", "page", "per_page", "pages")},
    )
    item = (dd.get("items") or [{}])[0]
    expected_fields = {
        "id", "gender", "age", "driving_license", "region_code", "previously_insured",
        "vehicle_age", "vehicle_damage", "annual_premium", "policy_sales_channel",
        "vintage", "response", "predicted_prob", "created_at",
    }
    check("B3 item has all doc fields", expected_fields <= set(item), sorted(expected_fields - set(item)))
    r = client.get("/api/v1/data/customers?gender=Male&age_min=30&age_max=50&previously_insured=1", headers=hdr)
    its = r.get_json()["data"]["items"]
    check(
        "B4 filters work",
        all(i["gender"] == "Male" and 30 <= i["age"] <= 50 and i["previously_insured"] == 1 for i in its),
        len(its),
    )
    r = client.get("/api/v1/data/customers?per_page=999", headers=hdr)
    check("B5 per_page capped at 200", r.get_json()["data"]["per_page"] == 200, r.get_json()["data"]["per_page"])
    r = client.get("/api/v1/data/customers?page=abc", headers=hdr)
    check("B6 invalid param -> 1001", r.get_json()["code"] == 1001, r.get_json())
    r = client.get("/api/v1/data/customers")
    check("B7 no token -> 1002", r.get_json()["code"] == 1002, r.get_json())

    # ---------- C. statistics ----------
    r = client.get("/api/v1/data/statistics", headers=hdr)
    b = r.get_json(); dd = b.get("data") or {}
    check("C1 statistics HTTP200 code0", r.status_code == 200 and b.get("code") == 0, b)
    check(
        "C2 statistics schema",
        {"total", "gender_distribution", "response_distribution", "age_stats"} <= set(dd)
        and {"min", "max", "avg"} <= set(dd.get("age_stats", {})),
        dd,
    )
    check("C3 statistics numbers real", dd.get("total") == 120
          and sum(dd["gender_distribution"].values()) == 120
          and sum(dd["response_distribution"].values()) == 120, dd)

    # ---------- D. quality ----------
    r = client.get("/api/v1/data/quality", headers=hdr)
    b = r.get_json(); dd = b.get("data") or {}
    check("D1 quality HTTP200 code0", r.status_code == 200 and b.get("code") == 0, b)
    check(
        "D2 quality schema",
        {"total_rows", "total_cols", "missing_values", "duplicates", "dtypes"} <= set(dd), list(dd)
    )
    check("D3 quality total_rows==120", dd.get("total_rows") == 120, dd.get("total_rows"))
    check("D4 dtypes json-serializable strings",
          all(isinstance(v, str) for v in (dd.get("dtypes") or {}).values()), dd.get("dtypes"))

    # ---------- E. visualization ----------
    for ct in ["response_distribution", "gender_response", "age_distribution", "premium_distribution"]:
        r = client.get(f"/api/v1/data/visualization/{ct}", headers=hdr)
        b = r.get_json(); dd = b.get("data") or {}
        ok = r.status_code == 200 and b.get("code") == 0 and dd.get("format") == "png" and dd.get("chart_type") == ct
        raw = b""
        try:
            raw = base64.b64decode(dd.get("image_base64", ""))
        except Exception:
            pass
        check(f"E {ct} -> real PNG base64",
              ok and raw.startswith(PNG_MAGIC) and len(raw) > 3000,
              f"ok={ok} bytes={len(raw)}")
    r = client.get("/api/v1/data/visualization/nope", headers=hdr)
    check("E5 unknown chart_type -> 1001", r.get_json()["code"] == 1001, r.get_json())

    # ---------- F. 模型层接口 ----------
    check("F1 Customer.bulk_create exists", hasattr(Customer, "bulk_create"), "no bulk_create on Customer")
    check("F2 Customer.paginate exists", hasattr(Customer, "paginate"), "no paginate")
    check("F3 app/models/customers.py exists", Path("app/models/customers.py").exists(), "only customer.py (singular)")

    # ---------- G. 路由注册 ----------
    rules = {str(r_.rule) for r_ in app.url_map.iter_rules()}
    need = [
        "/api/v1/data/upload", "/api/v1/data/customers", "/api/v1/data/statistics",
        "/api/v1/data/quality", "/api/v1/data/visualization/<chart_type>",
    ]
    for u in need:
        check(f"G {u} registered", u in rules, "missing")

    p = sum(1 for _, c, _ in results if c)
    f = len(results) - p
    print(f"\n=== acceptance: {p} passed, {f} failed / {len(results)} ===")
    if f:
        print("FAILED ITEMS:")
        for n, c, e in results:
            if not c:
                print(f"  - {n} :: {e}")
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())