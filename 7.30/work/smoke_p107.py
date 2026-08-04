"""P1-07 上传数据预测（不入库）· 端到端 smoke test。"""
from __future__ import annotations

import io
import random
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib
import numpy as np
import pandas as pd

from app import create_app
from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.experiment import Experiment
from app.models.operation_log import OperationLog
from app.utils.data_processor import prepare_features

VA = ["< 1 Year", "1-2 Year", "> 2 Years"]
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:220]) if not cond else ""))


def rows_for(n, seed=21, with_response=True, with_id=True):
    rnd = random.Random(seed)
    out = []
    for i in range(1, n + 1):
        age = rnd.randint(20, 70)
        prev = rnd.randint(0, 1)
        dmg = "Yes" if rnd.random() > 0.5 else "No"
        row = {
            "Gender": "Male" if i % 2 else "Female",
            "Age": age,
            "Driving_License": 1,
            "Region_Code": float(rnd.randint(0, 52)),
            "Previously_Insured": prev,
            "Vehicle_Age": VA[i % 3],
            "Vehicle_Damage": dmg,
            "Annual_Premium": float(rnd.randint(2600, 60000)),
            "Policy_Sales_Channel": float(rnd.randint(1, 163)),
            "Vintage": rnd.randint(10, 299),
        }
        if with_id:
            row = {"id": 9000 + i, **row}
        if with_response:
            score = (0 if prev else 0.5) + (0.4 if dmg == "Yes" else 0) + age / 200
            row["Response"] = 1 if score + rnd.gauss(0, 0.15) > 1.05 else 0
        out.append(row)
    return out


def to_xlsx(rows):
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, index=False)
    buf.seek(0)
    return buf

def seed_customers(n=400):
    """训练用数据入库（predict_upload 不该改动它）。"""
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        for i, r in enumerate(rows_for(n, seed=7), start=1):
            db.add(Customer(
                id=i,
                gender=r["Gender"], age=r["Age"], driving_license=r["Driving_License"],
                region_code=r["Region_Code"], previously_insured=r["Previously_Insured"],
                vehicle_age=r["Vehicle_Age"], vehicle_damage=r["Vehicle_Damage"],
                annual_premium=r["Annual_Premium"],
                policy_sales_channel=r["Policy_Sales_Channel"],
                vintage=r["Vintage"], response=r["Response"],
            ))
        db.commit()
    finally:
        db.close()


def token(client, u="admin", p="admin123"):
    return client.post("/api/v1/auth/login", json={"username": u, "password": p}).get_json()["data"]["access_token"]


def post_upload(client, hdr, rows, filename="new_batch.xlsx", model=None):
    data = {"file": (to_xlsx(rows), filename)}
    if model is not None:
        data["model"] = model
    return client.post("/api/v1/model/predict_upload", data=data,
                       headers=hdr, content_type="multipart/form-data")


