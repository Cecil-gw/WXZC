"""P1-02 客户分页查询 · 端到端 smoke test（10 用例）。"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402


# -------- 工具 --------

def _seed(n: int = 25) -> None:
    """Seed n customers：ids 1..n，gender 交替，age 20+i，previously_insured 0/1 交替。"""
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        for i in range(1, n + 1):
            db.add(Customer(
                id=i,
                gender="Male" if i % 2 == 0 else "Female",
                age=20 + i,  # 21..45
                driving_license=1,
                region_code=28.0,
                previously_insured=i % 2,  # 0/1 交替
                vehicle_age="1-2 Year",
                vehicle_damage="Yes" if i % 3 == 0 else "No",
                annual_premium=30000.0 + i * 10,
                policy_sales_channel=152.0,
                vintage=100 + i,
                response=0,
            ))
        db.commit()
    finally:
        db.close()


def _admin_token(client) -> str:
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200
    return r.get_json()["data"]["access_token"]


def _hdr(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# -------- 用例 --------

def case_1_page_1(client, token) -> None:
    """page=1, per_page=10 -> 前 10 个 id (1..10)"""
    r = client.get("/api/v1/data/customers?page=1&per_page=10", headers=_hdr(token))
    assert r.status_code == 200
    body = r.get_json()
    assert body["code"] == 0
    data = body["data"]
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["per_page"] == 10
    assert data["pages"] == 3
    ids = [item["id"] for item in data["items"]]
    assert ids == list(range(1, 11)), f"ids={ids}"
    # items 包含 14 字段（含 created_at/updated_at/predicted_prob）
    assert len(data["items"][0]) == 15, f"item keys={list(data['items'][0].keys())}"
    print(f"[1] page=1 per_page=10 -> total=25, pages=3, ids=1..10, item 15 字段齐全")


def case_2_page_2(client, token) -> None:
    """page=2, per_page=10 -> id 11..20"""
    r = client.get("/api/v1/data/customers?page=2&per_page=10", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    ids = [item["id"] for item in data["items"]]
    assert ids == list(range(11, 21)), f"ids={ids}"
    print(f"[2] page=2 per_page=10 -> ids=11..20")


def case_3_gender_filter(client, token) -> None:
    """gender=Female -> i%2==1 的 id (1,3,5..25) 共 13 个"""
    r = client.get("/api/v1/data/customers?gender=Female&per_page=50", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["total"] == 13
    assert all(item["gender"] == "Female" for item in data["items"])
    print(f"[3] gender=Female -> total=13, 全部 Female")


def case_4_age_min(client, token) -> None:
    """age_min=40 -> age>=40, 即 id 21..25 (age=41..45) 共 5 个"""
    r = client.get("/api/v1/data/customers?age_min=40&per_page=50", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["total"] == 6  # 20+21=41? 等等, age=20+i >= 40 -> i>=20 -> 6 个 (20..25)
    assert all(item["age"] >= 40 for item in data["items"])
    print(f"[4] age_min=40 -> total={data['total']} (age=20+i >= 40 -> i=20..25)")


def case_5_age_max(client, token) -> None:
    """age_max=25 -> age<=25, 即 id 1..5 (age=21..25) 共 5 个"""
    r = client.get("/api/v1/data/customers?age_max=25&per_page=50", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["total"] == 5
    assert all(item["age"] <= 25 for item in data["items"])
    print(f"[5] age_max=25 -> total=5, age<=25")


def case_6_previously_insured(client, token) -> None:
    """previously_insured=1 -> i%2==1 的 id (1,3,5..25) 共 13 个"""
    r = client.get("/api/v1/data/customers?previously_insured=1&per_page=50", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["total"] == 13
    assert all(item["previously_insured"] == 1 for item in data["items"])
    print(f"[6] previously_insured=1 -> total=13")


def case_7_keyword(client, token) -> None:
    """keyword=5 -> id=5 的 1 个"""
    r = client.get("/api/v1/data/customers?keyword=5&per_page=50", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["total"] == 1
    assert data["items"][0]["id"] == 5
    print(f"[7] keyword=5 -> total=1, id=5")


def case_8_per_page_cap(client, token) -> None:
    """per_page=500 -> cap 到 200"""
    r = client.get("/api/v1/data/customers?per_page=500", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["per_page"] == 200, f"per_page={data['per_page']}"
    assert data["total"] == 25
    assert len(data["items"]) == 25  # 实际数据只有 25
    print(f"[8] per_page=500 -> cap 到 200, 实际 25 条全返回")


def case_9_empty_data(client, token) -> None:
    """清空 DB -> total=0, pages=0, items=[]"""
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()
    r = client.get("/api/v1/data/customers", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["total"] == 0
    assert data["pages"] == 0
    assert data["items"] == []
    print(f"[9] empty data -> total=0, pages=0, items=[]")


def case_10_invalid_params(client, token) -> None:
    """非法参数 -> 1001"""
    # per_page=abc
    r = client.get("/api/v1/data/customers?per_page=abc", headers=_hdr(token))
    assert r.status_code == 400
    assert r.get_json()["code"] == 1001
    # age_min=-1
    r = client.get("/api/v1/data/customers?age_min=-1", headers=_hdr(token))
    assert r.status_code == 400
    assert r.get_json()["code"] == 1001
    # page=0
    r = client.get("/api/v1/data/customers?page=0", headers=_hdr(token))
    assert r.status_code == 400
    assert r.get_json()["code"] == 1001
    # previously_insured=2 越界
    r = client.get("/api/v1/data/customers?previously_insured=2", headers=_hdr(token))
    assert r.status_code == 400
    assert r.get_json()["code"] == 1001
    print(f"[10] invalid params (per_page=abc / age_min=-1 / page=0 / previously_insured=2) -> 1001")


def main() -> int:
    app = create_app()
    client = app.test_client()
    token = _admin_token(client)

    _seed(25)

    cases = [
        ("page_1",        lambda: case_1_page_1(client, token)),
        ("page_2",        lambda: case_2_page_2(client, token)),
        ("gender",        lambda: case_3_gender_filter(client, token)),
        ("age_min",       lambda: case_4_age_min(client, token)),
        ("age_max",       lambda: case_5_age_max(client, token)),
        ("prev_insured",  lambda: case_6_previously_insured(client, token)),
        ("keyword",       lambda: case_7_keyword(client, token)),
        ("per_page_cap",  lambda: case_8_per_page_cap(client, token)),
        ("empty",         lambda: case_9_empty_data(client, token)),
        ("invalid",       lambda: case_10_invalid_params(client, token)),
    ]
    for name, fn in cases:
        fn()

    # 清场
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()

    print()
    print("=" * 60)
    print(f"P1-02 smoke: {len(cases)} / {len(cases)} cases passed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())