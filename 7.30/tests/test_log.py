"""操作日志测试。

覆盖日志查询 / 权限控制 / 过滤 等场景。
日志接口仅 admin 可访问。
"""

from __future__ import annotations

import io

from tests.test_data import _make_excel


class TestLogs:
    """GET /api/v1/logs"""

    def test_list_logs_admin(self, client, admin_token):
        """admin 查询日志成功。"""
        data = _make_excel(rows=25)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        client.post(
            "/api/v1/model/train",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"models": ["logistic_regression"]},
        )
        resp = client.get(
            "/api/v1/logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["total"] >= 1

    def test_list_logs_user_forbidden(self, client, user_token):
        """user 被拒。"""
        resp = client.get(
            "/api/v1/logs",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert resp.status_code == 403

    def test_logs_filter_action(self, client, admin_token):
        """按 action 过滤。"""
        data = _make_excel(rows=25)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        client.post(
            "/api/v1/model/train",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"models": ["logistic_regression"]},
        )
        resp = client.get(
            "/api/v1/logs?action=model_training",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        for item in body["data"]["items"]:
            assert item["action"] == "model_training"

    def test_logs_filter_user(self, client, admin_token, admin_user):
        """按 user_id 过滤。"""
        data = _make_excel(rows=25)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        client.post(
            "/api/v1/model/train",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"models": ["logistic_regression"]},
        )
        resp = client.get(
            f"/api/v1/logs?user_id={admin_user['id']}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        for item in body["data"]["items"]:
            assert item["user_id"] == admin_user["id"]
