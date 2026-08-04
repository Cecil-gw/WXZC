"""用户模型（Model 层）。

归属：app/models/user.py —— ORM 用户表。

思路：
- 角色仅 admin/user 两种，注册时服务端硬编码为 user，防越权；
- 提供类方法 register / verify_login 供业务层调用。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.security import hash_password, verify_password


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role}>"

    @classmethod
    def register(cls, db, username: str, password: str, role: str = "user") -> "User":
        """注册新用户。"""
        user = cls(
            username=username,
            password_hash=hash_password(password),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def verify_login(cls, db, username: str, password: str) -> Optional["User"]:
        """校验用户名密码。成功返回 User，失败返回 None。"""
        user = db.query(cls).filter_by(username=username).first()
        if user is None:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user