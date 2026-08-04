"""P1-10 与真实预测链路的集成校验：train -> predict -> targets。

不属于 23 用例，单独跑一次确认 predicted_prob 由模型真实回写时 targets 可用。
"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from smoke_p110 import seed, token  # noqa: E402
from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402
from app.models.experiment import Experiment  # noqa: E402

app = create_app()
c = app.test_client()
db = SessionLocal(); db.query(Experiment).delete(); db.query(Customer).delete(); db.commit(); db.close()

seed(with_prob=False)
h = {"Authorization": f"Bearer {token(c)}"}
print("train:", c.post("/api/v1/model/train", json={}, headers=h).get_json().get("code"))
pr = c.post("/api/v1/model/predict", json={}, headers=h).get_json()
print("predict:", pr.get("code"), pr.get("data"))
t = c.get("/api/v1/email/targets", headers=h).get_json()
d = t.get("data", {})
print("targets:", t.get("code"), "threshold=", d.get("threshold"), "total=", d.get("total"))
print("top3:", [(x["id"], round(x["predicted_prob"], 4)) for x in d.get("customers", [])[:3]])
ok = (t.get("code") == 0 and 0 < d.get("threshold", -1) < 1 and d.get("total", 0) > 0)
print("INTEGRATION:", "PASS" if ok else "FAIL")