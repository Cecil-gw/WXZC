"""P1-11 LLM 邮件生成 · 端到端 smoke test。

覆盖 docs/03 §4.2 契约 + docs/02 §3.3/3.4/4.1（Prompt 工程、降级、反编码）。
LLM 调用用 monkeypatch 替换，不产生真实网络请求。
自清理所用表，不依赖删除 db 文件（BUG-016 教训）。
"""
from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.email_record import EmailRecord  # noqa: E402
from app.models.experiment import Experiment  # noqa: E402
from app.models.operation_log import OperationLog  # noqa: E402
from app.services import llm_service as llm_mod  # noqa: E402
from app.services.llm_service import (  # noqa: E402
    DEFAULT_PROMPT_TEMPLATE,
    LLMService,
    _strip_markdown_fence,
    naturalize,
)

VA = ["< 1 Year", "1-2 Year", "> 2 Years"]
N = 60
URL = "/api/v1/email/generate"
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("[PASS] " if cond else "[FAIL] ") + name + ((" | " + str(extra)[:220]) if not cond else ""))


def token(client, u="admin", p="admin123") -> str:
    return client.post("/api/v1/auth/login", json={"username": u, "password": p}).get_json()["data"]["access_token"]


def seed(n: int = N, with_prob: bool = True) -> None:
    rnd = random.Random(31)
    db = SessionLocal()
    try:
        db.query(EmailRecord).delete()
        db.query(Customer).delete()
        for i in range(1, n + 1):
            db.add(Customer(
                id=i, gender="Male" if i % 2 else "Female", age=rnd.randint(20, 70),
                driving_license=1, region_code=float(rnd.randint(0, 52)),
                previously_insured=rnd.randint(0, 1), vehicle_age=VA[i % 3],
                vehicle_damage="Yes" if rnd.random() > 0.5 else "No",
                annual_premium=float(rnd.randint(2600, 60000)),
                policy_sales_channel=float(rnd.randint(1, 163)),
                vintage=rnd.randint(10, 299), response=rnd.randint(0, 1),
                predicted_prob=(i / n) if with_prob else None,
            ))
        db.commit()
    finally:
        db.close()


class FakeChoice:
    def __init__(self, text):
        self.message = type("M", (), {"content": text})()


class FakeCompletions:
    def __init__(self, text=None, exc=None):
        self.text, self.exc, self.calls = text, exc, []

    def create(self, **kw):
        self.calls.append(kw)
        if self.exc:
            raise self.exc
        return type("R", (), {"choices": [FakeChoice(self.text)]})()


class FakeClient:
    def __init__(self, text=None, exc=None):
        self.completions = FakeCompletions(text, exc)
        self.chat = type("C", (), {"completions": self.completions})()


def patch_llm(text=None, exc=None):
    """让 LLMService 实例化后带上假 client，返回捕获到的 client。"""
    holder = {}

    def fake_init(self):
        self.client = FakeClient(text, exc)
        self.model, self.temperature = "fake-model", 0.7
        holder["client"] = self.client

    llm_mod.LLMService.__init__ = fake_init
    return holder

ORIG_INIT = LLMService.__init__
GOOD = '{"subject":"专属车险方案","content":"<p>尊敬的客户，您好</p>"}'


