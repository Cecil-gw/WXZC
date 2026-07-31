"""操作日志表（operation_logs）。

字段对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md §5.1`。

`action` ∈ {model_training, prediction, model_import, email_generation, email_update,
email_mark, email_delete}，有索引用于过滤。
`details` 以 JSON 字符串存储操作上下文。
"""

from __future__ import annotations

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
