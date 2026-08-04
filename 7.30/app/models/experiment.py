"""实验记录表（experiments）。

字段对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md §3.2`。

`params` 以 JSON 字符串存储 ROC/CM/特征重要性等可视化数据，供前端按需复原。
`is_best=True` 唯一标记当前最佳模型；`is_best` 有索引以加速 `/model/best` 查询。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

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

    # ----------------------------------------------------------------
    # P1-05: pagination + serialization
    # ----------------------------------------------------------------

    @staticmethod
    def paginate(db, page: int = 1, per_page: int = 50, model_name=None):
        """按 model_name 过滤并分页。返回 (items, total)。

        排序：created_at 倒序（最新实验在前），同一时间戳再按 id 倒序保证稳定。
        """
        q = db.query(Experiment)
        if model_name:
            q = q.filter(Experiment.model_name == model_name)
        total = q.count()
        items = (
            q.order_by(Experiment.created_at.desc(), Experiment.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def to_dict(self, parse_params: bool = True):
        """序列化为 dict，字段对齐 `docs/03_API接口文档.md §3.2`。

        `params` 落库是 JSON 字符串；`parse_params=True` 时反序列化成对象，
        便于前端与 P1-08 可视化接口直接取用。解析失败降级为 None，不让脏数据打断分页。
        """
        params: Any = self.params
        if parse_params and self.params:
            try:
                params = json.loads(self.params)
            except (TypeError, ValueError):
                params = None
        return {
            "id": self.id,
            "model_name": self.model_name,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "roc_auc": self.roc_auc,
            "params": params,
            "model_path": self.model_path,
            "is_best": self.is_best,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
