"""邮件接口测试。

覆盖邮件生成 / Prompt 模板管理 / 邮件记录 CRUD 等场景。
LLM_API_KEY 置空，所有生成走降级路径（status=failed），不依赖外部服务。
"""

from __future__ import annotations

import io

from tests.test_data import _make_excel


class TestEmailGenerate:
    """POST /api/v1/email/generate"""

    def test_generate_no_key(self, client, admin_token):
        """无 LLM key 降级：生成邮件但状态为 failed。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        resp = client.post(
            "/api/v1/email/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"customer_ids": [1, 2, 3]},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["failed_count"] == 3
        assert body["data"]["generated_count"] == 0

    def test_generate_with_ids(self, client, admin_token):
        """指定客户生成。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        resp = client.post(
            "/api/v1/email/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"customer_ids": [1, 2]},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert len(body["data"]["records"]) == 2


class TestPrompt:
    """GET/PUT /api/v1/email/prompt"""

    def test_prompt_get(self, client, admin_token):
        """获取当前 prompt。"""
        resp = client.get(
            "/api/v1/email/prompt",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert "content" in body["data"]

    def test_prompt_put(self, client, admin_token):
        """更新 prompt。"""
        new_content = (
            "你是保险营销专家。客户画像：性别{gender}，年龄{age}岁。\n"
            "请生成营销邮件，返回 JSON：{{\"subject\":\"主题\",\"content\":\"正文\"}}"
        )
        resp = client.put(
            "/api/v1/email/prompt",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"content": new_content, "name": "test"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["name"] == "test"


class TestEmailRecords:
    """邮件记录 CRUD"""

    def test_list_records(self, client, admin_token):
        """邮件记录列表。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        client.post(
            "/api/v1/email/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"customer_ids": [1, 2]},
        )
        resp = client.get(
            "/api/v1/email/records",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["total"] >= 2

    def test_record_detail(self, client, admin_token):
        """记录详情。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        client.post(
            "/api/v1/email/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"customer_ids": [1]},
        )
        resp = client.get(
            "/api/v1/email/records",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        record_id = resp.get_json()["data"]["items"][0]["id"]
        detail_resp = client.get(
            f"/api/v1/email/records/{record_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = detail_resp.get_json()
        assert body["code"] == 0
        assert "content" in body["data"]

    def test_record_update(self, client, admin_token):
        """更新记录。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        client.post(
            "/api/v1/email/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"customer_ids": [1]},
        )
        resp = client.get(
            "/api/v1/email/records",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        record_id = resp.get_json()["data"]["items"][0]["id"]
        update_resp = client.put(
            f"/api/v1/email/records/{record_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email_subject": "更新的主题"},
        )
        body = update_resp.get_json()
        assert body["code"] == 0
        assert body["data"]["subject"] == "更新的主题"

    def test_record_delete(self, client, admin_token):
        """删除记录。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        client.post(
            "/api/v1/email/generate",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"customer_ids": [1]},
        )
        resp = client.get(
            "/api/v1/email/records",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        record_id = resp.get_json()["data"]["items"][0]["id"]
        delete_resp = client.delete(
            f"/api/v1/email/records/{record_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = delete_resp.get_json()
        assert body["code"] == 0
        assert body["data"]["success"] is True
