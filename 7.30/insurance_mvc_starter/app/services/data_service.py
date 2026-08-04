"""数据业务服务层（Service 层）。

归属：app/services/data_service.py —— 数据相关业务编排。

思路：
- Service 层是路由层与模型/工具层之间的桥梁；
- 负责编排工具函数（Excel 解析）与模型操作（数据库读写）；
- upload 方法：解析 Excel → 校验 → 批量入库；
- list_customers 方法：分页查询客户。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.utils.data_processor import (
    check_required_columns,
    compute_quality_report,
    parse_excel,
    validate_rows,
)


_BATCH_SIZE: int = 5000
_MAX_PER_PAGE: int = 200


def bulk_insert(db: Session, rows: List[Dict[str, Any]], batch_size: int = _BATCH_SIZE) -> int:
    """先清空 customers，再按 batch_size 批量插入。"""
    db.query(Customer).delete()
    total = len(rows)
    for i in range(0, total, batch_size):
        db.bulk_insert_mappings(Customer, rows[i : i + batch_size])
    db.commit()
    return total


class DataService:
    """数据业务层。"""

    @staticmethod
    def upload(db: Session, file_storage: Any) -> Dict[str, Any]:
        """编排：parse_excel → check → compute_quality_report → validate_rows → bulk_insert。"""
        result = parse_excel(file_storage)
        quality = compute_quality_report(result["df"])
        imported_count = bulk_insert(db, result["valid_rows"])
        return {
            "imported_count": imported_count,
            "quality_report": quality,
            "valid_count": result["valid_count"],
            "error_count": result["error_count"],
            "errors": result["errors"],
        }

    @staticmethod
    def list_customers(
        db: Session,
        page: int = 1,
        per_page: int = 50,
        gender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """客户分页查询。"""
        if per_page > _MAX_PER_PAGE:
            per_page = _MAX_PER_PAGE
        if per_page < 1:
            per_page = 1
        if page < 1:
            page = 1
        items, total = Customer.paginate(db, page=page, per_page=per_page, gender=gender)
        pages = (total + per_page - 1) // per_page if total > 0 else 0
        return {
            "items": [c.to_dict() for c in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }