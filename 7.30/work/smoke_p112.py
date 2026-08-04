"""P1-12 Prompt 模板管理 · smoke test。

覆盖 docs/03 §4.3/4.4 + P0 Gate WARNING 5-C（is_active 唯一性靠业务层保证）。
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
from app.models.prompt_template import PromptTemplate  # noqa: E402
from app.services import llm_service as llm_mod  # noqa: E402
from app.services.llm_service import DEFAULT_PROMPT_TEMPLATE, LLMService  # noqa: E402
from smoke_p111 import GOOD, patch_llm, seed, token  # noqa: E402

URL = "/api/v1/email/prompt"
results = []
ORIG_INIT = LLMService.__init__


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:220]) if not cond else ""))


def active_rows():
    db = SessionLocal()
    try:
        return db.query(PromptTemplate).filter(PromptTemplate.is_active.is_(True)).all()
    finally:
        db.close()


VALID = "角色设定。客户：性别{gender}，年龄{age}岁。请输出 JSON。"


def main() -> int:
    app = create_app()
    client = app.test_client()

    db = SessionLocal()
    db.query(EmailRecord).delete()
    db.query(Customer).delete()
    # 只留一条 default 模板并激活，保证起点干净
    db.query(PromptTemplate).filter(PromptTemplate.name != "default").delete()
    db.query(PromptTemplate).update({"is_active": False})
    row = db.query(PromptTemplate).filter(PromptTemplate.name == "default").first()
    if row is None:
        row = PromptTemplate(name="default", content=DEFAULT_PROMPT_TEMPLATE, is_active=True)
        db.add(row)
    else:
        row.content = DEFAULT_PROMPT_TEMPLATE
        row.is_active = True
    db.commit()
    db.close()

    hdr: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}

    # ---- GET ----
    check("1 no token -> 1002", client.get(URL).get_json()["code"] == 1002)
    j = client.get(URL, headers=hdr).get_json()
    check("2 GET ok", j.get("code") == 0, j)
    check("3 data == {name, content}", set(j["data"].keys()) == {"name", "content"}, list(j["data"].keys()))
    check("4 content has placeholders (docs 4.3)",
          "{gender}" in j["data"]["content"] and "{age}" in j["data"]["content"])
    check("5 seeded content returned", j["data"]["content"] == DEFAULT_PROMPT_TEMPLATE)

    # ---- PUT 校验 ----
    bad = {}
    bad["missing content"] = client.put(URL, json={}, headers=hdr).get_json().get("code")
    bad["null"] = client.put(URL, json={"content": None}, headers=hdr).get_json().get("code")
    bad["empty"] = client.put(URL, json={"content": "   "}, headers=hdr).get_json().get("code")
    bad["int"] = client.put(URL, json={"content": 123}, headers=hdr).get_json().get("code")
    bad["no placeholder"] = client.put(URL, json={"content": "写一封邮件"}, headers=hdr).get_json().get("code")
    bad["only gender"] = client.put(URL, json={"content": "性别{gender}"}, headers=hdr).get_json().get("code")
    bad["too long"] = client.put(URL, json={"content": "{gender}{age}" + "x" * 5000}, headers=hdr).get_json().get("code")
    bad["unknown ph"] = client.put(URL, json={"content": "{gender}{age}{nope}"}, headers=hdr).get_json().get("code")
    check("6 invalid content -> 1001", all(c == 1001 for c in bad.values()), bad)

    check("7 failed PUT did not change stored template",
          client.get(URL, headers=hdr).get_json()["data"]["content"] == DEFAULT_PROMPT_TEMPLATE)
    check("8 failed PUT left exactly one active row", len(active_rows()) == 1, len(active_rows()))

    # ---- PUT 成功 ----
    j = client.put(URL, json={"content": VALID}, headers=hdr).get_json()
    check("9 PUT ok, echoes new content",
          j.get("code") == 0 and j["data"]["content"] == VALID, j)
    check("10 GET reflects update immediately",
          client.get(URL, headers=hdr).get_json()["data"]["content"] == VALID)
    check("11 still exactly one active row (WARNING 5-C)", len(active_rows()) == 1, len(active_rows()))

    # 前后空白被 strip
    j = client.put(URL, json={"content": "  " + VALID + "  "}, headers=hdr).get_json()
    check("12 content stripped", j["data"]["content"] == VALID)

    # name 可选更新
    j = client.put(URL, json={"content": VALID, "name": "促销版"}, headers=hdr).get_json()
    check("13 name updatable", j["data"]["name"] == "促销版", j.get("data"))
    j = client.put(URL, json={"content": VALID}, headers=hdr).get_json()
    check("14 name preserved when omitted", j["data"]["name"] == "促销版", j.get("data"))

    # ---- 多条 is_active 时的收敛（WARNING 5-C 的核心场景）----
    db = SessionLocal()
    db.add(PromptTemplate(name="stray-1", content=VALID, is_active=True))
    db.add(PromptTemplate(name="stray-2", content=VALID, is_active=True))
    db.commit()
    db.close()
    check("15 precondition: 3 active rows injected", len(active_rows()) == 3, len(active_rows()))
    r = client.put(URL, json={"content": VALID + " v2"}, headers=hdr).get_json()
    check("16 PUT converges to a single active row", r.get("code") == 0 and len(active_rows()) == 1,
          f"code={r.get('code')} active={len(active_rows())}")
    check("17 GET returns the converged one",
          client.get(URL, headers=hdr).get_json()["data"]["content"] == VALID + " v2")

    db = SessionLocal()
    db.query(PromptTemplate).filter(PromptTemplate.name.like("stray-%")).delete()
    db.commit()
    db.close()

    # ---- 无 active 行时 GET 回落 + PUT 新建 ----
    db = SessionLocal()
    db.query(PromptTemplate).update({"is_active": False})
    db.commit()
    db.close()
    j = client.get(URL, headers=hdr).get_json()
    check("18 GET falls back to default template when no active row",
          j["data"]["content"] == DEFAULT_PROMPT_TEMPLATE and j["data"]["name"] == "default", j.get("data"))
    j = client.put(URL, json={"content": VALID, "name": "重建版"}, headers=hdr).get_json()
    check("19 PUT creates a new active row when none active",
          j.get("code") == 0 and len(active_rows()) == 1, f"active={len(active_rows())}")

    # ---- 更新后立即生效于 /email/generate（验收标准 3）----
    seed(20)
    sentinel = "SENTINEL-P112 性别{gender} 年龄{age}"
    client.put(URL, json={"content": sentinel}, headers=hdr)
    holder = patch_llm(text=GOOD)
    r = client.post("/api/v1/email/generate", json={"customer_ids": [1]}, headers=hdr).get_json()
    sent = holder["client"].completions.calls[0]["messages"][0]["content"]
    check("20 updated template takes effect on next generate",
          r.get("code") == 0 and "SENTINEL-P112" in sent, sent[:60])

    client.put(URL, json={"content": sentinel.replace("P112", "P112B")}, headers=hdr)
    holder = patch_llm(text=GOOD)
    client.post("/api/v1/email/generate", json={"customer_ids": [2]}, headers=hdr)
    sent2 = holder["client"].completions.calls[0]["messages"][0]["content"]
    check("21 second update also takes effect (no caching staleness)",
          "SENTINEL-P112B" in sent2, sent2[:60])

    # ---- 普通用户 ----
    llm_mod.LLMService.__init__ = ORIG_INIT
    client.post("/api/v1/auth/register", json={"username": "u_p112", "password": "pwd12345"})
    uh = {"Authorization": f"Bearer {token(client, 'u_p112', 'pwd12345')}"}
    check("22 normal user can GET (docs 4.3 not admin-only)",
          client.get(URL, headers=uh).get_json().get("code") == 0)
    check("23 normal user can PUT (docs 4.4 not admin-only)",
          client.put(URL, json={"content": VALID}, headers=uh).get_json().get("code") == 0)

    # ---- 还原 seed 模板 ----
    db = SessionLocal()
    db.query(PromptTemplate).update({"is_active": False})
    row = db.query(PromptTemplate).order_by(PromptTemplate.id).first()
    row.name, row.content, row.is_active = "default", DEFAULT_PROMPT_TEMPLATE, True
    db.query(PromptTemplate).filter(PromptTemplate.id != row.id).delete()
    db.commit()
    db.close()
    check("24 restored to single default active row",
          len(active_rows()) == 1 and active_rows()[0].name == "default")

    passed = sum(1 for _, ok in results if ok)
    print(f"\n=== P1-12 smoke: {passed} passed, {len(results) - passed} failed / {len(results)} ===")
    if passed != len(results):
        print("FAILED:", [n for n, ok in results if not ok])
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())