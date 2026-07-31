"""Prompt 模板表（prompt_templates）。

字段对齐 `docs/04_技术框架方案.md §7` 与 `docs/03_API接口文档.md §4.3-4.4`。

`is_active=True` 标记当前生效模板（唯一约束或业务层保证唯一）。
`content` 含 `{gender}`、`{age}` 等占位符，运行时由 `str.format` 填充。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<PromptTemplate {self.name} active={self.is_active}>"
