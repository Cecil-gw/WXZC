"""模型接口测试。

覆盖实验记录查询 / 最佳模型 / 训练权限 / 预测 / 可视化 等场景。
"""

from __future__ import annotations

import io

from tests.test_data import _make_excel


class TestExperiments:
    """GET /api/v1/model/experiments"""

    def test_list_experiments(self, client, admin_token):
        """实验记录列表。"""
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
            "/api/v1/model/experiments",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["total"] >= 1


class TestBestModel:
    """GET /api/v1/model/best"""

    def test_get_best(self, client, admin_token):
        """获取最佳模型。"""
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
            "/api/v1/model/best",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert "model_name" in body["data"]
        assert "roc_auc" in body["data"]

    def test_get_best_none(self, client, admin_token):
        """无模型返回 3002。"""
        resp = client.get(
            "/api/v1/model/best",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 3002


class TestTrain:
    """POST /api/v1/model/train"""

    def test_train_admin_only(self, client, user_token):
        """训练接口仅 admin，user 访问返回 403。"""
        data = _make_excel(rows=25)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {user_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        resp = client.post(
            "/api/v1/model/train",
            headers={"Authorization": f"Bearer {user_token}"},
            json={"models": ["logistic_regression"]},
        )
        assert resp.status_code == 403


class TestVisualization:
    """GET /api/v1/model/visualization/{chart_type}"""

    def test_visualization_roc(self, client, admin_token):
        """ROC 图。"""
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
            "/api/v1/model/visualization/roc_curve",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["chart_type"] == "roc_curve"
        assert "image_base64" in body["data"]


class TestPredict:
    """POST /api/v1/model/predict"""

    def test_predict_no_model(self, client, admin_token):
        """无模型预测返回 3002。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        resp = client.post(
            "/api/v1/model/predict",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={},
        )
        body = resp.get_json()
        assert body["code"] == 3002
