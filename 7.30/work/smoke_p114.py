"""P1-14 操作日志查询 · smoke test（docs/03 §5.1）。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.email_record import EmailRecord  # noqa: E402
from app.models.operation_log import OperationLog  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services import llm_service as llm_mod  # noqa: E402
from app.services.llm_service import LLMService  # noqa: E402
from smoke_p111 import GOOD, patch_llm, seed, token  # noqa: E402

URL = "/api/v1/logs"
results = []
ORIG_INIT = LLMService.__init__


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:220]) if not cond else ""))


def main() -> int:
    app = create_app()
    client = app.test_client()

    db = SessionLocal()
    db.query(OperationLog).delete()
    db.query(EmailRecord).delete()
    db.query(Customer).delete()
    db.query(User).filter(User.username.like("u14_%")).delete()
    db.commit()
    db.close()

    ah: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}
    client.post("/api/v1/auth/register", json={"username": "u14_a", "password": "pwd12345"})
    ua = {"Authorization": f"Bearer {token(client, 'u14_a', 'pwd12345')}"}

    # ---- 空表 ----
    j = client.get(URL, headers=ah).get_json()
    check("1 empty -> total=0, pages=0",
          j.get("code") == 0 and j["data"]["total"] == 0 and j["data"]["pages"] == 0, j)
    check("2 pagination shape",
          set(j["data"].keys()) == {"items", "total", "page", "per_page", "pages"}, list(j["data"].keys()))
    check("3 default per_page=50", j["data"]["per_page"] == 50)

    # ---- 权限 ----
    check("4 no token -> 1002", client.get(URL).get_json()["code"] == 1002)
    r = client.get(URL, headers=ua)
    check("5 normal user -> 403/1003 (docs 5.1 admin only)",
          r.status_code == 403 or r.get_json().get("code") == 1003,
          f"{r.status_code} {r.get_json()}")

    # ---- 造日志：训练 + 预测 + 邮件生成 + 更新 + 标记 + 删除 ----
    seed(40)
    client.post("/api/v1/model/train", json={}, headers=ah)
    client.post("/api/v1/model/predict", json={}, headers=ah)
    patch_llm(text=GOOD)
    client.post("/api/v1/email/generate", json={"customer_ids": [1, 2]}, headers=ah)
    client.post("/api/v1/email/generate", json={"customer_ids": [3]}, headers=ua)
    llm_mod.LLMService.__init__ = ORIG_INIT
    db = SessionLocal()
    rec = db.query(EmailRecord).first()
    rid = rec.id
    a_uid = db.query(User).filter(User.username == "u14_a").first().id
    db.close()
    client.put(f"/api/v1/email/records/{rid}", json={"email_subject": "x"}, headers=ah)
    client.patch(f"/api/v1/email/records/{rid}", json={"status": "sent"}, headers=ah)
    client.delete(f"/api/v1/email/records/{rid}", headers=ah)

    j = client.get(URL, headers=ah).get_json()["data"]
    check("6 logs recorded", j["total"] >= 7, j["total"])
    check("7 item fields (+username)",
          set(j["items"][0].keys()) == {"id", "user_id", "username", "action", "details", "created_at"},
          list(j["items"][0].keys()))
    check("8 username resolved", j["items"][0]["username"] in ("admin", "u14_a"), j["items"][0]["username"])
    check("9 details deserialized to object (not JSON string)",
          isinstance(j["items"][0]["details"], dict), type(j["items"][0]["details"]).__name__)

    ids = [it["id"] for it in j["items"]]
    check("10 newest first", ids == sorted(ids, reverse=True), ids[:6])

    actions = {it["action"] for it in j["items"]}
    check("11 all six action types present",
          {"model_training", "prediction", "email_generation", "email_update",
           "email_mark", "email_delete"} <= actions, sorted(actions))

    # ---- action 过滤 ----
    for act, at_least in (("model_training", 1), ("prediction", 1), ("email_generation", 2),
                          ("email_update", 1), ("email_mark", 1), ("email_delete", 1)):
        d = client.get(f"{URL}?action={act}", headers=ah).get_json()["data"]
        ok = d["total"] >= at_least and all(it["action"] == act for it in d["items"])
        check(f"12.{act} filter works", ok, d["total"])

    check("13 unknown action -> 1001",
          client.get(f"{URL}?action=email_send", headers=ah).get_json().get("code") == 1001)

    # ---- user_id 过滤 ----
    d = client.get(f"{URL}?user_id={a_uid}", headers=ah).get_json()["data"]
    check("14 user_id filter isolates one user",
          d["total"] == 1 and all(it["user_id"] == a_uid for it in d["items"]), d)
    d1 = client.get(f"{URL}?user_id=1", headers=ah).get_json()["data"]
    check("15 admin's own logs", d1["total"] >= 6 and all(it["user_id"] == 1 for it in d1["items"]), d1["total"])
    check("16 nonexistent user_id -> total=0",
          client.get(f"{URL}?user_id=999999", headers=ah).get_json()["data"]["total"] == 0)

    # ---- 组合过滤 ----
    d = client.get(f"{URL}?user_id={a_uid}&action=email_generation", headers=ah).get_json()["data"]
    check("17 user_id + action combined",
          d["total"] == 1 and d["items"][0]["user_id"] == a_uid
          and d["items"][0]["action"] == "email_generation", d)
    check("18 combined filter with no match -> 0",
          client.get(f"{URL}?user_id={a_uid}&action=model_training", headers=ah).get_json()["data"]["total"] == 0)

    # ---- 分页 ----
    total = client.get(URL, headers=ah).get_json()["data"]["total"]
    p1 = client.get(f"{URL}?page=1&per_page=3", headers=ah).get_json()["data"]
    p2 = client.get(f"{URL}?page=2&per_page=3", headers=ah).get_json()["data"]
    check("19 paging splits result", len(p1["items"]) == 3 and p1["total"] == total)
    check("20 page 2 disjoint from page 1",
          not ({i["id"] for i in p1["items"]} & {i["id"] for i in p2["items"]}))
    check("21 pages computed", p1["pages"] == (total + 2) // 3, f"{p1['pages']} total={total}")
    check("22 per_page capped at 200",
          client.get(f"{URL}?per_page=999", headers=ah).get_json()["data"]["per_page"] == 200)
    bad = {}
    for q in ("page=0", "page=abc", "per_page=0", "per_page=x", "user_id=0", "user_id=abc"):
        bad[q] = client.get(f"{URL}?{q}", headers=ah).get_json().get("code")
    check("23 invalid params -> 1001", all(c == 1001 for c in bad.values()), bad)

    # ---- details 脏数据不打断分页 ----
    db = SessionLocal()
    row = db.query(OperationLog).first()
    row.details = "{not-json"
    db.commit()
    db.close()
    j = client.get(URL, headers=ah).get_json()
    check("24 corrupt details degrades to raw string, page still works",
          j.get("code") == 0 and any(it["details"] == "{not-json" for it in j["data"]["items"]), j.get("code"))

    # ---- 只读 ----
    db = SessionLocal()
    n = db.query(OperationLog).count()
    db.close()
    client.get(URL, headers=ah)
    db = SessionLocal()
    check("25 read-only (querying logs adds no log)", db.query(OperationLog).count() == n)
    db.close()

    passed = sum(1 for _, ok in results if ok)
    print(f"\n=== P1-14 smoke: {passed} passed, {len(results) - passed} failed / {len(results)} ===")
    if passed != len(results):
        print("FAILED:", [n for n, ok in results if not ok])
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())