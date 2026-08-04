"""认证 API（路由层）。

归属：app/api/v1/auth.py —— /api/v1/auth 下的认证路由。
"""

from __future__ import annotations

from flask import Blueprint, request
from pydantic import ValidationError

from app.core.database import get_db
from app.core.response import (
    CODE_PARAM_ERROR,
    CODE_USERNAME_EXISTS,
    CODE_UNAUTHORIZED,
    BizException,
    success,
)
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def _validate(schema_cls, data):
    """Pydantic 校验并统一转 BizException(1001)。"""
    try:
        return schema_cls(**data)
    except ValidationError as e:
        raise BizException(CODE_PARAM_ERROR, f"参数校验错误: {e}", 400) from e


@bp.route("/register", methods=["POST"])
def register():
    """POST /auth/register：注册新用户，角色强制 user。"""
    body = _validate(RegisterRequest, request.get_json(silent=True) or {})
    db = get_db()
    existing = db.query(User).filter_by(username=body.username).first()
    if existing is not None:
        raise BizException(CODE_USERNAME_EXISTS, "用户名已存在", 400)
    user = User.register(db, body.username, body.password, role="user")
    token = create_access_token(user.id, user.role, user.username)
    return success({
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "role": user.role},
    })


@bp.route("/login", methods=["POST"])
def login():
    """POST /auth/login：校验用户名密码，签发 JWT。"""
    body = _validate(LoginRequest, request.get_json(silent=True) or {})
    db = get_db()
    user = User.verify_login(db, body.username, body.password)
    if user is None:
        raise BizException(CODE_UNAUTHORIZED, "用户名或密码错误", 401)
    token = create_access_token(user.id, user.role, user.username)
    return success({
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "role": user.role},
    })
