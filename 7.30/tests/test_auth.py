"""认证模块测试。

覆盖注册 / 登录 / 鉴权 / 角色权限 / Token 过期 等场景。
"""

from __future__ import annotations

import time

from jose import jwt

from app.core.config import settings


class TestRegister:
    """POST /api/v1/auth/register"""

    def test_register_success(self, client):
        """注册成功返回 code=0 和 token。"""
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "newuser", "password": "password123"},
        )
        data = resp.get_json()
        assert data["code"] == 0
        assert "access_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
        assert data["data"]["user"]["username"] == "newuser"
        assert data["data"]["user"]["role"] == "user"

    def test_register_duplicate(self, client, admin_user):
        """重复用户名返回 code=1004。"""
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": admin_user["username"], "password": "password123"},
        )
        data = resp.get_json()
        assert data["code"] == 1004

    def test_register_validation(self, client):
        """密码太短返回 code=1001。"""
        resp = client.post(
            "/api/v1/auth/register",
            json={"username": "baduser", "password": ""},
        )
        data = resp.get_json()
        assert data["code"] == 1001


class TestLogin:
    """POST /api/v1/auth/login"""

    def test_login_success_admin(self, client):
        """admin 登录成功。"""
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "username": settings.DEFAULT_ADMIN_USERNAME,
                "password": settings.DEFAULT_ADMIN_PASSWORD,
            },
        )
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["user"]["role"] == "admin"
        assert "access_token" in data["data"]

    def test_login_success_user(self, client, regular_user):
        """user 登录成功。"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": regular_user["username"], "password": "user123"},
        )
        data = resp.get_json()
        assert data["code"] == 0
        assert data["data"]["user"]["role"] == "user"

    def test_login_wrong_password(self, client, regular_user):
        """密码错误返回 code=1002。"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": regular_user["username"], "password": "wrongpass"},
        )
        data = resp.get_json()
        assert data["code"] == 1002

    def test_login_no_user(self, client):
        """用户不存在返回 code=1002。"""
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "password"},
        )
        data = resp.get_json()
        assert data["code"] == 1002


class TestAuthorization:
    """鉴权与角色权限"""

    def test_unauthorized_access(self, client):
        """无 token 访问返回 401。"""
        resp = client.get("/api/v1/data/customers")
        assert resp.status_code == 401

    def test_admin_only_forbidden(self, client, user_token):
        """user 访问 admin-only 接口返回 403。"""
        resp = client.post(
            "/api/v1/model/train",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"models": ["logistic_regression"]},
        )
        assert resp.status_code == 403

    def test_token_expired(self, client, admin_user):
        """过期 token 返回 401。"""
        expired_payload = {
            "sub": str(admin_user["id"]),
            "role": admin_user["role"],
            "username": admin_user["username"],
            "iat": int(time.time()) - 200,
            "exp": int(time.time()) - 100,
        }
        expired_token = jwt.encode(
            expired_payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM,
        )
        resp = client.get(
            "/api/v1/data/customers",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401
