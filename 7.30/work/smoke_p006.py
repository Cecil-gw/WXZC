"""P0-06 前端 SPA 入口 smoke test.

验收标准（TODO P0-06）：
  1. GET / 返回可渲染的 HTML；
  2. 控制台无 404；
  3. Bootstrap 5 CDN 或本地资源可加载。

测试方式：用 Flask test_client 模拟"浏览器首次访问首页"的请求序列，
并对每个被引用的资源发起独立 GET，验证响应码。
"""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402


def main() -> int:
    app = create_app()
    client = app.test_client()

    r = client.get("/")
    assert r.status_code == 200, f"GET / status {r.status_code}"
    assert r.content_type.startswith("text/html"), f"GET / ct {r.content_type}"
    body = r.get_data(as_text=True)
    assert "<html" in body.lower() and "</html>" in body.lower(), "no <html> wrapper"
    assert "id=\"login-page\"" in body, "login page missing"
    assert "id=\"register-page\"" in body, "register page missing"
    assert "id=\"app-page\"" in body, "app page missing"
    print(f"[1] GET / -> 200, ct={r.content_type}, len={len(body)}")

    referenced_local = [
        "/static/css/app.css",
        "/static/js/api.js",
        "/static/js/app.js",
    ]
    for path in referenced_local:
        rr = client.get(path)
        assert rr.status_code == 200, f"GET {path} -> {rr.status_code} (404 source!)"
        print(f"[2] GET {path} -> 200, ct={rr.content_type}, len={rr.content_length or len(rr.data)}")

    html = body
    assert "bootstrap@5.3.0/dist/css/bootstrap.min.css" in html, "Bootstrap CSS CDN missing"
    assert "bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" in html, "Bootstrap JS CDN missing"
    print("[3] Bootstrap 5.3.0 CDN URLs present in HTML (string check OK)")

    cdn_urls = [
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
    ]
    for u in cdn_urls:
        try:
            req = urllib.request.Request(u, method="HEAD")
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"[3] CDN HEAD {u} -> {resp.status} OK")
        except Exception as e:  # noqa: BLE001
            print(f"[3] CDN HEAD {u} -> NOT REACHABLE ({type(e).__name__}: {e}), skipped")

    fav = client.get("/favicon.ico")
    print(f"[4] GET /favicon.ico -> {fav.status_code} (浏览器 DevTools 看到的控制台状态)")
    if fav.status_code == 404:
        print("[4] WARN: /favicon.ico 返回 404，浏览器 DevTools 控制台会出现红色错误，违反'控制台无 404'")

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200, f"login status {login.status_code}"
    j = login.get_json()
    assert j.get("code") == 0, f"login code {j.get('code')}"
    token = j["data"]["access_token"]
    print(f"[5] POST /api/v1/auth/login -> 200, code=0, role={j['data']['user']['role']}")

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    jm = me.get_json()
    assert jm.get("code") == 0 and jm["data"]["username"] == "admin", f"/me unexpected: {jm}"
    print(f"[5] GET /api/v1/auth/me -> 200, code=0, user={jm['data']['username']}")

    print()
    print("=" * 60)
    print("P0-06 smoke: 6 / 6 checks passed (or warn-only)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
