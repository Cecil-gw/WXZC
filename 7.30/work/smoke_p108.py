"""P1-08 模型评估可视化 · 端到端 smoke test。"""
from __future__ import annotations

import base64
import random
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.core.database import SessionLocal
from app.models.customer import Customer
from app.models.experiment import Experiment

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
VA = ["< 1 Year", "1-2 Year", "> 2 Years"]
CHARTS = ["roc_curve", "metrics_comparison", "confusion_matrix", "feature_importance"]
MODELS = ["logistic_regression", "random_forest", "xgboost"]
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:200]) if not cond else ""))


def seed(n=400):
    rnd = random.Random(31)
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


def is_png(b64, min_bytes=3000):
    try:
        raw = base64.b64decode(b64 or "")
    except Exception:
        return False, 0
    return raw.startswith(PNG_MAGIC) and len(raw) > min_bytes, len(raw)


def get_chart(client, hdr, chart, model=None):
    url = f"/api/v1/model/visualization/{chart}"
    if model:
        url += f"?model={model}"
    return client.get(url, headers=hdr)

def main():
    app = create_app()
    client = app.test_client()

    db = SessionLocal()
    db.query(Experiment).delete()
    db.query(Customer).delete()
    db.commit()
    db.close()

    hdr: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}

    # ---- 1-2. 未训练时 -> 3002 ----
    check("1 roc_curve without experiments -> 3002",
          get_chart(client, hdr, "roc_curve").get_json().get("code") == 3002)
    check("2 confusion_matrix without experiments -> 3002",
          get_chart(client, hdr, "confusion_matrix", "xgboost").get_json().get("code") == 3002)

    # ---- 3. 未认证 -> 1002 ----
    check("3 no token -> 1002",
          client.get("/api/v1/model/visualization/roc_curve").get_json()["code"] == 1002)

    # 训练（唯一一次训练：后续所有图表都从 experiments.params 复原）
    seed(400)
    tr = client.post("/api/v1/model/train", json={}, headers=hdr)
    check("4 train ok", tr.get_json().get("code") == 0, tr.get_json())

    db = SessionLocal()
    try:
        exp_count_before = db.query(Experiment).count()
    finally:
        db.close()

    # ---- 5. 未知 chart_type -> 1001 ----
    check("5 unknown chart_type -> 1001",
          get_chart(client, hdr, "nope").get_json()["code"] == 1001)

    # ---- 6-7. 缺 model 参数 -> 1001 ----
    check("6 confusion_matrix without model -> 1001",
          get_chart(client, hdr, "confusion_matrix").get_json()["code"] == 1001)
    check("7 feature_importance without model -> 1001",
          get_chart(client, hdr, "feature_importance").get_json()["code"] == 1001)

    # ---- 8. 非法 model -> 1001 ----
    check("8 unknown model -> 1001",
          get_chart(client, hdr, "confusion_matrix", "svm").get_json()["code"] == 1001)

    # ---- 9-10. 跨模型对比图返回真 PNG ----
    for i, chart in enumerate(["roc_curve", "metrics_comparison"], start=9):
        r = get_chart(client, hdr, chart)
        b = r.get_json()
        d = b.get("data") or {}
        ok_png, size = is_png(d.get("image_base64"))
        check(f"{i} {chart} -> real PNG",
              r.status_code == 200 and b.get("code") == 0
              and set(d) == {"chart_type", "image_base64", "format"}
              and d.get("chart_type") == chart and d.get("format") == "png" and ok_png,
              f"code={b.get('code')} keys={sorted(d)} bytes={size}")

    # ---- 11-16. 单模型图 x 3 算法 ----
    idx = 11
    for chart in ["confusion_matrix", "feature_importance"]:
        for m in MODELS:
            r = get_chart(client, hdr, chart, m)
            b = r.get_json()
            d = b.get("data") or {}
            ok_png, size = is_png(d.get("image_base64"))
            check(f"{idx} {chart}[{m}] -> real PNG",
                  b.get("code") == 0 and d.get("chart_type") == chart and ok_png,
                  f"code={b.get('code')} bytes={size}")
            idx += 1

    # ---- 17. 不重新训练：experiments 行数与 predicted_prob 均未变 ----
    db = SessionLocal()
    try:
        after = db.query(Experiment).count()
        nulls = db.query(Customer).filter(Customer.predicted_prob.is_(None)).count()
        check("17 charts do not retrain (experiments count & data unchanged)",
              after == exp_count_before == 3 and nulls == 400,
              f"before={exp_count_before} after={after} nulls={nulls}")
    finally:
        db.close()

    # ---- 18. 不同图表产出不同图像 ----
    imgs = {}
    for chart in ["roc_curve", "metrics_comparison"]:
        imgs[chart] = (get_chart(client, hdr, chart).get_json()["data"]["image_base64"])
    for m in MODELS:
        imgs[f"cm_{m}"] = get_chart(client, hdr, "confusion_matrix", m).get_json()["data"]["image_base64"]
    check("18 distinct charts produce distinct images",
          len(set(imgs.values())) == len(imgs), f"{len(set(imgs.values()))}/{len(imgs)}")

    # ---- 19. 同一请求可重复（幂等，不改状态） ----
    a = get_chart(client, hdr, "roc_curve").get_json()["data"]["image_base64"]
    b_ = get_chart(client, hdr, "roc_curve").get_json()["data"]["image_base64"]
    check("19 repeated request is idempotent", a == b_)

    # ---- 20. 单模型未训练过 -> 3002 ----
    db = SessionLocal()
    try:
        db.query(Experiment).filter(Experiment.model_name == "random_forest").delete()
        db.commit()
    finally:
        db.close()
    check("20 model without experiment -> 3002",
          get_chart(client, hdr, "feature_importance", "random_forest").get_json()["code"] == 3002)

    # ---- 21. params 损坏 -> 3002（而非 500） ----
    db = SessionLocal()
    try:
        e = db.query(Experiment).filter(Experiment.model_name == "xgboost").first()
        orig = e.params
        e.params = "{not-json"
        db.commit()
    finally:
        db.close()
    check("21 corrupted params -> 3002",
          get_chart(client, hdr, "confusion_matrix", "xgboost").get_json()["code"] == 3002)
    db = SessionLocal()
    try:
        e = db.query(Experiment).filter(Experiment.model_name == "xgboost").first()
        e.params = orig
        db.commit()
    finally:
        db.close()

    # ---- 22. 普通用户可读（docs §3.6 未限 admin） ----
    client.post("/api/v1/auth/register", json={"username": "u_p108", "password": "user1234"})
    uhdr = {"Authorization": f"Bearer {token(client, 'u_p108', 'user1234')}"}
    check("22 normal user can read charts",
          get_chart(client, uhdr, "metrics_comparison").get_json()["code"] == 0)

    # ---- 23. 数据模块的 4 个 EDA 图未受影响（P1-03 回归） ----
    eda_ok = all(
        client.get(f"/api/v1/data/visualization/{c}", headers=hdr).get_json().get("code") == 0
        for c in ["response_distribution", "gender_response", "age_distribution", "premium_distribution"]
    )
    check("23 P1-03 EDA charts still work", eda_ok)

    p_ = sum(1 for _, c in results if c)
    f_ = len(results) - p_
    print(f"\n=== P1-08 smoke: {p_} passed, {f_} failed / {len(results)} ===")
    if f_:
        for n_, c_ in results:
            if not c_:
                print(f"  - {n_}")
    return 0 if f_ == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
