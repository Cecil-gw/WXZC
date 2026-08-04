"""P1-13 邮件记录 CRUD · smoke test（docs/03 §4.5-4.10）。

重点：普通用户与 admin 的数据隔离、越权返回 2001 而非 1003。
"""
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

BASE = "/api/v1/email/records"
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
    db.query(User).filter(User.username.like("u13_%")).delete()
    db.commit()
    db.close()

    seed(30)
    ah: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}
    client.post("/api/v1/auth/register", json={"username": "u13_a", "password": "pwd12345"})
    client.post("/api/v1/auth/register", json={"username": "u13_b", "password": "pwd12345"})
    ua = {"Authorization": f"Bearer {token(client, 'u13_a', 'pwd12345')}"}
    ub = {"Authorization": f"Bearer {token(client, 'u13_b', 'pwd12345')}"}

    # admin 生成 3 条，u13_a 生成 2 条
    patch_llm(text=GOOD)
    client.post("/api/v1/email/generate", json={"customer_ids": [1, 2, 3]}, headers=ah)
    client.post("/api/v1/email/generate", json={"customer_ids": [4, 5]}, headers=ua)
    llm_mod.LLMService.__init__ = ORIG_INIT

    db = SessionLocal()
    all_rows = db.query(EmailRecord).order_by(EmailRecord.id).all()
    admin_ids = [r.id for r in all_rows if r.created_by == 1]
    a_ids = [r.id for r in all_rows if r.created_by != 1]
    db.close()
    check("1 fixture: 3 admin + 2 user records", len(admin_ids) == 3 and len(a_ids) == 2,
          f"admin={admin_ids} a={a_ids}")

    # ===== §4.5 列表 =====
    check("2 no token -> 1002", client.get(BASE).get_json()["code"] == 1002)
    j = client.get(BASE, headers=ah).get_json()
    check("3 admin sees all 5", j["data"]["total"] == 5, j["data"]["total"])
    check("4 pagination shape",
          set(j["data"].keys()) == {"items", "total", "page", "per_page", "pages"}, list(j["data"].keys()))
    check("5 item fields == docs 4.5 (+username for admin)",
          set(j["data"]["items"][0].keys()) == {"id", "customer_id", "subject", "status",
                                                "created_at", "created_by_username"},
          list(j["data"]["items"][0].keys()))
    check("6 admin list has no content field (list is lightweight)",
          all("content" not in it for it in j["data"]["items"]))
    names = {it["created_by_username"] for it in j["data"]["items"]}
    check("7 created_by_username resolved", names == {"admin", "u13_a"}, names)

    ja = client.get(BASE, headers=ua).get_json()
    check("8 normal user sees only own 2", ja["data"]["total"] == 2, ja["data"]["total"])
    check("9 normal user list omits created_by_username",
          all("created_by_username" not in it for it in ja["data"]["items"]))
    check("10 u13_b sees 0", client.get(BASE, headers=ub).get_json()["data"]["total"] == 0)

    # 排序：最新在前
    ids_desc = [it["id"] for it in j["data"]["items"]]
    check("11 ordered newest first", ids_desc == sorted(ids_desc, reverse=True), ids_desc)

    # status 过滤
    check("12 status=generated -> 5", client.get(BASE + "?status=generated", headers=ah).get_json()["data"]["total"] == 5)
    check("13 status=failed -> 0", client.get(BASE + "?status=failed", headers=ah).get_json()["data"]["total"] == 0)
    check("14 status=bogus -> 1001", client.get(BASE + "?status=bogus", headers=ah).get_json().get("code") == 1001)
    check("15 per_page capped at 200",
          client.get(BASE + "?per_page=999", headers=ah).get_json()["data"]["per_page"] == 200)
    check("16 invalid paging -> 1001",
          client.get(BASE + "?page=0", headers=ah).get_json().get("code") == 1001
          and client.get(BASE + "?page=abc", headers=ah).get_json().get("code") == 1001)
    p2 = client.get(BASE + "?page=2&per_page=2", headers=ah).get_json()["data"]
    check("17 page 2 works", p2["page"] == 2 and p2["pages"] == 3 and len(p2["items"]) == 2, p2["pages"])

    # ===== §4.6 详情 =====
    rid = admin_ids[0]
    j = client.get(f"{BASE}/{rid}", headers=ah).get_json()
    check("18 detail ok with full content",
          j.get("code") == 0 and "<p>" in j["data"]["content"], j.get("data", {}).get("content"))
    check("19 detail has created_by & updated_at",
          "created_by" in j["data"] and "updated_at" in j["data"], list(j["data"].keys()))
    check("20 missing record -> 2001", client.get(f"{BASE}/999999", headers=ah).get_json().get("code") == 2001)
    check("21 cross-user detail -> 2001 (not 1003, avoids id enumeration)",
          client.get(f"{BASE}/{rid}", headers=ua).get_json().get("code") == 2001)
    check("22 own record accessible by owner",
          client.get(f"{BASE}/{a_ids[0]}", headers=ua).get_json().get("code") == 0)
    check("23 admin can read others' record",
          client.get(f"{BASE}/{a_ids[0]}", headers=ah).get_json().get("code") == 0)
    # ===== §4.7 更新 =====
    j = client.put(f"{BASE}/{rid}", json={"email_subject": "改后主题"}, headers=ah).get_json()
    check("24 update subject only", j.get("code") == 0 and j["data"]["subject"] == "改后主题", j)
    check("25 content untouched when omitted", "<p>" in j["data"]["content"], j["data"]["content"][:40])

    j = client.put(f"{BASE}/{rid}", json={"email_content": "<p>新正文</p>"}, headers=ah).get_json()
    check("26 update content only",
          j["data"]["content"] == "<p>新正文</p>" and j["data"]["subject"] == "改后主题", j.get("data"))

    j = client.put(f"{BASE}/{rid}", json={"email_subject": "S2", "email_content": "C2"}, headers=ah).get_json()
    check("27 update both", j["data"]["subject"] == "S2" and j["data"]["content"] == "C2")

    j = client.put(f"{BASE}/{rid}", json={"email_subject": None}, headers=ah).get_json()
    check("28 explicit null clears subject", j["data"]["subject"] is None, j.get("data"))

    bad = {}
    bad["empty body"] = client.put(f"{BASE}/{rid}", json={}, headers=ah).get_json().get("code")
    bad["subject int"] = client.put(f"{BASE}/{rid}", json={"email_subject": 5}, headers=ah).get_json().get("code")
    bad["content int"] = client.put(f"{BASE}/{rid}", json={"email_content": 5}, headers=ah).get_json().get("code")
    bad["too long"] = client.put(f"{BASE}/{rid}", json={"email_subject": "x" * 300}, headers=ah).get_json().get("code")
    check("29 invalid update -> 1001", all(c == 1001 for c in bad.values()), bad)
    check("30 cross-user update -> 2001",
          client.put(f"{BASE}/{rid}", json={"email_subject": "hack"}, headers=ua).get_json().get("code") == 2001)
    db = SessionLocal()
    check("31 cross-user update did not modify row",
          db.query(EmailRecord).filter(EmailRecord.id == rid).first().subject is None)
    db.close()

    # ===== §4.8 标记状态 =====
    j = client.patch(f"{BASE}/{rid}", json={"status": "sent"}, headers=ah).get_json()
    check("32 mark sent", j.get("code") == 0 and j["data"]["status"] == "sent", j)
    db = SessionLocal()
    check("33 status persisted",
          db.query(EmailRecord).filter(EmailRecord.id == rid).first().status == "sent")
    db.close()
    check("34 mark failed ok",
          client.patch(f"{BASE}/{rid}", json={"status": "failed"}, headers=ah).get_json()["data"]["status"] == "failed")
    bad2 = {}
    for v in (None, "", "shipped", 1, True):
        bad2[str(v)] = client.patch(f"{BASE}/{rid}", json={"status": v}, headers=ah).get_json().get("code")
    check("35 invalid status -> 1001", all(c == 1001 for c in bad2.values()), bad2)
    check("36 cross-user mark -> 2001",
          client.patch(f"{BASE}/{rid}", json={"status": "sent"}, headers=ua).get_json().get("code") == 2001)
    check("37 status filter reflects mark",
          client.get(BASE + "?status=failed", headers=ah).get_json()["data"]["total"] == 1)

    # ===== §4.9 单条删除 =====
    check("38 cross-user delete -> 2001",
          client.delete(f"{BASE}/{rid}", headers=ua).get_json().get("code") == 2001)
    db = SessionLocal()
    check("39 cross-user delete did not remove row",
          db.query(EmailRecord).filter(EmailRecord.id == rid).first() is not None)
    db.close()
    j = client.delete(f"{BASE}/{rid}", headers=ah).get_json()
    check("40 delete ok -> {success:true}", j.get("code") == 0 and j["data"] == {"success": True}, j)
    db = SessionLocal()
    check("41 row actually gone", db.query(EmailRecord).filter(EmailRecord.id == rid).first() is None)
    db.close()
    check("42 delete twice -> 2001", client.delete(f"{BASE}/{rid}", headers=ah).get_json().get("code") == 2001)
    check("43 owner can delete own",
          client.delete(f"{BASE}/{a_ids[0]}", headers=ua).get_json().get("code") == 0)

    # ===== §4.10 批量删除 =====
    patch_llm(text=GOOD)
    client.post("/api/v1/email/generate", json={"customer_ids": [10, 11, 12]}, headers=ah)
    client.post("/api/v1/email/generate", json={"customer_ids": [13, 14]}, headers=ub)
    llm_mod.LLMService.__init__ = ORIG_INIT
    db = SessionLocal()
    rows = db.query(EmailRecord).all()
    admin_new = [r.id for r in rows if r.created_by == 1]
    b_uid = db.query(User).filter(User.username == "u13_b").first().id
    b_new = [r.id for r in rows if r.created_by == b_uid]
    db.close()
    check("44 fixture for bulk: 3 admin + 2 u13_b", len(admin_new) >= 3 and len(b_new) == 2,
          f"admin={admin_new} b={b_new}")

    bad3 = {}
    bad3["missing"] = client.delete(BASE, json={}, headers=ah).get_json().get("code")
    bad3["empty"] = client.delete(BASE, json={"record_ids": []}, headers=ah).get_json().get("code")
    bad3["str"] = client.delete(BASE, json={"record_ids": "1,2"}, headers=ah).get_json().get("code")
    bad3["str item"] = client.delete(BASE, json={"record_ids": ["1"]}, headers=ah).get_json().get("code")
    bad3["bool item"] = client.delete(BASE, json={"record_ids": [True]}, headers=ah).get_json().get("code")
    bad3["too many"] = client.delete(BASE, json={"record_ids": list(range(1, 300))}, headers=ah).get_json().get("code")
    check("45 invalid record_ids -> 1001", all(c == 1001 for c in bad3.values()), bad3)

    # 普通用户批量删除：只删掉自己的，别人的静默跳过
    mixed = [b_new[0], admin_new[0], 999999]
    j = client.delete(BASE, json={"record_ids": mixed}, headers=ub).get_json()
    check("46 user bulk delete removes only own (others skipped)",
          j.get("code") == 0 and j["data"] == {"deleted_count": 1}, j)
    db = SessionLocal()
    check("47 other user's record survived",
          db.query(EmailRecord).filter(EmailRecord.id == admin_new[0]).first() is not None)
    db.close()

    # 去重
    j = client.delete(BASE, json={"record_ids": [b_new[1], b_new[1]]}, headers=ub).get_json()
    check("48 duplicate ids counted once", j["data"]["deleted_count"] == 1, j.get("data"))

    # admin 批量删除跨用户
    db = SessionLocal()
    remaining = [r.id for r in db.query(EmailRecord).all()]
    db.close()
    j = client.delete(BASE, json={"record_ids": remaining + [888888]}, headers=ah).get_json()
    check("49 admin bulk delete across users",
          j["data"]["deleted_count"] == len(remaining), f"{j.get('data')} vs {len(remaining)}")
    db = SessionLocal()
    check("50 all records gone", db.query(EmailRecord).count() == 0)
    db.close()
    check("51 nonexistent ids -> deleted_count=0",
          client.delete(BASE, json={"record_ids": [777777]}, headers=ah).get_json()["data"]["deleted_count"] == 0)

    # ===== 操作日志 =====
    db = SessionLocal()
    acts = {a: db.query(OperationLog).filter(OperationLog.action == a).count()
            for a in ("email_update", "email_mark", "email_delete")}
    db.close()
    check("52 email_update/mark/delete all logged",
          acts["email_update"] >= 4 and acts["email_mark"] >= 2 and acts["email_delete"] >= 5, acts)

    passed = sum(1 for _, ok in results if ok)
    print(f"\n=== P1-13 smoke: {passed} passed, {len(results) - passed} failed / {len(results)} ===")
    if passed != len(results):
        print("FAILED:", [n for n, ok in results if not ok])
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
