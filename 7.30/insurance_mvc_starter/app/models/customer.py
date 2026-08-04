"""客户模型（Model 层）。

归属：app/models/customer.py —— ORM 客户表。

思路：
- 字段与主项目 Customer 模型对齐；
- id 直接使用数据集中的 id 作为主键；
- 提供 paginate 类方法供分页查询。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

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
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Customer id={self.id} response={self.response}>"

    def to_dict(self) -> dict:
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
        }

    @staticmethod
    def paginate(
        db,
        page: int = 1,
        per_page: int = 50,
        gender: Optional[str] = None,
    ):
        """分页查询。返回 (items, total)。"""
        q = db.query(Customer)
        if gender:
            q = q.filter(Customer.gender == gender)
        total = q.count()
        items = (
            q.order_by(Customer.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total