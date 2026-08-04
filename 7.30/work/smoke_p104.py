"""P1-04 特征工程 + 三模型训练 · 端到端 smoke test。"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.experiment import Experiment  # noqa: E402
from app.models.operation_log import OperationLog  # noqa: E402
from app.utils.data_processor import FEATURE_NAMES, prepare_features  # noqa: E402

VEHICLE_AGES = ["< 1 Year", "1-2 Year", "> 2 Years"]


def _seed(n: int = 600) -> None:
    """Seed n 条客户，正样本约 13%（贴近真实 87:13）。"""
    rnd = random.Random(7)
    db = SessionLocal()
    try:
        db.query(Experiment).delete()
        db.query(Customer).delete()
        for i in range(1, n + 1):
            age = rnd.randint(20, 70)
            prev = rnd.randint(0, 1)
            damage = "Yes" if rnd.random() > 0.5 else "No"
            # 让标签与特征有真实相关性，保证 AUC 明显 > 0.5
            score = (0 if prev else 0.5) + (0.4 if damage == "Yes" else 0) + age / 200
            resp = 1 if score + rnd.gauss(0, 0.15) > 1.05 else 0
            db.add(Customer(
                id=i,
                gender="Male" if i % 2 else "Female",
                age=age,
                driving_license=1,
                region_code=float(rnd.randint(0, 52)),
                previously_insured=prev,
                vehicle_age=VEHICLE_AGES[i % 3],
                vehicle_damage=damage,
                annual_premium=float(rnd.randint(2600, 60000)),
                policy_sales_channel=float(rnd.randint(1, 163)),
                vintage=rnd.randint(10, 299),
                response=resp,
            ))
        db.commit()
    finally:
        db.close()


def _token(client, username: str = "admin", password: str = "admin123") -> str:
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.get_json()
    return r.get_json()["data"]["access_token"]


def _hdr(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def main() -> int:
    passed, failed = 0, 0

    def check(name: str, cond: bool, extra: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"[PASS] {name}")
        else:
            failed += 1
            print(f"[FAIL] {name} {extra}")

    app = create_app()
    client = app.test_client()

    # ---- case 1: 无数据训练 -> 2001 ----
    # 自清理所用表：不依赖删除 db 文件（Windows 下文件可能被其它进程占用，
    # 静默失败会让 operation_logs 跨轮累积，导致 case 13 计数偏大）
    db = SessionLocal()
    db.query(OperationLog).filter(OperationLog.action == "model_training").delete()
    db.query(Experiment).delete()
    db.query(Customer).delete()
    db.commit()
    db.close()
    admin = _token(client)
    r = client.post("/api/v1/model/train", json={}, headers=_hdr(admin))
    check("1 no-data -> 2001", r.get_json()["code"] == 2001, str(r.get_json()))

    _seed(600)

    # ---- case 2: prepare_features 编码正确 ----
    import pandas as pd
    dfx = pd.DataFrame([{
        "gender": "Male", "age": 30, "driving_license": 1, "region_code": 28.0,
        "previously_insured": 0, "vehicle_age": "> 2 Years", "vehicle_damage": "Yes",
        "annual_premium": 30000.0, "policy_sales_channel": 152.0, "vintage": 100,
        "response": 1,
    }])
    X, y, names = prepare_features(dfx)
    check(
        "2 prepare_features encoding",
        names == FEATURE_NAMES
        and int(X.iloc[0]["gender"]) == 0
        and int(X.iloc[0]["vehicle_age"]) == 2
        and int(X.iloc[0]["vehicle_damage"]) == 1
        and int(y.iloc[0]) == 1,
        str(X.to_dict("records")),
    )

    # ---- case 3: 非法 vehicle_age -> 1001 ----
    bad = dfx.copy()
    bad.loc[0, "vehicle_age"] = "10 Years"
    try:
        prepare_features(bad)
        check("3 bad vehicle_age -> BizException", False)
    except Exception as exc:
        check("3 bad vehicle_age -> BizException", getattr(exc, "code", None) == 1001, repr(exc))

    # ---- case 4: 普通用户训练 -> 1003 ----
    client.post("/api/v1/auth/register", json={"username": "u_p104", "password": "user1234"})
    user = _token(client, "u_p104", "user1234")
    r = client.post("/api/v1/model/train", json={}, headers=_hdr(user))
    check("4 non-admin -> 1003", r.status_code == 403 and r.get_json()["code"] == 1003, str(r.get_json()))

    # ---- case 5: 未认证 -> 1002 ----
    r = client.post("/api/v1/model/train", json={})
    check("5 no-token -> 1002", r.get_json()["code"] == 1002, str(r.get_json()))

    # ---- case 6: 非法模型名 -> 1001 ----
    r = client.post("/api/v1/model/train", json={"models": ["svm"]}, headers=_hdr(admin))
    check("6 unknown model -> 1001", r.get_json()["code"] == 1001, str(r.get_json()))

    # ---- case 7: 非法 test_size -> 1001 ----
    r = client.post("/api/v1/model/train", json={"test_size": 0.9}, headers=_hdr(admin))
    check("7 test_size out of range -> 1001", r.get_json()["code"] == 1001, str(r.get_json()))

    # ---- case 8: 全量训练三模型 ----
    t0 = time.time()
    r = client.post("/api/v1/model/train", json={}, headers=_hdr(admin))
    elapsed = time.time() - t0
    body = r.get_json()
    ok8 = (
        r.status_code == 200
        and body["code"] == 0
        and set(body["data"]["results"].keys())
        == {"logistic_regression", "random_forest", "xgboost"}
        and body["data"]["best_model"] in body["data"]["results"]
    )
    check("8 train all three models", ok8, str(body)[:300])
    print(f"       elapsed={elapsed:.2f}s")

    # ---- case 9: 指标完整 + AUC 合理 + best 按 AUC ----
    res = body["data"]["results"]
    keys = {"accuracy", "precision", "recall", "f1_score", "roc_auc"}
    best_by_auc = max(res, key=lambda k: res[k]["roc_auc"])
    check(
        "9 metrics complete & best by roc_auc",
        all(keys <= set(v.keys()) for v in res.values())
        and all(0.0 <= v["roc_auc"] <= 1.0 for v in res.values())
        and best_by_auc == body["data"]["best_model"]
        and res[best_by_auc]["roc_auc"] > 0.6,
        str(res),
    )

    # ---- case 10: experiments 3 条 + is_best 唯一 + params 可反序列化 ----
    db = SessionLocal()
    try:
        exps = db.query(Experiment).all()
        bests = [e for e in exps if e.is_best]
        params_ok = True
        for e in exps:
            p = json.loads(e.params)
            if not ({"roc", "confusion_matrix", "feature_importances", "feature_names"} <= set(p)):
                params_ok = False
            if len(p["feature_names"]) != len(p["feature_importances"]):
                params_ok = False
        check(
            "10 experiments rows & is_best unique & params json",
            len(exps) == 3 and len(bests) == 1 and params_ok,
            f"rows={len(exps)} best={len(bests)} params_ok={params_ok}",
        )
    finally:
        db.close()

    # ---- case 11: joblib 含 model + scaler ----
    import joblib
    paths = list(Path(settings.model_dir_abs).glob("*.joblib"))
    bundle_ok = bool(paths)
    for p in paths:
        b = joblib.load(p)
        if not ("model" in b and "scaler" in b):
            bundle_ok = False
    check("11 joblib bundle has model+scaler", bundle_ok and len(paths) >= 3, f"paths={[p.name for p in paths]}")

    # ---- case 12: 二次训练 is_best 仍唯一 ----
    r = client.post("/api/v1/model/train", json={"models": ["logistic_regression"]}, headers=_hdr(admin))
    db = SessionLocal()
    try:
        exps = db.query(Experiment).all()
        bests = [e for e in exps if e.is_best]
        check(
            "12 retrain keeps is_best unique",
            r.get_json()["code"] == 0 and len(exps) == 4 and len(bests) == 1,
            f"rows={len(exps)} best={len(bests)}",
        )
    finally:
        db.close()

    # ---- case 13: operation_logs 写入 ----
    db = SessionLocal()
    try:
        logs = db.query(OperationLog).filter(OperationLog.action == "model_training").all()
        check("13 operation_log written", len(logs) == 2, f"count={len(logs)}")
    finally:
        db.close()

    print(f"\n=== P1-04 smoke: {passed} passed, {failed} failed ===")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())