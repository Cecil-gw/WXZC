"""P1-06 全量预测 · 端到端 smoke test。"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import joblib  # noqa: E402
import pandas as pd  # noqa: E402

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.experiment import Experiment  # noqa: E402
from app.models.operation_log import OperationLog  # noqa: E402
from app.utils.data_processor import prepare_features  # noqa: E402

VA = ["< 1 Year", "1-2 Year", "> 2 Years"]
N = 400
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:220]) if not cond else ""))


def seed(n: int = N) -> None:
    rnd = random.Random(13)
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        for i in range(1, n + 1):
            age = rnd.randint(20, 70)
            prev = rnd.randint(0, 1)
            dmg = "Yes" if rnd.random() > 0.5 else "No"
            score = (0 if prev else 0.5) + (0.4 if dmg == "Yes" else 0) + age / 200
            db.add(Customer(
                id=i,
                gender="Male" if i % 2 else "Female",
                age=age,
                driving_license=1,
                region_code=float(rnd.randint(0, 52)),
                previously_insured=prev,
                vehicle_age=VA[i % 3],
                vehicle_damage=dmg,
                annual_premium=float(rnd.randint(2600, 60000)),
                policy_sales_channel=float(rnd.randint(1, 163)),
                vintage=rnd.randint(10, 299),
                response=1 if score + rnd.gauss(0, 0.15) > 1.05 else 0,
            ))
        db.commit()
    finally:
        db.close()


def token(client, u="admin", p="admin123") -> str:
    return client.post("/api/v1/auth/login", json={"username": u, "password": p}).get_json()["data"]["access_token"]


def main() -> int:
    app = create_app()
    client = app.test_client()

    # 自清理所用表：不依赖删除 db 文件（Windows 下文件可能被其它进程占用）
    db = SessionLocal()
    db.query(OperationLog).filter(OperationLog.action == "prediction").delete()
    db.query(Experiment).delete()
    db.query(Customer).delete()
    db.commit()
    db.close()

    hdr: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}

    # ---- 1. 未训练 -> 3002 ----
    check("1 predict without model -> 3002",
          client.post("/api/v1/model/predict", json={}, headers=hdr).get_json().get("code") == 3002)

    # ---- 2. 未认证 -> 1002 ----
    check("2 no token -> 1002", client.post("/api/v1/model/predict", json={}).get_json()["code"] == 1002)

    # ---- 3. 非法 model_name 类型 -> 1001 ----
    check("3 model_name='' -> 1001",
          client.post("/api/v1/model/predict", json={"model_name": "  "}, headers=hdr).get_json()["code"] == 1001)
    check("4 model_name=123 -> 1001",
          client.post("/api/v1/model/predict", json={"model_name": 123}, headers=hdr).get_json()["code"] == 1001)
    check("5 unknown model_name -> 1001",
          client.post("/api/v1/model/predict", json={"model_name": "svm"}, headers=hdr).get_json()["code"] == 1001)

    # ---- 训练 ----
    seed()
    r = client.post("/api/v1/model/train", json={}, headers=hdr)
    check("6 train ok", r.get_json().get("code") == 0, r.get_json())
    best_model = r.get_json()["data"]["best_model"]

    # 预测前 predicted_prob 全为 NULL
    db = SessionLocal()
    try:
        nulls = db.query(Customer).filter(Customer.predicted_prob.is_(None)).count()
        check("7 predicted_prob all NULL before predict", nulls == N, nulls)
    finally:
        db.close()

    # ---- 8. 缺省用最佳模型 ----
    r = client.post("/api/v1/model/predict", json={}, headers=hdr)
    b = r.get_json()
    d = b.get("data") or {}
    check(
        "8 predict default -> best model, count=N",
        r.status_code == 200 and b.get("code") == 0
        and set(d) == {"model_name", "predicted_count"}
        and d["model_name"] == best_model and d["predicted_count"] == N,
        f"{d} best={best_model}",
    )

    # ---- 9. 真实回写 + 概率区间 ----
    db = SessionLocal()
    try:
        rows = db.query(Customer).order_by(Customer.id).all()
        probs = [c.predicted_prob for c in rows]
        check("9 all predicted_prob written (no NULL)", all(p is not None for p in probs),
              sum(1 for p in probs if p is None))
        check("10 probs within [0,1]", all(0.0 <= p <= 1.0 for p in probs),
              f"min={min(probs)} max={max(probs)}")
        check("11 probs not constant (real model output)", len(set(round(p, 6) for p in probs)) > 10,
              len(set(round(p, 6) for p in probs)))
    finally:
        db.close()

    # ---- 12. scaler 复用一致性：手工复算与接口回写逐行一致 ----
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.model_name == best_model).order_by(
            Experiment.id.desc()).first()
        bundle = joblib.load(exp.model_path)
        rows = db.query(Customer).order_by(Customer.id).all()
        df = pd.DataFrame([c.to_dict() for c in rows])
        X, _, _ = prepare_features(df, with_target=False)
        expected = bundle["model"].predict_proba(bundle["scaler"].transform(X))[:, 1]
        stored = [c.predicted_prob for c in rows]
        max_diff = max(abs(float(a) - float(b_)) for a, b_ in zip(expected, stored))
        check("12 stored probs match manual recompute (scaler reused, not refit)",
              max_diff < 1e-9, f"max_diff={max_diff}")
    finally:
        db.close()

    # ---- 13. 指定 model_name 覆盖 ----
    r = client.post("/api/v1/model/predict", json={"model_name": "logistic_regression"}, headers=hdr)
    d = r.get_json().get("data") or {}
    check("13 explicit model_name honored", d.get("model_name") == "logistic_regression"
          and d.get("predicted_count") == N, d)

    # ---- 14. 指定模型后概率确实变了（覆盖回写生效） ----
    db = SessionLocal()
    try:
        lr_exp = db.query(Experiment).filter(
            Experiment.model_name == "logistic_regression").order_by(Experiment.id.desc()).first()
        bundle = joblib.load(lr_exp.model_path)
        rows = db.query(Customer).order_by(Customer.id).all()
        df = pd.DataFrame([c.to_dict() for c in rows])
        X, _, _ = prepare_features(df, with_target=False)
        expected = bundle["model"].predict_proba(bundle["scaler"].transform(X))[:, 1]
        stored = [c.predicted_prob for c in rows]
        max_diff = max(abs(float(a) - float(b_)) for a, b_ in zip(expected, stored))
        check("14 overwrite uses the specified model", max_diff < 1e-9, f"max_diff={max_diff}")
    finally:
        db.close()

    # ---- 15. 未训练过的模型名 -> 3002 ----
    db = SessionLocal()
    try:
        db.query(Experiment).filter(Experiment.model_name == "random_forest").delete()
        db.commit()
    finally:
        db.close()
    check("15 trained-but-absent model -> 3002",
          client.post("/api/v1/model/predict", json={"model_name": "random_forest"},
                      headers=hdr).get_json()["code"] == 3002)

    # ---- 16. 模型文件丢失 -> 3002 ----
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.is_best.is_(True)).first()
        exp.model_path = str(Path(exp.model_path).parent / "missing_model.joblib")
        db.commit()
    finally:
        db.close()
    b = client.post("/api/v1/model/predict", json={}, headers=hdr).get_json()
    check("16 missing model file -> 3002", b.get("code") == 3002, b)

    # ---- 17. 无客户数据 -> 2001 ----
    # 按模型名重建路径（不能从已被 case 16 改坏的记录里取）
    from app.core.config import settings as _settings
    db = SessionLocal()
    try:
        exp = db.query(Experiment).filter(Experiment.is_best.is_(True)).first()
        exp.model_path = str(Path(_settings.model_dir_abs) / f"{exp.model_name}.joblib")
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()
    b = client.post("/api/v1/model/predict", json={}, headers=hdr).get_json()
    check("17 no customers -> 2001", b.get("code") == 2001, b)

    # ---- 18. 操作日志 ----
    db = SessionLocal()
    try:
        logs = db.query(OperationLog).filter(OperationLog.action == "prediction").all()
        check("18 operation_log action=prediction written", len(logs) == 2, f"count={len(logs)}")
    finally:
        db.close()

    p_ = sum(1 for _, c in results if c)
    f_ = len(results) - p_
    print(f"\n=== P1-06 smoke: {p_} passed, {f_} failed / {len(results)} ===")
    if f_:
        for n_, c_ in results:
            if not c_:
                print(f"  - {n_}")
    return 0 if f_ == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())