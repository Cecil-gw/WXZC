"""P1-09 模型导出 / 导入 · 端到端 smoke test。"""
from __future__ import annotations

import io
import os
import random
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

from app import create_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.experiment import Experiment
from app.models.operation_log import OperationLog

VA = ["< 1 Year", "1-2 Year", "> 2 Years"]
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:200]) if not cond else ""))


def seed(n=300):
    rnd = random.Random(41)
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        for i in range(1, n + 1):
            age = rnd.randint(20, 70)
            prev = rnd.randint(0, 1)
            dmg = "Yes" if rnd.random() > 0.5 else "No"
            score = (0 if prev else 0.5) + (0.4 if dmg == "Yes" else 0) + age / 200
            db.add(Customer(
                id=i, gender="Male" if i % 2 else "Female", age=age,
                driving_license=1, region_code=float(rnd.randint(0, 52)),
                previously_insured=prev, vehicle_age=VA[i % 3], vehicle_damage=dmg,
                annual_premium=float(rnd.randint(2600, 60000)),
                policy_sales_channel=float(rnd.randint(1, 163)),
                vintage=rnd.randint(10, 299),
                response=1 if score + rnd.gauss(0, 0.15) > 1.05 else 0,
            ))
        db.commit()
    finally:
        db.close()


def token(client, u="admin", p="admin123"):
    return client.post("/api/v1/auth/login", json={"username": u, "password": p}).get_json()["data"]["access_token"]

