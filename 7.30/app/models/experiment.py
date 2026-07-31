"""实验记录表（experiments）。

字段对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md §3.2`。

`params` 以 JSON 字符串存储 ROC/CM/特征重要性等可视化数据，供前端按需复原。
`is_best=True` 唯一标记当前最佳模型；`is_best` 有索引以加速 `/model/best` 查询。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    roc_auc: Mapped[float] = mapped_column(Float, nullable=False)
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_best: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Experiment {self.model_name} auc={self.roc_auc:.4f} best={self.is_best}>"
