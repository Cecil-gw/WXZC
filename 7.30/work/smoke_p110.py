"""P1-10 高潜客户筛选 · 端到端 smoke test。

覆盖 docs/03 §4.1 契约 + docs/02 §2.7 分位数策略。
自清理所用表，不依赖删除 db 文件（BUG-016 教训）。
"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.experiment import Experiment  # noqa: E402
from app.models.operation_log import OperationLog  # noqa: E402

VA = ["< 1 Year", "1-2 Year", "> 2 Years"]
N = 400
URL = "/api/v1/email/targets"
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:220]) if not cond else ""))


def token(client, u="admin", p="admin123") -> str:
    return client.post("/api/v1/auth/login", json={"username": u, "password": p}).get_json()["data"]["access_token"]


def seed(n: int = N, with_prob: bool = False) -> None:
    """插入 n 条客户。with_prob=True 时直接写入确定的 predicted_prob。"""
    rnd = random.Random(29)
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        for i in range(1, n + 1):
            db.add(Customer(
                id=i,
                gender="Male" if i % 2 else "Female",
                age=rnd.randint(20, 70),
                driving_license=1,
                region_code=float(rnd.randint(0, 52)),
                previously_insured=rnd.randint(0, 1),
                vehicle_age=VA[i % 3],
                vehicle_damage="Yes" if rnd.random() > 0.5 else "No",
                annual_premium=float(rnd.randint(2600, 60000)),
                policy_sales_channel=float(rnd.randint(1, 163)),
                vintage=rnd.randint(10, 299),
                response=rnd.randint(0, 1),
                # i/n 让概率在 (0,1] 上均匀分布，分位数可手工精确复算
                predicted_prob=(i / n) if with_prob else None,
            ))
        db.commit()
    finally:
        db.close()


def main() -> int:
    app = create_app()
    client = app.test_client()

    db = SessionLocal()
    db.query(OperationLog).delete()
    db.query(Experiment).delete()
    db.query(Customer).delete()
    db.commit()
    db.close()

    hdr: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}

    # ---- 1. 未认证 ----
    check("1 no token -> 1002", client.get(URL).get_json()["code"] == 1002)

    # ---- 2. 无任何客户 -> 3002 ----
    check("2 empty table -> 3002", client.get(URL, headers=hdr).get_json().get("code") == 3002)

    # ---- 3. 有客户但 predicted_prob 全 NULL -> 3002 ----
    seed(with_prob=False)
    j = client.get(URL, headers=hdr).get_json()
    check("3 all predicted_prob NULL -> 3002", j.get("code") == 3002, j)

    # ---- 填入确定概率：prob_i = i/400，i=1..400 ----
    seed(with_prob=True)
    probs = [i / N for i in range(1, N + 1)]

    # ---- 4. 默认 percentile=0.9 ----
    j = client.get(URL, headers=hdr).get_json()
    check("4 default call ok", j.get("code") == 0, j)
    d = j.get("data", {})
    check("5 data has exactly {threshold,total,customers}",
          set(d.keys()) == {"threshold", "total", "customers"}, list(d.keys()))

    # ---- 6. threshold 等于 np.quantile(probs, 0.9) ----
    expected = float(np.quantile(np.asarray(probs), 0.9))
    check("6 threshold == np.quantile(probs,0.9)",
          abs(d["threshold"] - expected) < 1e-9, f"got={d['threshold']} exp={expected}")

    # ---- 7. total 与手工统计一致（top 10% 约 41 条，含边界） ----
    manual = sum(1 for p in probs if p >= expected)
    check("7 total matches manual count", d["total"] == manual, f"got={d['total']} exp={manual}")

    # ---- 8. 默认 per_page=20 ----
    check("8 default per_page=20 -> 20 items", len(d["customers"]) == 20, len(d["customers"]))

    # ---- 9. customers 字段恰为 docs 规定的五个 ----
    check("9 customer fields == docs §4.1",
          set(d["customers"][0].keys()) == {"id", "gender", "age", "annual_premium", "predicted_prob"},
          list(d["customers"][0].keys()))

    # ---- 10. 按 predicted_prob 倒序 ----
    seq = [c["predicted_prob"] for c in d["customers"]]
    check("10 sorted by predicted_prob desc", seq == sorted(seq, reverse=True), seq[:5])

    # ---- 11. 首条即全表最大概率 ----
    check("11 first item is global max prob",
          abs(d["customers"][0]["predicted_prob"] - max(probs)) < 1e-9, d["customers"][0])

    # ---- 12. 每条都 >= threshold ----
    check("12 every item >= threshold", all(c["predicted_prob"] >= d["threshold"] - 1e-12 for c in d["customers"]))

    # ---- 13. 第二页不与第一页重叠且延续排序 ----
    p2 = client.get(URL + "?page=2", headers=hdr).get_json()["data"]
    ids1 = {c["id"] for c in d["customers"]}
    ids2 = {c["id"] for c in p2["customers"]}
    check("13 page=2 disjoint from page=1 and continues order",
          not (ids1 & ids2) and p2["customers"][0]["predicted_prob"] <= seq[-1],
          f"overlap={ids1 & ids2}")

    # ---- 14. total 跨页恒定 ----
    check("14 total stable across pages", p2["total"] == d["total"], f"{p2['total']} vs {d['total']}")

    # ---- 15. percentile=0.5 命中约一半，且阈值更低 ----
    j5 = client.get(URL + "?percentile=0.5", headers=hdr).get_json()["data"]
    exp5 = float(np.quantile(np.asarray(probs), 0.5))
    check("15 percentile=0.5 -> lower threshold & more targets",
          abs(j5["threshold"] - exp5) < 1e-9 and j5["total"] > d["total"],
          f"th={j5['threshold']} total={j5['total']}")

    # ---- 16. percentile 越小命中越多（单调性） ----
    totals = []
    for pc in (0.99, 0.9, 0.5, 0.1):
        totals.append(client.get(URL + f"?percentile={pc}", headers=hdr).get_json()["data"]["total"])
    check("16 total monotonically increases as percentile drops",
          all(totals[i] <= totals[i + 1] for i in range(len(totals) - 1)), totals)

    # ---- 17. per_page 上限 200 ----
    big = client.get(URL + "?percentile=0.1&per_page=999", headers=hdr).get_json()["data"]
    check("17 per_page capped at 200", len(big["customers"]) <= 200, len(big["customers"]))

    # ---- 18. 非法 percentile -> 1001 ----
    bad = {}
    for v in ("0", "1", "-0.5", "1.5", "abc", "nan", "inf"):
        bad[v] = client.get(URL + f"?percentile={v}", headers=hdr).get_json().get("code")
    check("18 invalid percentile -> 1001", all(c == 1001 for c in bad.values()), bad)

    # ---- 19. 非法分页参数 -> 1001 ----
    bad2 = {}
    for q in ("page=abc", "page=0", "per_page=0", "per_page=xyz"):
        bad2[q] = client.get(URL + "?" + q, headers=hdr).get_json().get("code")
    check("19 invalid paging -> 1001", all(c == 1001 for c in bad2.values()), bad2)

    # ---- 20. 部分 NULL 时 NULL 行被排除 ----
    db = SessionLocal()
    db.query(Customer).filter(Customer.id <= 200).update({"predicted_prob": None})
    db.commit()
    db.close()
    part = client.get(URL + "?percentile=0.5&per_page=200", headers=hdr).get_json()["data"]
    rest = [i / N for i in range(201, N + 1)]
    exp_th = float(np.quantile(np.asarray(rest), 0.5))
    check("20 NULL rows excluded from quantile & results",
          abs(part["threshold"] - exp_th) < 1e-9
          and all(c["predicted_prob"] is not None for c in part["customers"]),
          f"th={part['threshold']} exp={exp_th}")

    # ---- 21. 普通用户可读（docs §4 未限 admin） ----
    client.post("/api/v1/auth/register", json={"username": "u_p110", "password": "pwd12345"})
    uh = {"Authorization": f"Bearer {token(client, 'u_p110', 'pwd12345')}"}
    check("21 normal user allowed", client.get(URL, headers=uh).get_json().get("code") == 0)

    # ---- 22. 幂等：同一请求两次结果一致 ----
    a = client.get(URL + "?percentile=0.8", headers=hdr).get_json()["data"]
    b = client.get(URL + "?percentile=0.8", headers=hdr).get_json()["data"]
    check("22 idempotent", a == b)

    # ---- 23. 只读：调用不写库 ----
    db = SessionLocal()
    n_cust = db.query(Customer).count()
    n_log = db.query(OperationLog).count()
    db.close()
    client.get(URL, headers=hdr)
    db = SessionLocal()
    check("23 read-only (no rows added)",
          db.query(Customer).count() == n_cust and db.query(OperationLog).count() == n_log)
    db.close()

    passed = sum(1 for _, ok in results if ok)
    print(f"\n=== P1-10 smoke: {passed} passed, {len(results) - passed} failed / {len(results)} ===")
    if passed != len(results):
        print("FAILED:", [n for n, ok in results if not ok])
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())