def main():
    app = create_app()
    client = app.test_client()

    db = SessionLocal()
    db.query(OperationLog).filter(OperationLog.action == "model_import").delete()
    db.query(Experiment).delete()
    db.query(Customer).delete()
    db.commit()
    db.close()

    hdr: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}
    client.post("/api/v1/auth/register", json={"username": "u_p109", "password": "user1234"})
    uhdr = {"Authorization": f"Bearer {token(client, 'u_p109', 'user1234')}"}
    model_dir = settings.model_dir_abs

    # 清掉可能残留的模型文件，保证 case 1 环境干净
    for f in Path(model_dir).glob("*.joblib"):
        f.unlink()

    # ---- 1. 未训练时导出 -> 3002 ----
    check("1 export before train -> 3002",
          client.get("/api/v1/model/export/xgboost", headers=hdr).get_json().get("code") == 3002)

    # ---- 2-3. 鉴权 ----
    check("2 export no token -> 1002",
          client.get("/api/v1/model/export/xgboost").get_json()["code"] == 1002)
    check("3 import no token -> 1002",
          client.post("/api/v1/model/import", data={}, content_type="multipart/form-data").get_json()["code"] == 1002)

    # ---- 4-5. 普通用户越权 -> 1003 ----
    r = client.get("/api/v1/model/export/xgboost", headers=uhdr)
    check("4 export as normal user -> 403/1003",
          r.status_code == 403 and r.get_json()["code"] == 1003, r.get_json())
    r = client.post("/api/v1/model/import", data={"file": (io.BytesIO(b"x"), "a.joblib")},
                    headers=uhdr, content_type="multipart/form-data")
    check("5 import as normal user -> 403/1003",
          r.status_code == 403 and r.get_json()["code"] == 1003, r.get_json())

    # 训练
    seed(300)
    tr = client.post("/api/v1/model/train", json={}, headers=hdr)
    check("6 train ok", tr.get_json().get("code") == 0, tr.get_json())

    # ---- 7. 正常导出：二进制流 + Content-Disposition ----
    r = client.get("/api/v1/model/export/xgboost", headers=hdr)
    cd = r.headers.get("Content-Disposition", "")
    check("7 export returns attachment stream",
          r.status_code == 200 and "attachment" in cd and "xgboost.joblib" in cd
          and len(r.data) > 1000,
          f"status={r.status_code} cd={cd} bytes={len(r.data)}")

    # ---- 8. 导出内容确实是可用 bundle ----
    exported = r.data
    tmp = Path(model_dir) / "_roundtrip_check.joblib"
    tmp.write_bytes(exported)
    try:
        b = joblib.load(tmp)
        check("8 exported bytes load as bundle with model+scaler",
              isinstance(b, dict) and "model" in b and "scaler" in b,
              type(b).__name__)
    finally:
        tmp.unlink(missing_ok=True)

    # ---- 9. 三个模型均可导出 ----
    ok9 = all(
        client.get(f"/api/v1/model/export/{m}", headers=hdr).status_code == 200
        for m in ["logistic_regression", "random_forest", "xgboost"]
    )
    check("9 all three models exportable", ok9)

    # ---- 10-12. 目录穿越防御 ----
    for i, evil in enumerate(["..%2f..%2f.env", "....//....//.env", "%2e%2e%2f.env"], start=10):
        r = client.get(f"/api/v1/model/export/{evil}", headers=hdr)
        body = r.get_json() if r.is_json else None
        # 要么被 Flask 路由拒绝(404)，要么被白名单拦为 1001；绝不能返回文件内容
        blocked = r.status_code in (400, 404) or (body and body.get("code") == 1001)
        check(f"{i} path traversal blocked [{evil}]", blocked,
              f"status={r.status_code} body={body}")

    # ---- 13. 未知模型名 -> 1001 ----
    check("13 unknown model name -> 1001",
          client.get("/api/v1/model/export/svm", headers=hdr).get_json()["code"] == 1001)

    # ---- 14. 导入：未上传文件 -> 1001 ----
    check("14 import missing file -> 1001",
          client.post("/api/v1/model/import", data={}, headers=hdr,
                      content_type="multipart/form-data").get_json()["code"] == 1001)

    # ---- 15. 非 .joblib 扩展名 -> 1001 ----
    check("15 import .txt -> 1001",
          client.post("/api/v1/model/import", data={"file": (io.BytesIO(b"x"), "m.txt")},
                      headers=hdr, content_type="multipart/form-data").get_json()["code"] == 1001)

    # ---- 16. 扩展名对但内容不是 joblib -> 1001 ----
    check("16 fake .joblib content -> 1001",
          client.post("/api/v1/model/import",
                      data={"file": (io.BytesIO(b"definitely-not-joblib"), "m.joblib")},
                      headers=hdr, content_type="multipart/form-data").get_json()["code"] == 1001)

    # ---- 17. 合法 joblib 但缺 scaler -> 1001 ----
    bad = io.BytesIO()
    joblib.dump({"model": LinearRegression()}, bad)
    bad.seek(0)
    check("17 bundle without scaler -> 1001",
          client.post("/api/v1/model/import", data={"file": (bad, "m.joblib")},
                      headers=hdr, content_type="multipart/form-data").get_json()["code"] == 1001)

    # ---- 18. 结构完整但模型类型不支持 -> 1001 ----
    bad2 = io.BytesIO()
    joblib.dump({"model": LinearRegression(), "scaler": StandardScaler()}, bad2)
    bad2.seek(0)
    b18 = client.post("/api/v1/model/import", data={"file": (bad2, "m.joblib")},
                      headers=hdr, content_type="multipart/form-data").get_json()
    check("18 unsupported estimator type -> 1001", b18.get("code") == 1001, b18)

    # ---- 19. 坏文件不污染已有模型 ----
    xgb_path = Path(model_dir) / "xgboost.joblib"
    size_before = xgb_path.stat().st_size
    tmp_leftover = list(Path(model_dir).glob(".import_tmp_*"))
    check("19 failed imports leave no temp files & existing model intact",
          not tmp_leftover and xgb_path.exists() and xgb_path.stat().st_size == size_before,
          f"tmp={[p.name for p in tmp_leftover]}")

    # ---- 20. 导出 -> 导入 往返成功 ----
    r = client.post("/api/v1/model/import",
                    data={"file": (io.BytesIO(exported), "whatever_name.joblib")},
                    headers=hdr, content_type="multipart/form-data")
    b20 = r.get_json()
    d20 = b20.get("data") or {}
    check("20 round-trip import ok, data schema {model_name,path}",
          b20.get("code") == 0 and set(d20) == {"model_name", "path"},
          b20)

    # ---- 21. 落盘名由 bundle 内容推断，不用上传文件名 ----
    check("21 saved name inferred from bundle (not upload filename)",
          d20.get("model_name") == "xgboost"
          and Path(d20.get("path", "")).name == "xgboost.joblib"
          and not (Path(model_dir) / "whatever_name.joblib").exists(),
          d20)

    # ---- 22. 导入文件落在 MODEL_DIR 内 ----
    check("22 saved inside MODEL_DIR",
          os.path.abspath(d20["path"]).startswith(os.path.abspath(model_dir)),
          d20.get("path"))

    # ---- 23. 导入后模型可用于预测 ----
    r = client.post("/api/v1/model/predict", json={"model_name": "xgboost"}, headers=hdr)
    check("23 imported model usable for predict", r.get_json().get("code") == 0, r.get_json())

    # ---- 24. 操作日志 ----
    db = SessionLocal()
    try:
        logs = db.query(OperationLog).filter(OperationLog.action == "model_import").all()
        check("24 model_import logged once (only successful import)",
              len(logs) == 1, f"count={len(logs)}")
    finally:
        db.close()

    # ---- 25. 无残留临时文件 ----
    leftover = list(Path(model_dir).glob(".import_tmp_*"))
    check("25 no temp files left after all imports", not leftover,
          [p.name for p in leftover])

    p_ = sum(1 for _, c in results if c)
    f_ = len(results) - p_
    print(f"\n=== P1-09 smoke: {p_} passed, {f_} failed / {len(results)} ===")
    if f_:
        for n_, c_ in results:
            if not c_:
                print(f"  - {n_}")
    return 0 if f_ == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
