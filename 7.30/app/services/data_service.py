"""数据业务层：bulk_insert + DataService。

P1-01-3 bulk_insert：清空 + 批量插入
P1-01-4 DataService.upload：编排 parse + quality + bulk_insert
P1-01-5 API 路由层调 DataService.upload
P1-02-?  DataService.list_customers：分页 + 过滤
P1-03    DataService.statistics / quality / visualization

设计要点：
- 纯业务层函数（不依赖 Flask），便于单测与 CLI 复用；
- bulk_insert 沿用 Gate Review WARNING 5-A 的"清空再写"策略；
- 不写 OperationLog，对齐 P0 Gate Review WARNING 7-C（P1-04 之后统一建 OperationLogService）。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.core.response import BizException
from app.models.customer import Customer
from app.utils.data_processor import (
    check_required_columns,
    compute_quality_report,
    read_excel_to_df,
    validate_rows,
)
from app.utils.visualizer import CHART_FUNCS


_BATCH_SIZE: int = 5000
_MAX_PER_PAGE: int = 200


# ====================================================================
# P1-01-3：批量入库
# ====================================================================

def bulk_insert(
    db: Session,
    rows: List[Dict[str, Any]],
    batch_size: int = _BATCH_SIZE,
) -> int:
    """先清空 customers，再按 batch_size 批量插入。"""
    db.query(Customer).delete()
    total = len(rows)
    for i in range(0, total, batch_size):
        db.bulk_insert_mappings(Customer, rows[i : i + batch_size])
    db.commit()
    return total


# ====================================================================
# Service 编排：P1-01 / P1-02 / P1-03
# ====================================================================

class DataService:
    """数据业务层。"""

    # ----- P1-01：Excel 上传 -----

    @staticmethod
    def upload(db: Session, file_storage: Any) -> Dict[str, Any]:
        """编排：read_excel_to_df -> check -> compute_quality_report -> validate_rows -> bulk_insert。"""
        df = read_excel_to_df(file_storage)
        check_required_columns(df)
        quality = compute_quality_report(df)
        validation = validate_rows(df)
        imported_count = bulk_insert(db, validation["rows"])
        return {
            "imported_count": imported_count,
            "quality_report": quality,
        }

    # ----- P1-02：客户分页查询 -----

    @staticmethod
    def list_customers(
        db: Session,
        page: int = 1,
        per_page: int = 50,
        gender: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        previously_insured: Optional[int] = None,
        keyword: Optional[str] = None,
    ) -> Dict[str, Any]:
        """客户分页查询（按 docs/03 §2.2）。"""
        if per_page > _MAX_PER_PAGE:
            per_page = _MAX_PER_PAGE
        if per_page < 1:
            per_page = 1
        if page < 1:
            page = 1
        items, total = Customer.paginate(
            db,
            page=page,
            per_page=per_page,
            gender=gender,
            age_min=age_min,
            age_max=age_max,
            previously_insured=previously_insured,
            keyword=keyword,
        )
        pages = (total + per_page - 1) // per_page if total > 0 else 0
        return {
            "items": [c.to_dict() for c in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    # ----- P1-03：统计 -----

    @staticmethod
    def statistics(db: Session) -> Dict[str, Any]:
        """GET /data/statistics（docs/03 §2.3）。"""
        total = db.query(Customer).count()
        if total == 0:
            return {
                "total": 0,
                "gender_distribution": {"Male": 0, "Female": 0},
                "response_distribution": {"0": 0, "1": 0},
                "age_stats": {"min": 0, "max": 0, "avg": 0.0},
            }
        rows = db.query(Customer.gender, Customer.response, Customer.age).all()
        gender_dist: Dict[str, int] = {}
        response_dist: Dict[str, int] = {}
        ages: List[int] = []
        for g, r, a in rows:
            gender_dist[g] = gender_dist.get(g, 0) + 1
            response_dist[str(int(r))] = response_dist.get(str(int(r)), 0) + 1
            ages.append(int(a))
        return {
            "total": total,
            "gender_distribution": gender_dist,
            "response_distribution": response_dist,
            "age_stats": {
                "min": min(ages),
                "max": max(ages),
                "avg": round(sum(ages) / len(ages), 2),
            },
        }

    # ----- P1-03：质量报告 -----

    @staticmethod
    def quality(db: Session) -> Dict[str, Any]:
        """GET /data/quality（docs/03 §2.4）。从 DB 读全量回 DataFrame，复用 P1-01-2 的 compute_quality_report。"""
        rows = [c.to_dict() for c in db.query(Customer).all()]
        if not rows:
            return {
                "total_rows": 0,
                "total_cols": 0,
                "missing_values": {},
                "duplicates": 0,
                "dtypes": {},
            }
        df = pd.DataFrame(rows)
        return compute_quality_report(df)

    # ----- P1-03：EDA 可视化 -----

    @staticmethod
    def visualization(db: Session, chart_type: str) -> Dict[str, Any]:
        """GET /data/visualization/{chart_type}（docs/03 §2.5）。"""
        if chart_type not in CHART_FUNCS:
            raise BizException(
                1001, f"未知图表类型: {chart_type}，可选 {list(CHART_FUNCS.keys())}", 400
            )
        rows = [c.to_dict() for c in db.query(Customer).all()]
        df = pd.DataFrame(rows) if rows else pd.DataFrame()
        image_base64 = CHART_FUNCS[chart_type](df)
        return {
            "chart_type": chart_type,
            "image_base64": image_base64,
            "format": "png",
        }