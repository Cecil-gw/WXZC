"""认证业务逻辑：登录、注册。

设计对齐 `docs/01_PRD_产品需求文档.md §3.1` 与 `docs/03_API接口文档.md §1.1-1.2`。

安全要点：
- 登录失败统一返回"用户名或密码错误"，防止用户名枚举撞库；
- 注册接口不接收 role，服务端硬编码为 `user`；
- 密码使用 bcrypt 哈希存储。
"""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.response import (
    CODE_UNAUTHORIZED,
    CODE_USERNAME_EXISTS,
    BizException,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User


class AuthService:
    """认证服务（纯函数，无状态，不依赖 Flask）。"""

    @staticmethod
    def login(db: Session, username: str, password: str) -> Dict[str, Any]:
        """校验用户名密码，签发 JWT。失败抛 `BizException(1002)`。"""
        user = db.query(User).filter_by(username=username).first()
        if user is None or not verify_password(password, user.password_hash):
            raise BizException(CODE_UNAUTHORIZED, "用户名或密码错误", 401)
        token = create_access_token(user.id, user.role, user.username)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_SECONDS,
            "user": {"id": user.id, "username": user.username, "role": user.role},
        }

    @staticmethod
    def register(db: Session, username: str, password: str) -> Dict[str, Any]:
        """注册新用户，角色强制为 user。重名抛 `BizException(1004)`。"""
        existing = db.query(User).filter_by(username=username).first()
        if existing is not None:
            raise BizException(CODE_USERNAME_EXISTS, "用户名已存在", 400)
        user = User(
            username=username,
            password_hash=hash_password(password),
            role="user",
        )
        db.add(user)
        db.commit()
        token = create_access_token(user.id, user.role, user.username)
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_SECONDS,
            "user": {"id": user.id, "username": user.username, "role": user.role},
        }
