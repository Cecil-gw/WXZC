"""邮件记录表（email_records）。

字段对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md §4.5-4.10`。

`status` ∈ {generated, sent, failed}，有索引用于过滤。
`created_by` = 生成该邮件的用户 ID（外键关联 users.id）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EmailRecord(Base):
    __tablename__ = "email_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="generated", index=True
    )
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # -------- 关系 --------
    customer: Mapped["Customer"] = relationship(back_populates="email_records")  # type: ignore[name-defined]
    creator: Mapped[Optional["User"]] = relationship(back_populates="email_records")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<EmailRecord id={self.id} customer={self.customer_id} status={self.status}>"