def main():
    app = create_app()
    client = app.test_client()

    db = SessionLocal()
    db.query(OperationLog).filter(OperationLog.action == "prediction").delete()
    db.query(Experiment).delete()
    db.query(Customer).delete()
    db.commit()
    db.close()

    hdr: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}

    # ---- 1. 未训练 -> 3002 ----
    check("1 no model trained -> 3002", post_upload(client, hdr, rows_for(5)).get_json().get("code") == 3002)

    # ---- 2. 未认证 -> 1002 ----
    r = client.post("/api/v1/model/predict_upload",
                    data={"file": (to_xlsx(rows_for(3)), "a.xlsx")},
                    content_type="multipart/form-data")
    check("2 no token -> 1002", r.get_json()["code"] == 1002)

    # 训练
    seed_customers(400)
    tr = client.post("/api/v1/model/train", json={}, headers=hdr)
    check("3 train ok", tr.get_json().get("code") == 0, tr.get_json())
    best_model = tr.get_json()["data"]["best_model"]

    # ---- 4. 未上传文件 -> 1001 ----
    check("4 missing file -> 1001",
          client.post("/api/v1/model/predict_upload", data={}, headers=hdr,
                      content_type="multipart/form-data").get_json()["code"] == 1001)

    # ---- 5. 非法扩展名 -> 1001 ----
    check("5 .txt -> 1001",
          client.post("/api/v1/model/predict_upload",
                      data={"file": (io.BytesIO(b"x"), "a.txt")}, headers=hdr,
                      content_type="multipart/form-data").get_json()["code"] == 1001)

    # ---- 6. 损坏 Excel -> 2002 ----
    check("6 broken xlsx -> 2002",
          client.post("/api/v1/model/predict_upload",
                      data={"file": (io.BytesIO(b"not-excel"), "a.xlsx")}, headers=hdr,
                      content_type="multipart/form-data").get_json()["code"] == 2002)

    # ---- 7. 缺特征列 -> 1001 ----
    bad = rows_for(5)
    for r_ in bad:
        r_.pop("Vehicle_Age")
    check("7 missing feature column -> 1001", post_upload(client, hdr, bad).get_json()["code"] == 1001)

    # ---- 8. 未知 model -> 1001 ----
    check("8 unknown model -> 1001", post_upload(client, hdr, rows_for(5), model="svm").get_json()["code"] == 1001)

    # ---- 9. 正常预测：响应结构 ----
    N = 30
    up = rows_for(N)
    r = post_upload(client, hdr, up)
    b = r.get_json()
    d = b.get("data") or {}
    check("9 response schema (docs 3.5)",
          r.status_code == 200 and b.get("code") == 0
          and set(d) == {"model_name", "total_count", "statistics", "predictions"}
          and d["model_name"] == best_model and d["total_count"] == N,
          f"keys={sorted(d)} model={d.get('model_name')} total={d.get('total_count')}")

    # ---- 10. predictions 长度与字段 ----
    preds = d.get("predictions") or []
    check("10 predictions length & fields",
          len(preds) == N and all(set(p) == {"id", "predicted_prob"} for p in preds),
          f"len={len(preds)} first={preds[0] if preds else None}")

    # ---- 11. 概率区间 + 非常量 ----
    probs = [p["predicted_prob"] for p in preds]
    check("11 probs in [0,1] and not constant",
          all(0.0 <= v <= 1.0 for v in probs) and len(set(probs)) > 5,
          f"min={min(probs)} max={max(probs)} distinct={len(set(probs))}")

    # ---- 12. 按概率倒序 ----
    check("12 predictions sorted desc by prob", probs == sorted(probs, reverse=True), probs[:5])

    # ---- 13. id 透传（上传的 id 是 9001+） ----
    check("13 uploaded ids preserved",
          set(p["id"] for p in preds) == set(range(9001, 9001 + N)),
          sorted(p["id"] for p in preds)[:5])

    # ---- 14. statistics 结构与数值自洽 ----
    st = d.get("statistics") or {}
    need = {"count", "mean_prob", "min_prob", "max_prob",
            "high_potential_threshold", "high_potential_count"}
    ok14 = (
        set(st) == need and st["count"] == N
        and abs(st["min_prob"] - min(probs)) < 1e-6
        and abs(st["max_prob"] - max(probs)) < 1e-6
        and st["min_prob"] <= st["mean_prob"] <= st["max_prob"]
        and 1 <= st["high_potential_count"] <= N
    )
    check("14 statistics schema & self-consistent", ok14, st)

    # 手工复算全精度概率，供 case 15 / 17 共用
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.model_name == best_model).order_by(
            Experiment.id.desc()).first()
        bundle = joblib.load(exp.model_path)
    finally:
        db.close()
    X, _, _ = prepare_features(pd.DataFrame(up), with_target=False)
    expected = bundle["model"].predict_proba(bundle["scaler"].transform(X))[:, 1]

    # ---- 15. high_potential 阈值即 0.9 分位数 ----
    # 注意：必须在全精度概率上算分位数。服务端是先算分位数再 round(6)，
    # 若在已舍入的 predictions 上重算会有 1e-6 级偏差，那是断言不严谨而非实现有误。
    exp_thr = round(float(np.quantile(expected, 0.9)), 6)
    check("15 threshold == 0.9 quantile (full precision)",
          abs(st["high_potential_threshold"] - exp_thr) < 1e-9,
          f"api={st['high_potential_threshold']} expect={exp_thr}")

    # ---- 16. 不入库：customers 行数与 predicted_prob 均未变 ----
    db = SessionLocal()
    try:
        cnt = db.query(Customer).count()
        nulls = db.query(Customer).filter(Customer.predicted_prob.is_(None)).count()
        maxid = db.query(Customer).order_by(Customer.id.desc()).first().id
        check("16 NOT persisted (count/predicted_prob/max_id unchanged)",
              cnt == 400 and nulls == 400 and maxid == 400,
              f"count={cnt} nulls={nulls} maxid={maxid}")
    finally:
        db.close()

    # ---- 17. scaler 复用一致性：手工复算比对（复用上面的 expected） ----
    by_id = {p["id"]: p["predicted_prob"] for p in preds}
    max_diff = max(abs(round(float(e), 6) - by_id[9000 + i])
                   for i, e in enumerate(expected, start=1))
    check("17 probs match manual recompute (scaler reused)", max_diff < 1e-6, f"max_diff={max_diff}")

    # ---- 18. 无 Response 列也能预测（预测场景不需要标签） ----
    r = post_upload(client, hdr, rows_for(8, with_response=False))
    b18 = r.get_json()
    check("18 works without Response column",
          b18.get("code") == 0 and b18["data"]["total_count"] == 8, b18.get("code"))

    # ---- 19. 无 id 列时用行号兜底 ----
    r = post_upload(client, hdr, rows_for(6, with_response=False, with_id=False))
    b19 = r.get_json()
    ids19 = sorted(p["id"] for p in (b19.get("data") or {}).get("predictions", []))
    check("19 no id column -> 1-based row numbers", b19.get("code") == 0 and ids19 == [1, 2, 3, 4, 5, 6], ids19)

    # ---- 20. 指定 model 生效 ----
    r = post_upload(client, hdr, rows_for(10), model="logistic_regression")
    d20 = r.get_json().get("data") or {}
    check("20 explicit model honored", d20.get("model_name") == "logistic_regression", d20.get("model_name"))

    # ---- 21. 空 model 表单字段 -> 1001 ----
    check("21 empty model field -> 1001",
          post_upload(client, hdr, rows_for(3), model="   ").get_json()["code"] == 1001)

    # ---- 22. 模型文件丢失 -> 3002 ----
    db = SessionLocal()
    try:
        e = db.query(Experiment).filter(Experiment.is_best.is_(True)).first()
        orig = e.model_path
        e.model_path = str(Path(orig).parent / "gone.joblib")
        db.commit()
    finally:
        db.close()
    check("22 missing model file -> 3002", post_upload(client, hdr, rows_for(3)).get_json()["code"] == 3002)
    db = SessionLocal()
    try:
        e = db.query(Experiment).filter(Experiment.is_best.is_(True)).first()
        e.model_path = orig
        db.commit()
    finally:
        db.close()

    # ---- 23. 操作日志 ----
    db = SessionLocal()
    try:
        logs = db.query(OperationLog).filter(OperationLog.action == "prediction").all()
        check("23 operation_log written for each success", len(logs) == 4, f"count={len(logs)}")
    finally:
        db.close()

    p_ = sum(1 for _, c in results if c)
    f_ = len(results) - p_
    print(f"\n=== P1-07 smoke: {p_} passed, {f_} failed / {len(results)} ===")
    if f_:
        for n_, c_ in results:
            if not c_:
                print(f"  - {n_}")
    return 0 if f_ == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
