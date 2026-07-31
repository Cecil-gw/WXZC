"""客户表（customers）。

字段对齐 `docs/01_PRD_产品需求文档.md §5.1` 与
`docs/04_技术框架方案.md §7`。

`predicted_prob` 由 ML 预测阶段回写，解耦训练与营销两条链路。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    # 直接使用数据集中的 id 作为主键（上传时覆盖旧数据）
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    gender: Mapped[str] = mapped_column(String(16), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    driving_license: Mapped[int] = mapped_column(Integer, nullable=False)
    region_code: Mapped[float] = mapped_column(Float, nullable=False)
    previously_insured: Mapped[int] = mapped_column(Integer, nullable=False)
    vehicle_age: Mapped[str] = mapped_column(String(32), nullable=False)
    vehicle_damage: Mapped[str] = mapped_column(String(8), nullable=False)
    annual_premium: Mapped[float] = mapped_column(Float, nullable=False)
    policy_sales_channel: Mapped[float] = mapped_column(Float, nullable=False)
    vintage: Mapped[int] = mapped_column(Integer, nullable=False)
    response: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    predicted_prob: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, default=None, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # -------- 关系 --------
    email_records: Mapped[List["EmailRecord"]] = relationship(  # type: ignore[name-defined]
        back_populates="customer",
    )

    def __repr__(self) -> str:
        return f"<Customer id={self.id} response={self.response}>"

    # ----------------------------------------------------------------
    # P1-02: pagination + serialization
    # ----------------------------------------------------------------

    @staticmethod
    def paginate(
        db,
        page: int = 1,
        per_page: int = 50,
        gender=None,
        age_min=None,
        age_max=None,
        previously_insured=None,
        keyword=None,
    ):
        """按过滤条件分页查询。返回 (items, total)。"""
        q = db.query(Customer)
        if gender:
            q = q.filter(Customer.gender == gender)
        if age_min is not None:
            q = q.filter(Customer.age >= age_min)
        if age_max is not None:
            q = q.filter(Customer.age <= age_max)
        if previously_insured is not None:
            q = q.filter(Customer.previously_insured == previously_insured)
        if keyword:
            try:
                kid = int(keyword)
            except (TypeError, ValueError):
                kid = None
            if kid is not None:
                q = q.filter(Customer.id == kid)
        total = q.count()
        items = (
            q.order_by(Customer.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def to_dict(self):
        """序列化为 dict，供 JSON 响应。"""
        return {
            "id": self.id,
            "gender": self.gender,
            "age": self.age,
            "driving_license": self.driving_license,
            "region_code": self.region_code,
            "previously_insured": self.previously_insured,
            "vehicle_age": self.vehicle_age,
            "vehicle_damage": self.vehicle_damage,
            "annual_premium": self.annual_premium,
            "policy_sales_channel": self.policy_sales_channel,
            "vintage": self.vintage,
            "response": self.response,
            "predicted_prob": self.predicted_prob,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
