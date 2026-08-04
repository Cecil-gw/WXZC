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

    # -------- 查询构造（分层约定：查询在 Model，编排在 Service） --------

    @staticmethod
    def paginate(
        db,
        page: int = 1,
        per_page: int = 50,
        status: Optional[str] = None,
        created_by: Optional[int] = None,
    ):
        """分页查询邮件记录。返回 (items, total)。

        `created_by` 非 None 时只取该用户的记录 —— 普通用户的数据隔离靠这个
        参数实现，admin 传 None 看全部（docs/03 §4.5）。

        排序 `created_at desc, id desc`：最新生成的在前，同一时间戳用 id 兜底
        保证翻页稳定。
        """
        q = db.query(EmailRecord)
        if status:
            q = q.filter(EmailRecord.status == status)
        if created_by is not None:
            q = q.filter(EmailRecord.created_by == created_by)
        total = q.count()
        items = (
            q.order_by(EmailRecord.created_at.desc(), EmailRecord.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return items, total

    def to_dict(self, with_content: bool = False, username: Optional[str] = None):
        """序列化。

        列表页不返回 content（docs §4.5 的字段清单里没有它）—— 邮件正文是
        HTML 全文，50 条一页会让响应体膨胀好几百 KB。详情页才带正文。
        """
        data = {
            "id": self.id,
            "customer_id": self.customer_id,
            "subject": self.subject,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if with_content:
            data["content"] = self.content
            data["created_by"] = self.created_by
            data["updated_at"] = self.updated_at.isoformat() if self.updated_at else None
        if username is not None:
            data["created_by_username"] = username
        return data