def main() -> int:
    app = create_app()
    client = app.test_client()

    db = SessionLocal()
    db.query(OperationLog).delete()
    db.query(EmailRecord).delete()
    db.query(Experiment).delete()
    db.query(Customer).delete()
    db.commit()
    db.close()

    hdr: Dict[str, str] = {"Authorization": f"Bearer {token(client)}"}

    # ===== A. 纯单元：反编码 / markdown 清理 / Prompt 渲染 =====
    nat = naturalize({"gender": "Male", "age": 44, "driving_license": 1,
                      "vehicle_age": "> 2 Years", "vehicle_damage": "Yes",
                      "annual_premium": 30000.0, "previously_insured": 0})
    check("1 naturalize decodes ML encodings (docs/02 4.1)",
          nat["gender"] == "男" and nat["driving_license"] == "有"
          and nat["vehicle_damage"] == "曾受损" and nat["vehicle_age"] == "2 年以上", nat)

    nat2 = naturalize({"gender": "X", "age": None, "driving_license": 0,
                       "vehicle_damage": "??", "annual_premium": None})
    check("2 naturalize tolerates unknown values",
          nat2["gender"] == "X" and nat2["age"] == "未知"
          and nat2["driving_license"] == "无" and nat2["annual_premium"] == "未知", nat2)

    check("3 markdown fence stripped",
          _strip_markdown_fence('```json\n{"a":1}\n```') == '{"a":1}'
          and _strip_markdown_fence('```\n{"a":1}\n```') == '{"a":1}'
          and _strip_markdown_fence('{"a":1}') == '{"a":1}')

    LLMService.__init__ = ORIG_INIT
    rendered = LLMService().render_prompt({"gender": "Female", "age": 33, "driving_license": 1,
                                           "vehicle_age": "1-2 Year", "vehicle_damage": "No",
                                           "annual_premium": 8888.0})
    check("4 prompt rendered with natural language & JSON example intact",
          "女" in rendered and "33" in rendered and "无损记录" in rendered
          and '{"subject"' in rendered and "{gender}" not in rendered, rendered[-90:])

    # 模板占位符 DB 里没有 -> ValueError（由 generate_email 降级）
    try:
        LLMService().render_prompt({"gender": "Male"}, "hi {not_a_field}")
        ok4 = False
    except ValueError:
        ok4 = True
    check("5 unknown placeholder -> ValueError", ok4)

    # ===== B. 无 API_KEY 降级（docs/02 3.4 核心要求）=====
    seed()
    check("6 no API_KEY -> service unavailable", LLMService().available is False)

    r = client.post(URL, json={"limit": 3}, headers=hdr)
    j = r.get_json()
    check("7 no API_KEY still returns code=0 (graceful degrade)", j.get("code") == 0, j)
    d = j.get("data", {})
    check("8 data has exactly {generated_count,failed_count,records}",
          set(d.keys()) == {"generated_count", "failed_count", "records"}, list(d.keys()))
    check("9 all failed, none generated",
          d["generated_count"] == 0 and d["failed_count"] == 3 and len(d["records"]) == 3, d)
    check("10 record item fields == docs 4.2",
          set(d["records"][0].keys()) == {"customer_id", "status", "subject"},
          list(d["records"][0].keys()))

    db = SessionLocal()
    rows = db.query(EmailRecord).all()
    check("11 failed rows persisted to DB (not discarded)",
          len(rows) == 3 and all(x.status == "failed" for x in rows), len(rows))
    check("12 failure reason recorded in content",
          all(x.content and "LLM_API_KEY" in x.content for x in rows),
          rows[0].content if rows else None)
    db.close()

    # ===== C. LLM 成功路径（mock）=====
    holder = patch_llm(text=GOOD)
    db = SessionLocal(); db.query(EmailRecord).delete(); db.commit(); db.close()

    j = client.post(URL, json={"limit": 4}, headers=hdr).get_json()
    d = j.get("data", {})
    check("13 mocked LLM -> all generated",
          j.get("code") == 0 and d["generated_count"] == 4 and d["failed_count"] == 0, d)
    check("14 subject came from LLM JSON",
          all(x["subject"] == "专属车险方案" for x in d["records"]), d["records"][:1])

    db = SessionLocal()
    rows = db.query(EmailRecord).order_by(EmailRecord.id).all()
    check("15 content persisted with HTML body",
          len(rows) == 4 and all("<p>" in (x.content or "") for x in rows), len(rows))
    check("16 created_by = admin id", all(x.created_by == 1 for x in rows))
    check("17 status=generated", all(x.status == "generated" for x in rows))
    db.close()

    # 只对 top N 调用（docs/02 3.6 成本控制）
    check("18 LLM called exactly once per customer",
          len(holder["client"].completions.calls) == 4, len(holder["client"].completions.calls))
    kw = holder["client"].completions.calls[0]
    check("19 temperature=0.7 passed (docs/02 3.3)", kw.get("temperature") == 0.7, kw.get("temperature"))
    check("20 prompt contains natural language profile",
          "性别" in kw["messages"][0]["content"] and "岁" in kw["messages"][0]["content"])

    # 高潜优先：应取概率最大的 4 个（id 57..60）
    check("21 targets are top-prob customers",
          sorted(x["customer_id"] for x in d["records"]) == [57, 58, 59, 60],
          [x["customer_id"] for x in d["records"]])

    # ===== D. markdown 包裹 / 脏返回 =====
    patch_llm(text='```json\n' + GOOD + '\n```')
    j = client.post(URL, json={"customer_ids": [1]}, headers=hdr).get_json()
    check("22 markdown-wrapped JSON parsed ok",
          j["data"]["generated_count"] == 1, j.get("data"))

    patch_llm(text="这不是 JSON")
    j = client.post(URL, json={"customer_ids": [2]}, headers=hdr).get_json()
    check("23 non-JSON reply -> failed, not 500",
          j.get("code") == 0 and j["data"]["failed_count"] == 1, j)

    patch_llm(text='{"subject":"only subject"}')
    j = client.post(URL, json={"customer_ids": [3]}, headers=hdr).get_json()
    check("24 missing content -> failed", j["data"]["failed_count"] == 1, j.get("data"))

    patch_llm(text='["not","an","object"]')
    j = client.post(URL, json={"customer_ids": [4]}, headers=hdr).get_json()
    check("25 JSON array reply -> failed", j["data"]["failed_count"] == 1, j.get("data"))

    patch_llm(text="")
    j = client.post(URL, json={"customer_ids": [5]}, headers=hdr).get_json()
    check("26 empty reply -> failed", j["data"]["failed_count"] == 1, j.get("data"))

    patch_llm(exc=RuntimeError("rate limit exceeded"))
    j = client.post(URL, json={"customer_ids": [6]}, headers=hdr).get_json()
    check("27 SDK exception -> failed, not 500", j.get("code") == 0 and j["data"]["failed_count"] == 1, j)
    db = SessionLocal()
    row = db.query(EmailRecord).filter(EmailRecord.customer_id == 6).first()
    check("28 exception detail saved in content",
          row is not None and "rate limit" in (row.content or ""), row.content if row else None)
    db.close()

    # ===== E. 部分成功混合 =====
    class MixedCompletions:
        def __init__(self):
            self.n = 0
            self.calls = []

        def create(self, **kw):
            self.calls.append(kw)
            self.n += 1
            if self.n % 2:
                return type("R", (), {"choices": [FakeChoice(GOOD)]})()
            raise RuntimeError("boom")

    def mixed_init(self):
        comp = MixedCompletions()
        self.client = type("Cl", (), {"chat": type("C", (), {"completions": comp})()})()
        self.model, self.temperature = "fake", 0.7

    llm_mod.LLMService.__init__ = mixed_init
    j = client.post(URL, json={"customer_ids": [11, 12, 13, 14]}, headers=hdr).get_json()
    d = j.get("data", {})
    check("29 partial failure: 2 ok + 2 failed, one failure does not abort others",
          d["generated_count"] == 2 and d["failed_count"] == 2 and len(d["records"]) == 4, d)

    # ===== F. 参数校验 =====
    patch_llm(text=GOOD)
    bad = {}
    bad["ids=[]"] = client.post(URL, json={"customer_ids": []}, headers=hdr).get_json().get("code")
    bad["ids=str"] = client.post(URL, json={"customer_ids": "1,2"}, headers=hdr).get_json().get("code")
    bad["ids=[str]"] = client.post(URL, json={"customer_ids": ["1"]}, headers=hdr).get_json().get("code")
    bad["ids=[bool]"] = client.post(URL, json={"customer_ids": [True]}, headers=hdr).get_json().get("code")
    bad["limit=0"] = client.post(URL, json={"limit": 0}, headers=hdr).get_json().get("code")
    bad["limit=-1"] = client.post(URL, json={"limit": -1}, headers=hdr).get_json().get("code")
    bad["limit=str"] = client.post(URL, json={"limit": "5"}, headers=hdr).get_json().get("code")
    bad["limit=999"] = client.post(URL, json={"limit": 999}, headers=hdr).get_json().get("code")
    bad["ids too many"] = client.post(URL, json={"customer_ids": list(range(1, 60))}, headers=hdr).get_json().get("code")
    check("30 invalid params -> 1001", all(c == 1001 for c in bad.values()), bad)

    check("31 unknown customer_ids -> 2001",
          client.post(URL, json={"customer_ids": [999999]}, headers=hdr).get_json().get("code") == 2001)
    check("32 no token -> 1002", client.post(URL, json={"limit": 1}).get_json()["code"] == 1002)

    # ===== G. customer_ids 优先，不走分位数 =====
    db = SessionLocal(); db.query(EmailRecord).delete(); db.commit(); db.close()
    j = client.post(URL, json={"customer_ids": [1, 2], "limit": 30}, headers=hdr).get_json()
    check("33 customer_ids wins over limit, no quantile filter",
          j["data"]["generated_count"] == 2
          and sorted(x["customer_id"] for x in j["data"]["records"]) == [1, 2], j.get("data"))

    # 低概率客户（不在 top 10%）也能被显式指定
    check("34 explicit low-prob customer accepted",
          client.post(URL, json={"customer_ids": [1]}, headers=hdr).get_json()["data"]["generated_count"] == 1)

    # 去重
    j = client.post(URL, json={"customer_ids": [7, 7, 7]}, headers=hdr).get_json()
    check("35 duplicate ids deduped", j["data"]["generated_count"] == 1, j.get("data"))

    # ===== H. 无预测数据 =====
    seed(with_prob=False)
    check("36 limit mode without predictions -> 3002",
          client.post(URL, json={"limit": 3}, headers=hdr).get_json().get("code") == 3002)
    check("37 customer_ids mode works without predictions",
          client.post(URL, json={"customer_ids": [1]}, headers=hdr).get_json().get("code") == 0)

    # ===== I. Prompt 模板来自 DB =====
    seed()
    from app.models.prompt_template import PromptTemplate
    db = SessionLocal()
    tpl = db.query(PromptTemplate).filter(PromptTemplate.is_active.is_(True)).first()
    check("38 seeded active prompt template exists", tpl is not None)
    orig_content = tpl.content if tpl else None
    tpl.content = "SENTINEL-TPL 客户性别{gender} 年龄{age}"
    db.commit(); db.close()

    holder = patch_llm(text=GOOD)
    client.post(URL, json={"customer_ids": [8]}, headers=hdr)
    sent = holder["client"].completions.calls[0]["messages"][0]["content"]
    check("39 DB template used at generation time (docs/02 3.5)", "SENTINEL-TPL" in sent, sent[:60])

    db = SessionLocal()
    tpl = db.query(PromptTemplate).filter(PromptTemplate.is_active.is_(True)).first()
    tpl.content = orig_content
    db.commit(); db.close()

    # 无 active 模板时回落到默认
    db = SessionLocal()
    db.query(PromptTemplate).update({"is_active": False})
    db.commit(); db.close()
    holder = patch_llm(text=GOOD)
    client.post(URL, json={"customer_ids": [9]}, headers=hdr)
    sent = holder["client"].completions.calls[0]["messages"][0]["content"]
    check("40 falls back to DEFAULT_PROMPT_TEMPLATE when no active row",
          "保险营销文案专家" in sent and "SENTINEL" not in sent, sent[:50])
    db = SessionLocal()
    db.query(PromptTemplate).filter(PromptTemplate.name == "default").update({"is_active": True})
    db.commit(); db.close()

    # ===== J. 日志与权限 =====
    db = SessionLocal()
    n_before = db.query(OperationLog).filter(OperationLog.action == "email_generation").count()
    db.close()
    patch_llm(text=GOOD)
    client.post(URL, json={"customer_ids": [10]}, headers=hdr)
    db = SessionLocal()
    n_after = db.query(OperationLog).filter(OperationLog.action == "email_generation").count()
    db.close()
    check("41 email_generation logged", n_after == n_before + 1, f"{n_before}->{n_after}")

    client.post("/api/v1/auth/register", json={"username": "u_p111", "password": "pwd12345"})
    uh = {"Authorization": f"Bearer {token(client, 'u_p111', 'pwd12345')}"}
    check("42 normal user allowed (docs 4.2 not admin-only)",
          client.post(URL, json={"customer_ids": [15]}, headers=uh).get_json().get("code") == 0)

    LLMService.__init__ = ORIG_INIT
    passed = sum(1 for _, ok in results if ok)
    print(f"\n=== P1-11 smoke: {passed} passed, {len(results) - passed} failed / {len(results)} ===")
    if passed != len(results):
        print("FAILED:", [n for n, ok in results if not ok])
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
