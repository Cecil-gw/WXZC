"""P1-03 数据统计 + 质量 + EDA 可视化 · 端到端 smoke test。"""
from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.models.customer import Customer  # noqa: E402


# PNG magic bytes for base64 validation
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


# -------- 工具 --------

def _seed() -> None:
    """Seed 25 customers：gender/age/previously_insured/response 多样。"""
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        for i in range(1, 26):
            db.add(Customer(
                id=i,
                gender="Male" if i % 2 == 0 else "Female",
                age=20 + (i % 30),     # 21..50
                driving_license=1,
                region_code=28.0,
                previously_insured=i % 2,
                vehicle_age="1-2 Year",
                vehicle_damage="Yes" if i % 3 == 0 else "No",
                annual_premium=30000.0 + i * 100,
                policy_sales_channel=152.0,
                vintage=100 + i,
                response=1 if i % 4 == 0 else 0,  # 25% positive
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


def _is_valid_png_b64(b64str: str) -> bool:
    """校验 base64 字符串确实解码为合法 PNG。"""
    try:
        raw = base64.b64decode(b64str)
        return raw[:8] == _PNG_MAGIC and len(raw) > 100
    except Exception:
        return False


# -------- 用例 --------

def case_1_unauthorized(client) -> None:
    """无 token -> 1002"""
    r = client.get("/api/v1/data/statistics")
    assert r.status_code == 401
    assert r.get_json()["code"] == 1002
    print("[1] no token (statistics) -> 401 / 1002")


def case_2_statistics_on_25_rows(client, token) -> None:
    """25 行数据 -> statistics 完整结构"""
    r = client.get("/api/v1/data/statistics", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["total"] == 25
    # gender: i%2==0 是 Male，共 12 个 (i=2,4,6,8,10,12,14,16,18,20,22,24)；Female 13 个
    assert data["gender_distribution"]["Male"] == 12
    assert data["gender_distribution"]["Female"] == 13
    # response: i%4==0 是 1，共 6 个 (i=4,8,12,16,20,24)；0 共 19 个
    assert data["response_distribution"]["0"] == 19
    assert data["response_distribution"]["1"] == 6
    # age_stats
    assert data["age_stats"]["min"] == 21  # i=1, age=20+1=21
    assert data["age_stats"]["max"] == 45  # i=25, age=20+25=45 (25%30=25)
    assert isinstance(data["age_stats"]["avg"], (int, float))
    print(f"[2] statistics(25) -> total=25, gender M/F=12/13, response 0/1=19/6, age range=21..45")


def case_3_statistics_empty(client, token) -> None:
    """清空 -> statistics zeroed"""
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()
    r = client.get("/api/v1/data/statistics", headers=_hdr(token))
    data = r.get_json()["data"]
    assert data["total"] == 0
    assert data["gender_distribution"] == {"Male": 0, "Female": 0}
    assert data["response_distribution"] == {"0": 0, "1": 0}
    assert data["age_stats"]["min"] == 0
    assert data["age_stats"]["max"] == 0
    assert data["age_stats"]["avg"] == 0.0
    print("[3] statistics(empty) -> zeroed structure")


def case_4_quality_on_25_rows(client, token) -> None:
    """25 行 -> quality 报告"""
    _seed()
    r = client.get("/api/v1/data/quality", headers=_hdr(token))
    body = r.get_json()
    data = body["data"]
    assert data["total_rows"] == 25
    assert data["total_cols"] == 15  # 12 + predicted_prob + created_at + updated_at
    assert data["duplicates"] == 0
    # dtypes 全部 str
    for col, dt in data["dtypes"].items():
        assert isinstance(dt, str)
    # missing_values：业务字段全 0；predicted_prob 未设置（默认 None）会有 25
    for col, n in data["missing_values"].items():
        if col == "predicted_prob":
            assert n == 25
        else:
            assert n == 0, f"col={col} n={n}"
    print(f"[4] quality(25) -> total=25, cols=15, dup=0, all missing=0")


def case_5_quality_empty(client, token) -> None:
    """空表 -> quality zeroed"""
    db = SessionLocal()
    try:
        db.query(Customer).delete()
        db.commit()
    finally:
        db.close()
    r = client.get("/api/v1/data/quality", headers=_hdr(token))
    data = r.get_json()["data"]
    assert data["total_rows"] == 0
    assert data["total_cols"] == 0
    assert data["duplicates"] == 0
    assert data["missing_values"] == {}
    assert data["dtypes"] == {}
    print("[5] quality(empty) -> zeroed structure")


def case_6_visualization_response(client, token) -> None:
    """response_distribution -> 合法 PNG base64"""
    _seed()
    r = client.get("/api/v1/data/visualization/response_distribution", headers=_hdr(token))
    data = r.get_json()["data"]
    assert data["chart_type"] == "response_distribution"
    assert data["format"] == "png"
    assert _is_valid_png_b64(data["image_base64"]), "image_base64 不是合法 PNG"
    print(f"[6] visualization/response_distribution -> PNG OK, b64 len={len(data['image_base64'])}")


def case_7_visualization_gender_response(client, token) -> None:
    """gender_response -> PNG"""
    r = client.get("/api/v1/data/visualization/gender_response", headers=_hdr(token))
    data = r.get_json()["data"]
    assert data["chart_type"] == "gender_response"
    assert _is_valid_png_b64(data["image_base64"])
    print(f"[7] visualization/gender_response -> PNG OK, b64 len={len(data['image_base64'])}")


def case_8_visualization_age(client, token) -> None:
    """age_distribution -> PNG"""
    r = client.get("/api/v1/data/visualization/age_distribution", headers=_hdr(token))
    data = r.get_json()["data"]
    assert _is_valid_png_b64(data["image_base64"])
    print(f"[8] visualization/age_distribution -> PNG OK, b64 len={len(data['image_base64'])}")


def case_9_visualization_premium(client, token) -> None:
    """premium_distribution -> PNG"""
    r = client.get("/api/v1/data/visualization/premium_distribution", headers=_hdr(token))
    data = r.get_json()["data"]
    assert _is_valid_png_b64(data["image_base64"])
    print(f"[9] visualization/premium_distribution -> PNG OK, b64 len={len(data['image_base64'])}")


def case_10_visualization_unknown(client, token) -> None:
    """未知 chart_type -> 1001"""
    r = client.get("/api/v1/data/visualization/foobar", headers=_hdr(token))
    assert r.status_code == 400
    body = r.get_json()
    assert body["code"] == 1001
    assert "foobar" in body["message"]
    print(f"[10] visualization/foobar -> 1001, message 含未知类型名")


def main() -> int:
    app = create_app()
    client = app.test_client()
    token = _admin_token(client)

    _seed()  # 起点：25 行

    cases = [
        ("unauthorized",     lambda: case_1_unauthorized(client)),
        ("stats_25",         lambda: case_2_statistics_on_25_rows(client, token)),
        ("stats_empty",      lambda: case_3_statistics_empty(client, token)),
        ("quality_25",       lambda: case_4_quality_on_25_rows(client, token)),
        ("quality_empty",    lambda: case_5_quality_empty(client, token)),
        ("viz_response",     lambda: case_6_visualization_response(client, token)),
        ("viz_gender_resp",  lambda: case_7_visualization_gender_response(client, token)),
        ("viz_age",          lambda: case_8_visualization_age(client, token)),
        ("viz_premium",      lambda: case_9_visualization_premium(client, token)),
        ("viz_unknown",      lambda: case_10_visualization_unknown(client, token)),
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
    print(f"P1-03 smoke: {len(cases)} / {len(cases)} cases passed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
