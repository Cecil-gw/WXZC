"""操作日志表（operation_logs）。

字段对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md §5.1`。

`action` ∈ {model_training, prediction, model_import, email_generation, email_update,
email_mark, email_delete}，有索引用于过滤。
`details` 以 JSON 字符串存储操作上下文。
"""

from __future__ import annotations

import json

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False, index=True)

    # -------- 关系 --------
    user: Mapped["User"] = relationship(back_populates="operation_logs")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<OperationLog user={self.user_id} action={self.action}>"

    # -------- 查询构造（分层约定：查询在 Model） --------

    ALLOWED_ACTIONS = (
        "model_training",
        "prediction",
        "model_import",
        "email_generation",
        "email_update",
        "email_mark",
        "email_delete",
    )

    @staticmethod
    def paginate(
        db,
        page: int = 1,
        per_page: int = 50,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
    ):
        """按 user_id / action 过滤并分页。返回 (items, total)。

        排序 `created_at desc, id desc`：审计场景关心最近发生了什么。
        """
        q = db.query(OperationLog)
        if user_id is not None:
            q = q.filter(OperationLog.user_id == user_id)
        if action:
            q = q.filter(OperationLog.action == action)
        total = q.count()
        items = (
            q.order_by(OperationLog.created_at.desc(), OperationLog.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def to_dict(self, username: Optional[str] = None):
        """序列化。`details` 落库是 JSON 字符串，这里反序列化成对象。

        解析失败降级为原始字符串而非抛错 —— 审计日志的价值在于「能看到」，
        不该因为某条记录的 details 格式异常就让整页查询失败。
        """
        details: object = self.details
        if self.details:
            try:
                details = json.loads(self.details)
            except (TypeError, ValueError):
                details = self.details
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "details": details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if username is not None:
            data["username"] = username
        return data
