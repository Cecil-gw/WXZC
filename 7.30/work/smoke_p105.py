"""P1-05 实验记录分页 + 最佳模型查询 · 端到端 smoke test。"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.experiment import Experiment  # noqa: E402

VA = ["< 1 Year", "1-2 Year", "> 2 Years"]
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:220]) if not cond else ""))


def seed_customers(n: int = 500) -> None:
    rnd = random.Random(5)
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

    # 干净起点
    db = SessionLocal()
    db.query(Experiment).delete()
    db.query(Customer).delete()
    db.commit()
    db.close()

    admin = token(client)
    hdr: Dict[str, str] = {"Authorization": f"Bearer {admin}"}

    # ---- 1. 未训练时 /best -> 3002 ----
    r = client.get("/api/v1/model/best", headers=hdr)
    b = r.get_json()
    check("1 /best without model -> 3002", b.get("code") == 3002, b)

    # ---- 2. 未训练时 /experiments -> 空分页而非报错 ----
    r = client.get("/api/v1/model/experiments", headers=hdr)
    d = r.get_json().get("data") or {}
    check(
        "2 /experiments empty -> items=[] total=0 pages=0",
        r.status_code == 200 and d.get("items") == [] and d.get("total") == 0 and d.get("pages") == 0,
        d,
    )

    # ---- 3. 鉴权 ----
    check("3 /experiments no token -> 1002", client.get("/api/v1/model/experiments").get_json()["code"] == 1002)
    check("4 /best no token -> 1002", client.get("/api/v1/model/best").get_json()["code"] == 1002)

    # 普通用户可读（docs §3.2/§3.3 只要求登录，不限 admin）
    client.post("/api/v1/auth/register", json={"username": "u_p105", "password": "user1234"})
    uhdr = {"Authorization": f"Bearer {token(client, 'u_p105', 'user1234')}"}

    # ---- 训练两轮，产生 4 条实验 ----
    seed_customers(500)
    r1 = client.post("/api/v1/model/train", json={}, headers=hdr)
    check("5 train#1 ok (3 experiments)", r1.get_json().get("code") == 0, r1.get_json())
    r2 = client.post("/api/v1/model/train", json={"models": ["logistic_regression"]}, headers=hdr)
    check("6 train#2 ok (+1 experiment)", r2.get_json().get("code") == 0, r2.get_json())

    # ---- 7. 分页第 1 页 ----
    r = client.get("/api/v1/model/experiments?page=1&per_page=3", headers=hdr)
    d = r.get_json()["data"]
    check(
        "7 page1 per_page=3 -> 3 items, total=4, pages=2",
        len(d["items"]) == 3 and d["total"] == 4 and d["pages"] == 2 and d["page"] == 1,
        {k: d.get(k) for k in ("total", "page", "per_page", "pages")},
    )
    page1_ids = [i["id"] for i in d["items"]]

    # ---- 8. 第 2 页无重叠 ----
    r = client.get("/api/v1/model/experiments?page=2&per_page=3", headers=hdr)
    d2 = r.get_json()["data"]
    page2_ids = [i["id"] for i in d2["items"]]
    check(
        "8 page2 -> 1 item, no overlap with page1",
        len(page2_ids) == 1 and not set(page1_ids) & set(page2_ids),
        f"p1={page1_ids} p2={page2_ids}",
    )

    # ---- 9. items 字段齐全（docs §3.2） ----
    item = d["items"][0] if d["items"] else {}
    need = {
        "id", "model_name", "accuracy", "precision", "recall", "f1_score",
        "roc_auc", "params", "model_path", "is_best", "created_at",
    }
    check("9 item fields match docs 3.2", need <= set(item), sorted(need - set(item)))

    # ---- 10. params 含可复现可视化数据 ----
    p = item.get("params") or {}
    ok10 = (
        isinstance(p, dict)
        and {"roc", "confusion_matrix", "feature_importances", "feature_names"} <= set(p)
        and isinstance(p["roc"].get("fpr"), list) and len(p["roc"]["fpr"]) > 1
        and len(p["roc"]["fpr"]) == len(p["roc"]["tpr"])
        and len(p["confusion_matrix"]) == 2 and len(p["confusion_matrix"][0]) == 2
        and len(p["feature_importances"]) == len(p["feature_names"]) == 10
    )
    check("10 params reproducible (ROC/CM/importances)", ok10, list(p) if isinstance(p, dict) else type(p))

    # ---- 11. model_name 过滤 ----
    r = client.get("/api/v1/model/experiments?model_name=logistic_regression", headers=hdr)
    d = r.get_json()["data"]
    check(
        "11 filter model_name -> only LR, total=2",
        d["total"] == 2 and all(i["model_name"] == "logistic_regression" for i in d["items"]),
        d["total"],
    )

    # ---- 12. 非法 model_name -> 1001 ----
    check(
        "12 unknown model_name -> 1001",
        client.get("/api/v1/model/experiments?model_name=svm", headers=hdr).get_json()["code"] == 1001,
    )

    # ---- 13. per_page 上限 200 ----
    d = client.get("/api/v1/model/experiments?per_page=999", headers=hdr).get_json()["data"]
    check("13 per_page capped at 200", d["per_page"] == 200, d["per_page"])

    # ---- 14. 非法分页参数 -> 1001 ----
    check("14 page=abc -> 1001", client.get("/api/v1/model/experiments?page=abc", headers=hdr).get_json()["code"] == 1001)
    check("15 page=0 -> 1001", client.get("/api/v1/model/experiments?page=0", headers=hdr).get_json()["code"] == 1001)

    # ---- 16. /best 结构 + 与 DB 一致 ----
    r = client.get("/api/v1/model/best", headers=hdr)
    b = r.get_json()
    d = b.get("data") or {}
    db = SessionLocal()
    try:
        rows = db.query(Experiment).all()
        bests = [e for e in rows if e.is_best]
        db_best = bests[0] if bests else None
        check(
            "16 /best schema & matches DB is_best row",
            b.get("code") == 0
            and set(d) == {"model_name", "roc_auc", "experiment_id"}
            and db_best is not None
            and d["experiment_id"] == db_best.id
            and d["model_name"] == db_best.model_name
            and abs(d["roc_auc"] - db_best.roc_auc) < 1e-9,
            f"api={d} db_best_id={getattr(db_best, 'id', None)}",
        )
        check("17 is_best still unique across 4 rows", len(rows) == 4 and len(bests) == 1, f"rows={len(rows)} best={len(bests)}")
        # /best 的 roc_auc 应是全部实验里的最大值
        check(
            "18 best roc_auc == max over experiments",
            abs(d["roc_auc"] - max(e.roc_auc for e in rows)) < 1e-9,
            f"api={d.get('roc_auc')} max={max(e.roc_auc for e in rows)}",
        )
    finally:
        db.close()

    # ---- 19. 普通用户可读两个接口 ----
    check(
        "19 normal user can read /experiments and /best",
        client.get("/api/v1/model/experiments", headers=uhdr).get_json()["code"] == 0
        and client.get("/api/v1/model/best", headers=uhdr).get_json()["code"] == 0,
    )

    # ---- 20. 排序：created_at 倒序 ----
    d = client.get("/api/v1/model/experiments?per_page=200", headers=hdr).get_json()["data"]
    ids = [i["id"] for i in d["items"]]
    check("20 ordered by created_at desc (id desc tiebreak)", ids == sorted(ids, reverse=True), ids)

    p_ = sum(1 for _, c in results if c)
    f_ = len(results) - p_
    print(f"\n=== P1-05 smoke: {p_} passed, {f_} failed / {len(results)} ===")
    return 0 if f_ == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())