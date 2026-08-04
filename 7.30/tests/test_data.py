"""数据接口测试。

覆盖 Excel 上传 / 客户分页查询 / 数据统计 / 鉴权 等场景。
"""

from __future__ import annotations

import io

from openpyxl import Workbook


REQUIRED_COLUMNS = [
    "id",
    "Gender",
    "Age",
    "Driving_License",
    "Region_Code",
    "Previously_Insured",
    "Vehicle_Age",
    "Vehicle_Damage",
    "Annual_Premium",
    "Policy_Sales_Channel",
    "Vintage",
    "Response",
]


def _make_excel(rows: int = 10, missing_col: str | None = None) -> bytes:
    """生成测试用 xlsx 字节流。

    Parameters
    ----------
    rows : int
        数据行数（不含表头）。
    missing_col : str or None
        若指定，则从表头中移除该列（模拟缺列场景）。
    """
    wb = Workbook()
    ws = wb.active

    headers = [c for c in REQUIRED_COLUMNS if c != missing_col]
    ws.append(headers)

    for i in range(rows):
        row = []
        for col in headers:
            if col == "id":
                row.append(i + 1)
            elif col == "Gender":
                row.append("Male" if i % 2 == 0 else "Female")
            elif col == "Age":
                row.append(25 + i % 40)
            elif col == "Driving_License":
                row.append(1 if i % 3 != 0 else 0)
            elif col == "Region_Code":
                row.append(float(1000 + i * 10))
            elif col == "Previously_Insured":
                row.append(0 if i % 2 == 0 else 1)
            elif col == "Vehicle_Age":
                row.append(["< 1 Year", "1-2 Year", "> 2 Years"][i % 3])
            elif col == "Vehicle_Damage":
                row.append("No" if i % 3 == 0 else "Yes")
            elif col == "Annual_Premium":
                row.append(float(20000 + i * 500))
            elif col == "Policy_Sales_Channel":
                row.append(float(26.0))
            elif col == "Vintage":
                row.append(100 + i)
            elif col == "Response":
                row.append(1 if i % 5 == 0 else 0)
            else:
                row.append("")
        ws.append(row)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestUpload:
    """POST /api/v1/data/upload"""

    def test_upload_success(self, client, admin_token):
        """上传合法 xlsx 成功。"""
        data = _make_excel(rows=10)
        resp = client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["imported_count"] == 10
        assert "quality_report" in body["data"]

    def test_upload_no_file(self, client, admin_token):
        """无文件返回 1001。"""
        resp = client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            content_type="multipart/form-data",
        )
        body = resp.get_json()
        assert body["code"] == 1001

    def test_upload_wrong_ext(self, client, admin_token):
        """错扩展名返回 1001。"""
        data = _make_excel(rows=3)
        resp = client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.csv")},
            content_type="multipart/form-data",
        )
        body = resp.get_json()
        assert body["code"] == 1001

    def test_upload_missing_columns(self, client, admin_token):
        """缺列返回 1001。"""
        data = _make_excel(rows=3, missing_col="Annual_Premium")
        resp = client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        body = resp.get_json()
        assert body["code"] == 1001


class TestCustomersList:
    """GET /api/v1/data/customers"""

    def test_customers_list(self, client, admin_token):
        """分页查询成功。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        resp = client.get(
            "/api/v1/data/customers?page=1&per_page=5",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["total"] == 10
        assert len(body["data"]["items"]) == 5
        assert body["data"]["page"] == 1
        assert body["data"]["pages"] == 2

    def test_customers_filter(self, client, admin_token):
        """按性别筛选。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        resp = client.get(
            "/api/v1/data/customers?gender=Male",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        for item in body["data"]["items"]:
            assert item["gender"] == "Male"

    def test_customers_unauthorized(self, client):
        """未认证被拒。"""
        resp = client.get("/api/v1/data/customers")
        assert resp.status_code == 401


class TestStatistics:
    """GET /api/v1/data/statistics"""

    def test_statistics(self, client, admin_token):
        """统计数据接口。"""
        data = _make_excel(rows=10)
        client.post(
            "/api/v1/data/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            data={"file": (io.BytesIO(data), "test.xlsx")},
            content_type="multipart/form-data",
        )
        resp = client.get(
            "/api/v1/data/statistics",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = resp.get_json()
        assert body["code"] == 0
        assert body["data"]["total"] == 10
        assert "gender_distribution" in body["data"]
        assert "response_distribution" in body["data"]
        assert "age_stats" in body["data"]
