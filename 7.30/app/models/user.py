"""用户表（users）。

字段对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md §1`。
角色仅 `admin` / `user`，注册时服务端硬编码为 `user`，防越权。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # -------- 关系 --------
    operation_logs: Mapped[List["OperationLog"]] = relationship(  # type: ignore[name-defined]
        back_populates="user",
    )
    email_records: Mapped[List["EmailRecord"]] = relationship(  # type: ignore[name-defined]
        back_populates="creator",
    )

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role}>"
